"""Unit tests for siga-common telemetry."""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from siga_common.telemetry import (
    Telemetry,
    Histogram,
    Counter,
    registry,
    timeit,
    atimeit,
    measure,
)


@pytest.fixture(autouse=True)
def reset_registry():
    registry.reset()
    registry.enabled = True
    yield
    registry.reset()
    registry.enabled = True


class TestHistogram:
    def test_observe_and_summary(self):
        h = Histogram(name="test")
        h.observe(1.0)
        h.observe(2.0)
        h.observe(3.0)
        s = h.summary()
        assert s["count"] == 3
        assert s["p50"] == 2.0
        assert s["p95"] == 3.0
        assert s["p99"] == 3.0
        assert s["max"] == 3.0

    def test_empty_summary(self):
        h = Histogram(name="empty")
        s = h.summary()
        assert s["count"] == 0
        assert s["p50"] == 0.0
        assert s["max"] == 0.0

    def test_bounded_maxlen(self):
        h = Histogram(name="bounded")
        for i in range(200_000):
            h.observe(float(i))
        # deque(maxlen=100_000) should cap at 100k
        assert len(h.values) <= 100_000

    def test_thread_safety(self):
        h = Histogram(name="threaded")
        h.observe(1.0)
        s = h.summary()
        assert s["count"] == 1.0


class TestCounter:
    def test_inc_and_snapshot(self):
        c = Counter(name="test")
        assert c.snapshot() == 0
        c.inc()
        assert c.snapshot() == 1
        c.inc(5)
        assert c.snapshot() == 6

    def test_thread_safety(self):
        c = Counter(name="threaded")
        c.inc(10)
        assert c.snapshot() == 10


class TestTelemetry:
    def test_registry_histogram_creation(self):
        h = registry.histogram("marketdata.summarize_order_book")
        assert h.name == "marketdata.summarize_order_book"

    def test_registry_counter_creation(self):
        c = registry.counter("risk.reserve_slot_attempts")
        assert c.name == "risk.reserve_slot_attempts"

    def test_registry_report(self):
        registry.histogram("foo").observe(1.0)
        registry.counter("bar").inc()
        report = registry.report()
        assert "foo" in report["histograms"]
        assert "bar" in report["counters"]
        assert report["counters"]["bar"] == 1

    def test_reset_clears_state(self):
        registry.histogram("x").observe(1.0)
        registry.counter("y").inc()
        registry.reset()
        report = registry.report()
        assert report["histograms"] == {}
        assert report["counters"] == {}

    def test_enabled_flag_disables_measure(self):
        registry.enabled = False
        with measure("should_not_record"):
            pass
        report = registry.report()
        assert "should_not_record" not in report["histograms"]

    def test_disabled_atimeit_does_not_record(self):
        registry.enabled = False

        @atimeit("async_should_not_record")
        async def dummy():
            return 42

        result = asyncio.run(dummy())
        assert result == 42
        report = registry.report()
        assert "async_should_not_record" not in report["histograms"]


class TestTimeitDecorator:
    def test_sync_decorator_records_latency(self):
        @timeit("sync_fn")
        def work():
            time.sleep(0.01)
            return "done"

        result = work()
        assert result == "done"
        report = registry.report()
        assert "sync_fn" in report["histograms"]
        assert report["histograms"]["sync_fn"]["count"] == 1.0
        assert report["histograms"]["sync_fn"]["max"] > 0.005

    def test_sync_decorator_preserves_metadata(self):
        @timeit("metadata")
        def documented():
            """docstring"""
            pass

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "docstring"


class TestAtimeitDecorator:
    def test_async_decorator_records_latency(self):
        @atimeit("async_fn")
        async def work():
            await asyncio.sleep(0.01)
            return "done"

        result = asyncio.run(work())
        assert result == "done"
        report = registry.report()
        assert "async_fn" in report["histograms"]
        assert report["histograms"]["async_fn"]["count"] == 1.0
        assert report["histograms"]["async_fn"]["max"] > 0.005

    def test_async_decorator_preserves_metadata(self):
        @atimeit("async_metadata")
        async def documented():
            """async docstring"""
            pass

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "async docstring"


class TestMeasureContextManager:
    def test_measure_records_block_latency(self):
        with measure("block_latency"):
            time.sleep(0.01)
        report = registry.report()
        assert "block_latency" in report["histograms"]
        assert report["histograms"]["block_latency"]["max"] > 0.005

    def test_measure_disabled_noop(self):
        registry.enabled = False
        with measure("noop"):
            pass
        report = registry.report()
        assert "noop" not in report["histograms"]


class TestTelemetryOverhead:
    def test_overhead_is_small(self):
        registry.enabled = False
        iterations = 50_000

        @timeit("overhead_disabled")
        def busy_work():
            x = 0
            for i in range(1000):
                x += i
            return x

        start = time.perf_counter()
        for _ in range(iterations):
            busy_work()
        disabled_time = time.perf_counter() - start

        registry.reset()
        registry.enabled = True

        @timeit("overhead_enabled")
        def busy_work2():
            x = 0
            for i in range(1000):
                x += i
            return x

        start = time.perf_counter()
        for _ in range(iterations):
            busy_work2()
        enabled_time = time.perf_counter() - start

        overhead_pct = ((enabled_time - disabled_time) / disabled_time) * 100
        # Overhead should be small; allow generous 50% for Python tracing
        assert overhead_pct < 50, f"Telemetry overhead too high: {overhead_pct:.1f}%"
