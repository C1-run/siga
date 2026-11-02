# siga-cli v0.2.0 — unreleased

## Three checks, each of which moves a verdict on the bundled example log

Every number below comes from `siga-audit/examples/plant_sample.csv`, a synthetic
1,500-trade log shipped in this repo. Four commands, and you have reproduced the
whole release note — no log here is one we cannot show you.

1. **Cost now enters the verdict.** `--cost` / `--cost-bps` used to append a line
   to the reasons and judge the verdict on gross: `--cost 1.0` — a per-trade cost
   larger than any edge — still printed `PASS`. On the bundled log, gross reads
   `PASS (t=+2.28, p=0.0230)`; the same log `--cost 30` reads
   `FAIL (t=-3.01, p=0.0028)`. A cost that eats the edge can no longer produce a
   PASS.
2. **`--cluster-days`: the day is the unit, not the ticket.** The statistic is
   read on per-UTC-day means of the OOS slice, floored at `--min-days` days
   (default 10) instead of `--min-oos` tickets. The 450 OOS trades that read
   `PASS` per ticket read `INCONCLUSIVE (t=+1.88, p=0.0767)` on their 18 daily
   means: 450 trades settling on 18 days are 18 observations, not 450. Add the
   cost back and the same log is a `FAIL (t=-2.48, p=0.0237)`. The two checks ask
   different questions — is the edge real across time, does it survive what it
   costs to take — and a PASS that ignores either is a claim about the wrong
   quantity.
3. **`--plant`: the auditor audits itself.** Plant a known edge into one labeled
   stratum — a contrast, so the whole-log mean is left exactly where it was
   found — and report the smallest planted edge this log can prove. On the
   bundled stratum the first planted edge that reaches `PASS` is 30/trade, so a
   FAIL there rules out anything larger than 30/trade and *nothing* smaller.
   Without it, a FAIL is a claim about the market; with it you learn whether the
   verdict was ever capable of seeing what it says it did not find.

Also: a p-value below 1e-4 now prints as `<0.0001` in the verdict reasons instead
of `0.0000`, and `docs/demo.gif` is generated from live CLI output by
`docs/make_demo.py` — the demo can no longer drift from the release it advertises.

Tests: 195 → 210 passing across all seven packages (1 pre-existing skip in
siga-connect), on Python 3.12.
BREAKING: verdicts on the same input can differ from v0.1.0 — see rule 1.

# siga-cli v0.1.0 — 2026-10-14

## tl;dr

The first public release of the siga audit engine.

One command turns your backtest trade log into a verdict:

```bash
siga audit your_trades.csv
# → VERDICT: PASS / FAIL / INCONCLUSIVE
```

## What's in this release

`siga-cli` is a Python monorepo with seven packages. The one that matters most
is `siga-audit` — a zero-dependency backtest audit engine that splits your
trade log into in-sample (70%) and out-of-sample (30%), judges **only the OOS
portion**, and prints a verdict. No normal approximations, no hidden parameters.

### siga-audit — the engine

- **OOS split:** chronological 70/30 by default, adjustable via `--oos`
- **Exact statistics:** two-tailed p-values via the incomplete beta function
- **Cost sensitivity:** `--cost` (fixed cost/trade) or `--cost-bps` (bps of
  notional) — re-runs the verdict net of assumed cost
- **Small-sample guard:** OOS n < 30 forces INCONCLUSIVE
- **Output:** plain text (default) or `--json` for CI pipelines

### siga CLI — the interface

```
siga audit <trades.csv>         # backtest audit
siga audit --from binance --symbol BTCUSDT --api-key $KEY --api-secret $SECRET
siga fetch --from binance --symbol BTCUSDT -o trades.csv   # pull to CSV first
siga portfolio add <sym> <qty>  # manage holdings
siga portfolio list|value|brief # portfolio-aware daily briefing
```

### Other packages

| Package | Role |
|---|---|
| `siga-trail` | Append-only JSONL audit trail — `--trail` records verdicts |
| `siga-core` | SQLite state store + async event bus |
| `siga-common` | Logging, telemetry, test helpers |
| `siga-book` | Single-frame L2 order book summaries. Zero deps |
| `siga-briefing` | `siga` CLI umbrella — portfolio management + news briefing |
| `siga-connect` | Data connectors — Binance, Dune, Helius (optional) |

## Verification

- **192 tests**, all passing (pure stdlib except pytest; siga-connect adds httpx)
- **MIT licensed** — copyright siga <team@c1.run>
- **Requires:** Python >= 3.11

## Known limitations

- `siga audit` is single-series only (one strategy, one time horizon). Multi-asset
  and cross-validation folds are on the roadmap.
- Cost sensitivity assumes a fixed per-trade cost. Path-dependent execution costs
  (slippage as a function of size, time-of-day) are not modelled.
- The portfolio commands require a running price feed (calls CoinGecko via httpx).
  Offline mode is not yet implemented.

## Install

```bash
git clone https://github.com/c1-run/siga && cd siga
pip install ./siga-common ./siga-core ./siga-book ./siga-trail ./siga-audit ./siga-briefing ./siga-connect
```

For editable development:

```bash
pip install -e ./siga-common -e ./siga-core -e ./siga-book -e ./siga-trail -e ./siga-audit -e ./siga-briefing -e ./siga-connect
pip install pytest ruff
pytest siga-common siga-core siga-book siga-trail siga-audit siga-briefing siga-connect
```

## What's next

The audit engine will stay small and opinionated. Upcoming work is tracked in
private milestones, but the public surface will only expand when a new check
has killed a real strategy first.

## Changelog

- **v0.2.0** (unreleased) — cost enters the verdict (BREAKING: the same log can
  verdict differently than v0.1.0), `--cluster-days` / `--min-days` judge the
  UTC day instead of the ticket, and `--plant` reports the smallest planted edge
  a log can prove. New files: `siga_audit/plant.py`, `examples/plant_sample.csv`.
- **v0.1.0** (2026-10-14) — Initial release. `siga audit` command, portfolio
  management, data connectors (Binance, Dune, Helius), seven packages, 192 tests.
