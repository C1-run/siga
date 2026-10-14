# siga-audit

Backtest audit engine — zero dependencies, exact statistics.

Give it a CSV of per-trade P&L (chronological). It splits the log into
in-sample (first 70%) and out-of-sample (last 30%), judges **only the OOS
portion**, and prints a verdict: `PASS` / `FAIL` / `INCONCLUSIVE`.

```bash
siga audit trades.csv
siga audit trades.csv --cost-bps 10     # net of assumed round-trip cost
siga audit trades.csv --json            # machine-readable
```

Rules, non-negotiable:

- Verdict comes from OOS only. Full-sample numbers are informational.
- OOS n < 30 forces `INCONCLUSIVE`. We would rather give no answer than a fake one.
- p-values are exact (t-distribution via incomplete beta), not normal approximations.

MIT — siga <team@c1.run>
