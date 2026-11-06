from decimal import Decimal

import pytest
from conftest import d

from lotbook.importers import ImportError_, read_actions, read_broker_1099b, read_trades
from lotbook.models import Action

HEADER = "trade_id,account,date,action,symbol,quantity,price,fees,lot_ref"


def test_reads_trades(write_csv):
    path = write_csv(
        "trades.csv",
        f"""
{HEADER}
T1,A1,2025-01-02,BUY,abc,10,12.50,1.00,
T2,A1,2025-02-03,sell,ABC,4.5,13,,T1
""",
    )
    t1, t2 = read_trades(path)
    assert t1.action is Action.BUY and t1.symbol == "ABC"
    assert t1.quantity == Decimal("10") and t1.fees == Decimal("1.00")
    assert t2.action is Action.SELL and t2.date == d("2025-02-03")
    assert t2.fees == Decimal("0") and t2.lot_ref == "T1"
    assert t2.quantity == Decimal("4.5")


def test_blank_lines_are_skipped(write_csv):
    path = write_csv("trades.csv", f"{HEADER}\nT1,A1,2025-01-02,BUY,ABC,10,1,,\n,,,,,,,,\n")
    assert len(read_trades(path)) == 1


def test_missing_column(write_csv):
    path = write_csv("trades.csv", "trade_id,account,date\nT1,A1,2025-01-02")
    with pytest.raises(ImportError_, match="missing columns"):
        read_trades(path)


@pytest.mark.parametrize(
    "row, message",
    [
        ("T1,A1,2025-01-02,HOLD,ABC,10,1,,", "unknown action"),
        ("T1,A1,2025-01-02,BUY,ABC,0,1,,", "quantity must be positive"),
        ("T1,A1,2025-01-02,BUY,ABC,ten,1,,", "quantity 'ten' is not a number"),
        ("T1,A1,2025-01-02,BUY,ABC,10,-1,,", "price must not be negative"),
    ],
)
def test_bad_trade_rows(write_csv, row, message):
    path = write_csv("trades.csv", f"{HEADER}\n{row}")
    with pytest.raises(ImportError_, match=message):
        read_trades(path)


def test_error_names_file_and_line(write_csv):
    path = write_csv("trades.csv", f"{HEADER}\nT1,A1,2025-01-02,BUY,ABC,10,1,,\nT2,A1,2025-01-02,BUY,ABC,x,1,,")
    with pytest.raises(ImportError_, match=r"trades.csv:3"):
        read_trades(path)


def test_duplicate_trade_id(write_csv):
    path = write_csv("trades.csv", f"{HEADER}\nT1,A1,2025-01-02,BUY,ABC,10,1,,\nT1,A1,2025-01-03,BUY,ABC,1,1,,")
    with pytest.raises(ImportError_, match="duplicate trade_id"):
        read_trades(path)


def test_reads_splits(write_csv):
    path = write_csv(
        "actions.csv",
        """
action_id,date,symbol,type,ratio
CA1,2025-03-14,xyz,SPLIT,2:1
""",
    )
    (s,) = read_actions(path)
    assert s.symbol == "XYZ" and s.new_shares == 2 and s.old_shares == 1
    assert s.date == d("2025-03-14")


def test_no_actions_file():
    assert read_actions(None) == []


@pytest.mark.parametrize(
    "row, message",
    [
        ("CA1,2025-03-14,XYZ,DIVIDEND,", "unsupported corporate action"),
        ("CA1,2025-03-14,XYZ,SPLIT,2-1", "not of the form NEW:OLD"),
        ("CA1,2025-03-14,XYZ,SPLIT,0:1", "must be positive"),
    ],
)
def test_bad_actions(write_csv, row, message):
    path = write_csv("actions.csv", f"action_id,date,symbol,type,ratio\n{row}")
    with pytest.raises(ImportError_, match=message):
        read_actions(path)


def test_reads_broker_rows(write_csv):
    path = write_csv(
        "b.csv",
        """
account,symbol,quantity,date_acquired,date_sold,proceeds,cost_basis,adjustment_code,adjustment,gain_loss,term
A1,ABC,10,2025-01-02,2025-02-03,130.00,125.00,,0.00,5.00,SHORT
""",
    )
    (row,) = read_broker_1099b(path)
    assert row["proceeds"] == "130.00" and row["term"] == "SHORT"
