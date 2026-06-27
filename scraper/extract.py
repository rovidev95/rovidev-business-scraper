from __future__ import annotations

from bs4 import BeautifulSoup

from .models import SourceSpec


def extract(html: str, spec: SourceSpec) -> list[dict[str, str | None]]:
    """Turn a page into a list of raw field dictionaries, one per item element."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str | None]] = []
    for node in soup.select(spec.item_selector):
        row: dict[str, str | None] = {}
        for field_name, field in spec.fields.items():
            element = node.select_one(field.selector)
            if element is None:
                row[field_name] = None
            elif field.attr:
                value = element.get(field.attr)
                if isinstance(value, list):
                    value = " ".join(value)
                row[field_name] = value
            else:
                row[field_name] = element.get_text(strip=True)
        rows.append(row)
    return rows
