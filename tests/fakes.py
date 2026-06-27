from __future__ import annotations

from scraper.fetcher import FetchError


class FakeFetcher:
    """In-memory fetcher mapping URLs to response bodies.

    Unknown URLs raise :class:`FetchError`, mirroring a 404. Records every
    requested URL in ``calls`` for assertions.
    """

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.calls: list[str] = []

    async def get(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        self.calls.append(url)
        if url not in self.pages:
            raise FetchError(url, "not found", status=404)
        return self.pages[url]
