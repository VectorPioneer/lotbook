"""The ledger: replays trades and corporate actions into lots and disposals."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable, Union

from lotbook.corporate_actions import apply_split
from lotbook.models import ZERO, Action, Disposal, Lot, Split, Trade
from lotbook.relief import ReliefMethod, order_lots

Event = Union[Trade, Split]


class InsufficientSharesError(ValueError):
    """A sale asks for more shares than the account holds at that point."""


def build_events(trades: Iterable[Trade], splits: Iterable[Split]) -> list[Event]:
    """Order events by date. On one date, splits come first (they take effect at
    the open), then trades in the order they appear in the export."""
    keyed: list[tuple] = []
    for i, split in enumerate(splits):
        keyed.append((split.date, 0, i, split))
    for i, trade in enumerate(trades):
        keyed.append((trade.date, 1, i, trade))
    keyed.sort(key=lambda item: item[:3])
    return [item[3] for item in keyed]


class Ledger:
    def __init__(self, method: ReliefMethod = ReliefMethod.FIFO) -> None:
        self.method = method
        self.lots: list[Lot] = []
        self.disposals: list[Disposal] = []
        self._seq = 0

    # -- replay -----------------------------------------------------------

    def run(self, trades: Iterable[Trade], splits: Iterable[Split] = ()) -> "Ledger":
        for event in build_events(trades, splits):
            if isinstance(event, Split):
                apply_split(self.lots, event)
            elif event.action is Action.BUY:
                self.buy(event)
            else:
                self.sell(event)
        return self

    def buy(self, trade: Trade) -> Lot:
        self._seq += 1
        lot = Lot(
            lot_id=trade.trade_id,
            trade_id=trade.trade_id,
            account=trade.account,
            symbol=trade.symbol,
            date_acquired=trade.date,
            quantity=trade.quantity,
            basis=trade.gross + trade.fees,
            holding_start=trade.date,
            seq=self._seq,
        )
        self.lots.append(lot)
        return lot

    def sell(self, trade: Trade) -> list[Disposal]:
        open_lots = self.open_lots(trade.account, trade.symbol)
        held = sum((lot.quantity for lot in open_lots), ZERO)
        if held < trade.quantity:
            raise InsufficientSharesError(
                f"sale {trade.trade_id} on {trade.date}: {trade.account} sells "
                f"{trade.quantity} {trade.symbol} but holds {held}"
            )

        candidates = order_lots(open_lots, self.method, trade.lot_ref)
        net_proceeds = trade.gross - trade.fees
        remaining = trade.quantity
        made: list[Disposal] = []
        for lot in candidates:
            if remaining == 0:
                break
            take = min(remaining, lot.quantity)
            basis = lot.basis * take / lot.quantity
            made.append(
                Disposal(
                    sale_id=trade.trade_id,
                    lot_id=lot.lot_id,
                    account=trade.account,
                    symbol=trade.symbol,
                    quantity=take,
                    date_acquired=lot.date_acquired,
                    holding_start=lot.holding_start,
                    date_sold=trade.date,
                    proceeds=net_proceeds * take / trade.quantity,
                    cost_basis=basis,
                )
            )
            lot.quantity -= take
            lot.basis -= basis
            remaining -= take

        if remaining:
            raise InsufficientSharesError(
                f"sale {trade.trade_id}: lot {trade.lot_ref} has only "
                f"{trade.quantity - remaining} of the {trade.quantity} shares sold"
            )

        # TODO(#14): wash sales (docs/lot-relief-policy.md section 5) are not
        # applied yet, so every loss is reported in full.
        self.lots = [lot for lot in self.lots if lot.quantity > 0]
        self.disposals.extend(made)
        return made

    # -- queries ----------------------------------------------------------

    def open_lots(self, account: str, symbol: str) -> list[Lot]:
        return [lot for lot in self.lots if lot.account == account and lot.symbol == symbol]

    def positions(self) -> dict[tuple[str, str], Decimal]:
        totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
        for lot in self.lots:
            totals[(lot.account, lot.symbol)] += lot.quantity
        return dict(sorted(totals.items()))

    def disposals_in(self, year: int | None) -> list[Disposal]:
        if year is None:
            return list(self.disposals)
        return [d for d in self.disposals if d.date_sold.year == year]
