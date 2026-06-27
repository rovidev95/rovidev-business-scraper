import pytest

from scraper.normalize import parse_currency, parse_price, parse_stock


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("€1.299,99", 1299.99),
        ("$1,299.99", 1299.99),
        ("12,50 €", 12.5),
        ("12.99", 12.99),
        ("1.299", 1299.0),
        ("1,299", 1299.0),
        ("USD 49.00", 49.0),
        ("Price: 7", 7.0),
        ("free", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_parse_currency_symbol_and_code():
    assert parse_currency("€10") == "EUR"
    assert parse_currency("10 USD") == "USD"
    assert parse_currency(None, "£5") == "GBP"
    assert parse_currency("nothing here") is None


def test_parse_stock():
    assert parse_stock("In stock (12 available)") is True
    assert parse_stock("Out of stock") is False
    assert parse_stock("Agotado") is False
    assert parse_stock("???") is None
    assert parse_stock(None) is None
