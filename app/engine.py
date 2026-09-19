"""The orchestration spine: plan, spawn, gather, criticise.

A plain async orchestrator that emits events directly, which is the fallback
path named in ARCHITECTURE.md. It is deliberately small so that swapping it for
the NVIDIA Agent Toolkit means re-implementing `run_investigation` alone —
everything either side of it (providers, agents, event bus, report) is
untouched by that decision.

Specialists run concurrently under `asyncio.gather`. They coordinate through
the blackboard rather than through the orchestrator, so one slow agent delays
only the agents that chose to wait on it.
"""

from __future__ import annotations

import asyncio
import time

from app.agents import AGENT_TYPES, Blackboard, CriticAgent, RunContext
from app.events import EventBus
from app.hypothesis import extract_hypothesis
from app.models import AgentSummary, PatientBundle, Report, Verdict
from app.execution import DEFAULT_VARIANT_CONCURRENCY, initial_metrics
from app.providers.base import Providers, SubTask
from app.weak_points import assess_weak_points
from app.skills import role_metadata, resolve_task_mode
from app.review import ReviewAgent, ReviewCritic, run_discussion

ORCHESTRATOR_ID = "orchestrator-0"
SPECIALIST_TIMEOUT = 180.0  # seconds; a hung live call must not hang the demo


