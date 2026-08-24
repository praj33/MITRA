"""
runtime_event_bus.py — MITRA Real-Time Runtime Event Bus
Provides real-time Server-Sent Events (SSE) / WebSocket distribution of execution state transitions.
State events: requested, queued, running, capability_running, waiting, retrying, completed, failed, timed_out, cancelled, health_changes.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set, AsyncGenerator

logger = logging.getLogger(__name__)

class RuntimeEventBus:
    def __init__(self) -> None:
        self._subscribers: Set[asyncio.Queue] = set()
        self._recent_events: list[Dict[str, Any]] = []

    async def publish(
        self,
        event_type: str,
        user_id: str,
        trace_id: str,
        execution_id: str,
        capability: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Publish a runtime lifecycle event."""
        event = {
            "event_type": event_type,
            "user_id": user_id,
            "trace_id": trace_id,
            "execution_id": execution_id,
            "capability": capability or "none",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }

        # Cache in memory
        self._recent_events.append(event)
        if len(self._recent_events) > 500:
            self._recent_events = self._recent_events[-500:]

        logger.info(
            "RUNTIME_EVENT [%s] user=%s trace=%s cap=%s",
            event_type, user_id, trace_id, capability,
        )

        # Broadcast to active SSE subscribers
        stale_queues = set()
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except Exception:
                stale_queues.add(q)

        for q in stale_queues:
            self._subscribers.discard(q)

        return event

    async def subscribe(self, user_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Subscribe to real-time events formatted as Server-Sent Events (SSE)."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)

        try:
            # Yield initial connection confirmation
            yield f"data: {json.dumps({'event_type': 'connected', 'message': 'Subscribed to MITRA Runtime Event Feed'})}\n\n"

            while True:
                event = await queue.get()
                if user_id and event.get("user_id") not in (user_id, "anonymous", "system"):
                    continue
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self._subscribers.discard(queue)

    def get_recent_events(self, user_id: Optional[str] = None, limit: int = 50) -> list[Dict[str, Any]]:
        """Return recent runtime events for debugging / UI init."""
        events = self._recent_events
        if user_id:
            events = [e for e in events if e.get("user_id") in (user_id, "anonymous")]
        return events[-limit:]

# Global Singleton
runtime_event_bus = RuntimeEventBus()
