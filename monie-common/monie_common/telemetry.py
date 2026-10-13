"""Lightweight telemetry for monie packages."""

from __future__ import annotations

import functools
import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable


@dataclass
class Histogram:
    """Bounded latency histogram."""

    name: str
    values: deque[float] = field(default_factory=lambda: deque(maxlen=100_000))
    _lock: Lock = field(default_factory=Lock, repr=False)

    def observe(self, value: float) -> None:
        with self._lock:
            self.values.append(value)

    def summary(self) -> dict[str, float]:
        with self._lock:
            if not self.values:
                return {
                    "count": 0,
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                    "max": 0.0,
                }
            s = sorted(self.values)

        n = len(s)

        def pct(p: float) -> float:
            idx = int(n * p / 100.0)
            idx = max(0, min(idx, n - 1))
            return s[idx]

        return {
            "count": float(n),
            "p50": pct(50),
            "p95": pct(95),
            "p99": pct(99),
            "max": s[-1],
        }


@dataclass
class Counter:
    """Thread-safe counter."""

    name: str
    value: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def inc(self, amount: int = 1) -> None:
        with self._lock:
            self.value += amount

    def snapshot(self) -> int:
        with self._lock:
            return self.value


class Telemetry:
    """Global metrics registry."""

    def __init__(self) -> None:
        self._histograms: dict[str, Histogram] = {}
        self._counters: dict[str, Counter] = {}
        self._lock = Lock()
        self.enabled: bool = True

    def histogram(self, name: str) -> Histogram:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name=name)
            return self._histograms[name]

    def counter(self, name: str) -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name=name)
            return self._counters[name]

    def report(self) -> dict[str, Any]:
        with self._lock:
            histograms = dict(self._histograms)
            counters = dict(self._counters)

        return {
            "histograms": {
                name: histogram.summary()
                for name, histogram in sorted(histograms.items())
            },
            "counters": {
                name: counter.snapshot()
                for name, counter in sorted(counters.items())
            },
        }

    def reset(self) -> None:
        with self._lock:
            self._histograms.clear()
            self._counters.clear()


# Module-level singleton.
registry = Telemetry()


def timeit(name: str) -> Callable:
    """Decorator to record synchronous function latency."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not registry.enabled:
                return fn(*args, **kwargs)
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                registry.histogram(name).observe(elapsed)

        return wrapper

    return decorator


def atimeit(name: str) -> Callable:
    """Decorator to record async function latency."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not registry.enabled:
                return await fn(*args, **kwargs)
            start = time.perf_counter()
            try:
                return await fn(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                registry.histogram(name).observe(elapsed)

        return wrapper

    return decorator


class measure:
    """Context manager to time a block and record into a histogram."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._start: float = 0.0

    def __enter__(self) -> None:
        if registry.enabled:
            self._start = time.perf_counter()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if registry.enabled:
            elapsed = time.perf_counter() - self._start
            registry.histogram(self.name).observe(elapsed)
