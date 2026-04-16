"""Deal timeout / expiry manager.

Uses asyncio.call_later to fire a callback when a deal's negotiation
window expires.  The callback transitions the deal to DEAL_EXPIRED and
publishes an SSE event.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable


class TimeoutManager:
    """Register and cancel per-deal expiry timers."""

    def __init__(self) -> None:
        self._handles: dict[str, asyncio.TimerHandle] = {}

    def register(
        self,
        deal_id: str,
        timeout_seconds: float,
        callback: Callable[[str], Any],
    ) -> None:
        """Register a timeout for a deal.  Replaces any existing timer."""
        self.cancel(deal_id)  # idempotent
        loop = asyncio.get_running_loop()
        handle = loop.call_later(timeout_seconds, callback, deal_id)
        self._handles[deal_id] = handle

    def cancel(self, deal_id: str) -> None:
        """Cancel a pending timeout (no-op if none registered)."""
        handle = self._handles.pop(deal_id, None)
        if handle:
            handle.cancel()


timeout_manager = TimeoutManager()
