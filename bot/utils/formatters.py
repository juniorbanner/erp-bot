def fmt_uzs(amount: float) -> str:
    """Format amount as UZS currency string."""
    return f"{amount:,.0f} UZS".replace(",", " ")


def fmt_date(dt) -> str:
    """Format datetime to short human-readable string."""
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y %H:%M")
