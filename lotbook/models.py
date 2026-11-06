"""Core data types for the ledger.

All quantities and money amounts are ``Decimal``. Amounts are kept unrounded
inside the ledger and are only rounded to cents when a report row is written
(see ``lotbook.report``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from lotbook.dates import is_long_term

ZERO = Decimal("0")


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Term(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"


@dataclass(frozen=True)
class Trade:
    """One row of a broker trade export."""

    trade_id: str
    account: str
    date: date
    action: Action
    symbol: str
    quantity: Decimal
    price: Decimal
    fees: Decimal = ZERO
    lot_ref: str | None = None  # buy trade_id to relieve (specific identification)

    @property
    def gross(self) -> Decimal:
        return self.quantity * self.price


@dataclass(frozen=True)
class Split:
    """A forward or reverse stock split, e.g. ``3:2`` (3 new shares for every 2 held)."""

    action_id: str
    date: date
    symbol: str
    new_shares: int
    old_shares: int

    @property
    def ratio(self) -> Decimal:
        return Decimal(self.new_shares // self.old_shares)


@dataclass
class Lot:
    """Shares bought in one purchase that are still held.

    ``basis`` is the total cost basis of the shares in the lot, purchase fees
    included. ``holding_start`` is the date the holding period runs from; it is
    the purchase date unless the policy says otherwise.
    """

    lot_id: str
    trade_id: str
    account: str
    symbol: str
    date_acquired: date
    quantity: Decimal
    basis: Decimal
    holding_start: date
    seq: int

    @property
    def unit_basis(self) -> Decimal:
        return self.basis / self.quantity


@dataclass
class Disposal:
    """Shares from one lot relieved by one sale; one row of the gains report."""

    sale_id: str
    lot_id: str
    account: str
    symbol: str
    quantity: Decimal
    date_acquired: date
    holding_start: date
    date_sold: date
    proceeds: Decimal
    cost_basis: Decimal
    adjustment_code: str = ""
    adjustment: Decimal = ZERO

    @property
    def gain_loss(self) -> Decimal:
        return self.proceeds - self.cost_basis + self.adjustment

    @property
    def term(self) -> Term:
        return Term.LONG if is_long_term(self.holding_start, self.date_sold) else Term.SHORT
