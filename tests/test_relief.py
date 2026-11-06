from decimal import Decimal

import pytest
from conftest import d

from lotbook.models import Lot
from lotbook.relief import LotRefError, ReliefMethod, order_lots


def lot(lot_id, day, qty, basis, seq):
    return Lot(
        lot_id=lot_id,
        trade_id=lot_id,
        account="A1",
        symbol="ABC",
        date_acquired=d(day),
        quantity=Decimal(qty),
        basis=Decimal(basis),
        holding_start=d(day),
        seq=seq,
    )


@pytest.fixture
def lots():
    # Listed out of order on purpose.
    return [
        lot("L3", "2025-03-01", 10, 300, 3),
        lot("L1", "2025-01-01", 10, 100, 1),
        lot("L2", "2025-02-01", 10, 500, 2),
        lot("L2b", "2025-02-01", 10, 500, 4),
    ]


def ids(lots):
    return [lot.lot_id for lot in lots]


def test_fifo(lots):
    assert ids(order_lots(lots, ReliefMethod.FIFO)) == ["L1", "L2", "L2b", "L3"]


def test_lifo(lots):
    assert ids(order_lots(lots, ReliefMethod.LIFO)) == ["L3", "L2b", "L2", "L1"]


def test_hifo_ties_oldest_first(lots):
    assert ids(order_lots(lots, ReliefMethod.HIFO)) == ["L2", "L2b", "L3", "L1"]


def test_specific_identification_overrides_method(lots):
    assert ids(order_lots(lots, ReliefMethod.HIFO, lot_ref="L1")) == ["L1"]


def test_specific_identification_unknown_lot(lots):
    with pytest.raises(LotRefError):
        order_lots(lots, ReliefMethod.FIFO, lot_ref="nope")
