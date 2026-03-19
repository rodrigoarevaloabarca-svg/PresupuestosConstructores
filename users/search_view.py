from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from clients.models import Client
from catalog.models import Product
from budgets.models import Budget


@login_required
def global_search(request):
    q = request.GET.get('q', '').strip()
    results = {'clients': [], 'products': [], 'budgets': [], 'q': q}

    if len(q) >= 2:
        results['clients'] = Client.objects.filter(
            contractor=request.user, name__icontains=q
        )[:5]
        results['products'] = Product.objects.filter(
            contractor=request.user, is_active=True, name__icontains=q
        )[:5]
        results['budgets'] = Budget.objects.filter(
            contractor=request.user, title__icontains=q
        ).select_related('client')[:5]

        if not results['budgets']:
            # Also search by client name inside budgets
            results['budgets'] = Budget.objects.filter(
                contractor=request.user, client__name__icontains=q
            ).select_related('client')[:5]

    results['total'] = (
        len(results['clients']) +
        len(results['products']) +
        len(results['budgets'])
    )
    return render(request, 'users/search.html', results)
