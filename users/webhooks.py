import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Payment, Subscription

logger = logging.getLogger("users.auth")


def _verify_mp_signature(request) -> bool:
    """Valida la firma HMAC-SHA256 del webhook de Mercado Pago."""
    secret = settings.MP_WEBHOOK_SECRET
    if not secret:
        return True  # En dev sin secret configurado, permitir
    signature = request.headers.get("x-signature", "")
    if not signature:
        return False
    parts = {p.split("=")[0]: p.split("=")[1] for p in signature.split(",") if "=" in p}
    ts = parts.get("ts", "")
    v1 = parts.get("v1", "")
    query_id = request.GET.get("data.id", "")
    manifest = f"id:{query_id};request-id:{request.headers.get('x-request-id', '')};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    if not _verify_mp_signature(request):
        return JsonResponse({"error": "firma inválida"}, status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "payload inválido"}, status=400)

    event_type = payload.get("type", "")
    data = payload.get("data", {})

    if event_type == "subscription_preapproval":
        _handle_subscription(data)
    elif event_type == "payment":
        _handle_payment(data)

    return JsonResponse({"status": "ok"})


def _handle_subscription(data):
    preapproval_id = data.get("id", "")
    if not preapproval_id:
        return
    try:
        import mercadopago

        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        result = sdk.preapproval().get(preapproval_id)
        if result["status"] != 200:
            return
        info = result["response"]
        sub = Subscription.objects.filter(mp_preapproval_id=preapproval_id).first()
        if not sub:
            return
        sub.status = info.get("status", sub.status)
        next_date = info.get("next_payment_date")
        if next_date:
            sub.next_billing_date = parse_date(next_date[:10])
        sub.save()
    except Exception as e:
        logger.error("Error procesando webhook subscription %s: %s", preapproval_id, e)


def _handle_payment(data):
    payment_id = str(data.get("id", ""))
    if not payment_id:
        return
    try:
        import mercadopago

        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        result = sdk.payment().get(payment_id)
        if result["status"] != 200:
            return
        info = result["response"]
        preapproval_id = info.get("metadata", {}).get("preapproval_id", "")
        sub = Subscription.objects.filter(mp_preapproval_id=preapproval_id).first()
        if not sub:
            return
        Payment.objects.get_or_create(
            mp_payment_id=payment_id,
            defaults={
                "subscription": sub,
                "amount": int(info.get("transaction_amount", 0)),
                "paid_at": timezone.now(),
            },
        )
    except Exception as e:
        logger.error("Error procesando webhook payment %s: %s", payment_id, e)
