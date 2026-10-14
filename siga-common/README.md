# siga-common

Lightweight Python utilities — logging, time helpers, telemetry, and test fixtures.

No external dependencies beyond `pyyaml`. Works standalone.

## Install

```bash
pip install siga-common
```

## What's Inside

| Module | Description |
|--------|-------------|
| `siga_common.logger` | Structured stdout logger with file output |
| `siga_common.time_utils` | UTC time helpers (`utc_now`, `utc_iso`, `iso_to_dt`) |
| `siga_common.telemetry` | In-process metrics: `Histogram`, `Counter`, `timeit` decorator |
| `siga_common.test_helpers` | `temp_db_path()` context manager for SQLite tests |

## Quick Start

```python
from siga_common import get_logger, utc_now, registry, measure

logger = get_logger(__name__)
logger.info("started")

# Telemetry
with measure("fetch_data"):
    data = fetch()

# Histograms
hist = registry.histogram("latency_ms")
hist.record(42)
print(hist.summary())  # p50, p95, p99
```

## Why?

These are generic utilities with zero domain coupling. Use them in any project.

## License

MIT — Selo <team@c1.run>
