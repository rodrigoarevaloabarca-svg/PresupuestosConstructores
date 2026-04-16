import re
import secrets
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, F, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .models import Budget, BudgetItemMaterial, BudgetItemLabor, BudgetPublicToken
from .forms import BudgetForm
from clients.models import Client
from common.tenant import get_tenant_object_or_404
from users.plan_guard import PlanGuard


@login_required
def budget_list(request):
    budgets = (
        Budget.objects
        .filter(contractor=request.user)
        .select_related('client')
        .prefetch_related('material_items', 'labor_items')
        .with_totals()
    )
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    if status:
        budgets = budgets.filter(status=status)
    if q:
        budgets = budgets.filter(
            Q(title__icontains=q) | Q(client__name__icontains=q)
        )
    # Calculate totals for stats bar using DB aggregation (no N+1)
    totals_agg = budgets.aggregate(
        accepted_total=Coalesce(
            Sum(F('_subtotal_materials') + F('_subtotal_labor'), filter=Q(status='aceptado')),
            Value(0), output_field=DecimalField(),
        ),
        sent_total=Coalesce(
            Sum(F('_subtotal_materials') + F('_subtotal_labor'), filter=Q(status='enviado')),
            Value(0), output_field=DecimalField(),
        ),
    )
    accepted_total = int(totals_agg['accepted_total'])
    sent_total = int(totals_agg['sent_total'])

    paginator = Paginator(budgets.order_by('-created_at'), 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)

    return render(request, 'budgets/list.html', {
        'budgets': page_obj,
        'page_obj': page_obj,
        'status': status,
        'q': q,
        'status_choices': Budget._meta.get_field('status').choices,
        'accepted_total': accepted_total,
        'sent_total': sent_total,
    })


@login_required
def budget_create(request):
    allowed, msg = PlanGuard.can_create_budget(request.user)
    if not allowed:
        messages.warning(request, msg)
        return redirect('budget_list')

    clients = Client.objects.filter(contractor=request.user)
    preselect_client = request.GET.get('client', '')

    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                # Re-check limit inside transaction to prevent race condition
                if not request.user.is_pro():
                    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
                    count = Budget.objects.select_for_update().filter(
                        contractor=request.user, created_at__gte=month_start
                    ).count()
                    if count >= settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH:
                        messages.warning(request, 'Límite mensual alcanzado.')
                        return redirect('budget_list')
                budget = form.save(commit=False)
                budget.contractor = request.user
                budget.save()
                _save_line_items(request, budget, 'mat', BudgetItemMaterial, 'un')
                _save_line_items(request, budget, 'lab', BudgetItemLabor, 'gl')
            messages.success(request, f'✅ Presupuesto #{budget.number} creado exitosamente.')
            return redirect('budget_detail', pk=budget.pk)
    else:
        profile = getattr(request.user, 'profile', None)
        initial = {
            'validity_days': profile.budget_validity_days if profile else 15,
            'payment_terms': profile.payment_terms if profile else '',
            'notes': profile.notes_template if profile else '',
        }
        if preselect_client:
            initial['client'] = preselect_client
        form = BudgetForm(user=request.user, initial=initial)
    return render(request, 'budgets/form.html', {'form': form, 'clients': clients, 'action': 'Nuevo'})


