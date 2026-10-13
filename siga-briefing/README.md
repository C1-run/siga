# siga-briefing

**Portfolio-aware daily briefing — know what affects your holdings in 5 minutes.**

Stop spending 45 minutes every morning flipping through Twitter, news, and exchange apps. Siga tells you exactly what matters to *your* portfolio.

## Quick Start

```bash
pip install siga-briefing

siga add BTC 0.5@62000
siga add ETH 5@3200
siga brief
```

That's it. Three lines.

## What It Does

```markdown
# Brief — 2026-09-12 15:53

**Market:** Fear & Greed 63 (Greed)

**Total:** $61,410.20  (cost $62,000.00, P&L -$589.80 / -1.0%)

## Holdings

| Symbol | Price | 24h | 7d | P&L | P&L% | Wt% |
|---|---|---|---|---|---|---|
| BTC | $77,264.00 | +0.1% | -2.9% | +$7,632.00 | +24.6% | 62.9% |
| ETH | $2,522.24 | +2.3% | +2.8% | -$3,388.80 | -21.2% | 20.5% |
| SOL | $101.67 | +2.0% | -0.2% | -$4,833.00 | -32.2% | 16.6% |
```

- **24h / 7d changes** — what moved today and this week
- **Risk flags** — concentration warnings, P&L extremes
- **Fear & Greed** — market sentiment at a glance
- **Your data stays local** — portfolio in `~/.siga/portfolio.json`

## Commands

```bash
siga add BTC 0.5@62000     # add holding (shorthand)
siga add SOL 100            # add without cost basis
siga list                   # show all holdings
siga value                  # current prices + P&L
siga brief                  # generate briefing
siga remove BTC             # remove a holding
siga import portfolio.csv   # import from CSV
```

Cost basis is optional. Without it, you see value and allocation but not P&L.

## CSV Format

```csv
symbol,quantity,cost_basis,acquired_at,notes
BTC,0.5,62000.00,2024-11-20,
ETH,5,3200.00,2025-02-01,
SOL,100,,2025-01-15,early position
```

`cost_basis` and `acquired_at` are optional.

## Python API

```python
from siga_briefing import Holding, Portfolio
from siga_briefing.briefing import PortfolioBriefing

pf = Portfolio()
pf.add(Holding("BTC", 0.5, 62000.0))
pf.add(Holding("ETH", 5, 3200.0))
pf.add(Holding("SOL", 100))  # no cost basis

briefing = PortfolioBriefing(pf)
print(briefing.render_markdown())
```

## Price Sources

- Default: CoinGecko (free, no API key needed)
- 60s in-memory cache
- Offline mode: `SIGA_PRICE_SOURCE=stub siga brief`

## What's Included vs Paid

| Feature | Open Source | Paid ($19/mo) |
|---------|:-----------:|:-------------:|
| Holdings P&L | ✅ | ✅ |
| 24h / 7d changes | ✅ | ✅ |
| Risk flags | ✅ | ✅ |
| Fear & Greed | ✅ | ✅ |
| Telegram push | — | ✅ |
| Daily action list | — | ✅ |
| Event calendar | — | ✅ |
| Auto-push at 8:30am | — | ✅ |

## Design Principles

- **Facts only** — "BTC is 63% of portfolio", not "sell BTC"
- **Your data stays local** — no account, no cloud
- **No API keys needed** — CoinGecko free tier for prices

## License

[Apache-2.0](LICENSE)