async def run_investigation(
    *,
    run_id: str,
    question: str,
    bundle: PatientBundle,
    bus: EventBus,
    providers: Providers,
    report: Report,
    specialists: list[str] | None = None,
    variant_concurrency: int = DEFAULT_VARIANT_CONCURRENCY,
    task_mode: str = "investigation",
) -> Report:
    """Run one investigation to completion, filling and returning `report`."""
    if type(variant_concurrency) is not int or not 1 <= variant_concurrency <= 16:
        raise ValueError("variant_concurrency must be an integer between 1 and 16")
    if task_mode not in {"auto", "investigation", "idea_review"}:
        raise ValueError("Unknown task_mode")
    effective_mode, routing_reason = resolve_task_mode(task_mode, question, bundle)
    if effective_mode == "idea_review" and specialists is not None:
        raise ValueError("Idea review uses a fixed research/supporter/challenger team; omit specialists")
    report.config.update(requested_task_mode=task_mode, task_mode=effective_mode,
                         routing_reason=routing_reason)
    if effective_mode == "idea_review":
        report.config.update(specialists=["research", "supporter", "challenger"],
                             roster_source="idea_review_workflow")
    start = time.perf_counter()
    report.metrics = initial_metrics()
    report.config["variant_concurrency"] = variant_concurrency
    report.started_ts = bus._next_ts()  # noqa: SLF001 - the bus owns run time
    bus.emit(
        "run_started",
        agent_id=ORCHESTRATOR_ID,
        agent_role="orchestrator",
        payload={
            "question": question,
            "run_mode": providers.mode,
            "bundle": bundle.summary(),
            "files": [f.model_dump() for f in bundle.files],
            "config": dict(report.config),
        },
    )
    bus.emit(
        "agent_spawned",
        agent_id=ORCHESTRATOR_ID,
        agent_role="orchestrator",
        parent_id=None,
        payload={"task": "Decompose the question and direct the specialists.", **role_metadata("orchestrator")},
    )

    ctx = RunContext(
        run_id=run_id,
        question=question,
        bundle=bundle,
        bus=bus,
        providers=providers,
        blackboard=Blackboard(),
        hypothesis=extract_hypothesis(question),
        extras={"metrics": report.metrics, "variant_concurrency": variant_concurrency},
    )
    agents = []
    critic = None

    async def timed(name, work):
        phase_start = time.perf_counter()
        try:
            return await work
        finally:
            report.metrics[name] = round((time.perf_counter() - phase_start) * 1000, 3)

    def collect_agents():
        return [AgentSummary(agent_id=agent.agent_id, agent_role=agent.role,
            parent_id=agent.parent_id, task=agent.task, status=agent.status,
            n_findings=len(agent.findings), **role_metadata(agent.role)) for agent in [*agents, *([critic] if critic else [])]]

    try:
        if effective_mode == "idea_review":
            report.config["specialists"] = ["research", "supporter", "challenger"]
            report.config["roster_source"] = "idea_review_workflow"
            agents = [ReviewAgent(role, ctx, report.discussion)
                      for role in ("research", "supporter", "challenger")]
            for agent in agents:
                agent.spawned("Bounded proposal review; arguments are not evidence findings.")
            await timed("specialists_ms", asyncio.wait_for(run_discussion(agents), SPECIALIST_TIMEOUT))
            critic = ReviewCritic("critic", ctx, report.discussion)
        else:
            if bundle.is_empty:
                # Nothing was uploaded, or nothing parsed. Say so and let the critic
                # abstain on an empty blackboard rather than inventing an answer.
                bus.emit(
                    "agent_message",
                    agent_id=ORCHESTRATOR_ID,
                    agent_role="orchestrator",
                    payload={
                        "text": "No parsable patient data in the upload; the specialists have "
                                "nothing to work from."
                    },
                )
                plan_tasks = []
            else:
                plan_tasks = await timed("planning_ms", _plan(ctx))

            if specialists is not None:
                # A user-selected roster is authoritative, even if the planner omits
                # a role or the upload is empty. Agents can explain missing evidence.
                by_role = {task.role: task for task in plan_tasks}
                plan_tasks = [by_role.get(role) or SubTask(
                    role=role,
                    task=f"Investigate the question using the available {role} evidence: {question}",
                    rationale="Specialist explicitly selected by the user.",
                ) for role in specialists]
            report.config["specialists"] = [task.role for task in plan_tasks if task.role in AGENT_TYPES]
            if specialists is not None:
                bus.emit("agent_message", agent_id=ORCHESTRATOR_ID, agent_role="orchestrator",
                         payload={"text": f"User-selected roster: {', '.join(specialists)} "
                                  f"({len(specialists)} specialists, plus orchestrator and critic)."})
            agents = _spawn(ctx, plan_tasks)
            ctx.blackboard.expect({agent.role for agent in agents})
            if agents:
                try:
                    await timed("specialists_ms", asyncio.wait_for(
                        asyncio.gather(*(agent.run() for agent in agents)),
                        timeout=SPECIALIST_TIMEOUT,
                    ))
                except asyncio.TimeoutError:
                    bus.emit(
                        "error",
                        agent_id=ORCHESTRATOR_ID,
                        agent_role="orchestrator",
                        payload={
                            "error": f"specialists exceeded {SPECIALIST_TIMEOUT:.0f}s; "
                                     f"continuing with whatever they filed"
                        },
                    )

            critic = CriticAgent("critic-0", "Cross-check findings and answer.", ctx,
                                 parent_id=ORCHESTRATOR_ID)
        critic.spawned("Independent check on the specialists' claims.")
        critic.status = "running"
        verdict = await timed("synthesis_ms", critic.synthesize())
        critic.status = "done"

        report.findings = ctx.blackboard.all()
        report.agents = collect_agents()
        report.verdict = verdict
        report.status = "complete"
        report.weak_points = assess_weak_points(report, bundle, bus.history, ctx.hypothesis)
        report.metrics["wall_ms"] = round((time.perf_counter() - start) * 1000, 3)
        report.finished_ts = bus.emit(
            "run_complete",
            agent_id="critic-0",
            agent_role="critic",
            parent_id=ORCHESTRATOR_ID,
            payload={
                "verdict": verdict.answer,
                "rationale": verdict.rationale,
                "confidence": verdict.confidence,
                "abstained": verdict.abstained,
                "abstain_reason": verdict.abstain_reason,
                "caveats": verdict.caveats,
                "n_findings": len(report.findings),
                "weak_points": report.weak_points.model_dump(),
                "metrics": dict(report.metrics),
                "status": report.status,
                "agent_statuses": {agent.agent_id: agent.status for agent in report.agents},
                "task_mode": report.config.get("task_mode", "investigation"),
                "discussion": list(report.discussion),
            },
        ).ts
    except asyncio.CancelledError:
        if critic and critic.status == "running":
            critic.status = "cancelled"
        report.findings = ctx.blackboard.all()
        report.agents = collect_agents()
        report.metrics["wall_ms"] = round((time.perf_counter() - start) * 1000, 3)
        finalize_cancelled(report, bundle, bus, ctx.hypothesis)
        raise
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not swallowed
        if critic and critic.status == "running":
            critic.status = "error"
        report.agents = collect_agents()
        report.status = "error"
        report.error = f"{type(exc).__name__}: {exc}"
        bus.emit(
            "error",
            agent_id=ORCHESTRATOR_ID,
            agent_role="orchestrator",
            payload={"error": report.error, "fatal": True},
        )
        report.findings = ctx.blackboard.all()
        report.weak_points = assess_weak_points(report, bundle, bus.history, ctx.hypothesis)
        report.metrics["wall_ms"] = round((time.perf_counter() - start) * 1000, 3)
        report.finished_ts = bus.emit(
            "run_complete",
            agent_id=ORCHESTRATOR_ID,
            agent_role="orchestrator",
            payload={
                "verdict": "Run failed before a verdict could be produced.",
                "confidence": 0.0,
                "abstained": True,
                "abstain_reason": report.error,
                "error": report.error,
                "weak_points": report.weak_points.model_dump(),
                "metrics": dict(report.metrics),
                "status": report.status,
                "agent_statuses": {agent.agent_id: agent.status for agent in report.agents},
                "task_mode": report.config.get("task_mode", "investigation"),
                "discussion": list(report.discussion),
            },
        ).ts
    finally:
        bus.close()
    return report


