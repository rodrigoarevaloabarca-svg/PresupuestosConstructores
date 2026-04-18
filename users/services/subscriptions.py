from django.utils.timezone import now


def has_active_subscription(user) -> bool:
    """Retorna True si el usuario tiene suscripción Pro activa.
    Usa _pro_cache para evitar N+1 en bucles.
    """
    if hasattr(user, '_pro_cache'):
        return user._pro_cache
    return user.is_pro()
