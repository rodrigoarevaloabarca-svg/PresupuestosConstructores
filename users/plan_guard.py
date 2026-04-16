from django.conf import settings
from django.utils import timezone


class PlanGuard:
    """
    Centraliza los chequeos de límites del plan gratuito.
    Cada método retorna (permitido: bool, mensaje: str).
    """

    @staticmethod
    def can_create_budget(user) -> tuple:
        if user.is_pro():
            return True, ''
        from budgets.models import Budget
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = Budget.objects.filter(
            contractor=user, created_at__gte=month_start
        ).count()
        limit = settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH
        if count >= limit:
            return False, (
                f'Límite de {limit} presupuestos/mes del plan gratuito alcanzado. '
                '¡Actualiza a Pro!'
            )
        return True, ''

    @staticmethod
    def can_create_client(user) -> tuple:
        if user.is_pro():
            return True, ''
        from clients.models import Client
        count = Client.objects.filter(contractor=user).count()
        limit = settings.PLAN_FREE_MAX_CLIENTS
        if count >= limit:
            return False, (
                f'Alcanzaste el límite de {limit} clientes del plan gratuito. '
                '¡Actualiza a Pro!'
            )
        return True, ''

    @staticmethod
    def can_create_product(user) -> tuple:
        if user.is_pro():
            return True, ''
        from catalog.models import Product
        count = Product.objects.filter(contractor=user, is_active=True).count()
        limit = settings.PLAN_FREE_MAX_PRODUCTS
        if count >= limit:
            return False, (
                f'Límite de {limit} productos del plan gratuito alcanzado. '
                '¡Actualiza a Pro!'
            )
        return True, ''
