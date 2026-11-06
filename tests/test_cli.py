import pytest

from lotbook.cli import main

TRADES = """
trade_id,account,date,action,symbol,quantity,price,fees,lot_ref
T1,A1,2024-01-02,BUY,ABC,10,10.00,1.00,
T2,A1,2025-02-03,SELL,ABC,4,15.00,1.00,
T3,A1,2025-02-03,BUY,XYZ,5,20.00,,
"""

BROKER = """
account,symbol,quantity,date_acquired,date_sold,proceeds,cost_basis,adjustment_code,adjustment,gain_loss,term
A1,ABC,4,2024-01-02,2025-02-03,59.00,40.40,,0.00,18.60,LONG
"""


@pytest.fixture
def trades(write_csv):
    return write_csv("trades.csv", TRADES)


def test_report_to_stdout(trades, capsys):
    assert main(["report", "--trades", str(trades), "--year", "2025"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[1] == "A1,ABC,4,2024-01-02,2025-02-03,59.00,40.40,,0.00,18.60,LONG"


def test_report_to_file(trades, tmp_path):
    target = tmp_path / "out.csv"
    assert main(["report", "--trades", str(trades), "--out", str(target)]) == 0
    assert target.read_text().count("\n") == 2


def test_positions(trades, capsys):
    assert main(["positions", "--trades", str(trades)]) == 0
    assert capsys.readouterr().out.splitlines() == ["A1\tABC\t6", "A1\tXYZ\t5"]


def test_summary(trades, capsys):
    assert main(["summary", "--trades", str(trades), "--year", "2025"]) == 0
    out = capsys.readouterr().out
    assert "LONG" in out and "18.60" in out


def test_reconcile_ties_out(trades, write_csv, capsys):
    broker = write_csv("broker.csv", BROKER)
    code = main(["reconcile", "--trades", str(trades), "--broker", str(broker), "--year", "2025"])
    assert code == 0
    assert "ties out" in capsys.readouterr().out


def test_reconcile_reports_differences(trades, write_csv, capsys):
    broker = write_csv("broker.csv", BROKER.replace("40.40,,0.00,18.60", "41.40,,0.00,17.60"))
    code = main(["reconcile", "--trades", str(trades), "--broker", str(broker), "--year", "2025"])
    assert code == 1
    out = capsys.readouterr().out
    assert "DIFF" in out and "cost_basis" in out


def test_errors_exit_2(write_csv, capsys):
    bad = write_csv("t.csv", TRADES.replace("SELL,ABC,4", "SELL,ABC,40"))
    assert main(["report", "--trades", str(bad)]) == 2
    assert "holds 10" in capsys.readouterr().err
