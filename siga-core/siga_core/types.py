"""Core domain types for the siga trading system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol, runtime_checkable
from abc import abstractmethod


class Direction(Enum):
    """Trade direction."""
    LONG = "LONG"
    SHORT = "SHORT"


class SignalType(Enum):
    """Type of trading signal."""
    SWEEP_RECLAIM = "sweep_reclaim"
    BOS_CONTINUATION = "bos_continuation"
    OB_CALLBACK = "ob_callback"
    FVG_FILL = "fvg_fill"
    UNKNOWN = "unknown"


@dataclass
class Signal:
    """Trading signal emitted by a strategy.

    Attributes:
        symbol: Trading symbol (e.g. "BTC/USDC")
        timeframe: Candle timeframe (e.g. "15m", "1h")
        signal_type: Type of signal
        direction: LONG or SHORT
        entry: Recommended entry price
        stop: Stop loss price
        target: Take profit price
        confidence: Confidence score 0-1
        reason: Human-readable explanation
        atr: Average True Range at signal time
        volume_ratio: Volume / average volume ratio
        trend: LONG / SHORT / NEUTRAL
    """
    symbol: str
    timeframe: str
    signal_type: SignalType
    direction: Direction
    entry: float
    stop: float
    target: float
    confidence: float
    reason: str = ""
    atr: Optional[float] = None
    volume_ratio: Optional[float] = None
    trend: Optional[str] = None


@dataclass
class MarketData:
    """Market data passed to strategies.

    candles: list of [timestamp, open, high, low, close, volume]
    """
    symbol: str
    timeframe: str
    candles: list


@runtime_checkable
class StrategyBase(Protocol):
    """Protocol for trading strategies.

    Strategies must implement `name` and `compute`.
    """
    def name(self) -> str: ...
    def compute(self, data: MarketData) -> Optional[Signal]: ...
