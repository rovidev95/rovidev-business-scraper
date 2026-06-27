from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Protocol

from .models import ScrapedItem


class StateStore(Protocol):
    """Persists the last snapshot per source so runs can detect changes."""

    def load(self, source: str) -> list[ScrapedItem]: ...
    def save(self, source: str, items: list[ScrapedItem]) -> None: ...


class MemoryStateStore:
    def __init__(self) -> None:
        self._data: dict[str, list[ScrapedItem]] = {}

    def load(self, source: str) -> list[ScrapedItem]:
        return list(self._data.get(source, []))

    def save(self, source: str, items: list[ScrapedItem]) -> None:
        self._data[source] = list(items)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-") or "source"


class JsonStateStore:
    """Stores each source's latest snapshot as a JSON file in a directory."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def _path(self, source: str) -> Path:
        return self.directory / f"{_slug(source)}.json"

    def load(self, source: str) -> list[ScrapedItem]:
        path = self._path(source)
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [ScrapedItem.model_validate(entry) for entry in raw]

    def save(self, source: str, items: list[ScrapedItem]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = [item.model_dump(mode="json") for item in items]
        self._path(source).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
