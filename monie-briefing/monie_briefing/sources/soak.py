"""Soak testing source — placeholder for engine_health aggregation."""

from typing import Any


def get_trends(limit: int = 200) -> dict[str, Any]:
    """Get engine health trends.

    In a full implementation, this reads from engine_health_history table.
    Returns an explicit unavailable status until that is implemented.
    """
    return {
        "status": "unavailable",
        "cycle_count": 0,
        "history_points": 0,
        "avg_cycle_ms": None,
        "max_cycle_ms": None,
        "min_cycle_ms": None,
        "memory_mb": None,
        "max_memory_mb": None,
        "fetch_errors": 0,
        "spike_count": 0,
        "spike_pct": 0.0,
        "trend": "no_data",
        "error": "unavailable: engine_health_history table not found",
    }
