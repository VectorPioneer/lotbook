import io
from decimal import Decimal

from conftest import buy, sell

from lotbook.ledger import Ledger
from lotbook.report import COLUMNS, cents, disposal_row, report_rows, summarize, write_report


def test_cents_rounds_half_up():
    assert cents(Decimal("1.005")) == Decimal("1.01")
    assert cents(Decimal("-1.005")) == Decimal("-1.01")
    assert cents(Decimal("2.004999")) == Decimal("2.00")


def test_gain_is_worked_out_from_rounded_columns():
    ledger = Ledger().run(
        [
            buy("B1", "2025-01-02", "ABC", 3, "10.00", fees="0.01"),
            sell("S1", "2025-02-03", "ABC", 1, "11.00", fees="0.005"),
        ]
    )
    row = disposal_row(ledger.disposals[0])
    assert row["cost_basis"] == "10.00"  # 30.01 / 3 = 10.00333
    assert row["proceeds"] == "11.00"  # 10.995 rounds up
    assert row["gain_loss"] == "1.00"
    assert row["adjustment"] == "0.00" and row["adjustment_code"] == ""


def test_row_columns_and_quantity_format():
    ledger = Ledger().run([buy("B1", "2024-01-02", "ABC", 100, 1), sell("S1", "2025-02-03", "ABC", "12.50", 2)])
    row = disposal_row(ledger.disposals[0])
    assert list(row) == COLUMNS
    assert row["quantity"] == "12.5"
    assert row["term"] == "LONG"


def test_report_is_sorted_and_written_as_csv():
    ledger = Ledger().run(
        [
            buy("B1", "2025-01-02", "XYZ", 10, 1),
            buy("B2", "2025-01-02", "ABC", 10, 1),
            sell("S1", "2025-03-01", "XYZ", 10, 2),
            sell("S2", "2025-03-02", "ABC", 10, 2),
        ]
    )
    assert [r["symbol"] for r in report_rows(ledger.disposals)] == ["ABC", "XYZ"]
    out = io.StringIO()
    write_report(ledger.disposals, out)
    lines = out.getvalue().splitlines()
    assert lines[0] == ",".join(COLUMNS)
    assert len(lines) == 3


def test_summarize_by_term():
    ledger = Ledger().run(
        [
            buy("B1", "2023-01-02", "ABC", 10, 10),
            buy("B2", "2025-01-02", "ABC", 10, 10),
            sell("S1", "2025-03-01", "ABC", 20, 12),
        ]
    )
    totals = summarize(report_rows(ledger.disposals))
    assert totals["LONG"]["gain_loss"] == Decimal("20.00")
    assert totals["SHORT"]["gain_loss"] == Decimal("20.00")
    assert totals["SHORT"]["proceeds"] == Decimal("120.00")
