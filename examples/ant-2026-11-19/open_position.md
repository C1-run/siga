# Open position — excluded from the audit

- Instrument: `xyz:ANT` (Hyperliquid)
- Direction: LONG
- Entry: `97.0`
- Mark at time of writing: ≈ `91.4`
- Unrealized: ≈ −5.8% (per $100 notional: −$5.8)
- Status: **OPEN / unsettled**

Excluded from `trades.csv` on purpose. `siga audit` judges outcomes; an open
position has no outcome yet. Moving it into the log would convert a
mark-to-market observation into a fabricated "trade result".

When it is closed, record it with the exit time and realized pnl. The pair of
trades then becomes a 2-row log — still below the tool's 10-trade minimum, which
is the correct answer at that sample size too.
