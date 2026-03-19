from .models import ContractorProfile
from django.conf import settings


def contractor_profile(request):
    """Hace que el perfil del contratista esté disponible en todos los templates."""
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile is None:
            try:
                profile = ContractorProfile.objects.get(user=request.user)
            except ContractorProfile.DoesNotExist:
                profile = None
        return {
            'contractor_profile': profile,
            'is_pro': request.user.is_pro(),
            'plan_limits': {
                'max_clients': settings.PLAN_FREE_MAX_CLIENTS,
                'max_products': settings.PLAN_FREE_MAX_PRODUCTS,
                'max_budgets_month': settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH,
            }
        }
    return {}
