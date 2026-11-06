# lotbook

Cost basis ledger for taxable brokerage accounts. It replays a broker trade
export (plus splits) into tax lots, works out realized gains per lot, and
ties the result out against the broker's Form 1099-B detail.

The rules it follows are in [docs/lot-relief-policy.md](docs/lot-relief-policy.md);
file layouts are in [docs/file-formats.md](docs/file-formats.md).

## Usage

```
python -m lotbook report    --trades T.csv [--actions A.csv] [--method fifo|lifo|hifo] [--year 2025] [--out gains.csv]
python -m lotbook summary   --trades T.csv [--actions A.csv] [--year 2025]
python -m lotbook positions --trades T.csv [--actions A.csv]
python -m lotbook reconcile --trades T.csv [--actions A.csv] --broker 1099b.csv --year 2025
```

`reconcile` exits 0 when the year ties out, 1 when it does not, and 2 on bad
input (unreadable file, selling shares the account does not hold, ...).

Example accounts are in `examples/`:

```
python -m lotbook reconcile --trades examples/acct-1001/trades.csv \
    --actions examples/acct-1001/actions.csv \
    --broker examples/acct-1001/broker-1099b-2025.csv --year 2025
```

## Layout

```
lotbook/
  models.py             Trade, Split, Lot, Disposal
  importers.py          CSV readers
  ledger.py             replays events into lots and disposals
  relief.py             FIFO / LIFO / HIFO / specific identification
  corporate_actions.py  splits
  dates.py              holding periods
  report.py             gains report rows, rounding, totals
  reconcile.py          compare against broker 1099-B
  cli.py                command line
tests/                  pytest suite
examples/               sample accounts with the broker's 1099-B
```

## Development

```
python -m pip install -e ".[dev]"
python -m pytest
```

## Status

- Wash sales (policy section 5) are not implemented yet (#14). Until they are,
  losses are reported in full and accounts with wash sales will not tie out.
