"""Async event bus for siga packages."""

import asyncio
from collections import defaultdict
from typing import Any, Callable, Awaitable

from siga_common.telemetry import registry, measure


class EventBus:
    """Simple async pub/sub event bus.

    Usage:
        bus = EventBus()

        async def handler(event):
            print(event)

        bus.subscribe("signal", handler)
        await bus.publish("signal", {"symbol": "BTC/USDC"})
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable[[Any], Awaitable[None]]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Any], Awaitable[None]]) -> None:
        """Register an async handler for a topic."""
        self._handlers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unregister a handler from a topic."""
        if handler in self._handlers[topic]:
            self._handlers[topic].remove(handler)

    async def publish(self, topic: str, event: Any) -> None:
        """Publish an event to all handlers of a topic.

        Exceptions in handlers are caught and logged but do not stop other handlers.
        """
        registry.counter("event_bus.publish_count").inc()
        with measure("event_bus.publish"):
            if topic not in self._handlers:
                return
            await asyncio.gather(
                *(self._safe_call(h, event) for h in self._handlers[topic]),
                return_exceptions=True,
            )

    @staticmethod
    async def _safe_call(handler, event) -> None:
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            registry.counter("event_bus.handler_exceptions").inc()
            pass  # swallow in handler

    def clear(self, topic: str = None) -> None:
        """Clear handlers for a topic, or all handlers if no topic given."""
        if topic is None:
            self._handlers.clear()
        elif topic in self._handlers:
            del self._handlers[topic]
