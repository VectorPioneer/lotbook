"""Corporate actions (policy section 6)."""

from __future__ import annotations

from lotbook.models import Lot, Split


def apply_split(lots: list[Lot], split: Split) -> None:
    """Restate every open lot of the symbol in post-split shares.

    The total basis of a lot does not change; only the share count does, so the
    per-share basis moves by the inverse of the ratio. Holding periods carry over.
    """
    for lot in lots:
        if lot.symbol == split.symbol:
            lot.quantity = lot.quantity * split.ratio
