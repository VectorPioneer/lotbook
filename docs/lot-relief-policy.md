# Lot relief policy

Owner: Tax Operations. This is the policy the ledger implements. Where it is
narrower or more specific than IRS guidance, this document wins: it is written
to match what our broker reports on Form 1099-B, so that our numbers tie out.

## 1. Scope

- Taxable brokerage accounts, US-listed common stock and ETFs.
- Each account is treated on its own. Nothing in this policy looks across
  accounts (no wash sales across accounts, no IRA matching).
- Two positions are "the same security" only if they have the same symbol.
- Short sales and options are out of scope; exports containing them are
  rejected upstream.

## 2. Lots and basis

- Every buy opens a lot. Its basis is `quantity × price + fees`.
- A sale's proceeds are `quantity × price − fees`. When one sale takes shares
  from several lots, proceeds are shared out in proportion to the shares taken
  from each lot.
- Basis taken out of a lot is in proportion to the shares taken.
- Amounts are kept unrounded inside the ledger. Rounding happens only when a
  report row is written (section 7).

## 3. Lot relief

- The account's default method is FIFO unless the account is set up otherwise
  (LIFO or HIFO). FIFO and LIFO order lots by purchase date (the date the
  shares were actually bought), then by the order of the trades in the export.
- HIFO takes the lot with the highest basis per share first, ties oldest first.
- A sale with a `lot_ref` uses specific identification: it takes shares only
  from the lot(s) bought by that purchase, whatever the default method is. If
  that purchase does not have enough shares left, the sale is rejected.
- A sale of more shares than the account holds is rejected.

## 4. Holding period

- The holding period runs from the day after the holding period start. A
  disposal is long term if it is sold after the one-year anniversary of the
  holding period start, and short term otherwise.
- The holding period start is the purchase date, except as set out in 5.4.
- A start on 29 February has its anniversary on 28 February.

## 5. Wash sales

### 5.1 When a sale is a wash sale

A sale that produces a loss is a wash sale, to the extent that the account
acquires replacement shares of the same security within 30 calendar days before
or after the sale date. The window is the sale date ±30 days, both ends
included. A disposal with a gain (or exactly zero) is never a wash sale.

Wash sales are judged disposal by disposal: a sale that takes shares from
three lots produces three disposals, and each disposal with a loss is checked
on its own, in the order the sale relieved them.

### 5.2 Which shares are replacement shares

Replacement shares for a sale are shares of the same security, in the same
account, acquired by a buy dated within the window, **except**:

1. Shares bought by the same purchase as any of the shares this sale takes.
   (Selling half of a lot never makes the other half a replacement.)
2. Shares bought before the sale that are no longer held right after it.
   A buy before the sale counts only for the shares from it that the account
   still holds once the sale has gone through.
3. Shares that have already served as replacement shares for an earlier wash
   sale. A replacement share can absorb at most one wash sale.

Buys later in the export on the same date as the sale count as buys after
the sale.

Replacement shares are used earliest purchase first (purchase date, then
export order).

### 5.3 How much loss is disallowed

Match the shares sold in the disposal share for share against the replacement
shares, in the order given in 5.2. For each share matched, that share's part of
the loss is disallowed:

    disallowed = loss × (shares matched ÷ shares in the disposal)

where `loss` is the disposal's loss as a positive number. If there are fewer
replacement shares than shares in the disposal, only part of the loss is
disallowed; the rest is allowed as normal.

On the report, a disposal with any disallowed loss gets adjustment code `W`
and the disallowed amount (positive) in `adjustment`. Its gain or loss is
`proceeds − cost basis + adjustment`.

### 5.4 What happens to the replacement shares

- The disallowed loss is added to the basis of the replacement shares that
  were matched, share for share. If only some shares of a lot were matched,
  only those shares get the extra basis; treat them as a separate lot from the
  rest from then on.
- The matched replacement shares take over the holding period of the shares
  that were sold: their holding period start moves back by the number of days
  between the sold shares' holding period start and the sale date.
- They keep their real purchase date. It is still what FIFO/LIFO order by, and
  what goes in `date_acquired` on the report.
- If the replacement shares are bought after the sale, the adjustment is
  applied to them when they are bought.

A wash sale can happen in one tax year with replacement shares bought in the
next: the disallowed loss is reported in the year of the sale.

### 5.5 Splits inside the window

If a split takes effect between a loss sale and a buy of replacement shares
after it, compare share counts in post-split shares: the shares sold count
as `shares sold × ratio` when matching against those replacement shares.

## 6. Splits

- Splits are given as `NEW:OLD`, e.g. `2:1` (two shares for each one held),
  `3:2`, or a reverse split `1:10`.
- A split restates every open lot of the symbol, in every account, from the
  start of its effective date: shares × NEW ÷ OLD. Total basis per lot is
  unchanged. Holding period starts and purchase dates are unchanged.
- Trades on or after the effective date are already in post-split shares.
- Fractional shares from a split are kept exactly as fractions. (Cash in lieu
  is booked by the broker as a separate sale; we receive it as a normal SELL in
  the export.)

## 7. Reporting

- One report row per disposal: shares from one lot relieved by one sale.
- `proceeds`, `cost_basis` and `adjustment` are each rounded to cents, half
  up. `gain_loss` is worked out from those rounded figures.
- `term` is `SHORT` or `LONG` (section 4).
- A tax year's report has the disposals sold in that year.

## 8. Reconciliation

The broker's 1099-B detail lists one row per disposal in the same columns as
our report. Rows are paired on account, symbol, date acquired, date sold and
quantity, and every money field must agree within $0.01. The account ties out
when every row pairs and agrees.
