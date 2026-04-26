import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger('budgets.whatsapp')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_budget_whatsapp_task(self, budget_id, phone, public_url):
    """Task Celery: envía link del presupuesto por WhatsApp vía Twilio."""
    from budgets.models import Budget
    try:
        budget = Budget.objects.select_related('contractor__profile', 'client').get(pk=budget_id)
    except Budget.DoesNotExist:
        logger.error('Budget %s no encontrado para WhatsApp', budget_id)
        return

    if not settings.TWILIO_ACCOUNT_SID:
        logger.warning('Twilio no configurado — omitiendo envío WhatsApp')
        return

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        body = (
            f"Hola {budget.client.name}, te enviamos el presupuesto "
            f"N°{budget.number}: {public_url}"
        )
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=f'whatsapp:{phone}',
        )
        logger.info('WhatsApp enviado budget=%s sid=%s', budget_id, message.sid)
    except Exception as exc:
        logger.error('Error WhatsApp budget=%s: %s', budget_id, exc)
        raise self.retry(exc=exc) from exc
