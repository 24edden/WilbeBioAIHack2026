"""Agent scaffolding: identity, event emission, and the shared blackboard.

Agents never touch the transport. They emit onto the bus and publish to the
blackboard; whether anyone is watching is not their problem.
"""

from __future__ import annotations

import asyncio
import itertools
from dataclasses import dataclass, field
from typing import Any

from app.events import EventBus
from app.models import AgentRole, Finding, PatientBundle, Provenance, Stance
from app.providers.base import Providers
from app.skills import role_metadata

_counter = itertools.count(1)


def new_finding_id() -> str:
    return f"finding-{next(_counter)}"


class Blackboard:
    """Where specialists read each other's work.

    The literature agent, for example, waits on the genomics agent's first
    finding so it can search for the gene that was actually found rather than a
    generic query. That wait is what makes the agents a system instead of three
    independent calls, and the timeout is what stops one slow specialist from
    taking the run down with it.
    """

    def __init__(self) -> None:
        self._findings: list[Finding] = []
        self._signals: dict[str, asyncio.Event] = {}
        self._expected: set[str] | None = None

    def _signal(self, role: str) -> asyncio.Event:
        return self._signals.setdefault(role, asyncio.Event())

    def expect(self, roles: set[str]) -> None:
        """Roles the orchestrator actually spawned. Waiting on a role that was
        never spawned returns immediately instead of burning the timeout."""
        self._expected = set(roles)

    def finished(self, role: str) -> None:
        """Wake anyone waiting on `role`, whether or not it filed anything."""
        self._signal(role).set()

    def publish(self, finding: Finding) -> None:
        self._findings.append(finding)
        self._signal(finding.agent_role).set()

    def all(self) -> list[Finding]:
        return list(self._findings)

    def by_role(self, role: AgentRole) -> list[Finding]:
        return [f for f in self._findings if f.agent_role == role]

    async def wait_for(self, role: AgentRole, timeout: float) -> list[Finding]:
        """Findings from `role`, waiting up to `timeout` seconds for the first
        one. Returns whatever exists when the wait ends — an empty list is a
        normal outcome, not an error."""
        if self._expected is not None and role not in self._expected:
            return []
        try:
            await asyncio.wait_for(self._signal(role).wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        return self.by_role(role)


@dataclass
class RunContext:
    """Everything an agent needs that is not its own task."""

    run_id: str
    question: str
    bundle: PatientBundle
    bus: EventBus
    providers: Providers
    blackboard: Blackboard
    hypothesis: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


class Agent:
    """Base class. Subclasses implement `investigate`."""

    role: AgentRole = "clinical"

    def __init__(
        self,
        agent_id: str,
        task: str,
        ctx: RunContext,
        parent_id: str | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.task = task
        self.ctx = ctx
        self.parent_id = parent_id
        self.findings: list[Finding] = []
        self.status = "spawned"

    # --- event helpers ---------------------------------------------------

    def spawned(self, rationale: str = "") -> None:
        self.ctx.bus.emit(
            "agent_spawned",
            agent_id=self.agent_id,
            agent_role=self.role,
            parent_id=self.parent_id,
            payload={"task": self.task, "rationale": rationale, **role_metadata(self.role)},
        )

    def say(self, text: str, to: str | None = None) -> None:
        self.ctx.bus.emit(
            "agent_message",
            agent_id=self.agent_id,
            agent_role=self.role,
            parent_id=to or self.parent_id,
            payload={"text": text},
        )

    def tool_call(self, tool: str, **args: Any) -> None:
        self.ctx.bus.emit(
            "tool_call",
            agent_id=self.agent_id,
            agent_role=self.role,
            parent_id=self.parent_id,
            payload={"tool": tool, "args": args},
        )

    def tool_result(self, tool: str, result: Any, **meta: Any) -> None:
        self.ctx.bus.emit(
            "tool_result",
            agent_id=self.agent_id,
            agent_role=self.role,
            parent_id=self.parent_id,
            payload={"tool": tool, "result": result, **meta},
        )

    def record(
        self,
        claim: str,
        *,
        confidence: float,
        provenance: list[Provenance],
        stance: Stance = "neutral",
        detail: dict[str, Any] | None = None,
    ) -> Finding:
        """Emit a finding and publish it to the blackboard.

        Every finding carries provenance. An agent with nothing to cite has
        nothing to say, and the critic's evidence gate enforces that.
        """
        finding = Finding(
            finding_id=new_finding_id(),
            agent_id=self.agent_id,
            agent_role=self.role,
            claim=claim,
            stance=stance,
            confidence=max(0.0, min(1.0, confidence)),
            provenance=provenance,
            detail=detail or {},
        )
        self.findings.append(finding)
        self.ctx.blackboard.publish(finding)
        self.ctx.bus.emit(
            "finding",
            agent_id=self.agent_id,
            agent_role=self.role,
            parent_id=self.parent_id,
            payload={
                "finding_id": finding.finding_id,
                "finding": finding.claim,
                "stance": finding.stance,
                "confidence": finding.confidence,
                "provenance": [p.model_dump() for p in finding.provenance],
                "detail": finding.detail,
            },
        )
        return finding

    # --- lifecycle -------------------------------------------------------

    async def investigate(self) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    async def run(self) -> list[Finding]:
        """Run the agent, converting any failure into an `error` event.

        One specialist falling over must not take the investigation with it;
        the critic is told what is missing and lowers its confidence instead.
        """
        self.status = "running"
        try:
            await self.investigate()
            self.status = "done"
        except asyncio.CancelledError:
            self.status = "cancelled"
            raise
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            self.status = "error"
            self.ctx.bus.emit(
                "error",
                agent_id=self.agent_id,
                agent_role=self.role,
                parent_id=self.parent_id,
                payload={"error": f"{type(exc).__name__}: {exc}", "task": self.task},
            )
        finally:
            # Release anyone waiting on this role even if it found nothing.
            self.ctx.blackboard.finished(self.role)
        return self.findings
