from django.db import models
from django.db.models import Sum, F, Value, Subquery, OuterRef
from django.db.models.functions import Coalesce, TruncMonth
from django.db.models import DecimalField


_DECIMAL = DecimalField(max_digits=14, decimal_places=2)


class BudgetQuerySet(models.QuerySet):

    def with_totals(self):
        """Anota _subtotal_materials y _subtotal_labor con Subquery (sin cartesian join)."""
        from .models import BudgetItemMaterial, BudgetItemLabor

        mat_sum = (
            BudgetItemMaterial.objects
            .filter(budget=OuterRef('pk'))
            .values('budget')
            .annotate(s=Sum(F('quantity') * F('unit_price'), output_field=_DECIMAL))
            .values('s')
        )
        labor_sum = (
            BudgetItemLabor.objects
            .filter(budget=OuterRef('pk'))
            .values('budget')
            .annotate(s=Sum(F('quantity') * F('unit_price'), output_field=_DECIMAL))
            .values('s')
        )
        return self.annotate(
            _subtotal_materials=Coalesce(
                Subquery(mat_sum, output_field=_DECIMAL),
                Value(0, output_field=_DECIMAL),
            ),
            _subtotal_labor=Coalesce(
                Subquery(labor_sum, output_field=_DECIMAL),
                Value(0, output_field=_DECIMAL),
            ),
        )

    def for_user(self, user):
        """Filtra presupuestos del contratista dado."""
        return self.filter(contractor=user)

    def revenue_by_month(self, user, months=6):
        """
        Retorna los ingresos aceptados agrupados por mes (últimos N meses).
        Uso: Budget.objects.revenue_by_month(user, months=6)
        """
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=months * 31)
        return (
            self.for_user(user)
            .filter(status='aceptado', created_at__gte=cutoff)
            .with_totals()
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                revenue=Coalesce(
                    Sum(F('_subtotal_materials') + F('_subtotal_labor')),
                    Value(0),
                    output_field=_DECIMAL,
                )
            )
            .order_by('month')
        )
