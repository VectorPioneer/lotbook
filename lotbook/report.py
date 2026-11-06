"""Realized gains report, one row per disposal (policy section 7)."""

from __future__ import annotations

import csv
from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, TextIO

from lotbook.models import ZERO, Disposal, Term

COLUMNS = [
    "account",
    "symbol",
    "quantity",
    "date_acquired",
    "date_sold",
    "proceeds",
    "cost_basis",
    "adjustment_code",
    "adjustment",
    "gain_loss",
    "term",
]

CENT = Decimal("0.01")


def cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def format_quantity(quantity: Decimal) -> str:
    text = format(quantity.normalize(), "f")
    return text


def disposal_row(d: Disposal) -> dict[str, str]:
    proceeds = cents(d.proceeds)
    basis = cents(d.cost_basis)
    adjustment = cents(d.adjustment)
    return {
        "account": d.account,
        "symbol": d.symbol,
        "quantity": format_quantity(d.quantity),
        "date_acquired": d.date_acquired.isoformat(),
        "date_sold": d.date_sold.isoformat(),
        "proceeds": str(proceeds),
        "cost_basis": str(basis),
        "adjustment_code": d.adjustment_code,
        "adjustment": str(adjustment),
        # Gain is computed from the rounded columns so every row adds up.
        "gain_loss": str(proceeds - basis + adjustment),
        "term": d.term.value,
    }


def report_rows(disposals: Iterable[Disposal]) -> list[dict[str, str]]:
    ordered = sorted(
        disposals,
        key=lambda d: (d.account, d.symbol, d.date_sold, d.date_acquired, d.sale_id, d.lot_id),
    )
    return [disposal_row(d) for d in ordered]


def write_report(disposals: Iterable[Disposal], out: TextIO) -> None:
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(report_rows(disposals))


def summarize(rows: Iterable[dict[str, str]]) -> "OrderedDict[str, dict[str, Decimal]]":
    """Totals by term, from report rows (so they match what was written)."""
    totals: "OrderedDict[str, dict[str, Decimal]]" = OrderedDict(
        (term.value, {"proceeds": ZERO, "cost_basis": ZERO, "adjustment": ZERO, "gain_loss": ZERO})
        for term in (Term.SHORT, Term.LONG)
    )
    for row in rows:
        bucket = totals[row["term"]]
        for field in bucket:
            bucket[field] += Decimal(row[field])
    return totals