def finalize_cancelled(report: Report, bundle: PatientBundle, bus: EventBus,
                       hypothesis: str | None = None) -> None:
    """Also works when cancellation happened before the engine coroutine began."""
    if report.status != "running" or bus.closed:
        return
    report.status = "cancelled"
    report.verdict = Verdict(answer="Investigation cancelled.",
        rationale="Execution was stopped; retained findings are partial and no synthesis was requested after cancellation.",
        confidence=0, abstained=True, abstain_reason="The investigation was cancelled before completion.")
    report.weak_points = assess_weak_points(report, bundle, bus.history, hypothesis)
    report.finished_ts = bus.emit("run_complete", agent_id=ORCHESTRATOR_ID, agent_role="orchestrator",
        payload={"status": "cancelled", "cancelled": True, "verdict": report.verdict.answer,
                 "confidence": 0.0, "abstained": True, "abstain_reason": report.verdict.abstain_reason,
                 "agent_statuses": {agent.agent_id: agent.status for agent in report.agents},
                "task_mode": report.config.get("task_mode", "investigation"),
                "discussion": list(report.discussion),
                 "weak_points": report.weak_points.model_dump(), "metrics": dict(report.metrics)}).ts
    bus.close()


async def _plan(ctx: RunContext) -> list:
    """Ask the reasoning provider for sub-investigations and narrate the result."""
    bus = ctx.bus
    bus.emit(
        "tool_call",
        agent_id=ORCHESTRATOR_ID,
        agent_role="orchestrator",
        payload={
            "tool": "reasoning.plan",
            "args": {"question": ctx.question, "bundle": ctx.bundle.summary()},
        },
    )
    plan = await ctx.providers.reasoning.plan(ctx.question, ctx.bundle)
    if plan.hypothesis:
        ctx.hypothesis = plan.hypothesis
    bus.emit(
        "tool_result",
        agent_id=ORCHESTRATOR_ID,
        agent_role="orchestrator",
        payload={
            "tool": "reasoning.plan",
            "result": {
                "restated_question": plan.restated_question,
                "hypothesis": plan.hypothesis,
                "tasks": [{"role": t.role, "task": t.task} for t in plan.tasks],
            },
        },
    )
    bus.emit(
        "agent_message",
        agent_id=ORCHESTRATOR_ID,
        agent_role="orchestrator",
        payload={
            "text": f"{plan.restated_question} {plan.notes} Planner proposed "
                    f"{len(plan.tasks)} specialist(s)."
        },
    )
    return plan.tasks


def _spawn(ctx: RunContext, tasks: list) -> list:
    """Instantiate one agent per planned sub-task, skipping unknown roles."""
    agents = []
    counters: dict[str, int] = {}
    for task in tasks:
        agent_cls = AGENT_TYPES.get(task.role)
        if agent_cls is None:
            ctx.bus.emit(
                "error",
                agent_id=ORCHESTRATOR_ID,
                agent_role="orchestrator",
                payload={"error": f"planner asked for unknown role {task.role!r}"},
            )
            continue
        counters[task.role] = counters.get(task.role, 0) + 1
        agent = agent_cls(
            f"{task.role}-{counters[task.role]}",
            task.task,
            ctx,
            parent_id=ORCHESTRATOR_ID,
        )
        agent.spawned(task.rationale)
        agents.append(agent)
    return agents
