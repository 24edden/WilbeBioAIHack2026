"""Event schema: SHARED CONTRACT with the backend (see ARCHITECTURE.md).

Field names here mirror the contract exactly. Do not rename them unilaterally;
coordinate with the `hack-infra` worktree first.

Parsing is deliberately forgiving: an unknown `type`, a missing field or a
malformed payload must never take the UI down mid-demo. Anything unparseable
becomes an `error` event and is rendered as such.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable

EVENT_TYPES = (
    "run_started",
    "agent_spawned",
    "agent_message",
    "tool_call",
    "tool_result",
    "finding",
    "run_complete",
    "error",
)

AGENT_ROLES = (
    "orchestrator",
    "genomics",
    "literature",
    "clinical",
    "stats",
    "critic",
)


@dataclass
class Event:
    type: str
    ts: int = 0
    run_id: str = ""
    agent_id: str | None = None
    agent_role: str | None = None
    parent_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Any) -> "Event":
        if not isinstance(raw, dict):
            return cls(type="error", payload={"message": f"non-object event: {raw!r}"})
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            payload = {} if payload is None else {"value": payload}
        try:
            ts = int(raw.get("ts") or 0)
        except (TypeError, ValueError):
            ts = 0
        return cls(
            type=str(raw.get("type") or "error"),
            ts=ts,
            run_id=str(raw.get("run_id") or ""),
            agent_id=raw.get("agent_id"),
            agent_role=raw.get("agent_role"),
            parent_id=raw.get("parent_id"),
            payload=payload,
        )

    @classmethod
    def from_json(cls, blob: str) -> "Event":
        try:
            return cls.from_dict(json.loads(blob))
        except json.JSONDecodeError as exc:
            return cls(type="error", payload={"message": f"bad JSON from stream: {exc}"})

    @property
    def known_type(self) -> bool:
        return self.type in EVENT_TYPES

    @property
    def text(self) -> str:
        """Best-effort human-readable line for this event."""
        p = self.payload
        for key in ("message", "text", "finding", "verdict", "summary"):
            value = p.get(key)
            if isinstance(value, str) and value:
                return value
        if self.type == "tool_call":
            return f"{p.get('tool', 'tool')}({_fmt_args(p.get('args'))})"
        if self.type == "tool_result":
            return _fmt_short(p.get("result", p))
        return _fmt_short(p) if p else ""

    @property
    def confidence(self) -> float | None:
        value = self.payload.get("confidence")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return max(0.0, min(1.0, float(value)))
        return None

    @property
    def provenance(self) -> list[dict[str, Any]]:
        items = self.payload.get("provenance")
        if not isinstance(items, list):
            return []
        return [i if isinstance(i, dict) else {"source": str(i)} for i in items]


def _fmt_args(args: Any) -> str:
    if not isinstance(args, dict):
        return _fmt_short(args)
    return ", ".join(f"{k}={_fmt_short(v)}" for k, v in args.items())


def _fmt_short(value: Any, limit: int = 120) -> str:
    if isinstance(value, str):
        text = value
    elif value is None:
        text = ""
    else:
        try:
            text = json.dumps(value, default=str)
        except (TypeError, ValueError):
            text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def parse_many(raws: Iterable[Any]) -> list[Event]:
    return [Event.from_dict(r) for r in raws]
