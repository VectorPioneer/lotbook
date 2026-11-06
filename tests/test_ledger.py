from decimal import Decimal

import pytest
from conftest import buy, d, sell, split

from lotbook.ledger import InsufficientSharesError, Ledger, build_events
from lotbook.models import Term
from lotbook.relief import ReliefMethod


def test_buy_basis_includes_fees():
    ledger = Ledger().run([buy("B1", "2025-01-02", "ABC", 10, "12.50", fees="1.00")])
    (lot,) = ledger.lots
    assert lot.basis == Decimal("126.00")
    assert lot.holding_start == d("2025-01-02")


def test_partial_sale_takes_basis_in_proportion():
    ledger = Ledger().run(
        [
            buy("B1", "2024-01-02", "ABC", 10, 10, fees="3"),
            sell("S1", "2025-06-02", "ABC", 4, 15, fees="2"),
        ]
    )
    (disposal,) = ledger.disposals
    assert disposal.quantity == 4
    assert disposal.cost_basis == Decimal("41.2")
    assert disposal.proceeds == Decimal("58")
    assert disposal.gain_loss == Decimal("16.8")
    assert disposal.term is Term.LONG
    (lot,) = ledger.lots
    assert lot.quantity == 6 and lot.basis == Decimal("61.8")


def test_sale_across_lots_shares_out_proceeds():
    ledger = Ledger().run(
        [
            buy("B1", "2025-01-02", "ABC", 10, 10),
            buy("B2", "2025-01-03", "ABC", 30, 20),
            sell("S1", "2025-02-01", "ABC", 20, 25, fees="10"),
        ]
    )
    first, second = ledger.disposals
    assert (first.lot_id, first.quantity, first.proceeds) == ("B1", 10, Decimal("245"))
    assert (second.lot_id, second.quantity, second.proceeds) == ("B2", 10, Decimal("245"))
    assert second.cost_basis == Decimal("200")


def test_relief_method_is_used():
    ledger = Ledger(ReliefMethod.HIFO).run(
        [
            buy("B1", "2025-01-02", "ABC", 10, 10),
            buy("B2", "2025-01-03", "ABC", 10, 30),
            sell("S1", "2025-02-01", "ABC", 5, 25),
        ]
    )
    assert ledger.disposals[0].lot_id == "B2"


def test_specific_identification():
    ledger = Ledger().run(
        [
            buy("B1", "2025-01-02", "ABC", 10, 10),
            buy("B2", "2025-01-03", "ABC", 10, 30),
            sell("S1", "2025-02-01", "ABC", 5, 25, lot_ref="B2"),
        ]
    )
    assert ledger.disposals[0].lot_id == "B2"


def test_specific_identification_short_of_shares():
    trades = [
        buy("B1", "2025-01-02", "ABC", 10, 10),
        buy("B2", "2025-01-03", "ABC", 3, 30),
        sell("S1", "2025-02-01", "ABC", 5, 25, lot_ref="B2"),
    ]
    with pytest.raises(InsufficientSharesError, match="lot B2 has only 3"):
        Ledger().run(trades)


def test_selling_more_than_held():
    trades = [buy("B1", "2025-01-02", "ABC", 10, 10), sell("S1", "2025-02-01", "ABC", 11, 10)]
    with pytest.raises(InsufficientSharesError, match="holds 10"):
        Ledger().run(trades)


def test_accounts_are_kept_apart():
    trades = [
        buy("B1", "2025-01-02", "ABC", 10, 10, account="A1"),
        buy("B2", "2025-01-02", "ABC", 10, 10, account="A2"),
        sell("S1", "2025-02-01", "ABC", 10, 12, account="A1"),
    ]
    ledger = Ledger().run(trades)
    assert ledger.positions() == {("A2", "ABC"): Decimal("10")}


def test_positions():
    ledger = Ledger().run(
        [
            buy("B1", "2025-01-02", "ABC", 10, 10),
            buy("B2", "2025-01-02", "XYZ", 5, 10),
            sell("S1", "2025-02-01", "ABC", 4, 12),
        ]
    )
    assert ledger.positions() == {("A1", "ABC"): Decimal("6"), ("A1", "XYZ"): Decimal("5")}


def test_events_ordered_by_date_then_splits_then_export_order():
    t1 = buy("B1", "2025-03-01", "ABC", 1, 1)
    t2 = sell("S1", "2025-03-01", "ABC", 1, 1)
    t0 = buy("B0", "2025-02-01", "ABC", 1, 1)
    s1 = split("C1", "2025-03-01", "ABC", 2, 1)
    assert build_events([t1, t2, t0], [s1]) == [t0, s1, t1, t2]


def test_disposals_in_year():
    ledger = Ledger().run(
        [
            buy("B1", "2024-01-02", "ABC", 10, 10),
            sell("S1", "2024-12-31", "ABC", 4, 12),
            sell("S2", "2025-01-02", "ABC", 4, 12),
        ]
    )
    assert [x.sale_id for x in ledger.disposals_in(2025)] == ["S2"]
    assert len(ledger.disposals_in(None)) == 2
