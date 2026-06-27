import pytest

from scraper.models import SourceSpec
from scraper.pipeline import DisallowedByRobots, ScrapePipeline
from scraper.state import MemoryStateStore
from tests.fakes import FakeFetcher

SPEC = SourceSpec(
    name="shop",
    url="https://shop.example.com/list",
    item_selector="li.product",
    fields={
        "title": {"selector": "h3"},
        "price": {"selector": ".price"},
        "availability": {"selector": ".stock"},
        "url": {"selector": "a", "attr": "href"},
    },
    key_field="url",
)


def page(price: str = "€10,00", stock: str = "In stock") -> str:
    return (
        '<ul><li class="product"><h3>Widget</h3><a href="/p/a">x</a>'
        f'<span class="price">{price}</span><span class="stock">{stock}</span></li></ul>'
    )


async def test_scrape_normalizes_items():
    pipeline = ScrapePipeline(FakeFetcher({SPEC.url: page()}), respect_robots=False)
    items = await pipeline.scrape(SPEC)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Widget"
    assert item.price == 10.0
    assert item.currency == "EUR"
    assert item.in_stock is True
    assert item.url == "https://shop.example.com/p/a"
    assert item.key == "https://shop.example.com/p/a"


async def test_robots_disallow_blocks_scrape():
    fetcher = FakeFetcher(
        {
            "https://shop.example.com/robots.txt": "User-agent: *\nDisallow: /list",
            SPEC.url: page(),
        }
    )
    pipeline = ScrapePipeline(fetcher, respect_robots=True)
    with pytest.raises(DisallowedByRobots):
        await pipeline.scrape(SPEC)


async def test_missing_robots_allows_scrape():
    pipeline = ScrapePipeline(FakeFetcher({SPEC.url: page()}), respect_robots=True)
    items = await pipeline.scrape(SPEC)
    assert len(items) == 1


async def test_run_diffs_against_stored_snapshot():
    store = MemoryStateStore()

    first = ScrapePipeline(
        FakeFetcher({SPEC.url: page("€10,00", "In stock")}), respect_robots=False
    )
    _, changes_first = await first.run(SPEC, store=store)
    assert len(changes_first.added) == 1

    second = ScrapePipeline(
        FakeFetcher({SPEC.url: page("€8,00", "Out of stock")}), respect_robots=False
    )
    _, changes_second = await second.run(SPEC, store=store)

    assert len(changes_second.price_changes) == 1
    assert changes_second.price_changes[0].new_price == 8.0
    assert [i.key for i in changes_second.out_of_stock] == ["https://shop.example.com/p/a"]
