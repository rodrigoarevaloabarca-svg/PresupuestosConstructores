"""
Utilidades para envío de emails relacionados con cuentas de usuario.
"""

import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)


def send_password_reset_email(user, request):
    """Envía email con enlace para restablecer contraseña.

    Genera un token de un solo uso usando PasswordResetTokenGenerator (se invalida
    automáticamente al cambiar la contraseña porque la firma incluye el hash).

    Returns:
        bool: True si se envió correctamente.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    path = reverse("password_reset_confirm", args=[uidb64, token])
    reset_url = request.build_absolute_uri(path)

    profile = getattr(user, "profile", None)
    company_name = profile.company_name if profile else "Constructor Express"
    brand_color = profile.brand_color if profile else "#1d3461"
    valid_hours = max(1, settings.PASSWORD_RESET_TIMEOUT // 3600)

    context = {
        "user_email": user.email,
        "company_name": company_name,
        "brand_color": brand_color,
        "reset_url": reset_url,
        "valid_hours": valid_hours,
    }

    subject = "Recuperación de contraseña — Constructor Express"
    text_body = render_to_string("emails/password_reset.txt", context)
    html_body = render_to_string("emails/password_reset.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")

    try:
        msg.send()
        return True
    except Exception as e:
        logger.error("Error enviando email de recuperación a %s: %s", user.email, e)
        return False
