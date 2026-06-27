from __future__ import annotations

import re

_NUMBER = re.compile(r"\d[\d.,\s\u00a0]*\d|\d")

_CURRENCY_SYMBOLS = {
    "€": "EUR",
    "$": "USD",
    "£": "GBP",
    "¥": "JPY",
    "₿": "BTC",
}
_CURRENCY_CODES = ("EUR", "USD", "GBP", "JPY", "CHF", "CAD", "AUD")

_IN_STOCK = ("in stock", "en stock", "disponible", "available", "add to cart", "comprar")
_OUT_OF_STOCK = ("out of stock", "sold out", "agotado", "no disponible", "unavailable")


def parse_price(text: str | None) -> float | None:
    """Parse a price from messy text, handling EU and US separators.

    Examples: ``"€1.299,99"`` -> 1299.99, ``"$1,299.99"`` -> 1299.99,
    ``"12,50 €"`` -> 12.5, ``"1.299"`` (thousands) -> 1299.
    """
    if not text:
        return None
    match = _NUMBER.search(text)
    if not match:
        return None

    token = re.sub(r"[\s\u00a0]", "", match.group(0))
    has_comma = "," in token
    has_dot = "." in token

    if has_comma and has_dot:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif has_comma:
        if re.search(r",\d{1,2}$", token):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif has_dot:
        # A lone group of exactly three trailing digits is a thousands group.
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", token):
            token = token.replace(".", "")

    try:
        return round(float(token), 2)
    except ValueError:
        return None


def parse_currency(*texts: str | None) -> str | None:
    for text in texts:
        if not text:
            continue
        for symbol, code in _CURRENCY_SYMBOLS.items():
            if symbol in text:
                return code
        upper = text.upper()
        for code in _CURRENCY_CODES:
            if code in upper:
                return code
    return None


def parse_stock(text: str | None) -> bool | None:
    if not text:
        return None
    lowered = text.lower()
    for needle in _OUT_OF_STOCK:
        if needle in lowered:
            return False
    for needle in _IN_STOCK:
        if needle in lowered:
            return True
    return None