@login_required
def budget_detail(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    return render(request, 'budgets/detail.html', {'budget': budget})


@login_required
def budget_edit(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    clients = Client.objects.filter(contractor=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            budget.material_items.all().delete()
            budget.labor_items.all().delete()
            _save_line_items(request, budget, 'mat', BudgetItemMaterial, 'un')
            _save_line_items(request, budget, 'lab', BudgetItemLabor, 'gl')
            messages.success(request, '✅ Presupuesto actualizado correctamente.')
            return redirect('budget_detail', pk=budget.pk)
    else:
        form = BudgetForm(instance=budget, user=request.user)
    return render(request, 'budgets/form.html', {'form': form, 'clients': clients, 'budget': budget, 'action': 'Editar'})


def _parse_decimal(value, default='0'):
    """Parse string to Decimal safely, clamped to >= 0."""
    try:
        d = Decimal(str(value).replace(',', '.'))
        return max(Decimal('0'), d)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _save_line_items(request, budget, prefix, model, default_unit):
    """Guarda ítems de línea (materiales o mano de obra) desde el POST."""
    names = request.POST.getlist(f'{prefix}_name[]')
    units = request.POST.getlist(f'{prefix}_unit[]')
    qtys = request.POST.getlist(f'{prefix}_qty[]')
    prices = request.POST.getlist(f'{prefix}_price[]')
    for i, name in enumerate(names):
        if name.strip():
            try:
                model.objects.create(
                    budget=budget,
                    name=name.strip(),
                    unit=units[i] if i < len(units) else default_unit,
                    quantity=_parse_decimal(qtys[i], '1') if i < len(qtys) and qtys[i] else Decimal('1'),
                    unit_price=_parse_decimal(prices[i]) if i < len(prices) and prices[i] else Decimal('0'),
                    order=i,
                )
            except (ValueError, IndexError):
                pass


@login_required
def budget_update_status(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid = [s[0] for s in Budget._meta.get_field('status').choices]
        if new_status in valid:
            budget.status = new_status
            if new_status == 'enviado' and not budget.sent_at:
                budget.sent_at = timezone.now()
            budget.save()
            messages.success(request, f'Estado actualizado a: {budget.get_status_display()}')
    return redirect('budget_detail', pk=pk)


@login_required
def budget_delete(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method == 'POST':
        num = budget.number
        budget.delete()
        messages.success(request, f'Presupuesto #{num} eliminado.')
        return redirect('budget_list')
    return render(request, 'budgets/confirm_delete.html', {'budget': budget})


@login_required
def budget_pdf(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    profile = getattr(request.user, 'profile', None)
    context = {'budget': budget, 'profile': profile}

    try:
        from weasyprint import HTML, CSS
        from django.template.loader import render_to_string

        html_string = render_to_string('budgets/pdf_template.html', context)
        html = HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/'),
        )
        css = CSS(string='@page { size: A4; margin: 0; }')
        pdf_bytes = html.write_pdf(stylesheets=[css])

        safe_name = re.sub(r'[^\w\s-]', '', budget.client.name[:20]).strip().replace(' ', '-')
        filename = f'presupuesto-{budget.number}-{safe_name}.pdf'
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    except ImportError:
        messages.warning(request, 'WeasyPrint no está instalado. Mostrando vista HTML del PDF.')
        return render(request, 'budgets/pdf_template.html', context)
    except Exception as e:
        messages.error(request, f'Error al generar el PDF: {e}')
        return redirect('budget_detail', pk=pk)


@login_required
def budget_duplicate(request, pk):
    original = get_tenant_object_or_404(Budget, request, pk=pk)

    with transaction.atomic():
        if not request.user.is_pro():
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
            count = Budget.objects.select_for_update().filter(
                contractor=request.user, created_at__gte=month_start
            ).count()
            if count >= settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH:
                messages.warning(request, 'Límite mensual de presupuestos alcanzado.')
                return redirect('budget_list')

        new_budget = Budget.objects.create(
            contractor=request.user,
            client=original.client,
            title=f"COPIA — {original.title}",
            status='borrador',
            validity_days=original.validity_days,
            payment_terms=original.payment_terms,
            notes=original.notes,
            tax_percent=original.tax_percent,
        )
        for item in original.material_items.all():
            BudgetItemMaterial.objects.create(
                budget=new_budget, name=item.name, unit=item.unit,
                quantity=item.quantity, unit_price=item.unit_price, order=item.order,
            )
        for item in original.labor_items.all():
            BudgetItemLabor.objects.create(
                budget=new_budget, name=item.name, unit=item.unit,
                quantity=item.quantity, unit_price=item.unit_price, order=item.order,
            )
    messages.success(request, f'✅ Presupuesto duplicado como #{new_budget.number}. Ya puedes editarlo.')
    return redirect('budget_edit', pk=new_budget.pk)


@login_required
def budget_generate_link(request, pk):
    """Genera o regenera el link público para compartir con el cliente. Solo POST."""
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method != 'POST':
        return redirect('budget_detail', pk=pk)
    token, created = BudgetPublicToken.objects.get_or_create(budget=budget)
    if not created and request.POST.get('regenerate'):
        from datetime import timedelta
        token.token = secrets.token_urlsafe(32)
        token.expires_at = timezone.now() + timedelta(days=30)
        token.is_revoked = False
        token.save()
        messages.success(request, '🔄 Link regenerado. El link anterior ya no es válido.')
    else:
        messages.success(request, '🔗 Link público generado. Cópialo y envíalo a tu cliente.')
    return redirect('budget_detail', pk=pk)


@login_required
def budget_revoke_link(request, pk):
    """Revoca el link público activo de un presupuesto."""
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method == 'POST':
        try:
            token = budget.public_token
            token.is_revoked = True
            token.save(update_fields=['is_revoked'])
            messages.success(request, 'Link público revocado. El cliente ya no puede acceder.')
        except BudgetPublicToken.DoesNotExist:
            pass
    return redirect('budget_detail', pk=pk)


@ratelimit(key='ip', rate='20/m', block=True)
def budget_public_view(request, token):
    """Vista pública del presupuesto para el cliente final (sin login)."""
    public_token = get_object_or_404(
        BudgetPublicToken,
        token=token,
        is_revoked=False,
        expires_at__gt=timezone.now(),
    )
    budget = public_token.budget
    profile = getattr(budget.contractor, 'profile', None)
    public_token.views += 1
    public_token.save(update_fields=['views'])
    return render(request, 'budgets/public_view.html', {
        'budget': budget,
        'profile': profile,
        'token': public_token,
    })


@login_required
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def budget_send_email(request, pk):
    """Envía el presupuesto por email al cliente."""
    budget = get_tenant_object_or_404(Budget, request, pk=pk)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            email = budget.client.email

        if not email:
            messages.error(request, 'El cliente no tiene email registrado. Ingrésalo manualmente.')
            return redirect('budget_detail', pk=pk)

        BudgetPublicToken.objects.get_or_create(budget=budget)

        from .email_utils import send_budget_email
        ok = send_budget_email(budget, email, request=request)

        if ok:
            if budget.status == 'borrador':
                budget.status = 'enviado'
                budget.sent_at = timezone.now()
                budget.save()
            messages.success(request, f'✅ Presupuesto enviado a {email}.')
        else:
            messages.error(request, 'Error al enviar el email. Verifica la configuración SMTP.')

    return redirect('budget_detail', pk=pk)
