import csv
import io
import itertools
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from common.tenant import get_tenant_object_or_404
from users.plan_guard import PlanGuard

from .forms import ProductForm
from .models import Product


@login_required
def product_list(request):
    products = Product.objects.filter(contractor=request.user, is_active=True)
    q = request.GET.get("q", "")
    cat = request.GET.get("cat", "")
    if q:
        products = products.filter(name__icontains=q)
    if cat:
        products = products.filter(category=cat)
    categories = Product._meta.get_field("category").choices
    return render(request, "catalog/list.html", {"products": products, "q": q, "cat": cat, "categories": categories})


@login_required
def product_create(request):
    allowed, msg = PlanGuard.can_create_product(request.user)
    if not allowed:
        messages.warning(request, msg)
        return redirect("product_list")
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.contractor = request.user
            p.save()
            messages.success(request, f'Producto "{p.name}" creado.')
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "catalog/form.html", {"form": form, "action": "Crear"})


@login_required
def product_edit(request, pk):
    product = get_tenant_object_or_404(Product, request, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado.")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "catalog/form.html", {"form": form, "action": "Editar", "product": product})


@login_required
def product_delete(request, pk):
    product = get_tenant_object_or_404(Product, request, pk=pk)
    if request.method == "POST":
        product.is_active = False
        product.save()
        messages.success(request, f'Producto "{product.name}" eliminado.')
        return redirect("product_list")
    return render(request, "catalog/confirm_delete.html", {"product": product})


@login_required
def product_search_api(request):
    """API endpoint for budget builder autocomplete."""
    q = request.GET.get("q", "")
    products = Product.objects.filter(contractor=request.user, is_active=True, name__icontains=q).values("id", "name", "unit", "sale_price", "category")[:10]
    return JsonResponse({"results": list(products)})


MAX_CSV_ROWS = 5000


def _sanitize_csv_value(value):
    """Prevent CSV formula injection by escaping dangerous prefixes."""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _parse_csv_price(raw):
    """Parse Chilean-format price string to Decimal safely."""
    try:
        cleaned = str(raw).replace(".", "").replace(",", ".").strip() or "0"
        d = Decimal(cleaned)
        return max(Decimal("0"), d)
    except (InvalidOperation, ValueError):
        return Decimal("0")


@login_required
def product_export_csv(request):
    """Exporta el catálogo completo a CSV."""
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="catalogo_productos.csv"'

    writer = csv.writer(response)
    writer.writerow(["Nombre", "Descripción", "Categoría", "Unidad", "Precio Costo", "Precio Venta", "SKU"])

    products = Product.objects.filter(contractor=request.user, is_active=True)
    for p in products:
        writer.writerow([_sanitize_csv_value(p.name), _sanitize_csv_value(p.description), p.get_category_display(), p.get_unit_display(), p.cost_price, p.sale_price, _sanitize_csv_value(p.sku)])
    return response


@login_required
def product_import_csv(request):
    """Importa productos desde un archivo CSV."""
    if request.method != "POST":
        return render(request, "catalog/import.html", {})

    csv_file = request.FILES.get("csv_file")
    if not csv_file:
        messages.error(request, "No se seleccionó ningún archivo.")
        return redirect("product_import_csv")

    if not csv_file.name.endswith(".csv"):
        messages.error(request, "El archivo debe ser CSV (.csv)")
        return redirect("product_import_csv")

    # Map display names back to values
    unit_map = {v.lower(): k for k, v in dict(Product._meta.get_field("unit").choices).items()}
    cat_map = {v.lower(): k for k, v in dict(Product._meta.get_field("category").choices).items()}
    unit_map.update({k: k for k in unit_map.values()})
    cat_map.update({k: k for k in cat_map.values()})

    created = 0
    errors = []
    skipped_rows = 0

    try:
        decoded = csv_file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(itertools.islice(reader, MAX_CSV_ROWS + 1))
        if len(rows) > MAX_CSV_ROWS:
            skipped_rows = len(rows) - MAX_CSV_ROWS
            rows = rows[:MAX_CSV_ROWS]
        for i, row in enumerate(rows, start=2):
            name = row.get("Nombre", "").strip()
            if not name:
                continue
            try:
                unit_raw = row.get("Unidad", "un").strip().lower()
                cat_raw = row.get("Categoría", "otro").strip().lower()
                product = Product(
                    contractor=request.user,
                    name=name,
                    description=row.get("Descripción", "").strip(),
                    category=cat_map.get(cat_raw, "otro"),
                    unit=unit_map.get(unit_raw, "un"),
                    cost_price=_parse_csv_price(row.get("Precio Costo", "0")),
                    sale_price=_parse_csv_price(row.get("Precio Venta", "0")),
                    sku=row.get("SKU", "").strip(),
                )
                product.full_clean()
                product.save()
                created += 1
            except Exception as e:
                errors.append(f"Fila {i}: {e}")
    except Exception as e:
        messages.error(request, f"Error al procesar el archivo: {e}")
        return redirect("product_list")

    if created:
        messages.success(request, f"✅ {created} producto(s) importados correctamente.")
    if skipped_rows:
        messages.warning(request, f"Se omitieron {skipped_rows} filas por límite máximo de {MAX_CSV_ROWS} filas.")
    if errors:
        display_errors = errors[:20]
        for err in display_errors:
            messages.warning(request, err)
        if len(errors) > 20:
            messages.warning(request, f"...y {len(errors) - 20} errores más.")

    return redirect("product_list")
