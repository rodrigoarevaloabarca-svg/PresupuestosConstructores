from django.shortcuts import render, redirect


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    features = [
        {'icon': '📄', 'title': 'Presupuestos en PDF', 'desc': 'Genera PDFs profesionales con tu logo y colores de empresa. Listos para enviar por WhatsApp o email.'},
        {'icon': '🔨', 'title': 'Materiales + Mano de Obra', 'desc': 'Agrega ítems de materiales y partidas de mano de obra. El sistema calcula los totales automáticamente.'},
        {'icon': '👥', 'title': 'Gestión de Clientes', 'desc': 'Registra tus clientes con RUT, datos de contacto e historial completo de presupuestos.'},
        {'icon': '📦', 'title': 'Catálogo Propio', 'desc': 'Crea tu catálogo de productos y materiales frecuentes con precios de costo y venta.'},
        {'icon': '📊', 'title': 'Dashboard de Control', 'desc': 'Ve de un vistazo los presupuestos enviados, aceptados y el estado de tu negocio.'},
        {'icon': '🇨🇱', 'title': 'Localizado para Chile', 'desc': 'Validación de RUT, precios en pesos chilenos, soporte para IVA y adaptado al mercado local.'},
    ]

    free_features = [
        'Hasta 5 presupuestos por mes',
        'Hasta 10 clientes',
        'Catálogo de 20 productos',
        'PDF con tu marca',
        'Dashboard básico',
    ]

    pro_features = [
        'Presupuestos ilimitados',
        'Clientes ilimitados',
        'Catálogo ilimitado',
        'PDF premium personalizado',
        'Reportes avanzados',
        'Soporte prioritario',
        'Próximamente: Facturación DTE',
    ]

    return render(request, 'landing.html', {
        'features': features,
        'free_features': free_features,
        'pro_features': pro_features,
    })
