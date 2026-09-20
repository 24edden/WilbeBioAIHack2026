"""Durable interpretation lifecycle; no external inference or scientific re-run."""
import asyncio
import copy

import pytest

from app import research_brief, providers
from app.brief_operations import enqueue_research_brief, input_identity
from app.store import Conflict, digest
from test_harness import harness, complete


@pytest.fixture
def completed_live(harness):
    client, store, worker = harness
    record = complete(harness)
    record = store.mutate(record["id"], lambda run: run.update(mode="live"))
    return client, store, worker, record


def request():
    return {"decision_version": 1, "idempotency_key": "one-explicit-interpretation"}


def fake_result(run):
    return {"schema": "team-tbd-research-brief-1", "content": {"headline": "Software fixture only"},
            "provider_metadata": {"dispatched_requests": 2, "usage": {"input_tokens": 100, "output_tokens": 50}},
            "skill_receipts": [], "model_review": {"verdict": "accepted"}}


def test_queue_and_retry_preserve_scientific_history_and_do_not_call_models(completed_live, monkeypatch):
    client, store, worker, original = completed_live
    monkeypatch.setattr(research_brief, "generate_research_brief", lambda *_args, **_kw: pytest.fail("Queue cannot call a model"))
    endpoint = f"/api/runs/{original['id']}/research-briefs"
    queued = client.post(endpoint, json=request())
    assert queued.status_code == 202
    assert queued.json()["operation"]["kind"] == "research_brief"
    assert input_identity(store.get(original["id"])) == input_identity(original)
    assert len(queued.json()["research_brief_operations"]) == 1
    assert client.post(endpoint, json=request()).json() == queued.json()
    assert client.post(endpoint, json={**request(), "idempotency_key": "double-click"}).status_code == 409
    assert client.post(endpoint, json={**request(), "molecular_audit": {"verified": True}}).status_code == 422


def test_two_pass_result_publishes_addendum_without_another_decision_or_governance_loop(completed_live, monkeypatch):
    client, store, worker, original = completed_live
    calls = []
    async def generate(run, case, emit=None, cancelled=None, **kwargs):
        calls.append(copy.deepcopy(run))
        assert kwargs["extra_context"]["molecular_audit"]["run_id"] == run["id"]
        assert store.get(run["id"])["actions"][-1]["state"] == "submitting"
        return fake_result(run)
    monkeypatch.setattr(research_brief, "generate_research_brief", generate)
    monkeypatch.setattr(providers, "investigate", lambda *_a, **_kw: pytest.fail("No specialist investigation is authorized"))
    enqueue_research_brief(store, original["id"], request())
    asyncio.run(worker.execute(original["id"]))
    final = store.get(original["id"])
    assert final["status"] == "completed", final.get("error")
    assert len(calls) == 1 and len(final["research_briefs"]) == 1
    assert input_identity(final) == input_identity(original)
    assert final.get("governance_state") == original.get("governance_state")
    assert final["research_briefs"][0]["source_decision_sha256"] == original["decisions"][-1]["sha256"]
    assert final["research_briefs"][0]["human_review_status"] == "unreviewed"
    brief = final["research_briefs"][0]
    assert brief["sha256"] == digest({key: value for key, value in brief.items() if key != "sha256"})
    assert final["usage"]["model_calls"] == original["usage"]["model_calls"] + 2
    assert final["research_brief_operations"][-1]["status"] == "completed"
    assert final["actions"][-1]["state"] == "succeeded"
    # An uncertain acknowledgement with the same request key never adds work.
    assert enqueue_research_brief(store, original["id"], request())["status"] == "completed"
    assert len(store.get(original["id"])["research_briefs"]) == 1


def test_changed_source_rejected_before_model_dispatch(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    enqueue_research_brief(store, original["id"], request())
    store.mutate(original["id"], lambda run: run["evidence"][0].update(summary="Changed since selection"))
    monkeypatch.setattr(research_brief, "generate_research_brief", lambda *_a, **_kw: pytest.fail("Changed sources must not reach a provider"))
    asyncio.run(worker.execute(original["id"]))
    final = store.get(original["id"])
    assert final["status"] == "failed"
    assert "source results changed" in final["error"]
    assert final["research_brief_operations"][-1]["status"] == "failed"


def test_timeout_remains_unknown_and_cannot_be_replayed(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    async def timeout(*_a, **_kw):
        raise providers.ProviderError("Timed out", status="unknown", reason_code="model_request_timeout",
             metadata={"dispatched_requests": 1, "requests": [{"status": "dispatched"}], "usage": {}})
    monkeypatch.setattr(research_brief, "generate_research_brief", timeout)
    enqueue_research_brief(store, original["id"], request())
    asyncio.run(worker.execute(original["id"]))
    final = store.get(original["id"])
    assert final["status"] == "blocked"
    assert final["actions"][-1]["state"] == "unknown"
    assert final["research_brief_operations"][-1]["status"] == "blocked"
    assert not final.get("research_briefs")
    assert input_identity(final) == input_identity(original)
    with pytest.raises(Conflict, match="unresolved"):
        enqueue_research_brief(store, original["id"], {**request(), "idempotency_key": "new-key"})


def test_queued_cancel_updates_operation_without_model_call(completed_live):
    client, store, worker, original = completed_live
    enqueue_research_brief(store, original["id"], request())
    response = client.post(f"/api/runs/{original['id']}/cancel")
    assert response.status_code == 200
    final = store.get(original["id"])
    assert final["status"] == "cancelled"
    assert final["research_brief_operations"][-1]["status"] == "cancelled"
    assert input_identity(final) == input_identity(original)


def test_restart_marks_running_brief_unknown_and_preserves_results(completed_live):
    _, store, worker, original = completed_live
    queued = enqueue_research_brief(store, original["id"], request())
    action_id = queued["operation"]["id"] + "-research-brief"
    store.begin_action(original["id"], action_id, "research-interpretation", {})
    def running(run):
        run["status"] = "running"
        run["research_brief_operations"][-1]["status"] = "running"
    store.mutate(original["id"], running)
    worker.recover()
    final = store.get(original["id"])
    assert final["status"] == "blocked"
    assert final["research_brief_operations"][-1]["status"] == "blocked"
    assert final["actions"][-1]["state"] == "unknown"
    assert input_identity(final) == input_identity(original)


def test_saved_success_publishes_without_reauditing_or_repeating_model_calls(completed_live, monkeypatch):
    import app.molecular_interpretation as molecular
    _, store, worker, original = completed_live
    queued = enqueue_research_brief(store, original["id"], request())
    entry = queued["operation"]["input"]
    action_id = entry["id"] + "-research-brief"
    audit = {"run_id": original["id"], "sequence_inventory": [], "status": "no_molecular_evidence"}
    receipt = {key: entry[key] for key in ("input_versions", "instruction_hashes", "model", "source_decision_sha256")}
    receipt["molecular_audit_sha256"] = digest(audit)
    store.begin_action(original["id"], action_id, "research-interpretation", receipt)
    result = {**fake_result(original), "molecular_audit": audit, "sha256": "provider-envelope-hash"}
    store.end_action(original["id"], action_id, "succeeded", result)
    monkeypatch.setattr(research_brief, "generate_research_brief", lambda *_a, **_kw: pytest.fail("Stored success cannot rerun the model"))
    monkeypatch.setattr(molecular, "audit_molecular_evidence", lambda *_a, **_kw: pytest.fail("Stored success reuses its frozen audit"))
    asyncio.run(worker.execute(original["id"]))
    final = store.get(original["id"])
    assert final["status"] == "completed", final.get("error")
    brief = final["research_briefs"][0]
    assert brief["molecular_audit"] == audit
    assert brief["sha256"] == digest({key: value for key, value in brief.items() if key != "sha256"})
    assert input_identity(final) == input_identity(original)


def test_changed_required_study_receipt_rejected_before_model_dispatch(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    store.mutate(original["id"], lambda run: run.update(required_analysis_operations=[
        {"analysis_id": "registered-study-analysis", "status": "completed", "evidence_id": "accepted-study-evidence"}]))
    enqueue_research_brief(store, original["id"], request())
    store.mutate(original["id"], lambda run: run["required_analysis_operations"][0].update(status="changed"))
    monkeypatch.setattr(research_brief, "generate_research_brief", lambda *_a, **_kw: pytest.fail("Changed study coverage must not reach a provider"))
    asyncio.run(worker.execute(original["id"]))
    final = store.get(original["id"])
    assert final["status"] == "failed" and "source results changed" in final["error"]
    assert not final.get("research_briefs") and final["actions"] == original["actions"]
