import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.agents.base import Blackboard, RunContext
from app.agents.genomics import GenomicsAgent
from app.engine import run_investigation
from app.events import EventBus
from app.execution import bounded_map, DEFAULT_VARIANT_CONCURRENCY
from app.ingest import build_bundle
from app.main import app, cancel_run
from app.models import Report
from app.providers import build_providers
from app.providers.mock import MockBioProvider
from app.store import runs


async def test_bounded_workers_preserve_order_and_cancel_siblings_on_failure():
    active = peak = 0

    async def work(index):
        nonlocal active, peak
        active += 1
        peak = max(active, peak)
        try:
            await asyncio.sleep(0.005)
            return index * 2
        finally:
            active -= 1

    assert await bounded_map(list(range(20)), work, 3) == [i * 2 for i in range(20)]
    assert peak == 3 and active == 0

    async def failing(index):
        nonlocal active
        active += 1
        try:
            if index == 0:
                await asyncio.sleep(0)
                raise RuntimeError("test")
            await asyncio.sleep(20)
        finally:
            active -= 1

    with pytest.raises(RuntimeError):
        await bounded_map(list(range(8)), failing, 3)
    assert active == 0


async def test_duplicate_scores_reused_with_original_source_provenance():
    files = [(f"f-{i}", f"source-{i}.vcf",
              f"12\t{25398284 + i % 5}\trs121913529\tC\tT\t.\tPASS\tGENE=KRAS;CSQ=p.Gly12Asp")
             for i in range(20)]
    bundle = build_bundle(files)
    providers = build_providers()
    original = providers.bio.score_variant
    calls = 0
    active = peak = 0

    async def measured(variant):
        nonlocal calls, active, peak
        calls += 1
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(0.005)
            return await original(variant)
        finally:
            active -= 1

    providers.bio.score_variant = measured
    ctx = RunContext(run_id="dedup", question="Why?", bundle=bundle, bus=EventBus("dedup"),
                     providers=providers, blackboard=Blackboard(), extras={"variant_concurrency": 3})
    agent = GenomicsAgent("genomics-1", "Investigate", ctx)
    await agent.run()
    assert calls == 5 and peak == 3 and active == 0
    assert len(agent.findings) == 20
    assert {f.provenance[0].ref for f in agent.findings} == {name for _, name, _ in files}
    assert ctx.extras["metrics"]["variant_cache_hits"] == 15
    assert ctx.extras["metrics"]["variant_requests"] == 20
    assert ctx.extras["metrics"]["variant_unique_requests"] == 5


async def test_cancel_before_engine_starts_terminates_report_and_stream(sample_bundle):
    run = runs.create("Why?", sample_bundle, "mock")
    run.task = asyncio.create_task(run_investigation(run_id=run.run_id, question=run.question,
        bundle=run.bundle, bus=run.bus, providers=build_providers(), report=run.report))
    result = await cancel_run(run.run_id)
    assert result["status"] == "cancelled" and run.bus.closed
    assert run.task.done()
    assert [event.type for event in run.bus.history] == ["run_complete"]
    assert run.bus.history[-1].payload["metrics"] == run.report.metrics
    assert (await cancel_run(run.run_id))["status"] == "cancelled"
    assert len(run.bus.history) == 1


async def test_running_cancel_stops_workers_preserves_findings_and_never_synthesizes(sample_bundle):
    providers = build_providers()
    entered = asyncio.Event()
    active = 0

    async def slow_score(variant):
        nonlocal active
        active += 1
        entered.set()
        try:
            await asyncio.sleep(30)
        finally:
            active -= 1

    providers.bio.score_variant = slow_score
    run = runs.create("Why?", sample_bundle, "mock")
    run.task = asyncio.create_task(run_investigation(run_id=run.run_id, question=run.question,
        bundle=sample_bundle, bus=run.bus, providers=providers, report=run.report))
    await entered.wait()
    # Allow the independent clinical specialist to file its findings.
    for _ in range(20):
        if any(event.type == "finding" for event in run.bus.history):
            break
        await asyncio.sleep(0)
    await cancel_run(run.run_id)
    assert active == 0 and run.bus.closed
    assert run.report.status == "cancelled"
    assert run.report.findings
    assert not any(method == "synthesize" for method, _ in providers.reasoning.calls)
    terminal = [event for event in run.bus.history if event.type == "run_complete"]
    assert len(terminal) == 1 and terminal[0].payload["cancelled"] is True
    assert any(item.id == "cancelled-investigation" for item in run.report.weak_points.items)
    assert any(agent.status == "cancelled" for agent in run.report.agents)
    assert run.report.metrics["variant_peak_concurrency"] <= DEFAULT_VARIANT_CONCURRENCY
    assert terminal[0].payload["agent_statuses"] == {agent.agent_id: agent.status for agent in run.report.agents}


async def test_disconnected_cancel_caller_does_not_interrupt_cleanup(sample_bundle):
    run = runs.create("Why?", sample_bundle, "mock")
    entered = asyncio.Event()
    cleaning = asyncio.Event()
    release = asyncio.Event()

    async def task_with_cleanup():
        entered.set()
        try:
            await asyncio.sleep(30)
        finally:
            cleaning.set()
            await release.wait()

    run.task = asyncio.create_task(task_with_cleanup())
    await entered.wait()
    caller = asyncio.create_task(cancel_run(run.run_id))
    await cleaning.wait()
    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await caller
    assert not run.task.done()
    release.set()
    for _ in range(20):
        if run.bus.closed:
            break
        await asyncio.sleep(0)
    assert run.task.done() and run.bus.closed
    assert run.report.status == "cancelled"
    assert len(run.bus.history) == 1


def test_cancel_http_acknowledges_terminal_state_and_unknown_id(monkeypatch):
    monkeypatch.setenv("MOCK_LATENCY_SCALE", "100")
    with TestClient(app) as client:
        assert client.post("/runs/missing/cancel").status_code == 404
        files = client.post("/demo/sample-patient").json()["files"]
        run_id = client.post("/investigate", json={"question": "Why?", "file_ids": [f["file_id"] for f in files]}).json()["run_id"]
        assert client.post(f"/runs/{run_id}/cancel").json()["status"] == "cancelled"
        report = client.get(f"/report/{run_id}").json()
        events = [json.loads(line[6:]) for line in client.get(f"/events/{run_id}").text.splitlines() if line.startswith("data: ")]
        assert events[-1]["payload"]["metrics"] == report["metrics"]
        assert events[-1]["payload"]["weak_points"] == report["weak_points"]
        assert client.post(f"/runs/{run_id}/cancel").json()["status"] == "cancelled"
