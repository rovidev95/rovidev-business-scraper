from scraper.extract import extract
from scraper.models import SourceSpec

HTML = """
<ul>
  <li class="product">
    <h3 title="Item A">Item A</h3>
    <a href="/p/a">link</a>
    <span class="price">€10,00</span>
  </li>
  <li class="product">
    <h3 title="Item B">Item B</h3>
    <a href="/p/b">link</a>
    <span class="price">€20,00</span>
  </li>
</ul>
"""

SPEC = SourceSpec(
    name="t",
    url="https://x.example.com",
    item_selector="li.product",
    fields={
        "title": {"selector": "h3", "attr": "title"},
        "price": {"selector": ".price"},
        "url": {"selector": "a", "attr": "href"},
        "missing": {"selector": ".nope"},
    },
)


def test_extract_returns_one_row_per_item():
    rows = extract(HTML, SPEC)
    assert len(rows) == 2
    assert rows[0] == {"title": "Item A", "price": "€10,00", "url": "/p/a", "missing": None}
    assert rows[1]["title"] == "Item B"


def test_extract_empty_when_selector_matches_nothing():
    spec = SPEC.model_copy(update={"item_selector": ".does-not-exist"})
    assert extract(HTML, spec) == []
