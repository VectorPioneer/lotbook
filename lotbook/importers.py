"""Readers for the CSV files described in docs/file-formats.md."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from lotbook.dates import parse_date
from lotbook.models import ZERO, Action, Split, Trade

TRADE_COLUMNS = ["trade_id", "account", "date", "action", "symbol", "quantity", "price", "fees", "lot_ref"]
ACTION_COLUMNS = ["action_id", "date", "symbol", "type", "ratio"]
BROKER_COLUMNS = [
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


class ImportError_(ValueError):
    """A row in an input file could not be read. The message names file and line."""


def _rows(path: Path, columns: list[str]):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in columns if c not in (reader.fieldnames or [])]
        if missing:
            raise ImportError_(f"{path}: missing columns {', '.join(missing)}")
        for line_no, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue
            yield line_no, {k: (v or "").strip() for k, v in row.items()}


def _decimal(value: str, *, where: str, field: str, default: Decimal | None = None) -> Decimal:
    if value == "" and default is not None:
        return default
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ImportError_(f"{where}: {field} {value!r} is not a number") from None


def read_trades(path: str | Path) -> list[Trade]:
    path = Path(path)
    trades: list[Trade] = []
    seen: set[str] = set()
    for line_no, row in _rows(path, TRADE_COLUMNS):
        where = f"{path}:{line_no}"
        try:
            action = Action(row["action"].upper())
        except ValueError:
            raise ImportError_(f"{where}: unknown action {row['action']!r}") from None
        if row["trade_id"] in seen:
            raise ImportError_(f"{where}: duplicate trade_id {row['trade_id']!r}")
        seen.add(row["trade_id"])
        quantity = _decimal(row["quantity"], where=where, field="quantity")
        if quantity <= 0:
            raise ImportError_(f"{where}: quantity must be positive")
        price = _decimal(row["price"], where=where, field="price")
        if price < 0:
            raise ImportError_(f"{where}: price must not be negative")
        trades.append(
            Trade(
                trade_id=row["trade_id"],
                account=row["account"],
                date=parse_date(row["date"]),
                action=action,
                symbol=row["symbol"].upper(),
                quantity=quantity,
                price=price,
                fees=_decimal(row["fees"], where=where, field="fees", default=ZERO),
                lot_ref=row["lot_ref"] or None,
            )
        )
    return trades


def read_actions(path: str | Path | None) -> list[Split]:
    if path is None:
        return []
    path = Path(path)
    splits: list[Split] = []
    for line_no, row in _rows(path, ACTION_COLUMNS):
        where = f"{path}:{line_no}"
        if row["type"].upper() != "SPLIT":
            raise ImportError_(f"{where}: unsupported corporate action {row['type']!r}")
        try:
            new, old = (int(part) for part in row["ratio"].split(":"))
        except ValueError:
            raise ImportError_(f"{where}: ratio {row['ratio']!r} is not of the form NEW:OLD") from None
        if new <= 0 or old <= 0:
            raise ImportError_(f"{where}: ratio parts must be positive")
        splits.append(
            Split(
                action_id=row["action_id"],
                date=parse_date(row["date"]),
                symbol=row["symbol"].upper(),
                new_shares=new,
                old_shares=old,
            )
        )
    return splits


def read_broker_1099b(path: str | Path) -> list[dict[str, str]]:
    """Broker 1099-B detail rows, as strings keyed like ``report.COLUMNS``."""
    path = Path(path)
    return [row for _, row in _rows(path, BROKER_COLUMNS)]
