# monie-common

Lightweight Python utilities — logging, time helpers, telemetry, and test fixtures.

No external dependencies beyond `pyyaml`. Works standalone.

## Install

```bash
pip install monie-common
```

## What's Inside

| Module | Description |
|--------|-------------|
| `monie_common.logger` | Structured stdout logger with file output |
| `monie_common.time_utils` | UTC time helpers (`utc_now`, `utc_iso`, `iso_to_dt`) |
| `monie_common.telemetry` | In-process metrics: `Histogram`, `Counter`, `timeit` decorator |
| `monie_common.test_helpers` | `temp_db_path()` context manager for SQLite tests |

## Quick Start

```python
from monie_common import get_logger, utc_now, registry, measure

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

[Apache-2.0](LICENSE)
