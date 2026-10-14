# siga-cli v0.1.0 — 2026-10-14

## tl;dr

The first public release of the siga audit engine.

One command turns your backtest trade log into a verdict:

```bash
siga audit your_trades.csv
# → VERDICT: PASS / FAIL / INCONCLUSIVE
```

## What's in this release

`siga-cli` is a Python monorepo with five packages. The one that matters most
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
- **MIT licensed** — copyright Selo <team@c1.run>
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

- **v0.1.0** (2026-10-14) — Initial release. `siga audit` command, portfolio
  management, data connectors (Binance, Dune, Helius), seven packages, 192 tests.
