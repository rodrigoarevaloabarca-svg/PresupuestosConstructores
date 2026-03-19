from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from .models import Product
from .forms import ProductForm


@login_required
def product_list(request):
    products = Product.objects.filter(contractor=request.user, is_active=True)
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    if q:
        products = products.filter(name__icontains=q)
    if cat:
        products = products.filter(category=cat)
    categories = Product._meta.get_field('category').choices
    return render(request, 'catalog/list.html', {'products': products, 'q': q, 'cat': cat, 'categories': categories})


@login_required
def product_create(request):
    if not request.user.is_pro():
        count = Product.objects.filter(contractor=request.user, is_active=True).count()
        if count >= settings.PLAN_FREE_MAX_PRODUCTS:
            messages.warning(request, f'Límite de {settings.PLAN_FREE_MAX_PRODUCTS} productos del plan gratuito alcanzado.')
            return redirect('product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.contractor = request.user
            p.save()
            messages.success(request, f'Producto "{p.name}" creado.')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'catalog/form.html', {'form': form, 'action': 'Crear'})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, contractor=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'catalog/form.html', {'form': form, 'action': 'Editar', 'product': product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, contractor=request.user)
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, f'Producto "{product.name}" eliminado.')
        return redirect('product_list')
    return render(request, 'catalog/confirm_delete.html', {'product': product})


@login_required
def product_search_api(request):
    """API endpoint for budget builder autocomplete."""
    q = request.GET.get('q', '')
    products = Product.objects.filter(
        contractor=request.user, is_active=True, name__icontains=q
    ).values('id', 'name', 'unit', 'sale_price', 'category')[:10]
    return JsonResponse({'results': list(products)})


import csv
import io
from django.http import HttpResponse


@login_required
def product_export_csv(request):
    """Exporta el catálogo completo a CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="catalogo_productos.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nombre', 'Descripción', 'Categoría', 'Unidad', 'Precio Costo', 'Precio Venta', 'SKU'])
    
    products = Product.objects.filter(contractor=request.user, is_active=True)
    for p in products:
        writer.writerow([
            p.name, p.description, p.get_category_display(),
            p.get_unit_display(), p.cost_price, p.sale_price, p.sku
        ])
    return response


@login_required
def product_import_csv(request):
    """Importa productos desde un archivo CSV."""
    if request.method != 'POST':
        return render(request, 'catalog/import.html', {})
    
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.error(request, 'No se seleccionó ningún archivo.')
        return redirect('product_import_csv')
    
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'El archivo debe ser CSV (.csv)')
        return redirect('product_import_csv')

    # Map display names back to values
    UNIT_MAP = {v.lower(): k for k, v in dict(Product._meta.get_field('unit').choices).items()}
    CAT_MAP  = {v.lower(): k for k, v in dict(Product._meta.get_field('category').choices).items()}
    UNIT_MAP.update({k: k for k in UNIT_MAP.values()})
    CAT_MAP.update({k: k for k in CAT_MAP.values()})

    created = 0
    errors = []
    
    try:
        decoded = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        for i, row in enumerate(reader, start=2):
            name = row.get('Nombre', '').strip()
            if not name:
                continue
            try:
                unit_raw = row.get('Unidad', 'un').strip().lower()
                cat_raw  = row.get('Categoría', 'otro').strip().lower()
                Product.objects.create(
                    contractor=request.user,
                    name=name,
                    description=row.get('Descripción', '').strip(),
                    category=CAT_MAP.get(cat_raw, 'otro'),
                    unit=UNIT_MAP.get(unit_raw, 'un'),
                    cost_price=float(str(row.get('Precio Costo', 0)).replace('.', '').replace(',', '.') or 0),
                    sale_price=float(str(row.get('Precio Venta', 0)).replace('.', '').replace(',', '.') or 0),
                    sku=row.get('SKU', '').strip(),
                )
                created += 1
            except Exception as e:
                errors.append(f'Fila {i}: {e}')
    except Exception as e:
        messages.error(request, f'Error al procesar el archivo: {e}')
        return redirect('product_list')

    if created:
        messages.success(request, f'✅ {created} producto(s) importados correctamente.')
    if errors:
        for err in errors[:5]:
            messages.warning(request, err)
    
    return redirect('product_list')
