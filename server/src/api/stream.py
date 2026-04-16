import asyncio
import json
from datetime import datetime

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter()


class SSEBus:
    """In-memory event bus for SSE streaming to dashboard clients."""

    def __init__(self):
        self._queues: list[asyncio.Queue] = []
        self._deal_history: list[dict] = []
        self._agent_statuses: dict[str, dict] = {}

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._queues:
            self._queues.remove(q)

    async def publish(self, event_type: str, data: dict):
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if event_type.startswith("deal"):
            self._deal_history.append(event)
        if event_type == "agent_status":
            agent_id = data.get("agent_id", "")
            if agent_id:
                self._agent_statuses[agent_id] = data
        for q in self._queues:
            await q.put(event)

    def get_deal_history(self) -> list[dict]:
        return self._deal_history

    def get_agent_statuses(self) -> dict[str, dict]:
        return self._agent_statuses


sse_bus = SSEBus()


@router.get("/deals")
async def stream_deals():
    """SSE stream of real-time deal state changes."""
    queue = sse_bus.subscribe()

    async def event_generator():
        try:
            # Send history first
            for event in sse_bus.get_deal_history():
                yield {"event": event["event"], "data": json.dumps(event["data"])}

            # Then stream live events
            while True:
                event = await queue.get()
                yield {"event": event["event"], "data": json.dumps(event["data"])}
        except asyncio.CancelledError:
            sse_bus.unsubscribe(queue)

    return EventSourceResponse(event_generator())


@router.get("/agents")
async def stream_agents():
    """SSE stream of agent status updates."""
    queue = sse_bus.subscribe()

    async def event_generator():
        try:
            # Send current agent statuses first
            for _agent_id, status in sse_bus.get_agent_statuses().items():
                yield {"event": "agent_status", "data": json.dumps(status)}

            while True:
                event = await queue.get()
                if event["event"] == "agent_status":
                    yield {"event": event["event"], "data": json.dumps(event["data"])}
        except asyncio.CancelledError:
            sse_bus.unsubscribe(queue)

    return EventSourceResponse(event_generator())


@router.post("/test-event")
async def push_test_event(event: dict):
    """Push a test event (for development/demo). Remove in production."""
    await sse_bus.publish(event.get("type", "deal_update"), event.get("data", {}))
    return {"status": "published"}
