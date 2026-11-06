# File formats

All files are UTF-8 CSV with a header row. Dates are ISO (`2025-03-14`).
Blank lines are ignored.

## Trade export (`trades.csv`)

| column     | meaning |
|------------|---------|
| `trade_id` | unique within the file |
| `account`  | account number |
| `date`     | trade date |
| `action`   | `BUY` or `SELL` |
| `symbol`   | ticker |
| `quantity` | shares, positive; may be fractional |
| `price`    | per share, before fees |
| `fees`     | commission and fees for the whole trade; blank means 0 |
| `lot_ref`  | SELL only, optional: the `trade_id` of the buy to relieve (specific identification) |

Trades are in the order the broker executed them; on the same date, that order
matters.

## Corporate actions (`actions.csv`)

| column      | meaning |
|-------------|---------|
| `action_id` | unique within the file |
| `date`      | effective date (start of day) |
| `symbol`    | ticker |
| `type`      | `SPLIT` (the only type supported) |
| `ratio`     | `NEW:OLD`, e.g. `2:1`, `3:2`, `1:10` |

## Gains report and broker 1099-B detail

Both use the same columns:

`account, symbol, quantity, date_acquired, date_sold, proceeds, cost_basis,
adjustment_code, adjustment, gain_loss, term`

`adjustment_code` is blank or `W` (wash sale). `adjustment` is the disallowed
loss as a positive amount, `0.00` when there is none. `term` is `SHORT` or
`LONG`.
