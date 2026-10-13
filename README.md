# siga-cli

Open-source core of the **siga** audit engine — Honesty / Reproducibility / Verdict.

We audit trading strategies and publish verdicts, not curves. This repo is the free,
MIT-licensed core: the same plumbing we use in production, plus the `siga` CLI.

## Packages

| Package | What it is |
|---|---|
| `siga-audit` | **Backtest audit engine** — OOS verdict, cost sensitivity, small-sample guard. Zero dependencies |
| `siga-core` | Core types, SQLite state store, and async event bus |
| `siga-common` | Lightweight utilities — logging, time, telemetry, test helpers |
| `siga-book` | Single-frame L2 order book summaries. Zero dependencies |
| `siga-briefing` | The `siga` CLI — portfolio-aware daily briefing |

## Install

```bash
git clone <this-repo> && cd siga-cli
pip install ./siga-common ./siga-core ./siga-book ./siga-audit ./siga-briefing
```

For development (editable installs + test tooling):

```bash
pip install -e ./siga-common -e ./siga-core -e ./siga-book -e ./siga-audit -e ./siga-briefing
pip install pytest ruff
```

## Quickstart — audit a backtest

```bash
siga audit siga-audit/examples/trades_sample.csv
# → Full sample   n=120  mean=-6.89   (informational only — never the verdict)
# → IS  (70%)     n=84   mean=+5.04   t=+0.89  p=0.3778
# → OOS (30%)     n=36   mean=-34.75  t=-3.45  p=0.0015
# → VERDICT: FAIL — OOS edge significant and negative

siga audit your_trades.csv --cost-bps 10   # net of round-trip cost
siga audit your_trades.csv --json          # machine-readable
```

The CSV needs one row per trade, chronological, with a P&L column
(`pnl`, `profit`, `return`, … auto-detected, or `--column name`).

### Verdict rules (non-negotiable)

- **Verdict comes from OOS only.** Full-sample numbers are informational.
- **OOS n < 30 forces INCONCLUSIVE.** We would rather give no answer than a fake one.
- **p-values are exact** (t-distribution via incomplete beta), not normal approximations.

## Quickstart — portfolio

```bash
siga portfolio add SOL 10 --cost 142.50
siga portfolio import examples.csv   # or siga-briefing/examples/portfolio.csv
siga portfolio value                 # current value and P&L
siga portfolio brief                 # portfolio-aware daily briefing
```

## Run the tests

```bash
pytest siga-common siga-core siga-book siga-audit siga-briefing
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
