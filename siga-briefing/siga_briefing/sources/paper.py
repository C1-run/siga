"""Paper trading source — placeholder for state.db aggregation.

In a full implementation, this would query the state.db SQLite database.
"""

from typing import Any


def get_24h_summary(cutoff_iso: str) -> dict[str, Any]:
    """Get 24h paper trading summary since cutoff timestamp.

    Returns an explicit unavailable status. Callers with access to state.db
    can inject real data by replacing the 'error' field.
    """
    return {
        "total_evaluations": 0,
        "signals_generated": 0,
        "waiting_count": 0,
        "long_signals": 0,
        "short_signals": 0,
        "trades_taken": 0,
        "wins": 0,
        "losses": 0,
        "open_trades": 0,
        "total_pnl": 0.0,
        "win_rate": 0.0,
        "shadow_count": 0,
        "shadow_reasons": {},
        "risk_state": None,
        "error": "unavailable: state.db not found",
    }
