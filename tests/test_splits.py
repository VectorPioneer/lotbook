from decimal import Decimal

from conftest import buy, d, sell, split

from lotbook.ledger import Ledger


def test_forward_split_restates_lots():
    ledger = Ledger().run(
        [buy("B1", "2024-05-01", "ABC", 100, 50, fees="5")],
        [split("C1", "2025-03-14", "ABC", 2, 1)],
    )
    (lot,) = ledger.lots
    assert lot.quantity == Decimal("200")
    assert lot.basis == Decimal("5005")
    assert lot.date_acquired == d("2024-05-01")
    assert lot.holding_start == d("2024-05-01")


def test_split_only_touches_its_symbol():
    ledger = Ledger().run(
        [buy("B1", "2024-05-01", "ABC", 100, 50), buy("B2", "2024-05-01", "XYZ", 100, 50)],
        [split("C1", "2025-03-14", "ABC", 2, 1)],
    )
    assert ledger.positions() == {("A1", "ABC"): Decimal("200"), ("A1", "XYZ"): Decimal("100")}


def test_sale_on_split_date_is_in_post_split_shares():
    ledger = Ledger().run(
        [buy("B1", "2024-05-01", "ABC", 100, 50), sell("S1", "2025-03-14", "ABC", 200, 30)],
        [split("C1", "2025-03-14", "ABC", 2, 1)],
    )
    (disposal,) = ledger.disposals
    assert disposal.quantity == 200
    assert disposal.cost_basis == Decimal("5000")
    assert ledger.positions() == {}


def test_buy_after_split_is_not_restated():
    ledger = Ledger().run(
        [buy("B1", "2025-04-01", "ABC", 10, 25)],
        [split("C1", "2025-03-14", "ABC", 2, 1)],
    )
    assert ledger.lots[0].quantity == 10
