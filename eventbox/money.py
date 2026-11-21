"""Money is stored in fils (1 BHD = 1000 fils) as a whole number, never as a float."""


def bhd(fils: int) -> str:
    """15000 -> "15.000 BHD", how EventBox shows prices. In templates: {{ event.price_fils | bhd }}."""
    return f"{fils // 1000}.{fils % 1000:03d} BHD"
