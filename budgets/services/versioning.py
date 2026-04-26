from django.db import transaction

EDITABLE_STATUSES = {'borrador'}


def create_new_version(budget):
    """Duplica un presupuesto en estado no-borrador y retorna la nueva versión."""
    from budgets.models import Budget, BudgetItemLabor, BudgetItemMaterial

    with transaction.atomic():
        new_budget = Budget.objects.create(
            contractor=budget.contractor,
            client=budget.client,
            parent=budget.parent or budget,
            version=(budget.version + 1),
            title=budget.title,
            status='borrador',
            validity_days=budget.validity_days,
            payment_terms=budget.payment_terms,
            notes=budget.notes,
            tax_percent=budget.tax_percent,
        )
        for item in budget.material_items.all():
            BudgetItemMaterial.objects.create(
                budget=new_budget, name=item.name, unit=item.unit,
                quantity=item.quantity, unit_price=item.unit_price, order=item.order,
            )
        for item in budget.labor_items.all():
            BudgetItemLabor.objects.create(
                budget=new_budget, name=item.name, unit=item.unit,
                quantity=item.quantity, unit_price=item.unit_price, order=item.order,
            )
    return new_budget


def should_create_version(budget):
    return budget.status not in EDITABLE_STATUSES
