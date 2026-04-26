import contextlib
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from common.formatting import format_clp

logger = logging.getLogger("budgets.email")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_budget_email_task(self, budget_id, recipient_email, public_url=None):
    """Task Celery: envía presupuesto por email con reintentos automáticos."""
    from budgets.models import Budget

    try:
        budget = Budget.objects.select_related("contractor__profile", "client").get(pk=budget_id)
    except Budget.DoesNotExist:
        logger.error("Budget %s no encontrado para envío de email", budget_id)
        return False
    return _do_send(budget, recipient_email, public_url)


def send_budget_email(budget, recipient_email, request=None):
    """Dispara el envío de email vía Celery (sync en tests)."""
    public_url = None
    if request and hasattr(budget, "public_token"):
        with contextlib.suppress(Exception):
            public_url = request.build_absolute_uri(budget.public_token.get_public_url())
    send_budget_email_task.delay(budget.pk, recipient_email, public_url)
    return True


def _do_send(budget, recipient_email, public_url=None):
    profile = getattr(budget.contractor, "profile", None)
    company_name = profile.company_name if profile else "Constructor Express"
    brand_color = profile.brand_color if profile else "#1e40af"
    iva_note = f"(IVA {budget.tax_percent}% incl.)" if budget.tax_percent > 0 else "(sin IVA)"

    context = {
        "client_name": budget.client.name,
        "company_name": company_name,
        "company_phone": profile.phone if profile else "",
        "company_address": f"{profile.address}, {profile.city}" if profile and profile.address else "",
        "brand_color": brand_color,
        "budget_number": budget.number,
        "budget_title": budget.title,
        "budget_total": format_clp(budget.total),
        "mat_total": format_clp(budget.subtotal_materials) if budget.subtotal_materials else None,
        "labor_total": format_clp(budget.subtotal_labor) if budget.subtotal_labor else None,
        "valid_until": budget.valid_until.strftime("%d/%m/%Y"),
        "validity_days": budget.validity_days,
        "payment_terms": budget.payment_terms,
        "iva_note": iva_note,
        "public_url": public_url,
    }

    subject = f"Presupuesto #{budget.number} — {company_name}"
    text_body = render_to_string("emails/budget_to_client.txt", context)
    html_body = render_to_string("emails/budget_to_client.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
        reply_to=[budget.contractor.email],
        headers={"X-Entity-Ref-ID": str(budget.pk)},
    )
    msg.attach_alternative(html_body, "text/html")
    if hasattr(msg, "tags"):
        msg.tags = ["presupuesto"]

    try:
        msg.send()
        logger.info("Email enviado budget=%s a %s", budget.pk, recipient_email)
        return True
    except Exception as exc:
        logger.error("Error enviando email budget=%s a %s: %s", budget.pk, recipient_email, exc)
        raise
