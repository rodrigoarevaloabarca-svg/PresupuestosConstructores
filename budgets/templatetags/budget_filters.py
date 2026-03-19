from django import template

register = template.Library()

@register.filter
def clp(value):
    """Format number as Chilean Peso: $1.234.567"""
    try:
        n = int(round(float(value)))
        s = f"{n:,}".replace(",", ".")
        return f"${s}"
    except (ValueError, TypeError):
        return "$0"

@register.filter
def pct(value, total):
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except Exception:
        return 0
