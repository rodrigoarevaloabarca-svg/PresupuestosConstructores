def format_clp(amount):
    """Formatea un monto CLP al estilo $1.234.567 (sin decimales)."""
    return f"{int(round(float(amount))):,}".replace(",", ".")
