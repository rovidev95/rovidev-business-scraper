from fastapi.testclient import TestClient

from scraper.api import create_app
from scraper.state import MemoryStateStore
from tests.fakes import FakeFetcher

SPEC = {
    "name": "shop",
    "url": "https://shop.example.com/list",
    "item_selector": "li.product",
    "key_field": "url",
    "fields": {
        "title": {"selector": "h3"},
        "price": {"selector": ".price"},
        "availability": {"selector": ".stock"},
        "url": {"selector": "a", "attr": "href"},
    },
}

PAGE = (
    '<ul><li class="product"><h3>Widget</h3><a href="/p/a">x</a>'
    '<span class="price">€10,00</span><span class="stock">In stock</span></li></ul>'
)


def make_client() -> TestClient:
    app = create_app(
        fetcher=FakeFetcher({SPEC["url"]: PAGE}),
        store=MemoryStateStore(),
        respect_robots=False,
    )
    return TestClient(app)


def test_health():
    assert make_client().get("/health").json() == {"status": "ok"}


def test_scrape_returns_items():
    response = make_client().post("/scrape", json=SPEC)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["price"] == 10.0
    assert body["changes"]["added"]


def test_get_source_after_scrape():
    client = make_client()
    client.post("/scrape", json=SPEC)
    response = client.get("/sources/shop")
    assert response.status_code == 200
    assert len(response.json()) == 1
