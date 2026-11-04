# siga-audit

Backtest audit engine — zero dependencies, exact statistics.

Give it a CSV of per-trade P&L (chronological). It splits the log into
in-sample (first 70%) and out-of-sample (last 30%), judges **only the OOS
portion**, and prints a verdict: `PASS` / `FAIL` / `INCONCLUSIVE`.

```bash
siga audit trades.csv
siga audit trades.csv --cost-bps 10     # net of assumed round-trip cost
siga audit trades.csv --cluster-days    # judge per-UTC-day means, not tickets
siga audit trades.csv --plant --stratum=pullback   # what edge could this log prove?
siga audit trades.csv --json            # machine-readable
```

Rules, non-negotiable:

- Verdict comes from OOS only. Full-sample numbers are informational.
- With `--cost` / `--cost-bps`, the verdict is judged **net** of that cost. Without
  it, it is judged gross — and gross is not a recommendation.
- With `--cluster-days`, the judged unit is the UTC day: one day contributes its
  average however many trades it held, and the floor is `--min-days` days.
- With `--plant`, a known edge is injected into one labeled stratum (a contrast: the
  whole-log mean is left exactly where it was found) and the run reports the smallest
  planted edge this log can prove. A FAIL that no plant can produce is not a market
  statement — it is an instrument limit.
- OOS n < 30 forces `INCONCLUSIVE`. We would rather give no answer than a fake one.
- p-values are exact (t-distribution via incomplete beta), not normal approximations.
- `PASS` is not a profitability guarantee. It describes this log under the stated
  audit assumptions and does not establish future returns.

MIT — siga <team@c1.run>
