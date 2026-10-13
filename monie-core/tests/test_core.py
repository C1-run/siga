"""Unit tests for monie-core."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pytest
from monie_common.test_helpers import temp_db_path
from monie_common.telemetry import registry

from monie_core import (
    Signal, Direction, SignalType, MarketData, StateStore, EventBus
)
from monie_core.types import StrategyBase


class TestTypes:
    def test_direction_enum(self):
        assert Direction.LONG.value == "LONG"
        assert Direction.SHORT.value == "SHORT"

    def test_signal_creation(self):
        sig = Signal(
            symbol="BTC/USDC",
            timeframe="15m",
            signal_type=SignalType.SWEEP_RECLAIM,
            direction=Direction.LONG,
            entry=100.0,
            stop=95.0,
            target=110.0,
            confidence=0.75,
        )
        assert sig.symbol == "BTC/USDC"
        assert sig.direction == Direction.LONG
        assert sig.confidence == 0.75

    def test_signal_type_enum(self):
        assert SignalType.SWEEP_RECLAIM.value == "sweep_reclaim"
        assert SignalType.BOS_CONTINUATION.value == "bos_continuation"

    def test_market_data(self):
        md = MarketData(symbol="BTC/USDC", timeframe="1h", candles=[["t", 1, 2, 3, 4, 100]])
        assert md.symbol == "BTC/USDC"
        assert len(md.candles) == 1


class TestStateStore:
    def test_set_and_get(self):
        with temp_db_path() as path:
            store = StateStore(path)
            store.set("risk", "trades_today", 3)
            assert store.get("risk", "trades_today") == 3

    def test_namespace(self):
        with temp_db_path() as path:
            store = StateStore(path)
            store.set("a", "x", 1)
            store.set("a", "y", 2)
            store.set("b", "z", 3)
            ns = store.namespace("a")
            assert ns == {"x": 1, "y": 2}

    def test_delete(self):
        with temp_db_path() as path:
            store = StateStore(path)
            store.set("a", "k", "v")
            assert store.delete("a", "k") is True
            assert store.get("a", "k") is None
            assert store.delete("a", "k") is False

    def test_clear(self):
        with temp_db_path() as path:
            store = StateStore(path)
            store.set("a", "k1", 1)
            store.set("a", "k2", 2)
            n = store.clear("a")
            assert n == 2
            assert store.namespace("a") == {}

    def test_overwrite(self):
        with temp_db_path() as path:
            store = StateStore(path)
            store.set("a", "k", 1)
            store.set("a", "k", 2)
            assert store.get("a", "k") == 2

    def test_complex_value(self):
        with temp_db_path() as path:
            store = StateStore(path)
            val = {"nested": [1, 2, 3], "flag": True}
            store.set("a", "complex", val)
            assert store.get("a", "complex") == val


class TestCoreTelemetry:
    def test_state_store_records_latency(self):
        with temp_db_path() as path:
            store = StateStore(path)
            registry.reset()
            registry.enabled = True
            store.set("risk", "trades_today", 3)
            value = store.get("risk", "trades_today")
            assert value == 3
            report = registry.report()
            assert report["histograms"]["state_store.set"]["count"] == 1.0
            assert report["histograms"]["state_store.get"]["count"] == 1.0


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("signal", handler)
        await bus.publish("signal", {"x": 1})
        await asyncio.sleep(0.01)
        assert received == [{"x": 1}]

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        bus = EventBus()
        r1, r2 = [], []

        async def h1(e):
            r1.append(e)

        async def h2(e):
            r2.append(e)

        bus.subscribe("topic", h1)
        bus.subscribe("topic", h2)
        await bus.publish("topic", "hi")
        await asyncio.sleep(0.01)
        assert r1 == ["hi"]
        assert r2 == ["hi"]

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        bus = EventBus()
        r = []

        async def h(e):
            r.append(e)

        bus.subscribe("t", h)
        bus.unsubscribe("t", h)
        await bus.publish("t", "x")
        await asyncio.sleep(0.01)
        assert r == []

    @pytest.mark.asyncio
    async def test_handler_exception_swallowed(self):
        bus = EventBus()
        r = []

        async def bad(e):
            raise ValueError("nope")

        async def good(e):
            r.append(e)

        bus.subscribe("t", bad)
        bus.subscribe("t", good)
        await bus.publish("t", "x")
        await asyncio.sleep(0.01)
        assert r == ["x"]

    @pytest.mark.asyncio
    async def test_publish_records_telemetry(self):
        bus = EventBus()
        registry.reset()
        registry.enabled = True

        async def handler(event):
            pass

        bus.subscribe("metrics", handler)
        await bus.publish("metrics", {"x": 1})
        report = registry.report()
        assert report["histograms"]["event_bus.publish"]["count"] == 1.0
        assert report["counters"]["event_bus.publish_count"] == 1
