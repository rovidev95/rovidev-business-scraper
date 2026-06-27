from scraper.changes import diff
from scraper.models import ScrapedItem


def item(key: str, price=None, in_stock=None, title=None) -> ScrapedItem:
    return ScrapedItem(source="s", key=key, title=title or key, price=price, in_stock=in_stock)


def test_detects_added_and_removed():
    changes = diff([item("a")], [item("a"), item("b")])
    assert [i.key for i in changes.added] == ["b"]
    assert changes.removed == []

    changes = diff([item("a"), item("b")], [item("a")])
    assert [i.key for i in changes.removed] == ["b"]


def test_detects_price_change_with_delta():
    changes = diff([item("a", price=10.0)], [item("a", price=8.5)])
    assert len(changes.price_changes) == 1
    change = changes.price_changes[0]
    assert change.old_price == 10.0
    assert change.new_price == 8.5
    assert change.delta == -1.5


def test_no_price_change_when_equal():
    assert diff([item("a", price=10.0)], [item("a", price=10.0)]).price_changes == []


def test_stock_transitions():
    changes = diff([item("a", in_stock=False)], [item("a", in_stock=True)])
    assert [i.key for i in changes.back_in_stock] == ["a"]
    assert changes.out_of_stock == []

    changes = diff([item("a", in_stock=True)], [item("a", in_stock=False)])
    assert [i.key for i in changes.out_of_stock] == ["a"]


def test_empty_changeset_flag():
    assert diff([item("a", price=1.0)], [item("a", price=1.0)]).is_empty
