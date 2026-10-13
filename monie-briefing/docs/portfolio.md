# Portfolio Management

Track your crypto holdings, calculate P&L, and monitor allocation.

## Quick Start

```bash
# Add a holding
monie portfolio add SOL 100 --cost 150.00 --date 2025-01-15

# Import from CSV
monie portfolio import portfolio.csv

# List holdings
monie portfolio list

# Show current value (requires prices)
monie portfolio value

# Remove a holding
monie portfolio remove ETH
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `portfolio add` | Add a new holding (merges if symbol exists) |
| `portfolio import` | Import holdings from CSV |
| `portfolio list` | List all holdings with cost basis |
| `portfolio remove` | Remove a holding by symbol |
| `portfolio value` | Show current value, P&L, and allocation |

### Global Options

| Option | Description |
|--------|-------------|
| `--file PATH` | Override portfolio file (default: `~/.monie/portfolio.json`) |

## CSV Format

```csv
symbol,quantity,cost_basis,acquired_at,notes
SOL,100,150.00,2025-01-15,early position
BTC,0.5,62000.00,2024-11-20,
ETH,5,3200.00,2025-02-01,
```

**Columns:**

| Column | Required | Description |
|--------|----------|-------------|
| `symbol` | Yes | Coin ticker (auto-uppercased) |
| `quantity` | Yes | Number of units held |
| `cost_basis` | Yes | Cost per unit in USD |
| `acquired_at` | Yes | Date in YYYY-MM-DD format |
| `notes` | No | Free-text note |

## Python API

```python
from monie_briefing import Holding, Portfolio
from datetime import date

# Create a portfolio
pf = Portfolio()
pf.add(Holding("SOL", 100, 150.0, date(2025, 1, 1)))
pf.add(Holding("BTC", 0.5, 60000.0, date(2025, 1, 1)))

# Same symbol merges with weighted-average cost
pf.add(Holding("SOL", 50, 200.0, date(2025, 2, 1)))
pf.find("SOL").quantity   # 150
pf.find("SOL").cost_basis # 166.67

# Import from CSV
pf = Portfolio.from_csv("portfolio.csv")

# Save/load
pf.save("~/.monie/portfolio.json")
pf = Portfolio.load("~/.monie/portfolio.json")

# Calculations (requires market prices)
prices = {"SOL": 200.0, "BTC": 70000.0}
pf.total_cost()              # total cost basis
pf.total_value(prices)       # total market value
pf.pnl(prices)               # {total: {...}, per_symbol: {...}}
pf.allocation(prices)        # {"SOL": 36.4, "BTC": 63.6}
```

## Storage

Portfolio data is stored as JSON at `~/.monie/portfolio.json`. Override with `--file`.

## Design Decisions

- `cost_basis` is per-unit, not total
- Same symbol merges with weighted-average cost on `add()`
- `acquired_at` is stored as YYYY-MM-DD string in JSON, `date` object in Python
- Missing price data treated as 0.0 (does not raise)
- Empty portfolio returns 0 for all calculations (no division by zero)

## Price Sources

`monie portfolio value` fetches USD prices from CoinGecko by default:

- Supports BTC, ETH, SOL (and 10 more in `COINGECKO_IDS`)
- In-memory cache: 60s TTL, multiple calls per minute share one API request
- Network failure falls back to stale cache (may be outdated), no crash
- Unknown symbols are skipped with a warning

### Offline Mode

```bash
MONIE_PRICE_SOURCE=stub monie portfolio value
```

All prices return $0, command still runs. For testing and offline environments.
