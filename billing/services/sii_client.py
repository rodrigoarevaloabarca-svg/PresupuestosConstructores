import logging

import requests
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("billing.sii")

_BASE_URLS = {
    "sandbox": "https://api.sandbox.openfactura.cl/v2",
    "prod": "https://api.openfactura.cl/v2",
}


def _base_url():
    return _BASE_URLS.get(settings.SII_ENV, _BASE_URLS["sandbox"])


def _headers():
    return {
        "apikey": settings.SII_PROVIDER_API_KEY,
        "Content-Type": "application/json",
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def emit_boleta(invoice) -> dict:
    """Emite una boleta electrónica vía OpenFactura. Retorna {track_id, pdf_url, xml_url}."""
    lines = [
        {
            "NmbItem": line.name,
            "QtyItem": float(line.quantity),
            "PrcItem": line.unit_price,
        }
        for line in invoice.lines.all()
    ]
    payload = {
        "Encabezado": {
            "IdDoc": {"TipoDTE": invoice.tipo_dte},
            "Emisor": {"RUTEmisor": settings.SII_RUT_EMISOR},
        },
        "Detalle": lines,
    }
    resp = requests.post(f"{_base_url()}/dte/document", json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    logger.info("Boleta emitida invoice=%s track_id=%s", invoice.pk, data.get("trackId"))
    return {
        "track_id": data.get("trackId", ""),
        "pdf_url": data.get("urlPdf", ""),
        "xml_url": data.get("urlXml", ""),
    }
