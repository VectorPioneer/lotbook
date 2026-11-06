"""Lot relief methods (policy section 3): which lots a sale takes shares from."""

from __future__ import annotations

from enum import Enum

from lotbook.models import Lot


class ReliefMethod(str, Enum):
    FIFO = "fifo"
    LIFO = "lifo"
    HIFO = "hifo"


class LotRefError(LookupError):
    """A specific-identification sale names a lot the account does not hold."""


def _fifo_key(lot: Lot):
    return (lot.date_acquired, lot.seq)


def order_lots(lots: list[Lot], method: ReliefMethod, lot_ref: str | None = None) -> list[Lot]:
    """Return the open lots in the order a sale relieves them.

    When ``lot_ref`` is given (specific identification) only the lots from that
    purchase are returned, oldest first, whatever the account's method is.
    """
    if lot_ref is not None:
        chosen = [lot for lot in lots if lot.trade_id == lot_ref]
        if not chosen:
            raise LotRefError(f"no open lot from purchase {lot_ref!r}")
        return sorted(chosen, key=_fifo_key)
    if method is ReliefMethod.FIFO:
        return sorted(lots, key=_fifo_key)
    if method is ReliefMethod.LIFO:
        return sorted(lots, key=_fifo_key, reverse=True)
    if method is ReliefMethod.HIFO:
        # Highest per-share basis first; ties broken oldest first.
        by_age = sorted(lots, key=_fifo_key)
        return sorted(by_age, key=lambda lot: lot.unit_basis, reverse=True)
    raise ValueError(f"unknown relief method {method!r}")
