"""Shared data models for siga-connect."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FetchResult:
    """Normalized result from any connector."""

    pnl: list[float]
    notional: list[float] | None
    source: str  # human-readable description, e.g. "binance:BTCUSDT"
    n_trades: int
