from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from budgets.models import Budget

from .serializers import BudgetReadSerializer, BudgetWriteSerializer


@extend_schema_view(
    list=extend_schema(summary='Listar presupuestos'),
    create=extend_schema(summary='Crear presupuesto con ítems'),
    retrieve=extend_schema(summary='Obtener presupuesto'),
    update=extend_schema(summary='Actualizar presupuesto'),
    partial_update=extend_schema(summary='Actualizar parcialmente'),
    destroy=extend_schema(summary='Eliminar presupuesto'),
)
class BudgetViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Budget.objects
            .filter(contractor=self.request.user)
            .select_related('client')
            .prefetch_related('material_items', 'labor_items')
            .order_by('-created_at')
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return BudgetReadSerializer
        return BudgetWriteSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx
