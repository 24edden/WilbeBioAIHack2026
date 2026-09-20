import asyncio
import copy
import json

import pytest
from fastapi.testclient import TestClient

from app.engine import run_investigation
from app.events import EventBus
from app.main import app
from app.models import PatientBundle, Report
from app.providers import build_providers
from app.skills import resolve_task_mode


async def review(question="Review my idea for a biology evidence tracker", providers=None):
    report = Report(run_id="review", question=question)
    bus = EventBus(report.run_id)
    await run_investigation(run_id=report.run_id, question=question, bundle=PatientBundle(),
                            providers=providers or build_providers(), bus=bus, report=report,
                            task_mode="idea_review")
    return report, bus


async def test_review_roles_exchange_prior_arguments_without_invented_findings():
    providers = build_providers()
    original = providers.reasoning.step
    calls = []

    async def observed(role, task, context):
        calls.append((role, copy.deepcopy(context)))
        return await original(role, task, context)

    providers.reasoning.step = observed
    report, bus = await review(providers=providers)
    assert report.status == "complete" and report.verdict.abstained
    assert report.verdict.answer.startswith("Idea review complete")
    assert report.findings == []
    assert [role for role, _ in calls] == ["supporter", "challenger", "supporter", "critic"]
    assert [len(context["discussion"]) for _, context in calls] == [1, 2, 3, 4]
    assert [item["phase"] for item in report.discussion] == ["input_inventory", "opening", "challenge", "revision", "summary"]
    assert all(not item["evidence_refs"] and not item["provenance"] for item in report.discussion)
    assert report.discussion[3]["reply_to"] == report.discussion[2]["id"]
    assert "Challenge to" in report.discussion[3]["text"]
    assert bus.history[0].payload["config"]["specialists"] == ["research", "supporter", "challenger"]
    assert bus.history[-1].payload["discussion"] == report.discussion
    assert not any(item.category == "conflicting_findings" for item in report.weak_points.items)
    assert all(event.payload["skills"] for event in bus.history if event.type == "agent_spawned")
    assert any(event.agent_role == "challenger" and event.parent_id == "supporter-1"
               for event in bus.history if event.type == "agent_message")


async def test_different_questions_produce_different_proposals():
    first, _ = await review("Review my idea: a protein search interface")
    second, _ = await review("Review my idea: a lab scheduling assistant")
    assert first.discussion[1]["text"] != second.discussion[1]["text"]
    assert "protein search" in first.verdict.answer
    assert "lab scheduling" in second.verdict.answer


async def test_research_inventory_reuses_real_upload_sources(sample_bundle):
    report = Report(run_id="source-review", question="Review my idea")
    bus = EventBus(report.run_id)
    await run_investigation(run_id=report.run_id, question=report.question, bundle=sample_bundle,
                           providers=build_providers(), bus=bus, report=report, task_mode="idea_review")
    inventory = report.discussion[0]
    assert inventory["basis"] == "source_grounded"
    assert inventory["provenance"] and len(inventory["provenance"]) <= 9
    assert set(inventory["evidence_refs"]) <= {file.filename for file in sample_bundle.files}
    assert "no external research" in inventory["text"]
    assert all(not item["provenance"] for item in report.discussion[1:])
    assert not report.findings


def test_routing_is_conservative_and_legacy_mode_unchanged(sample_bundle):
    empty = PatientBundle()
    assert resolve_task_mode("auto", "Review my idea", empty)[0] == "idea_review"
    assert resolve_task_mode("auto", "Why did treatment fail?", empty)[0] == "investigation"
    assert resolve_task_mode("auto", "Review my idea", sample_bundle)[0] == "idea_review"
    assert resolve_task_mode("auto", "Evaluate this proposal", sample_bundle)[0] == "idea_review"
    assert resolve_task_mode("auto", "What does the trial design reveal about these lab results?", sample_bundle)[0] == "investigation"
    assert resolve_task_mode("investigation", "Review my idea", empty)[0] == "investigation"
    assert resolve_task_mode("idea_review", "Review my idea", sample_bundle)[0] == "idea_review"


async def test_provider_failure_is_reported_without_manufactured_debate():
    providers = build_providers()
    original = providers.reasoning.step

    async def failing(role, task, context):
        if role == "challenger":
            raise RuntimeError("unavailable")
        return await original(role, task, context)

    providers.reasoning.step = failing
    report, bus = await review(providers=providers)
    assert any(agent.agent_role == "challenger" and agent.status == "error" for agent in report.agents)
    assert not any(item["phase"] == "challenge" for item in report.discussion)
    assert not any(item["phase"] == "revision" for item in report.discussion)
    assert "incomplete" in report.verdict.rationale
    assert any(item.category == "provider_failure" for item in report.weak_points.items)
    assert report.verdict.abstained and not report.findings


async def test_review_cancellation_keeps_partial_discussion_and_skips_summary():
    providers = build_providers()
    entered = asyncio.Event()

    async def slow(role, task, context):
        entered.set()
        await asyncio.sleep(30)

    providers.reasoning.step = slow
    report = Report(run_id="cancel-review", question="Review my idea")
    bus = EventBus(report.run_id)
    task = asyncio.create_task(run_investigation(run_id=report.run_id, question=report.question,
        bundle=PatientBundle(), providers=providers, report=report, bus=bus, task_mode="idea_review"))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert report.status == "cancelled" and len(report.discussion) == 1
    assert bus.history[-1].payload["discussion"] == report.discussion
    assert bus.history[-1].payload["task_mode"] == "idea_review"


def test_http_review_contract_and_incompatible_override():
    with TestClient(app) as client:
        caps = client.get("/capabilities").json()
        assert {role["id"] for role in caps["review_roles"]} == {"research", "supporter", "challenger"}
        invalid = {"question": "Review my idea", "config": {"task_mode": "idea_review", "specialists": ["clinical"]}}
        assert client.post("/investigate", json=invalid).status_code == 422
        run_id = client.post("/investigate", json={"question": "Review my idea", "config": {"task_mode": "auto"}}).json()["run_id"]
        events = [json.loads(line[6:]) for line in client.get(f"/events/{run_id}").text.splitlines() if line.startswith("data: ")]
        report = client.get(f"/report/{run_id}").json()
        assert report["config"]["task_mode"] == "idea_review"
        assert report["discussion"] == events[-1]["payload"]["discussion"]
