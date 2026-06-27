from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Protocol

from .models import ChangeSet, ScrapedItem

_COLUMNS = ["source", "key", "title", "price", "currency", "in_stock", "url", "scraped_at"]


class Sink(Protocol):
    """Receives the items (and computed changes) produced by a run."""

    def write(self, items: list[ScrapedItem], changes: ChangeSet | None = None) -> None: ...


class MemorySink:
    def __init__(self) -> None:
        self.items: list[ScrapedItem] = []
        self.changes: ChangeSet | None = None

    def write(self, items: list[ScrapedItem], changes: ChangeSet | None = None) -> None:
        self.items = list(items)
        self.changes = changes


class JsonSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, items: list[ScrapedItem], changes: ChangeSet | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "items": [item.model_dump(mode="json") for item in items],
            "changes": changes.model_dump(mode="json") if changes else None,
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


class CsvSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, items: list[ScrapedItem], changes: ChangeSet | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=_COLUMNS)
            writer.writeheader()
            for item in items:
                row = item.model_dump(mode="json")
                writer.writerow({column: row.get(column) for column in _COLUMNS})


class GoogleSheetsSink:
    """Appends each run's rows to a Google Sheet.

    Requires the ``sheets`` extra (``pip install rovidev-business-scraper[sheets]``)
    and a service-account JSON key with edit access to the spreadsheet.
    """

    def __init__(
        self, credentials_path: str, spreadsheet_id: str, worksheet: str = "items"
    ) -> None:
        import gspread  # imported lazily so the core has no hard dependency

        self._client = gspread.service_account(filename=credentials_path)
        self._spreadsheet = self._client.open_by_key(spreadsheet_id)
        self._worksheet_name = worksheet

    def _worksheet(self):
        try:
            return self._spreadsheet.worksheet(self._worksheet_name)
        except Exception:
            sheet = self._spreadsheet.add_worksheet(
                self._worksheet_name, rows=1, cols=len(_COLUMNS)
            )
            sheet.append_row(_COLUMNS)
            return sheet

    def write(self, items: list[ScrapedItem], changes: ChangeSet | None = None) -> None:
        sheet = self._worksheet()
        rows = []
        for item in items:
            data = item.model_dump(mode="json")
            rows.append([data.get(column) for column in _COLUMNS])
        if rows:
            sheet.append_rows(rows, value_input_option="USER_ENTERED")
