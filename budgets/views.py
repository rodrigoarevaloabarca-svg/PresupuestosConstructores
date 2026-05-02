import contextlib
import re
import secrets
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from clients.models import Client
from common.tenant import get_tenant_object_or_404
from users.plan_guard import PlanGuard

from .forms import BudgetForm
from .models import RECIPE_RUBROS, Budget, BudgetAttachment, BudgetItemLabor, BudgetItemMaterial, BudgetPublicToken, MaterialRecipe, MaterialRecipeItem


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(contractor=request.user).select_related("client").prefetch_related("material_items", "labor_items").with_totals()
    status = request.GET.get("status", "")
    q = request.GET.get("q", "")
    if status:
        budgets = budgets.filter(status=status)
    if q:
        budgets = budgets.filter(Q(title__icontains=q) | Q(client__name__icontains=q))
    # Calculate totals for stats bar using DB aggregation (no N+1)
    totals_agg = budgets.aggregate(
        accepted_total=Coalesce(
            Sum(F("_subtotal_materials") + F("_subtotal_labor"), filter=Q(status="aceptado")),
            Value(0),
            output_field=DecimalField(),
        ),
        sent_total=Coalesce(
            Sum(F("_subtotal_materials") + F("_subtotal_labor"), filter=Q(status="enviado")),
            Value(0),
            output_field=DecimalField(),
        ),
    )
    accepted_total = int(totals_agg["accepted_total"])
    sent_total = int(totals_agg["sent_total"])

    paginator = Paginator(budgets.order_by("-created_at"), 20)
    page_num = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_num)

    return render(
        request,
        "budgets/list.html",
        {
            "budgets": page_obj,
            "page_obj": page_obj,
            "status": status,
            "q": q,
            "status_choices": Budget._meta.get_field("status").choices,
            "accepted_total": accepted_total,
            "sent_total": sent_total,
        },
    )


@login_required
def budget_create(request):
    allowed, msg = PlanGuard.can_create_budget(request.user)
    if not allowed:
        messages.warning(request, msg)
        return redirect("budget_list")

    clients = Client.objects.filter(contractor=request.user)
    preselect_client = request.GET.get("client", "")

    if request.method == "POST":
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                budget = form.save(commit=False)
                budget.contractor = request.user
                budget.save()
                _save_line_items(request, budget, "mat", BudgetItemMaterial, "un")
                _save_line_items(request, budget, "lab", BudgetItemLabor, "gl")
                _save_attachments(request, budget)
            messages.success(request, f"✅ Presupuesto #{budget.number} creado exitosamente.")
            return redirect("budget_detail", pk=budget.pk)
    else:
        profile = getattr(request.user, "profile", None)
        initial = {
            "validity_days": profile.budget_validity_days if profile else 15,
            "payment_terms": profile.payment_terms if profile else "",
            "notes": profile.notes_template if profile else "",
        }
        if preselect_client:
            initial["client"] = preselect_client
        form = BudgetForm(user=request.user, initial=initial)
    return render(request, "budgets/form.html", {"form": form, "clients": clients, "action": "Nuevo"})


