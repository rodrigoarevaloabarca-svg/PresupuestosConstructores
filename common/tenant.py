from django.shortcuts import get_object_or_404


def get_tenant_object_or_404(model, request, **kwargs):
    """
    Idéntico a get_object_or_404, pero fuerza el filtro contractor=request.user.
    Centraliza la protección contra IDOR en un solo lugar.
    """
    return get_object_or_404(model, contractor=request.user, **kwargs)
