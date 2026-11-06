"""Tie our gains report out against the broker's 1099-B detail (policy section 8)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

MONEY_FIELDS = ("proceeds", "cost_basis", "adjustment", "gain_loss")
TEXT_FIELDS = ("adjustment_code", "term")
TOLERANCE = Decimal("0.01")

RowKey = tuple[str, str, str, str, str]


def row_key(row: dict[str, str]) -> RowKey:
    quantity = format(Decimal(row["quantity"]).normalize(), "f")
    return (row["account"], row["symbol"], row["date_acquired"], row["date_sold"], quantity)


@dataclass
class Difference:
    key: RowKey
    field: str
    ours: str
    broker: str

    def describe(self) -> str:
        account, symbol, acquired, sold, quantity = self.key
        return (
            f"{account} {symbol} {quantity} acquired {acquired} sold {sold}: "
            f"{self.field} ours={self.ours or '-'} broker={self.broker or '-'}"
        )


@dataclass
class ReconcileResult:
    matched: int = 0
    differences: list[Difference] = field(default_factory=list)
    only_ours: list[dict[str, str]] = field(default_factory=list)
    only_broker: list[dict[str, str]] = field(default_factory=list)

    @property
    def ties_out(self) -> bool:
        return not (self.differences or self.only_ours or self.only_broker)


def _money(value: str) -> Decimal:
    return Decimal(value) if value else Decimal("0")


def reconcile(ours: list[dict[str, str]], broker: list[dict[str, str]]) -> ReconcileResult:
    """Match rows on account, symbol, dates and quantity, then compare the rest.

    Rows with the same key are paired in the order they appear in each file.
    """
    result = ReconcileResult()
    pending: dict[RowKey, list[dict[str, str]]] = defaultdict(list)
    for row in broker:
        pending[row_key(row)].append(row)

    for row in ours:
        key = row_key(row)
        if not pending.get(key):
            result.only_ours.append(row)
            continue
        theirs = pending[key].pop(0)
        result.matched += 1
        for name in MONEY_FIELDS:
            if abs(_money(row[name]) - _money(theirs[name])) > TOLERANCE:
                result.differences.append(Difference(key, name, row[name], theirs[name]))
        for name in TEXT_FIELDS:
            if row[name].upper() != theirs[name].upper():
                result.differences.append(Difference(key, name, row[name], theirs[name]))

    for rows in pending.values():
        result.only_broker.extend(rows)
    return result
