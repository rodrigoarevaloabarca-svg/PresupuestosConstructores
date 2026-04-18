from django.core.exceptions import ValidationError

from billing.models import Invoice, InvoiceLine
from billing.services.sii_client import emit_boleta
from users.services.subscriptions import has_active_subscription


def budget_to_invoice(budget, tipo: int = 39) -> Invoice:
    """Convierte un presupuesto aceptado en una boleta/factura electrónica."""
    if budget.status != 'aceptado':
        raise ValidationError('Solo se pueden facturar presupuestos aceptados.')
    if hasattr(budget, 'invoice') and budget.invoice is not None:
        raise ValidationError('Este presupuesto ya fue facturado.')
    if not has_active_subscription(budget.contractor):
        raise ValidationError('Se requiere plan Pro para emitir facturas.')

    invoice = Invoice.objects.create(
        contractor=budget.contractor,
        budget=budget,
        tipo_dte=tipo,
        total_clp=int(budget.total),
    )

    for item in budget.material_items.all():
        InvoiceLine.objects.create(
            invoice=invoice,
            name=item.name,
            quantity=item.quantity,
            unit_price=int(item.unit_price),
            subtotal=int(item.total),
        )
    for item in budget.labor_items.all():
        InvoiceLine.objects.create(
            invoice=invoice,
            name=item.name,
            quantity=item.quantity,
            unit_price=int(item.unit_price),
            subtotal=int(item.total),
        )

    try:
        result = emit_boleta(invoice)
        invoice.sii_track_id = result['track_id']
        invoice.pdf_url = result['pdf_url']
        invoice.xml_url = result['xml_url']
        invoice.save()
    except Exception:
        invoice.status = 'pending'
        invoice.save()

    return invoice
