from django.apps import AppConfig


class BudgetsConfig(AppConfig):
    name = 'budgets'

    def ready(self):
        from auditlog.registry import auditlog

        from budgets.models import Budget, BudgetItemLabor, BudgetItemMaterial
        auditlog.register(Budget)
        auditlog.register(BudgetItemMaterial)
        auditlog.register(BudgetItemLabor)
