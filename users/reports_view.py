from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
import json


@login_required
def reports_view(request):
    user = request.user
    now = timezone.now()

    # Last 6 months
    months_data = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 28)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            next_month = (month_start + timedelta(days=32)).replace(day=1)
        else:
            next_month = now
        
        budgets_month = user.budgets.filter(created_at__gte=month_start, created_at__lt=next_month)
        accepted = budgets_month.filter(status='aceptado')
        
        # Calculate total for accepted budgets
        total_accepted = 0
        for b in accepted:
            total_accepted += int(b.total)
        
        months_data.append({
            'month': month_start.strftime('%b %Y'),
            'created': budgets_month.count(),
            'accepted': accepted.count(),
            'revenue': total_accepted,
        })

    # Overall stats
    all_budgets = user.budgets.all()
    total_count = all_budgets.count()
    accepted_count = all_budgets.filter(status='aceptado').count()
    sent_count = all_budgets.filter(status='enviado').count()
    rejected_count = all_budgets.filter(status='rechazado').count()
    draft_count = all_budgets.filter(status='borrador').count()

    # Total revenue from accepted budgets
    total_revenue = sum(int(b.total) for b in all_budgets.filter(status='aceptado'))
    pending_revenue = sum(int(b.total) for b in all_budgets.filter(status='enviado'))

    # Conversion rate
    conversion_rate = round((accepted_count / total_count * 100), 1) if total_count > 0 else 0

    # Top clients by budget value
    client_stats = []
    for client in user.clients.all():
        budgets = client.budgets.all()
        total = sum(int(b.total) for b in budgets.filter(status='aceptado'))
        if budgets.count() > 0:
            client_stats.append({
                'name': client.name,
                'budget_count': budgets.count(),
                'accepted': budgets.filter(status='aceptado').count(),
                'total_revenue': total,
            })
    client_stats.sort(key=lambda x: x['total_revenue'], reverse=True)

    context = {
        'months_data': months_data,
        'months_labels': json.dumps([m['month'] for m in months_data]),
        'months_created': json.dumps([m['created'] for m in months_data]),
        'months_accepted': json.dumps([m['accepted'] for m in months_data]),
        'months_revenue': json.dumps([m['revenue'] for m in months_data]),
        'total_count': total_count,
        'accepted_count': accepted_count,
        'sent_count': sent_count,
        'rejected_count': rejected_count,
        'draft_count': draft_count,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'conversion_rate': conversion_rate,
        'client_stats': client_stats[:5],
        'is_pro': user.is_pro(),
    }
    return render(request, 'users/reports.html', context)
