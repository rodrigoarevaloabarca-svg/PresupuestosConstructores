from django.db import models
from django.db.models import DecimalField, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth

_DECIMAL = DecimalField(max_digits=14, decimal_places=2)


class BudgetQuerySet(models.QuerySet):
    def with_totals(self):
        """Anota _subtotal_materials y _subtotal_labor con Subquery (sin cartesian join)."""
        from .models import BudgetItemLabor, BudgetItemMaterial

        mat_sum = BudgetItemMaterial.objects.filter(budget=OuterRef("pk")).values("budget").annotate(s=Sum(F("quantity") * F("unit_price"), output_field=_DECIMAL)).values("s")
        labor_sum = BudgetItemLabor.objects.filter(budget=OuterRef("pk")).values("budget").annotate(s=Sum(F("quantity") * F("unit_price"), output_field=_DECIMAL)).values("s")
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

    def client_lifetime_value(self, user):
        """Retorna CLV por cliente (suma de presupuestos aceptados)."""
        return (
            self.for_user(user)
            .filter(status="aceptado")
            .with_totals()
            .values("client__name", "client__pk")
            .annotate(
                total_value=Coalesce(
                    Sum(F("_subtotal_materials") + F("_subtotal_labor")),
                    Value(0),
                    output_field=_DECIMAL,
                )
            )
            .order_by("-total_value")
        )

    def top_products_by_margin(self, user, limit=5):
        """Retorna los productos del catálogo con mayor margen acumulado en presupuestos aceptados."""
        from budgets.models import BudgetItemMaterial

        return (
            BudgetItemMaterial.objects.filter(budget__contractor=user, budget__status="aceptado", product__isnull=False)
            .values("product__name", "product__pk")
            .annotate(
                margin_total=Coalesce(
                    Sum((F("unit_price") - F("product__cost_price")) * F("quantity"), output_field=_DECIMAL),
                    Value(0),
                    output_field=_DECIMAL,
                )
            )
            .order_by("-margin_total")[:limit]
        )

    def acceptance_rate(self, user, months=3):
        """Tasa de aceptación en los últimos N meses (aceptados / (aceptados + rechazados))."""
        from datetime import timedelta

        from django.db.models import Count, Q
        from django.utils import timezone

        cutoff = timezone.now() - timedelta(days=months * 31)
        agg = (
            self.for_user(user)
            .filter(created_at__gte=cutoff, is_template=False)
            .aggregate(
                accepted=Count("pk", filter=Q(status="aceptado")),
                rejected=Count("pk", filter=Q(status="rechazado")),
            )
        )
        total = agg["accepted"] + agg["rejected"]
        return round((agg["accepted"] / total) * 100, 1) if total else 0

    def revenue_by_month(self, user, months=6):
        """
        Retorna los ingresos aceptados agrupados por mes (últimos N meses).
        Uso: Budget.objects.revenue_by_month(user, months=6)
        """
        from datetime import timedelta

        from django.utils import timezone

        cutoff = timezone.now() - timedelta(days=months * 31)
        return (
            self.for_user(user)
            .filter(status="aceptado", created_at__gte=cutoff)
            .with_totals()
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(
                revenue=Coalesce(
                    Sum(F("_subtotal_materials") + F("_subtotal_labor")),
                    Value(0),
                    output_field=_DECIMAL,
                )
            )
            .order_by("month")
        )
