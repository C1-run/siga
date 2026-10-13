"""Arena source — placeholder for arena.db aggregation.

In a full implementation, this would query the arena.db SQLite database.
For the siga-briefing package, this returns a structured dict that can be
populated by callers (e.g. the main engine).
"""

from typing import Any


def get_24h_summary(cutoff_iso: str) -> dict[str, Any]:
    """Get 24h arena summary since cutoff timestamp.

    Returns an explicit unavailable status. Callers with access to arena.db
    can inject real data by replacing the 'error' field.
    """
    return {
        "total_bets": 0,
        "wins": 0,
        "losses": 0,
        "open_positions": 0,
        "total_pnl": 0.0,
        "win_rate": 0.0,
        "best_strategy": None,
        "worst_strategy": None,
        "trader_stats": {},
        "eliminations": [],
        "error": "unavailable: arena.db not found",
    }
