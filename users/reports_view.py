from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F, Q, Value, DecimalField, Count
from django.db.models.functions import Coalesce, TruncMonth
from datetime import timedelta
from budgets.models import Budget


def _revenue_expr(filter_q=None):
    """Expresión SQL reutilizable: suma de (materiales + mano de obra)."""
    expr = Sum(
        F('_subtotal_materials') + F('_subtotal_labor'),
        filter=filter_q,
    )
    return Coalesce(expr, Value(0), output_field=DecimalField())


@login_required
def reports_view(request):
    user = request.user
    now = timezone.now()
    # Build 6-month date range
    month_starts = []
    for i in range(5, -1, -1):
        ms = (now.replace(day=1) - timedelta(days=i * 28)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        month_starts.append(ms)
    cutoff = month_starts[0]

    # Monthly data — una sola query agrupada por mes
    monthly_qs = (
        Budget.objects.for_user(user)
        .filter(created_at__gte=cutoff)
        .with_totals()
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            created=Count('id'),
            accepted=Count('id', filter=Q(status='aceptado')),
            revenue=Coalesce(
                Sum(F('_subtotal_materials') + F('_subtotal_labor'), filter=Q(status='aceptado')),
                Value(0), output_field=DecimalField(),
            ),
        )
        .order_by('month')
    )
    monthly_map = {row['month']: row for row in monthly_qs}
    months_data = []
    for ms in month_starts:
        row = monthly_map.get(ms)
        months_data.append({
            'month': ms.strftime('%b %Y'),
            'created': row['created'] if row else 0,
            'accepted': row['accepted'] if row else 0,
            'revenue': int(row['revenue']) if row else 0,
        })

    # Overall stats — una sola query
    all_budgets = Budget.objects.for_user(user)
    total_count = all_budgets.count()
    counts = all_budgets.aggregate(
        accepted_count=Coalesce(Count('id', filter=Q(status='aceptado')), Value(0)),
        sent_count=Coalesce(Count('id', filter=Q(status='enviado')), Value(0)),
        rejected_count=Coalesce(Count('id', filter=Q(status='rechazado')), Value(0)),
        draft_count=Coalesce(Count('id', filter=Q(status='borrador')), Value(0)),
    )
    accepted_count = counts['accepted_count']
    sent_count = counts['sent_count']
    rejected_count = counts['rejected_count']
    draft_count = counts['draft_count']

    revenue_agg = all_budgets.with_totals().aggregate(
        total_revenue=_revenue_expr(Q(status='aceptado')),
        pending_revenue=_revenue_expr(Q(status='enviado')),
    )
    total_revenue = int(revenue_agg['total_revenue'])
    pending_revenue = int(revenue_agg['pending_revenue'])

    conversion_rate = round((accepted_count / total_count * 100), 1) if total_count > 0 else 0

    # Top clients — una sola query con GROUP BY
    client_stats = list(
        all_budgets
        .with_totals()
        .values('client__name')
        .annotate(
            budget_count=Count('id'),
            accepted=Coalesce(Count('id', filter=Q(status='aceptado')), Value(0)),
            total_revenue=Coalesce(
                Sum(F('_subtotal_materials') + F('_subtotal_labor'), filter=Q(status='aceptado')),
                Value(0), output_field=DecimalField(),
            ),
        )
        .filter(budget_count__gt=0)
        .order_by('-total_revenue')[:5]
    )
    client_stats = [
        {
            'name': row['client__name'],
            'budget_count': row['budget_count'],
            'accepted': row['accepted'],
            'total_revenue': int(row['total_revenue']),
        }
        for row in client_stats
    ]

    context = {
        'months_data': months_data,
        'months_labels': [m['month'] for m in months_data],
        'months_created': [m['created'] for m in months_data],
        'months_accepted': [m['accepted'] for m in months_data],
        'months_revenue': [m['revenue'] for m in months_data],
        'total_count': total_count,
        'accepted_count': accepted_count,
        'sent_count': sent_count,
        'rejected_count': rejected_count,
        'draft_count': draft_count,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'conversion_rate': conversion_rate,
        'client_stats': client_stats,
        'is_pro': user.is_pro(),
    }
    return render(request, 'users/reports.html', context)
