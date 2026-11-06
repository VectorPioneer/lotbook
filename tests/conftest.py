from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from lotbook.models import Action, Split, Trade


def d(text: str) -> date:
    return date.fromisoformat(text)


def buy(trade_id, day, symbol, qty, price, fees="0", account="A1"):
    return Trade(trade_id, account, d(day), Action.BUY, symbol, Decimal(str(qty)), Decimal(str(price)), Decimal(fees))


def sell(trade_id, day, symbol, qty, price, fees="0", account="A1", lot_ref=None):
    return Trade(
        trade_id, account, d(day), Action.SELL, symbol, Decimal(str(qty)), Decimal(str(price)), Decimal(fees), lot_ref
    )


def split(action_id, day, symbol, new, old):
    return Split(action_id, d(day), symbol, new, old)


@pytest.fixture
def write_csv(tmp_path):
    def _write(name: str, text: str):
        path = tmp_path / name
        path.write_text(text.strip() + "\n", encoding="utf-8")
        return path

    return _write
