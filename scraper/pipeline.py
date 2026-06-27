from __future__ import annotations

import logging
from collections.abc import Sequence
from urllib.parse import urljoin

from .changes import diff
from .extract import extract
from .fetcher import Fetcher, FetchError
from .models import ChangeSet, ScrapedItem, SourceSpec
from .normalize import parse_currency, parse_price, parse_stock
from .rate_limit import RateLimiter
from .robots import is_allowed, robots_url_for
from .sinks import Sink
from .state import StateStore

DEFAULT_USER_AGENT = "RoviDevBot/1.0 (+https://rovidev.com)"


class DisallowedByRobots(RuntimeError):
    def __init__(self, url: str) -> None:
        super().__init__(f"Fetching is disallowed by robots.txt: {url}")
        self.url = url


class ScrapePipeline:
    """Fetches a source politely and turns it into normalized items.

    Politeness is built in: robots.txt is honored by default and a rate limiter
    spaces out requests per host. The fetcher is injected, so the same pipeline
    runs against live sites or against fixtures in tests.
    """

    def __init__(
        self,
        fetcher: Fetcher,
        *,
        rate_limiter: RateLimiter | None = None,
        respect_robots: bool = True,
        default_user_agent: str = DEFAULT_USER_AGENT,
        logger: logging.Logger | None = None,
    ) -> None:
        self._fetcher = fetcher
        self._rate_limiter = rate_limiter
        self._respect_robots = respect_robots
        self._default_user_agent = default_user_agent
        self._log = logger or logging.getLogger("scraper")
        self._robots_cache: dict[str, str | None] = {}

    async def scrape(self, spec: SourceSpec) -> list[ScrapedItem]:
        user_agent = spec.user_agent or self._default_user_agent

        if self._respect_robots:
            robots_txt = await self._load_robots(spec.url, user_agent)
            if not is_allowed(robots_txt, spec.url, user_agent):
                raise DisallowedByRobots(spec.url)

        if self._rate_limiter is not None:
            await self._rate_limiter.acquire(spec.url)

        html = await self._fetcher.get(spec.url, headers={"User-Agent": user_agent})
        rows = extract(html, spec)
        items = [self._to_item(spec, row) for row in rows]
        self._log.info("scraped %d items from %s", len(items), spec.name)
        return items

    async def run(
        self,
        spec: SourceSpec,
        *,
        store: StateStore | None = None,
        sinks: Sequence[Sink] = (),
    ) -> tuple[list[ScrapedItem], ChangeSet | None]:
        items = await self.scrape(spec)

        changes: ChangeSet | None = None
        if store is not None:
            changes = diff(store.load(spec.name), items)
            store.save(spec.name, items)

        for sink in sinks:
            sink.write(items, changes)

        return items, changes

    async def _load_robots(self, url: str, user_agent: str) -> str | None:
        robots_url = robots_url_for(url)
        if robots_url in self._robots_cache:
            return self._robots_cache[robots_url]
        try:
            body: str | None = await self._fetcher.get(
                robots_url, headers={"User-Agent": user_agent}
            )
        except FetchError:
            body = None
        self._robots_cache[robots_url] = body
        return body

    def _to_item(self, spec: SourceSpec, row: dict[str, str | None]) -> ScrapedItem:
        known = {"title", "price", "currency", "availability", "url"}
        price_text = row.get("price")
        url = row.get("url")
        if url:
            url = urljoin(spec.url, url)

        key_source = url if spec.key_field == "url" else row.get(spec.key_field)
        key_value = key_source or url or row.get("title")
        return ScrapedItem(
            source=spec.name,
            key=str(key_value),
            title=row.get("title"),
            price=parse_price(price_text),
            currency=parse_currency(row.get("currency"), price_text),
            in_stock=parse_stock(row.get("availability")),
            url=url,
            extra={k: v for k, v in row.items() if k not in known and v is not None},
        )
