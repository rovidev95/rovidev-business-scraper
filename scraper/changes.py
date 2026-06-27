from __future__ import annotations

from .models import ChangeSet, PriceChange, ScrapedItem


def _index(items: list[ScrapedItem]) -> dict[str, ScrapedItem]:
    return {item.key: item for item in items}


def diff(previous: list[ScrapedItem], current: list[ScrapedItem]) -> ChangeSet:
    """Compare two snapshots and report added/removed items, price moves and
    stock transitions. Items are matched by their ``key``.
    """
    prev = _index(previous)
    cur = _index(current)

    changes = ChangeSet(
        added=[cur[k] for k in cur if k not in prev],
        removed=[prev[k] for k in prev if k not in cur],
    )

    for key in cur:
        before = prev.get(key)
        if before is None:
            continue
        after = cur[key]

        if before.price != after.price and not (before.price is None and after.price is None):
            changes.price_changes.append(
                PriceChange(
                    key=key,
                    title=after.title,
                    old_price=before.price,
                    new_price=after.price,
                )
            )

        if before.in_stock is False and after.in_stock is True:
            changes.back_in_stock.append(after)
        elif before.in_stock is True and after.in_stock is False:
            changes.out_of_stock.append(after)

    return changes
