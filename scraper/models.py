from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class FieldSpec(BaseModel):
    """How to pull a single field out of an item element.

    ``attr`` reads an HTML attribute (e.g. ``href``); when omitted the element's
    text content is used.
    """

    selector: str
    attr: str | None = None


class SourceSpec(BaseModel):
    """A page to scrape and the CSS selectors that describe its items."""

    name: str
    url: str
    item_selector: str
    fields: dict[str, FieldSpec]
    key_field: str = "url"
    user_agent: str | None = None


class ScrapedItem(BaseModel):
    source: str
    key: str
    title: str | None = None
    price: float | None = None
    currency: str | None = None
    in_stock: bool | None = None
    url: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=_utcnow)


class PriceChange(BaseModel):
    key: str
    title: str | None = None
    old_price: float | None = None
    new_price: float | None = None

    @property
    def delta(self) -> float | None:
        if self.old_price is None or self.new_price is None:
            return None
        return round(self.new_price - self.old_price, 2)


class ChangeSet(BaseModel):
    added: list[ScrapedItem] = Field(default_factory=list)
    removed: list[ScrapedItem] = Field(default_factory=list)
    price_changes: list[PriceChange] = Field(default_factory=list)
    back_in_stock: list[ScrapedItem] = Field(default_factory=list)
    out_of_stock: list[ScrapedItem] = Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (
            self.added
            or self.removed
            or self.price_changes
            or self.back_in_stock
            or self.out_of_stock
        )
