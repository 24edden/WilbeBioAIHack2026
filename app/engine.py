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

from app.agents import AGENT_TYPES, Blackboard, CriticAgent, RunContext
from app.events import EventBus
from app.hypothesis import extract_hypothesis
from app.models import AgentSummary, PatientBundle, Report
from app.providers.base import Providers

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
) -> Report:
    """Run one investigation to completion, filling and returning `report`."""
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
        },
    )
    bus.emit(
        "agent_spawned",
        agent_id=ORCHESTRATOR_ID,
        agent_role="orchestrator",
        parent_id=None,
        payload={"task": "Decompose the question and direct the specialists."},
    )

    ctx = RunContext(
        run_id=run_id,
        question=question,
        bundle=bundle,
        bus=bus,
        providers=providers,
        blackboard=Blackboard(),
        hypothesis=extract_hypothesis(question),
    )

    try:
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
            plan_tasks = await _plan(ctx)

        agents = _spawn(ctx, plan_tasks)
        ctx.blackboard.expect({agent.role for agent in agents})
        if agents:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*(agent.run() for agent in agents)),
                    timeout=SPECIALIST_TIMEOUT,
                )
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
        verdict = await critic.synthesize()

        report.findings = ctx.blackboard.all()
        report.agents = [
            AgentSummary(
                agent_id=agent.agent_id,
                agent_role=agent.role,
                parent_id=agent.parent_id,
                task=agent.task,
                status="done",
                n_findings=len(agent.findings),
            )
            for agent in [*agents, critic]
        ]
        report.verdict = verdict
        report.status = "complete"
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
            },
        ).ts
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not swallowed
        report.status = "error"
        report.error = f"{type(exc).__name__}: {exc}"
        bus.emit(
            "error",
            agent_id=ORCHESTRATOR_ID,
            agent_role="orchestrator",
            payload={"error": report.error, "fatal": True},
        )
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
            },
        ).ts
    finally:
        bus.close()
    return report


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
            "text": f"{plan.restated_question} {plan.notes} Spawning "
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
