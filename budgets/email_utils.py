"""
Utilidades para envío de presupuestos por email.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_budget_email(budget, recipient_email, request=None):
    """
    Envía el presupuesto por email al cliente.
    
    Args:
        budget: instancia de Budget
        recipient_email: email del destinatario
        request: HttpRequest (para construir URLs absolutas)
    
    Returns:
        bool: True si se envió correctamente
    """
    profile = getattr(budget.contractor, 'profile', None)
    company_name = profile.company_name if profile else "Constructor Express"
    brand_color = profile.brand_color if profile else "#1e40af"

    # URL pública del presupuesto
    public_url = None
    if request and hasattr(budget, 'public_token'):
        try:
            public_url = request.build_absolute_uri(budget.public_token.get_public_url())
        except Exception:
            pass

    iva_note = f"(IVA {budget.tax_percent}% incl.)" if budget.tax_percent > 0 else "(sin IVA)"

    def fmt(n):
        return f"{int(round(float(n))):,}".replace(",", ".")

    context = {
        'client_name': budget.client.name,
        'company_name': company_name,
        'company_phone': profile.phone if profile else '',
        'company_address': f"{profile.address}, {profile.city}" if profile and profile.address else '',
        'brand_color': brand_color,
        'budget_number': budget.number,
        'budget_title': budget.title,
        'budget_total': fmt(budget.total),
        'mat_total': fmt(budget.subtotal_materials) if budget.subtotal_materials else None,
        'labor_total': fmt(budget.subtotal_labor) if budget.subtotal_labor else None,
        'valid_until': budget.valid_until.strftime('%d/%m/%Y'),
        'validity_days': budget.validity_days,
        'payment_terms': budget.payment_terms,
        'iva_note': iva_note,
        'public_url': public_url,
    }

    subject = f"Presupuesto #{budget.number} — {company_name}"
    from_email = settings.DEFAULT_FROM_EMAIL
    text_body = render_to_string('emails/budget_to_client.txt', context)
    html_body = render_to_string('emails/budget_to_client.html', context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[recipient_email],
        reply_to=[budget.contractor.email],
    )
    msg.attach_alternative(html_body, "text/html")

    try:
        msg.send()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False
