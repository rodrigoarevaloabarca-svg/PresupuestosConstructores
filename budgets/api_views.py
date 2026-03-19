from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

    budgets = user.budgets.all()
    month_budgets = budgets.filter(created_at__gte=month_start)

    accepted = budgets.filter(status='aceptado')
    total_revenue = sum(int(b.total) for b in accepted)
    pending_revenue = sum(int(b.total) for b in budgets.filter(status='enviado'))

    return Response({
        'total_clients': user.clients.count(),
        'total_products': user.products.filter(is_active=True).count(),
        'total_budgets': budgets.count(),
        'budgets_this_month': month_budgets.count(),
        'accepted_budgets': accepted.count(),
        'pending_budgets': budgets.filter(status='enviado').count(),
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'conversion_rate': round(accepted.count() / budgets.count() * 100, 1) if budgets.count() > 0 else 0,
    })
