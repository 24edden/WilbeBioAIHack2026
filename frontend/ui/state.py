"""Accumulated view of a run, built by folding events in arrival order.

The UI renders `RunState` and nothing else — every panel is a pure function of
this object, so replaying a saved event log gives a pixel-identical view to a
live run. Keep it that way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .events import Event

RUNNING = "running"
DONE = "done"
FAILED = "failed"


@dataclass
class Agent:
    id: str
    role: str = "unknown"
    parent_id: str | None = None
    status: str = RUNNING
    spawned_ts: int = 0
    activity: int = 0
    last_line: str = ""


@dataclass
class Finding:
    agent_id: str
    role: str
    text: str
    confidence: float | None
    provenance: list[dict[str, Any]] = field(default_factory=list)
    ts: int = 0


@dataclass
class Message:
    ts: int
    type: str
    agent_id: str
    role: str
    parent_id: str | None
    text: str


@dataclass
class RunState:
    run_id: str = ""
    question: str = ""
    files: list[str] = field(default_factory=list)
    agents: dict[str, Agent] = field(default_factory=dict)
    edges: set[tuple[str, str]] = field(default_factory=set)
    # (sender, recipient) -> number of messages, used to label the graph edges
    talk: dict[tuple[str, str], int] = field(default_factory=dict)
    # the agent that produced the most recent event, highlighted in the graph
    active_id: str | None = None
    findings: list[Finding] = field(default_factory=list)
    timeline: list[Message] = field(default_factory=list)
    raw: list[Event] = field(default_factory=list)
    verdict: str = ""
    confidence: float | None = None
    abstained: bool = False
    complete: bool = False
    errors: list[str] = field(default_factory=list)

    # -- folding ---------------------------------------------------------

    def apply(self, ev: Event) -> None:
        self.raw.append(ev)
        if ev.run_id and not self.run_id:
            self.run_id = ev.run_id
        if ev.agent_id:
            self.active_id = ev.agent_id

        handler = getattr(self, f"_on_{ev.type}", None)
        if handler is None:
            # Unknown event type: still show it on the timeline rather than
            # dropping it, so a backend schema change is visible not silent.
            self._log(ev)
            return
        handler(ev)

    def _on_run_started(self, ev: Event) -> None:
        self.question = str(ev.payload.get("question") or self.question)
        files = ev.payload.get("files")
        if isinstance(files, list):
            self.files = [str(f) for f in files]
        self._log(ev)

    def _on_agent_spawned(self, ev: Event) -> None:
        if not ev.agent_id:
            return
        self.agents[ev.agent_id] = Agent(
            id=ev.agent_id,
            role=ev.agent_role or "unknown",
            parent_id=ev.parent_id,
            spawned_ts=ev.ts,
        )
        if ev.parent_id:
            self.edges.add((ev.parent_id, ev.agent_id))
        self._log(ev)

    def _on_agent_message(self, ev: Event) -> None:
        self._touch(ev)
        # A message names its recipient in parent_id; draw it so agent-to-agent
        # cross-examination is visible in the graph, not just the timeline.
        if ev.agent_id and ev.parent_id and ev.parent_id in self.agents:
            pair = (ev.agent_id, ev.parent_id)
            self.edges.add(pair)
            self.talk[pair] = self.talk.get(pair, 0) + 1
        self._log(ev)

    def _on_tool_call(self, ev: Event) -> None:
        self._touch(ev)
        self._log(ev)

    def _on_tool_result(self, ev: Event) -> None:
        self._touch(ev)
        self._log(ev)

    def _on_finding(self, ev: Event) -> None:
        self._touch(ev)
        agent = self.agents.get(ev.agent_id or "")
        if agent is not None:
            agent.status = DONE
        self.findings.append(
            Finding(
                agent_id=ev.agent_id or "?",
                role=ev.agent_role or (agent.role if agent else "unknown"),
                text=ev.text,
                confidence=ev.confidence,
                provenance=ev.provenance,
                ts=ev.ts,
            )
        )
        self._log(ev)

    def _on_run_complete(self, ev: Event) -> None:
        self.verdict = ev.text
        self.confidence = ev.confidence
        self.abstained = bool(ev.payload.get("abstained"))
        self.complete = True
        for agent in self.agents.values():
            if agent.status == RUNNING:
                agent.status = DONE
        self._log(ev)

    def _on_error(self, ev: Event) -> None:
        message = ev.text or "unknown error"
        self.errors.append(message)
        agent = self.agents.get(ev.agent_id or "")
        if agent is not None:
            agent.status = FAILED
        self._log(ev)

    # -- helpers ---------------------------------------------------------

    def _touch(self, ev: Event) -> None:
        if not ev.agent_id:
            return
        agent = self.agents.get(ev.agent_id)
        if agent is None:
            # Event from an agent we never saw spawn — synthesise it so the
            # graph stays connected instead of losing the activity.
            agent = Agent(id=ev.agent_id, role=ev.agent_role or "unknown", parent_id=ev.parent_id)
            self.agents[ev.agent_id] = agent
            if ev.parent_id:
                self.edges.add((ev.parent_id, ev.agent_id))
        agent.activity += 1
        if ev.text:
            agent.last_line = ev.text

    def _log(self, ev: Event) -> None:
        self.timeline.append(
            Message(
                ts=ev.ts,
                type=ev.type,
                agent_id=ev.agent_id or "system",
                role=ev.agent_role or "",
                parent_id=ev.parent_id,
                text=ev.text,
            )
        )

    # -- derived ---------------------------------------------------------

    @property
    def active_agents(self) -> int:
        return sum(1 for a in self.agents.values() if a.status == RUNNING)

    @property
    def elapsed_ms(self) -> int:
        if not self.raw:
            return 0
        return max(e.ts for e in self.raw) - min(e.ts for e in self.raw)

    @property
    def conversation(self) -> list[Message]:
        """Agent-to-agent talk only — the cross-examination, not the tool noise."""
        return [m for m in self.timeline if m.type == "agent_message"]

    def findings_by_confidence(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: (f.confidence is None, -(f.confidence or 0)))
