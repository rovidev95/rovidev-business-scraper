from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import get_settings
from .fetcher import Fetcher, FetchError, HttpxFetcher
from .models import ChangeSet, ScrapedItem, SourceSpec
from .pipeline import DisallowedByRobots, ScrapePipeline
from .rate_limit import RateLimiter
from .state import JsonStateStore, StateStore


class ScrapeResponse(BaseModel):
    items: list[ScrapedItem]
    changes: ChangeSet | None = None


def create_app(
    *,
    fetcher: Fetcher | None = None,
    store: StateStore | None = None,
    respect_robots: bool | None = None,
) -> FastAPI:
    settings = get_settings()
    active_fetcher = fetcher or HttpxFetcher(timeout=settings.timeout)
    active_store = store if store is not None else JsonStateStore(settings.state_dir)
    pipeline = ScrapePipeline(
        active_fetcher,
        rate_limiter=RateLimiter(settings.min_interval),
        respect_robots=settings.respect_robots if respect_robots is None else respect_robots,
        default_user_agent=settings.user_agent,
    )

    app = FastAPI(title="RoviDev Business Scraper", version="1.0.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/scrape", response_model=ScrapeResponse)
    async def scrape(spec: SourceSpec) -> ScrapeResponse:
        try:
            items, changes = await pipeline.run(spec, store=active_store)
        except DisallowedByRobots as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except FetchError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return ScrapeResponse(items=items, changes=changes)

    @app.get("/sources/{name}", response_model=list[ScrapedItem])
    async def get_source(name: str) -> list[ScrapedItem]:
        return active_store.load(name)

    return app


app = create_app()
