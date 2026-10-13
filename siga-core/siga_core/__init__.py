"""siga-core — core types, state, events, and config."""

from siga_core.types import (
    Signal,
    Direction,
    SignalType,
    MarketData,
    StrategyBase,
)

from siga_core.state import StateStore

from siga_core.events import EventBus

__all__ = [
    "Signal",
    "Direction",
    "SignalType",
    "MarketData",
    "StrategyBase",
    "StateStore",
    "EventBus",
]

__version__ = "0.1.0"
