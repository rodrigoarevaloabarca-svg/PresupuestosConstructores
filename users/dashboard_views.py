from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from users.services.dashboard_alerts import build_alerts


@login_required
def dashboard_view(request):
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    budgets = user.budgets.select_related("client")
    clients = user.clients.all()
    products = user.products.filter(is_active=True)

    budgets_this_month = budgets.filter(created_at__gte=month_start)
    recent_budgets = budgets.order_by("-created_at")[:6]
    alerts = build_alerts(user)

    accepted_budgets = budgets.filter(status="aceptado")
    revenue_agg = budgets.with_totals().aggregate(
        accepted=Coalesce(
            Sum(F("_subtotal_materials") + F("_subtotal_labor"), filter=Q(status="aceptado")),
            Value(0),
            output_field=DecimalField(),
        ),
        pending=Coalesce(
            Sum(F("_subtotal_materials") + F("_subtotal_labor"), filter=Q(status="enviado")),
            Value(0),
            output_field=DecimalField(),
        ),
    )
    total_revenue = int(revenue_agg["accepted"])
    pending_revenue = int(revenue_agg["pending"])

    stats = {
        "total_clients": clients.count(),
        "total_products": products.count(),
        "budgets_this_month": budgets_this_month.count(),
        "total_budgets": budgets.count(),
        "accepted_budgets": accepted_budgets.count(),
        "pending_budgets": budgets.filter(status="enviado").count(),
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue,
        "conversion_rate": round(accepted_budgets.count() / budgets.count() * 100, 0) if budgets.count() > 0 else 0,
    }

    plan_limits = {
        "max_clients": settings.PLAN_FREE_MAX_CLIENTS,
        "max_products": settings.PLAN_FREE_MAX_PRODUCTS,
        "max_budgets_month": settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH,
    }

    return render(
        request,
        "users/dashboard.html",
        {
            "stats": stats,
            "recent_budgets": recent_budgets,
            "plan_limits": plan_limits,
            "is_pro": user.is_pro(),
            "alerts": alerts,
            "total_revenue": total_revenue,
            "pending_revenue": pending_revenue,
        },
    )
