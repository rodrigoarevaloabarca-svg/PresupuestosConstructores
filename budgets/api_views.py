from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, F, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from .models import Budget
from .serializers import BudgetListSerializer, BudgetDetailSerializer


class BudgetListAPIView(generics.ListAPIView):
    serializer_class = BudgetListSerializer

    def get_queryset(self):
        qs = Budget.objects.filter(contractor=self.request.user).select_related('client')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class BudgetDetailAPIView(generics.RetrieveAPIView):
    serializer_class = BudgetDetailSerializer

    def get_queryset(self):
        return Budget.objects.filter(contractor=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_api(request):
    from django.utils import timezone
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    budgets = Budget.objects.for_user(user)
    month_budgets = budgets.filter(created_at__gte=month_start)

    counts = budgets.aggregate(
        total=Sum(Value(1), output_field=DecimalField()),
        accepted_count=Sum(Value(1), filter=Q(status='aceptado'), output_field=DecimalField()),
        pending_count=Sum(Value(1), filter=Q(status='enviado'), output_field=DecimalField()),
    )
    total_count = budgets.count()
    accepted_count = int(counts['accepted_count'] or 0)
    pending_count = int(counts['pending_count'] or 0)

    revenue_agg = budgets.with_totals().aggregate(
        total_revenue=Coalesce(
            Sum(F('_subtotal_materials') + F('_subtotal_labor'), filter=Q(status='aceptado')),
            Value(0), output_field=DecimalField(),
        ),
        pending_revenue=Coalesce(
            Sum(F('_subtotal_materials') + F('_subtotal_labor'), filter=Q(status='enviado')),
            Value(0), output_field=DecimalField(),
        ),
    )

    return Response({
        'total_clients': user.clients.count(),
        'total_products': user.products.filter(is_active=True).count(),
        'total_budgets': total_count,
        'budgets_this_month': month_budgets.count(),
        'accepted_budgets': accepted_count,
        'pending_budgets': pending_count,
        'total_revenue': int(revenue_agg['total_revenue']),
        'pending_revenue': int(revenue_agg['pending_revenue']),
        'conversion_rate': round(accepted_count / total_count * 100, 1) if total_count > 0 else 0,
    })
