"""The event bus — the second seam of the design (ARCHITECTURE.md).

Every agent action emits a structured event. The UI subscribes over SSE and
renders the live graph. Nothing in here imports anything UI-shaped, and the
agents never touch a socket.

Two properties the UI depends on:

* **Replay.** `POST /investigate` returns a `run_id` and the run starts
  immediately, so the browser always connects *after* the first events have
  fired. `subscribe()` therefore replays the history before switching to live
  delivery — otherwise the graph would be missing its own root node.
* **Monotonic `ts`.** Wall-clock ms, forced non-decreasing within a run, so the
  timeline can sort on it without tie-breaking.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models import AgentRole

EventType = Literal[
    "run_started",
    "agent_spawned",
    "agent_message",
    "tool_call",
    "tool_result",
    "finding",
    "run_complete",
    "error",
]


class Event(BaseModel):
    """SHARED CONTRACT with hack-frontend — coordinate changes."""

    type: EventType
    ts: int
    run_id: str
    agent_id: str
    agent_role: AgentRole
    parent_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class EventBus:
    """Fan-out of one run's events to any number of subscribers, with replay."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.history: list[Event] = []
        self._subscribers: set[asyncio.Queue[Event | None]] = set()
        self._last_ts = 0
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def _next_ts(self) -> int:
        ts = int(time.time() * 1000)
        if ts <= self._last_ts:
            ts = self._last_ts + 1
        self._last_ts = ts
        return ts

    def emit(
        self,
        type: EventType,
        *,
        agent_id: str,
        agent_role: AgentRole,
        parent_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Event:
        """Record and broadcast an event. Never blocks, never raises on a slow
        subscriber — a stalled browser must not stall the investigation."""
        if self._closed:
            raise RuntimeError(f"event bus for run {self.run_id} is closed")
        event = Event(
            type=type,
            ts=self._next_ts(),
            run_id=self.run_id,
            agent_id=agent_id,
            agent_role=agent_role,
            parent_id=parent_id,
            payload=payload or {},
        )
        self.history.append(event)
        for queue in list(self._subscribers):
            queue.put_nowait(event)
        return event

    def close(self) -> None:
        """Mark the run finished and let every open stream end cleanly."""
        if self._closed:
            return
        self._closed = True
        for queue in list(self._subscribers):
            queue.put_nowait(None)

    async def subscribe(self) -> AsyncIterator[Event]:
        """Replay everything so far, then yield live events until the run ends.

        The queue is registered *before* the replay so no event can slip through
        the gap; `ts` is strictly increasing per bus, so it doubles as the
        de-duplication key between the replayed tail and the live stream.
        """
        queue: asyncio.Queue[Event | None] = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            last_ts = 0
            seen = 0
            while seen < len(self.history):
                event = self.history[seen]
                seen += 1
                last_ts = event.ts
                yield event
            if self._closed:
                return
            while True:
                event = await queue.get()
                if event is None:
                    return
                if event.ts <= last_ts:
                    continue
                last_ts = event.ts
                yield event
        finally:
            self._subscribers.discard(queue)
