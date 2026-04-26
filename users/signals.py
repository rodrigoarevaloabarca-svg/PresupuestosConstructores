from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="users.Subscription")
def invalidate_pro_cache(sender, instance, **kwargs):
    """Invalida el cache _pro_cache del usuario cuando cambia la suscripción."""
    user = instance.contractor
    if hasattr(user, "_pro_cache"):
        del user._pro_cache
