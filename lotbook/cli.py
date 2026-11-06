"""Command line interface: ``python -m lotbook <command> ...``."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from lotbook.importers import ImportError_, read_actions, read_broker_1099b, read_trades
from lotbook.ledger import InsufficientSharesError, Ledger
from lotbook.relief import LotRefError, ReliefMethod
from lotbook.report import format_quantity, report_rows, summarize, write_report


def _add_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--trades", required=True, help="trade export CSV")
    parser.add_argument("--actions", help="corporate actions CSV")
    parser.add_argument(
        "--method",
        choices=[m.value for m in ReliefMethod],
        default=ReliefMethod.FIFO.value,
        help="default lot relief method (sales with a lot_ref always use that lot)",
    )


def _ledger(args: argparse.Namespace) -> Ledger:
    trades = read_trades(args.trades)
    splits = read_actions(args.actions)
    return Ledger(ReliefMethod(args.method)).run(trades, splits)


def cmd_report(args: argparse.Namespace) -> int:
    ledger = _ledger(args)
    disposals = ledger.disposals_in(args.year)
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            write_report(disposals, fh)
    else:
        write_report(disposals, sys.stdout)
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    ledger = _ledger(args)
    totals = summarize(report_rows(ledger.disposals_in(args.year)))
    print(f"{'term':<6} {'proceeds':>14} {'cost_basis':>14} {'adjustment':>12} {'gain_loss':>12}")
    for term, t in totals.items():
        print(
            f"{term:<6} {t['proceeds']:>14} {t['cost_basis']:>14} "
            f"{t['adjustment']:>12} {t['gain_loss']:>12}"
        )
    return 0


def cmd_positions(args: argparse.Namespace) -> int:
    ledger = _ledger(args)
    for (account, symbol), quantity in ledger.positions().items():
        print(f"{account}\t{symbol}\t{format_quantity(quantity)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    from lotbook.reconcile import reconcile

    ledger = _ledger(args)
    ours = report_rows(ledger.disposals_in(args.year))
    broker = [row for row in read_broker_1099b(args.broker) if row["date_sold"].startswith(str(args.year))]
    result = reconcile(ours, broker)

    print(f"matched rows: {result.matched}")
    for diff in result.differences:
        print(f"DIFF  {diff.describe()}")
    for row in result.only_ours:
        print(f"OURS  {row['account']} {row['symbol']} {row['quantity']} acquired {row['date_acquired']} sold {row['date_sold']}")
    for row in result.only_broker:
        print(f"BROKER {row['account']} {row['symbol']} {row['quantity']} acquired {row['date_acquired']} sold {row['date_sold']}")
    if result.ties_out:
        print("ties out")
        return 0
    print(
        f"does not tie out: {len(result.differences)} differences, "
        f"{len(result.only_ours)} rows only in ours, {len(result.only_broker)} rows only in broker"
    )
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lotbook", description="Cost basis ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("report", help="realized gains, one row per lot relieved")
    _add_inputs(p)
    p.add_argument("--year", type=int, help="only sales in this tax year")
    p.add_argument("--out", help="write CSV here instead of stdout")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("summary", help="totals by term")
    _add_inputs(p)
    p.add_argument("--year", type=int)
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("positions", help="shares held after the last trade")
    _add_inputs(p)
    p.set_defaults(func=cmd_positions)

    p = sub.add_parser("reconcile", help="compare against a broker 1099-B CSV")
    _add_inputs(p)
    p.add_argument("--broker", required=True, help="broker 1099-B detail CSV")
    p.add_argument("--year", type=int, required=True)
    p.set_defaults(func=cmd_reconcile)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ImportError_, InsufficientSharesError, LotRefError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
