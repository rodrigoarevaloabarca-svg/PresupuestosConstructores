from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta


@login_required
def dashboard_view(request):
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    budgets = user.budgets.select_related('client')
    clients = user.clients.all()
    products = user.products.filter(is_active=True)

    budgets_this_month = budgets.filter(created_at__gte=month_start)
    recent_budgets = budgets.order_by('-created_at')[:6]

    # ── Notificaciones / alertas ─────────────────────────────────────
    alerts = []

    # Presupuestos próximos a vencer (enviados, vencen en ≤3 días)
    expiring_soon = budgets.filter(
        status='enviado',
        created_at__gte=now - timedelta(days=60)
    )
    about_to_expire = []
    for b in expiring_soon:
        days_left = (b.valid_until - now).days
        if 0 <= days_left <= 3:
            about_to_expire.append({'budget': b, 'days_left': days_left})
    if about_to_expire:
        for item in about_to_expire:
            d = item['days_left']
            label = 'hoy' if d == 0 else f'en {d} día{"s" if d > 1 else ""}'
            alerts.append({
                'type': 'warning',
                'icon': '⏰',
                'msg': f'Presupuesto #{item["budget"].number} — {item["budget"].client.name} vence {label}.',
                'url_name': 'budget_detail',
                'url_pk': item['budget'].pk,
            })

    # Presupuestos enviados hace más de 7 días sin respuesta
    followup_date = now - timedelta(days=7)
    pending_followup = budgets.filter(
        status='enviado',
        sent_at__lte=followup_date
    )
    for b in pending_followup[:2]:
        alerts.append({
            'type': 'info',
            'icon': '📬',
            'msg': f'Presupuesto #{b.number} — {b.client.name} lleva más de 7 días sin respuesta.',
            'url_name': 'budget_detail',
            'url_pk': b.pk,
        })

    # Perfil incompleto
    profile = getattr(user, 'profile', None)
    if profile and not profile.logo:
        alerts.append({
            'type': 'info',
            'icon': '🏢',
            'msg': 'Completa tu perfil: sube el logo de tu empresa para que aparezca en los PDFs.',
            'url_name': 'profile',
            'url_pk': None,
        })

    # ── Stats ────────────────────────────────────────────────────────
    accepted_budgets = budgets.filter(status='aceptado')
    total_revenue = sum(int(b.total) for b in accepted_budgets)
    pending_revenue = sum(int(b.total) for b in budgets.filter(status='enviado'))

    stats = {
        'total_clients': clients.count(),
        'total_products': products.count(),
        'budgets_this_month': budgets_this_month.count(),
        'total_budgets': budgets.count(),
        'accepted_budgets': accepted_budgets.count(),
        'pending_budgets': budgets.filter(status='enviado').count(),
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'conversion_rate': round(
            accepted_budgets.count() / budgets.count() * 100, 0
        ) if budgets.count() > 0 else 0,
    }

    from django.conf import settings
    plan_limits = {
        'max_clients': settings.PLAN_FREE_MAX_CLIENTS,
        'max_products': settings.PLAN_FREE_MAX_PRODUCTS,
        'max_budgets_month': settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH,
    }

    context = {
        'stats': stats,
        'recent_budgets': recent_budgets,
        'plan_limits': plan_limits,
        'is_pro': user.is_pro(),
        'alerts': alerts,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
    }
    return render(request, 'users/dashboard.html', context)
