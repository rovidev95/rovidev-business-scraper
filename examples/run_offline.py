"""End-to-end demo that runs without touching the network.

A fake fetcher serves two versions of the same catalog page so you can see the
change detection (price drop, out of stock) between consecutive runs.
"""

from __future__ import annotations

import asyncio

from scraper import ScrapePipeline, SourceSpec
from scraper.state import MemoryStateStore

SPEC = SourceSpec(
    name="demo-shop",
    url="https://shop.example.com/laptops",
    item_selector="li.product",
    fields={
        "title": {"selector": "h3"},
        "price": {"selector": ".price"},
        "availability": {"selector": ".stock"},
        "url": {"selector": "a", "attr": "href"},
    },
    key_field="url",
)


def _page(thinkpad_price: str, macbook_stock: str) -> str:
    return f"""
    <ul>
      <li class="product">
        <h3>ThinkPad X1</h3>
        <a href="/p/thinkpad-x1">view</a>
        <span class="price">€1.299,00</span>
        <span class="stock">In stock</span>
      </li>
      <li class="product">
        <h3>MacBook Air</h3>
        <a href="/p/macbook-air">view</a>
        <span class="price">$1,199.00</span>
        <span class="stock">{macbook_stock}</span>
      </li>
      <li class="product">
        <h3>Framework 13</h3>
        <a href="/p/framework-13">view</a>
        <span class="price">{thinkpad_price}</span>
        <span class="stock">In stock</span>
      </li>
    </ul>
    """


class FakeFetcher:
    def __init__(self, html: str) -> None:
        self.html = html

    async def get(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        return self.html


async def main() -> None:
    store = MemoryStateStore()

    first = ScrapePipeline(FakeFetcher(_page("€1.099,00", "In stock")), respect_robots=False)
    items, _ = await first.run(SPEC, store=store)
    print(f"Run 1 — {len(items)} items:")
    for item in items:
        print(f"  {item.title:<14} {item.price} {item.currency}  in_stock={item.in_stock}")

    second = ScrapePipeline(FakeFetcher(_page("€999,00", "Out of stock")), respect_robots=False)
    _, changes = await second.run(SPEC, store=store)
    print("\nRun 2 — detected changes:")
    for change in changes.price_changes:
        print(f"  price {change.title}: {change.old_price} -> {change.new_price} ({change.delta})")
    for item in changes.out_of_stock:
        print(f"  out of stock: {item.title}")


if __name__ == "__main__":
    asyncio.run(main())
