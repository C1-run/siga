# siga-core

Core building blocks: domain types, SQLite state store, and async event bus.

## Install

```bash
pip install siga-core
```

## What's Inside

| Module | Description |
|--------|-------------|
| `siga_core.types` | `Signal`, `Direction`, `MarketData`, `StrategyBase` Protocol |
| `siga_core.state` | `StateStore` — SQLite-backed KV with durability levels |
| `siga_core.events` | `EventBus` — async pub/sub with safe exception handling |

## Quick Start

```python
from siga_core import Signal, Direction, StateStore, EventBus

# State store
store = StateStore(path="state.db")
store.set("risk", {"trades_today": 0})
val = store.get("risk")

# Event bus
bus = EventBus()

async def handler(event):
    print(event)

bus.subscribe("signal", handler)
await bus.publish("signal", {"symbol": "BTC/USDC"})
```

## Design Principles

- **Acyclic dependencies** — `core` depends only on `common`
- **Generic** — no trading-specific logic, use in any project
- **Durable** — `StateStore` uses WAL mode + proper PRAGMA tuning

## License

MIT — Selo <team@c1.run>
