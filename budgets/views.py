from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from .models import Budget, BudgetItemMaterial, BudgetItemLabor
from .forms import BudgetForm
from clients.models import Client


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(contractor=request.user).select_related('client')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    if status:
        budgets = budgets.filter(status=status)
    if q:
        budgets = budgets.filter(
            __import__('django.db.models', fromlist=['Q']).Q(title__icontains=q) |
            __import__('django.db.models', fromlist=['Q']).Q(client__name__icontains=q)
        )
    # Calculate totals for stats bar
    accepted_total = sum(int(b.total) for b in budgets.filter(status='aceptado'))
    sent_total = sum(int(b.total) for b in budgets.filter(status='enviado'))

    # Paginación
    from django.core.paginator import Paginator
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
    if not request.user.is_pro():
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        count = Budget.objects.filter(contractor=request.user, created_at__gte=month_start).count()
        if count >= settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH:
            messages.warning(request, f'Límite de {settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH} presupuestos/mes del plan gratuito alcanzado. ¡Actualiza a Pro!')
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
                        messages.warning(request, f'Límite mensual alcanzado.')
                        return redirect('budget_list')
                budget = form.save(commit=False)
                budget.contractor = request.user
                budget.save()
                _save_items(request, budget)
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
    budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
    return render(request, 'budgets/detail.html', {'budget': budget})


@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
    clients = Client.objects.filter(contractor=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            budget.material_items.all().delete()
            budget.labor_items.all().delete()
            _save_items(request, budget)
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


def _save_items(request, budget):
    mat_names  = request.POST.getlist('mat_name[]')
    mat_units  = request.POST.getlist('mat_unit[]')
    mat_qtys   = request.POST.getlist('mat_qty[]')
    mat_prices = request.POST.getlist('mat_price[]')
    for i, name in enumerate(mat_names):
        if name.strip():
            try:
                BudgetItemMaterial.objects.create(
                    budget=budget, name=name.strip(),
                    unit=mat_units[i] if i < len(mat_units) else 'un',
                    quantity=_parse_decimal(mat_qtys[i], '1') if i < len(mat_qtys) and mat_qtys[i] else Decimal('1'),
                    unit_price=_parse_decimal(mat_prices[i]) if i < len(mat_prices) and mat_prices[i] else Decimal('0'),
                    order=i,
                )
            except (ValueError, IndexError):
                pass

    lab_names  = request.POST.getlist('lab_name[]')
    lab_units  = request.POST.getlist('lab_unit[]')
    lab_qtys   = request.POST.getlist('lab_qty[]')
    lab_prices = request.POST.getlist('lab_price[]')
    for i, name in enumerate(lab_names):
        if name.strip():
            try:
                BudgetItemLabor.objects.create(
                    budget=budget, name=name.strip(),
                    unit=lab_units[i] if i < len(lab_units) else 'gl',
                    quantity=_parse_decimal(lab_qtys[i], '1') if i < len(lab_qtys) and lab_qtys[i] else Decimal('1'),
                    unit_price=_parse_decimal(lab_prices[i]) if i < len(lab_prices) and lab_prices[i] else Decimal('0'),
                    order=i,
                )
            except (ValueError, IndexError):
                pass


@login_required
def budget_update_status(request, pk):
    budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
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
    budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
    if request.method == 'POST':
        num = budget.number
        budget.delete()
        messages.success(request, f'Presupuesto #{num} eliminado.')
        return redirect('budget_list')
    return render(request, 'budgets/confirm_delete.html', {'budget': budget})


@login_required
def budget_pdf(request, pk):
    budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
    profile = getattr(request.user, 'profile', None)
    context = {'budget': budget, 'profile': profile}

    try:
        from weasyprint import HTML, CSS
        from django.template.loader import render_to_string

        html_string = render_to_string('budgets/pdf_template.html', context)

        # base_url sin request para evitar problemas con WeasyPrint y URLs relativas
        html = HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/'),
        )
        css = CSS(string='@page { size: A4; margin: 0; }')
        pdf_bytes = html.write_pdf(stylesheets=[css])

        import re
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
    original = get_object_or_404(Budget, pk=pk, contractor=request.user)

    with transaction.atomic():
        if not request.user.is_pro():
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
            count = Budget.objects.select_for_update().filter(
                contractor=request.user, created_at__gte=month_start
            ).count()
            if count >= settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH:
                messages.warning(request, f'Límite mensual de presupuestos alcanzado.')
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


from .models import BudgetPublicToken


@login_required
def budget_generate_link(request, pk):
    """Genera o regenera el link público para compartir con el cliente."""
    budget = get_object_or_404(Budget, pk=pk, contractor=request.user)
    token, created = BudgetPublicToken.objects.get_or_create(budget=budget)
    if not created and request.GET.get('regenerate'):
        import secrets
        token.token = secrets.token_urlsafe(32)
        token.save()
    messages.success(request, '🔗 Link público generado. Cópialo y envíalo a tu cliente.')
    return redirect('budget_detail', pk=pk)


def budget_public_view(request, token):
    """Vista pública del presupuesto para el cliente final (sin login)."""
    public_token = get_object_or_404(BudgetPublicToken, token=token)
    budget = public_token.budget
    profile = getattr(budget.contractor, 'profile', None)
    # Increment view counter
    public_token.views += 1
    public_token.save(update_fields=['views'])
    return render(request, 'budgets/public_view.html', {
        'budget': budget,
        'profile': profile,
        'token': public_token,
    })


@login_required
def budget_send_email(request, pk):
    """Envía el presupuesto por email al cliente."""
    budget = get_object_or_404(Budget, pk=pk, contractor=request.user)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            email = budget.client.email

        if not email:
            messages.error(request, 'El cliente no tiene email registrado. Ingrésalo manualmente.')
            return redirect('budget_detail', pk=pk)

        # Generar token público si no existe
        from .models import BudgetPublicToken
        BudgetPublicToken.objects.get_or_create(budget=budget)

        from .email_utils import send_budget_email
        ok = send_budget_email(budget, email, request=request)

        if ok:
            # Cambiar estado a enviado
            if budget.status == 'borrador':
                budget.status = 'enviado'
                budget.sent_at = timezone.now()
                budget.save()
            messages.success(request, f'✅ Presupuesto enviado a {email}.')
        else:
            messages.error(request, 'Error al enviar el email. Verifica la configuración SMTP.')

    return redirect('budget_detail', pk=pk)
