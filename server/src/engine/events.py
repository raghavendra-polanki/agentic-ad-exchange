"""In-memory event bus for Phase 1. Dashboard SSE subscribes to this."""

import asyncio
from datetime import UTC, datetime


class EventBus:
    """In-memory event bus for Phase 1. Dashboard SSE subscribes to this."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._history: list[dict] = []

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def publish(self, event_type: str, data: dict) -> None:
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._history.append(event)
        for queue in self._subscribers:
            await queue.put(event)

    def get_history(self) -> list[dict]:
        return list(self._history)


# Singleton
event_bus = EventBus()
