# siga-cli

Open-source core of the **siga** audit engine — Honesty / Reproducibility / Verdict.

We audit trading strategies and publish verdicts, not curves. This repo is the free,
MIT-licensed core: the same plumbing we use in production, plus the `monie` CLI.

## Packages

| Package | What it is |
|---|---|
| `monie-audit` | **Backtest audit engine** — OOS verdict, cost sensitivity, small-sample guard. Zero dependencies |
| `monie-core` | Core types, SQLite state store, and async event bus |
| `monie-common` | Lightweight utilities — logging, time, telemetry, test helpers |
| `monie-book` | Single-frame L2 order book summaries. Zero dependencies |
| `monie-briefing` | The `monie` CLI — portfolio-aware daily briefing |

## Install

```bash
git clone <this-repo> && cd siga-cli
pip install ./monie-common ./monie-core ./monie-book ./monie-audit ./monie-briefing
```

For development (editable installs + test tooling):

```bash
pip install -e ./monie-common -e ./monie-core -e ./monie-book -e ./monie-audit -e ./monie-briefing
pip install pytest ruff
```

## Quickstart — audit a backtest

```bash
monie audit monie-audit/examples/trades_sample.csv
# → Full sample   n=120  mean=-6.89   (informational only — never the verdict)
# → IS  (70%)     n=84   mean=+5.04   t=+0.89  p=0.3778
# → OOS (30%)     n=36   mean=-34.75  t=-3.45  p=0.0015
# → VERDICT: FAIL — OOS edge significant and negative

monie audit your_trades.csv --cost-bps 10   # net of round-trip cost
monie audit your_trades.csv --json          # machine-readable
```

The CSV needs one row per trade, chronological, with a P&L column
(`pnl`, `profit`, `return`, … auto-detected, or `--column name`).

## Quickstart — portfolio

```bash
monie portfolio add SOL 10 --cost 142.50
monie portfolio import examples.csv   # or monie-briefing/examples/portfolio.csv
monie portfolio value                 # current value and P&L
monie portfolio brief                 # portfolio-aware daily briefing
```

## Run the tests

```bash
pytest monie-common monie-core monie-book monie-audit monie-briefing
```

## Why "verdict, not curves"

Backtest tools hand you an equity curve and leave the judgment to you. We started
by auditing our own strategies first — four of them died under the audit
(lookahead leaks, cost drag, overfit parameters), one survived. Every check in
this toolchain exists because it killed something we believed in.

Verdicts are **PASS / FAIL / INCONCLUSIVE** — small samples force INCONCLUSIVE.
No third kind of talk.

## License

MIT — see [LICENSE](LICENSE).