@login_required
def budget_detail(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    return render(request, "budgets/detail.html", {"budget": budget})


@login_required
def budget_edit(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)

    from .services.versioning import create_new_version, should_create_version

    if request.method == "GET" and should_create_version(budget):
        new_version = create_new_version(budget)
        messages.info(request, f"✅ Nueva versión v{new_version.version} creada. Editando la nueva versión en borrador.")
        return redirect("budget_edit", pk=new_version.pk)

    clients = Client.objects.filter(contractor=request.user)
    if request.method == "POST":
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            budget.material_items.all().delete()
            budget.labor_items.all().delete()
            _save_line_items(request, budget, "mat", BudgetItemMaterial, "un")
            _save_line_items(request, budget, "lab", BudgetItemLabor, "gl")
            _save_attachments(request, budget)
            messages.success(request, "✅ Presupuesto actualizado correctamente.")
            return redirect("budget_detail", pk=budget.pk)
    else:
        form = BudgetForm(instance=budget, user=request.user)
    return render(request, "budgets/form.html", {"form": form, "clients": clients, "budget": budget, "action": "Editar"})


@login_required
def budget_template_list(request):
    templates = Budget.objects.filter(contractor=request.user, is_template=True).order_by("-created_at")
    return render(request, "budgets/template_list.html", {"templates": templates})


@login_required
def budget_save_as_template(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method != "POST":
        return redirect("budget_detail", pk=pk)
    with transaction.atomic():
        tpl = Budget.objects.create(
            contractor=request.user,
            client=budget.client,
            is_template=True,
            title=budget.title,
            status="borrador",
            validity_days=budget.validity_days,
            payment_terms=budget.payment_terms,
            notes=budget.notes,
            tax_percent=budget.tax_percent,
        )
        for item in budget.material_items.all():
            BudgetItemMaterial.objects.create(
                budget=tpl,
                name=item.name,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price,
                order=item.order,
            )
        for item in budget.labor_items.all():
            BudgetItemLabor.objects.create(
                budget=tpl,
                name=item.name,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price,
                order=item.order,
            )
    messages.success(request, f'✅ Plantilla "{tpl.title}" guardada.')
    return redirect("budget_template_list")


@login_required
def budget_delete_attachment(request, pk, att_pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method == "POST":
        att = get_object_or_404(BudgetAttachment, pk=att_pk, budget=budget)
        att.file.delete(save=False)
        att.delete()
        messages.success(request, "Adjunto eliminado.")
    return redirect("budget_edit", pk=pk)


def _parse_decimal(value, default="0"):
    """Parse string to Decimal safely, clamped to >= 0."""
    try:
        d = Decimal(str(value).replace(",", "."))
        return max(Decimal("0"), d)
    except (InvalidOperation, ValueError):
        return Decimal(default)


ALLOWED_ATTACHMENT_TYPES = {b"\xff\xd8\xff", b"\x89PNG", b"%PDF", b"RIFF", b"\x00\x00\x00"}


def _save_attachments(request, budget):
    """Guarda archivos adjuntos subidos, validando tipo por magic bytes (max 5 archivos, 5MB cada uno)."""
    files = request.FILES.getlist("attachments")
    existing = budget.attachments.count()
    saved = 0
    for f in files:
        if existing + saved >= 5:
            break
        if f.size > 5 * 1024 * 1024:
            continue
        header = f.read(8)
        f.seek(0)
        if not (header[:3] == b"\xff\xd8\xff" or header[:4] == b"\x89PNG" or header[:4] == b"%PDF" or header[:4] == b"RIFF"):
            continue
        BudgetAttachment.objects.create(budget=budget, file=f, filename=f.name)
        saved += 1


def _save_line_items(request, budget, prefix, model, default_unit):
    """Guarda ítems de línea (materiales o mano de obra) desde el POST."""
    names = request.POST.getlist(f"{prefix}_name[]")
    units = request.POST.getlist(f"{prefix}_unit[]")
    qtys = request.POST.getlist(f"{prefix}_qty[]")
    prices = request.POST.getlist(f"{prefix}_price[]")
    for i, name in enumerate(names):
        if name.strip():
            with contextlib.suppress(ValueError, IndexError):
                model.objects.create(
                    budget=budget,
                    name=name.strip(),
                    unit=units[i] if i < len(units) else default_unit,
                    quantity=_parse_decimal(qtys[i], "1") if i < len(qtys) and qtys[i] else Decimal("1"),
                    unit_price=_parse_decimal(prices[i]) if i < len(prices) and prices[i] else Decimal("0"),
                    order=i,
                )


@login_required
def budget_update_status(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        valid = [s[0] for s in Budget._meta.get_field("status").choices]
        if new_status in valid:
            budget.status = new_status
            if new_status == "enviado" and not budget.sent_at:
                budget.sent_at = timezone.now()
            budget.save()
            messages.success(request, f"Estado actualizado a: {budget.get_status_display()}")
    return redirect("budget_detail", pk=pk)


@login_required
def budget_delete(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method == "POST":
        num = budget.number
        budget.delete()
        messages.success(request, f"Presupuesto #{num} eliminado.")
        return redirect("budget_list")
    return render(request, "budgets/confirm_delete.html", {"budget": budget})


@login_required
def budget_pdf(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    profile = getattr(request.user, "profile", None)
    context = {"budget": budget, "profile": profile}

    try:
        from django.template.loader import render_to_string
        from weasyprint import CSS, HTML

        html_string = render_to_string("budgets/pdf_template.html", context)
        html = HTML(
            string=html_string,
            base_url=request.build_absolute_uri("/"),
        )
        css = CSS(string="@page { size: A4; margin: 0; }")
        pdf_bytes = html.write_pdf(stylesheets=[css])

        safe_name = re.sub(r"[^\w\s-]", "", budget.client.name[:20]).strip().replace(" ", "-")
        filename = f"presupuesto-{budget.number}-{safe_name}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

    except ImportError:
        messages.warning(request, "WeasyPrint no está instalado. Mostrando vista HTML del PDF.")
        return render(request, "budgets/pdf_template.html", context)
    except Exception as e:
        messages.error(request, f"Error al generar el PDF: {e}")
        return redirect("budget_detail", pk=pk)


@login_required
def budget_duplicate(request, pk):
    original = get_tenant_object_or_404(Budget, request, pk=pk)

    with transaction.atomic():
        if not request.user.is_pro():
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
            count = Budget.objects.select_for_update().filter(contractor=request.user, created_at__gte=month_start).count()
            if count >= settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH:
                messages.warning(request, "Límite mensual de presupuestos alcanzado.")
                return redirect("budget_list")

        new_budget = Budget.objects.create(
            contractor=request.user,
            client=original.client,
            title=f"COPIA — {original.title}",
            status="borrador",
            validity_days=original.validity_days,
            payment_terms=original.payment_terms,
            notes=original.notes,
            tax_percent=original.tax_percent,
        )
        for item in original.material_items.all():
            BudgetItemMaterial.objects.create(
                budget=new_budget,
                name=item.name,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price,
                order=item.order,
            )
        for item in original.labor_items.all():
            BudgetItemLabor.objects.create(
                budget=new_budget,
                name=item.name,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price,
                order=item.order,
            )
    messages.success(request, f"✅ Presupuesto duplicado como #{new_budget.number}. Ya puedes editarlo.")
    return redirect("budget_edit", pk=new_budget.pk)


@login_required
def budget_generate_link(request, pk):
    """Genera o regenera el link público para compartir con el cliente. Solo POST."""
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method != "POST":
        return redirect("budget_detail", pk=pk)
    token, created = BudgetPublicToken.objects.get_or_create(budget=budget)
    if not created and request.POST.get("regenerate"):
        from datetime import timedelta

        token.token = secrets.token_urlsafe(32)
        token.expires_at = timezone.now() + timedelta(days=30)
        token.is_revoked = False
        token.save()
        messages.success(request, "🔄 Link regenerado. El link anterior ya no es válido.")
    else:
        messages.success(request, "🔗 Link público generado. Cópialo y envíalo a tu cliente.")
    return redirect("budget_detail", pk=pk)


@login_required
def budget_revoke_link(request, pk):
    """Revoca el link público activo de un presupuesto."""
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    if request.method == "POST":
        try:
            token = budget.public_token
            token.is_revoked = True
            token.save(update_fields=["is_revoked"])
            messages.success(request, "Link público revocado. El cliente ya no puede acceder.")
        except BudgetPublicToken.DoesNotExist:
            pass
    return redirect("budget_detail", pk=pk)


@ratelimit(key="ip", rate="20/m", block=True)
def budget_public_view(request, token):
    """Vista pública del presupuesto para el cliente final (sin login)."""
    public_token = get_object_or_404(
        BudgetPublicToken,
        token=token,
        is_revoked=False,
        expires_at__gt=timezone.now(),
    )
    budget = public_token.budget
    profile = getattr(budget.contractor, "profile", None)
    public_token.views += 1
    public_token.save(update_fields=["views"])
    return render(
        request,
        "budgets/public_view.html",
        {
            "budget": budget,
            "profile": profile,
            "token": public_token,
        },
    )


@login_required
@ratelimit(key="user", rate="10/h", method="POST", block=True)
def budget_send_email(request, pk):
    """Envía el presupuesto por email al cliente."""
    budget = get_tenant_object_or_404(Budget, request, pk=pk)

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            email = budget.client.email

        if not email:
            messages.error(request, "El cliente no tiene email registrado. Ingrésalo manualmente.")
            return redirect("budget_detail", pk=pk)

        BudgetPublicToken.objects.get_or_create(budget=budget)

        from .email_utils import send_budget_email

        ok = send_budget_email(budget, email, request=request)

        if ok:
            if budget.status == "borrador":
                budget.status = "enviado"
                budget.sent_at = timezone.now()
                budget.save()
            messages.success(request, f"✅ Presupuesto enviado a {email}.")
        else:
            messages.error(request, "Error al enviar el email. Verifica la configuración SMTP.")

    return redirect("budget_detail", pk=pk)


# ─── WhatsApp (Sprint 28) ─────────────────────────────────────────────────────


@login_required
@ratelimit(key="user", rate="10/h", block=True, method="POST")
def budget_send_whatsapp(request, pk):
    budget = get_tenant_object_or_404(Budget, pk=pk, user=request.user)
    if request.method != "POST":
        return redirect("budget_detail", pk=pk)

    phone = budget.client.phone if hasattr(budget.client, "phone") else ""
    if not phone:
        messages.error(request, "El cliente no tiene teléfono registrado.")
        return redirect("budget_detail", pk=pk)

    token_obj, _ = BudgetPublicToken.objects.get_or_create(budget=budget)
    public_url = request.build_absolute_uri(token_obj.get_public_url())

    from .services.whatsapp import send_budget_whatsapp_task

    send_budget_whatsapp_task.delay(budget.pk, phone, public_url)
    messages.success(request, f"✅ Mensaje WhatsApp enviado a {phone}.")
    return redirect("budget_detail", pk=pk)


# ─── Facturar presupuesto (Sprint 25) ─────────────────────────────────────────


@ratelimit(key="ip", rate="3/h", block=True)
def budget_public_sign(request, token):
    """Recibe la firma PNG en base64 del cliente y acepta el presupuesto."""
    import base64
    import hashlib

    from django.core.files.base import ContentFile

    from .models import BudgetSignature

    public_token = get_object_or_404(
        BudgetPublicToken,
        token=token,
        is_revoked=False,
        expires_at__gt=timezone.now(),
    )
    budget = public_token.budget

    if budget.status != "enviado":
        return render(request, "budgets/public_sign_done.html", {"budget": budget, "already_signed": True})

    if hasattr(budget, "signature"):
        return render(request, "budgets/public_sign_done.html", {"budget": budget, "already_signed": True})

    if request.method != "POST":
        return redirect("budget_public", token=token)

    png_b64 = request.POST.get("signature_data", "").strip()
    if not png_b64:
        return redirect("budget_public", token=token)

    try:
        if "," in png_b64:
            png_b64 = png_b64.split(",", 1)[1]
        png_bytes = base64.b64decode(png_b64)
    except Exception:
        return redirect("budget_public", token=token)

    if len(png_bytes) < 1024:
        return redirect("budget_public", token=token)

    sha256 = hashlib.sha256(png_bytes).hexdigest()
    ip = request.META.get("REMOTE_ADDR", "")
    ua = request.headers.get("user-agent", "")

    sig = BudgetSignature(budget=budget, hash_sha256=sha256, ip=ip, user_agent=ua)
    sig.signature_png.save(f"firma-{budget.number}.png", ContentFile(png_bytes), save=False)
    sig.save()

    budget.status = "aceptado"
    budget.save(update_fields=["status"])

    from .email_utils import send_budget_email

    contractor_email = budget.contractor.email
    if contractor_email:
        send_budget_email(budget, contractor_email, request=request)

    return render(request, "budgets/public_sign_done.html", {"budget": budget, "already_signed": False})


@login_required
def budget_history(request, pk):
    budget = get_tenant_object_or_404(Budget, request, pk=pk)
    from auditlog.models import LogEntry

    history = LogEntry.objects.get_for_object(budget).order_by("-timestamp")
    return render(request, "budgets/history.html", {"budget": budget, "history": history})


@login_required
def budget_to_invoice_view(request, pk):
    budget = get_tenant_object_or_404(Budget, pk=pk, user=request.user)
    if request.method != "POST":
        return redirect("budget_detail", pk=pk)

    from django.core.exceptions import ValidationError

    from billing.services.converter import budget_to_invoice

    try:
        invoice = budget_to_invoice(budget)
        messages.success(request, f"✅ Boleta N°{invoice.folio} emitida correctamente.")
    except ValidationError as e:
        messages.error(request, str(e.message))
    except Exception as e:
        messages.error(request, f"Error al emitir boleta: {e}")
    return redirect("budget_detail", pk=pk)


# ─── Calculadora de Materiales ────────────────────────────────────────────────


@login_required
def calculadora_view(request):
    return render(request, "budgets/calculadora.html")


@login_required
def api_custom_recipes(request):
    recipes = MaterialRecipe.objects.filter(contractor=request.user, is_active=True).prefetch_related("items")
    return JsonResponse([r.to_api_dict() for r in recipes], safe=False)


@login_required
def recipe_list(request):
    recipes = MaterialRecipe.objects.filter(contractor=request.user, is_active=True).prefetch_related("items")
    return render(request, "budgets/recipe_list.html", {"recipes": recipes})


def _save_recipe(request, recipe=None):
    from catalog.models import UNIT_CHOICES as UC

    errors = []
    name = request.POST.get("name", "").strip()
    rubro = request.POST.get("rubro", "").strip()
    icon = request.POST.get("icon", "📦").strip() or "📦"
    input_label = request.POST.get("input_label", "").strip()
    input_unit = request.POST.get("input_unit", "").strip()
    input_placeholder = request.POST.get("input_placeholder", "").strip()

    if not name:
        errors.append("El nombre es obligatorio.")
    if not rubro:
        errors.append("La categoría es obligatoria.")
    if not input_label:
        errors.append("La etiqueta de medida es obligatoria.")
    if not input_unit:
        errors.append("La unidad de medida es obligatoria.")

    valid_units = {k for k, _ in UC}
    names = request.POST.getlist("item_name[]")
    units = request.POST.getlist("item_unit[]")
    factors = request.POST.getlist("item_factor[]")

    valid_items = []
    for idx, (n, u, f) in enumerate(zip(names, units, factors, strict=False)):
        n = n.strip()
        if not n:
            continue
        if u not in valid_units:
            errors.append(f"Ítem {idx + 1}: unidad inválida.")
            continue
        try:
            factor = Decimal(f)
            if factor <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            errors.append(f"Ítem {idx + 1}: el factor debe ser mayor que 0.")
            continue
        valid_items.append({"name": n, "unit": u, "factor": factor})

    if not valid_items and not errors:
        errors.append("Agrega al menos un material a la receta.")

    if errors:
        return errors

    if recipe is None:
        recipe = MaterialRecipe(contractor=request.user)

    recipe.name = name
    recipe.rubro = rubro
    recipe.icon = icon
    recipe.input_label = input_label
    recipe.input_unit = input_unit
    recipe.input_placeholder = input_placeholder
    recipe.save()

    recipe.items.all().delete()
    MaterialRecipeItem.objects.bulk_create([MaterialRecipeItem(recipe=recipe, name=i["name"], unit=i["unit"], quantity_factor=i["factor"], order=pos) for pos, i in enumerate(valid_items)])
    return []


@login_required
def recipe_create(request):
    from catalog.models import UNIT_CHOICES as UC

    if request.method == "POST":
        errors = _save_recipe(request)
        if not errors:
            messages.success(request, "Receta creada correctamente.")
            return redirect("recipe_list")
        return render(request, "budgets/recipe_form.html", {"action": "Crear", "unit_choices": UC, "rubros": RECIPE_RUBROS, "errors": errors, "post": request.POST})
    from catalog.models import UNIT_CHOICES as UC

    return render(request, "budgets/recipe_form.html", {"action": "Crear", "unit_choices": UC, "rubros": RECIPE_RUBROS})


@login_required
def recipe_edit(request, pk):
    from catalog.models import UNIT_CHOICES as UC

    recipe = get_object_or_404(MaterialRecipe, pk=pk, contractor=request.user)
    if request.method == "POST":
        errors = _save_recipe(request, recipe)
        if not errors:
            messages.success(request, "Receta actualizada.")
            return redirect("recipe_list")
        return render(request, "budgets/recipe_form.html", {"action": "Editar", "recipe": recipe, "unit_choices": UC, "rubros": RECIPE_RUBROS, "errors": errors, "post": request.POST})
    return render(request, "budgets/recipe_form.html", {"action": "Editar", "recipe": recipe, "unit_choices": UC, "rubros": RECIPE_RUBROS})


@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(MaterialRecipe, pk=pk, contractor=request.user)
    if request.method == "POST":
        recipe.delete()
        messages.success(request, "Receta eliminada.")
        return redirect("recipe_list")
    return render(request, "budgets/recipe_confirm_delete.html", {"recipe": recipe})
