# Working on lotbook

- `docs/lot-relief-policy.md` is the spec. It comes from Tax Ops; follow it
  even where it differs from what you know about IRS rules, and say so if you
  think it is wrong rather than changing behaviour on your own.
- Money and quantities are `Decimal` end to end. No floats, and no rounding
  inside the ledger; round only in `report.py`.
- No new runtime dependencies (standard library only). pytest is the only dev
  dependency.
- Keep the CLI and the CSV formats backwards compatible; other teams script
  against them.
- Run the tests with `python -m pytest`. New behaviour needs tests.
- The `examples/` accounts are real-shaped test data. Do not edit the broker
  1099-B files to make a reconciliation pass; they are what the broker sent.
