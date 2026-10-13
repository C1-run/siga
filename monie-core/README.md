# monie-core

Core building blocks: domain types, SQLite state store, and async event bus.

## Install

```bash
pip install monie-core
```

## What's Inside

| Module | Description |
|--------|-------------|
| `monie_core.types` | `Signal`, `Direction`, `MarketData`, `StrategyBase` Protocol |
| `monie_core.state` | `StateStore` — SQLite-backed KV with durability levels |
| `monie_core.events` | `EventBus` — async pub/sub with safe exception handling |

## Quick Start

```python
from monie_core import Signal, Direction, StateStore, EventBus

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

[Apache-2.0](LICENSE)
