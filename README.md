# siga-cli

[![CI](https://github.com/YOUR_ORG/siga-cli/workflows/CI/badge.svg)](https://github.com/YOUR_ORG/siga-cli/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Open-source core of the **siga** audit engine — Honesty / Reproducibility / Verdict.

We audit trading strategies and publish verdicts, not curves. This repo is the free,
MIT-licensed core: the same plumbing we use in production, plus the `siga` CLI.

## Packages

| Package | What it is |
|---|---|
| `siga-audit` | **Backtest audit engine** — OOS verdict, cost sensitivity, small-sample guard |
| `siga-trail` | Append-only JSONL audit trail — verdicts are recorded, not just printed. Zero dependencies |
| `siga-core` | Core types, SQLite state store, and async event bus |
| `siga-common` | Lightweight utilities — logging, time, telemetry, test helpers |
| `siga-book` | Single-frame L2 order book summaries. Zero dependencies |
| `siga-briefing` | The `siga` CLI — portfolio-aware daily briefing |

## Install

```bash
git clone <this-repo> && cd siga-cli
pip install ./siga-common ./siga-core ./siga-book ./siga-trail ./siga-audit ./siga-briefing
```

For development (editable installs + test tooling):

```bash
pip install -e ./siga-common -e ./siga-core -e ./siga-book -e ./siga-trail -e ./siga-audit -e ./siga-briefing
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
siga audit your_trades.csv --trail ~/.siga/audit.jsonl   # verdicts recorded, append-only
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
pytest siga-common siga-core siga-book siga-trail siga-audit siga-briefing
```

## Why "verdict, not curves"

Backtest tools hand you an equity curve and leave the judgment to you. We started
by auditing our own strategies first — four of them died under the audit
(lookahead leaks, cost drag, overfit parameters), one survived. Every check in
this toolchain exists because it killed something we believed in.

Verdicts are **PASS / FAIL / INCONCLUSIVE** — small samples force INCONCLUSIVE.
No third kind of talk.

### siga is a linter, not an engine

Every other tool answers *"how do I backtest?"* — backtrader, vectorbt, freqtrade
and QuantStats give you engines, indicators, charts, and speed. siga answers a
different question: **"is this backtest actually real?"**

That's why it's not a competitor to those projects — it's a complement. Its input
is a plain trade log, so it audits the output of *any* backtester:

```bash
# backtrader / vectorbt / Excel → a CSV → a verdict
siga audit whatever_you_ran.csv
```

The closer analogy is a linter: `pylint` never runs your code, it judges it.
`siga` never runs your strategy, it judges it.

### Why the big projects can't give you a verdict

Neutral tools can't afford to say "your strategy is fake" — it alienates the
users they depend on for adoption. Their business model rewards engagement; ours
rewards being right. So the differentiation here isn't a cleverer statistic
(OOS splits and t-tests are textbook). It's a discipline: **refusing to give a
flattering answer**, especially the ones nobody wants to hear:

- `OOS n < 30` → INCONCLUSIVE. We would rather give no answer than a fake one.
- The verdict comes from out-of-sample data only. Full-sample numbers are noise
  dressed as evidence.
- p-values are exact, not normal approximations — because small samples are
  exactly where the lie usually hides.

### The uncomfortable question: why is any of this open source?

Fair question, and worth answering head-on: a lot of open-source trading tools
are open *because* they have no alpha. When the strategy isn't the product, the
code has to be. We'd rather say it ourselves than let you wonder.

So, plainly:

- **Open: the measurement machinery.** The checks, the verdict rules, the
  discipline. Four of our own strategies died under them. That's not a confession
  — that's the product demo.
- **Closed: whatever survived.** A strategy that passes the audit doesn't get
  published; it gets traded. That asymmetry is the business model, and it's also
  your quality guarantee: we charge for what survives, so we can't afford to go
  easy on the grading.

One piece of advice, because it will save you the most money:

**Don't build the giant repo first.** The most expensive mistake in this field
isn't a losing strategy — it's six months of infra (executors, dashboards, risk
engines) built around a strategy that was never real. Audit the trade log first:
one CSV, one command, one hour. A FAIL verdict is the cheapest possible outcome —
you just skipped the infra. That's the highest-ROI hour in quantitative trading.

**Measure before you build.**

## License

MIT — see [LICENSE](LICENSE).
