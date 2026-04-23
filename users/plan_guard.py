class PlanGuard:
    """
    Centraliza los chequeos de límites del plan gratuito.
    Cada método retorna (permitido: bool, mensaje: str).
    """

    @staticmethod
    def can_create_budget(user) -> tuple:
        return True, ''

    @staticmethod
    def can_create_client(user) -> tuple:
        return True, ''

    @staticmethod
    def can_create_product(user) -> tuple:
        return True, ''
