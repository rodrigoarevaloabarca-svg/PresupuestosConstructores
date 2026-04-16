from datetime import timedelta

from django.utils import timezone


def build_alerts(user) -> list:
    """
    Construye la lista de alertas del dashboard para el usuario dado.
    Retorna lista de dicts con {type, icon, msg, url_name, url_pk}.
    """
    alerts = []
    now = timezone.now()
    budgets = user.budgets.select_related('client')

    # Presupuestos próximos a vencer (enviados, vencen en ≤3 días)
    expiring_soon = budgets.filter(
        status='enviado',
        created_at__gte=now - timedelta(days=60),
    )
    for b in expiring_soon:
        days_left = (b.valid_until - now).days
        if 0 <= days_left <= 3:
            label = 'hoy' if days_left == 0 else f'en {days_left} día{"s" if days_left > 1 else ""}'
            alerts.append({
                'type': 'warning',
                'icon': '⏰',
                'msg': f'Presupuesto #{b.number} — {b.client.name} vence {label}.',
                'url_name': 'budget_detail',
                'url_pk': b.pk,
            })

    # Presupuestos enviados hace más de 7 días sin respuesta
    followup_date = now - timedelta(days=7)
    pending_followup = budgets.filter(status='enviado', sent_at__lte=followup_date)
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

    return alerts
