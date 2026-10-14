# siga-connect

Data connectors for siga — pull trade history from exchanges, Dune, Helius.

## Install

```bash
pip install siga-connect
```

## Usage

### Binance (spot trade history)

```bash
# Public aggregate trades (any symbol, no API key needed)
siga fetch --from binance --symbol BTCUSDT --output trades.csv

# Your own trades (requires API key + secret)
siga fetch --from binance --symbol BTCUSDT --api-key $BINANCE_KEY --api-secret $BINANCE_SECRET --output trades.csv

# Audit directly without saving CSV
siga audit --from binance --symbol BTCUSDT --api-key $BINANCE_KEY --api-secret $BINANCE_SECRET
```

### Dune (query results)

```bash
siga fetch --from dune --query-id 12345 --api-key $DUNE_KEY --output trades.csv
siga audit --from dune --query-id 12345 --api-key $DUNE_KEY
```

Dune query must return columns: `pnl` (required), `notional` (optional), `time` (optional).

### Helius (Solana address transactions)

```bash
siga fetch --from helius --address $SOL_ADDRESS --api-key $HELIUS_KEY --output trades.csv
siga audit --from helius --address $SOL_ADDRESS --api-key $HELIUS_KEY
```

## Python API

```python
from siga_connect import fetch_trades

result = fetch_trades("binance", symbol="BTCUSDT", api_key="...", api_secret="...")
print(result.pnl)      # list of per-trade P&L
print(result.notional) # list of per-trade notional (or None)
print(result.source)   # "binance:BTCUSDT"
```

## License

MIT — Selo <team@c1.run>
