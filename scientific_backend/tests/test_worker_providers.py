"""Worker integration boundaries with explicitly mocked vendor adapters."""
import asyncio
import copy
import hashlib
import json
import uuid

import pytest

from app import providers, worker as w
from app.store import Store
from test_providers import decision, team_transport


@pytest.fixture
def running(monkeypatch, tmp_path):
    from governance_fixtures import pin_legacy_manual_policy
    monkeypatch.setattr(w, "RUNTIME", tmp_path / "runtime")
    monkeypatch.setattr(w, "DEMO_DELAY", 0)
    store = Store(tmp_path / "state.sqlite")
    case = {"id": "case-1", "title": "Test source packet", "hypothesis": "Original wording.",
            "evidence": [{"id": "e1", "title": "Source", "summary": "Observed evidence", "source": {"url": "https://example.org/source", "sha256": "b" * 64}}],
            "demo_decision": decision()}
    run = store.create(case, {"idempotency_key": uuid.uuid4().hex, "hypothesis": case["hypothesis"], "source_name": "test user", "mode": "live"})
    pin_legacy_manual_policy(store, run["id"])
    store.mutate(run["id"], lambda r: r.update(evidence=copy.deepcopy(case["evidence"])))
    return w.Worker(store), store, run["id"]


def model_metadata():
    return {"provider": "openai", "requested_model": providers.MODEL, "dispatched_requests": 2,
            "usage": {"input_tokens": 100, "output_tokens": 20},
            "requests": [{"request_id": "req-proof", "response_id": "resp-proof", "status": "completed", "returned_model": providers.MODEL}]}


def begin_modeling(worker, store, run_id):
    first = decision()
    first["metadata"] = model_metadata()
    worker.publish(run_id, first)
    store.mutate(run_id, lambda r: r.update(status="queued", operation={"kind": "modeling", "id": "modeling-action", "input": {
        "target_sequence": "AC", "reference_binder": "DE", "candidate_binder": "DF", "target_retained": True,
        "source_note": "Test reference accession and candidate design provenance."}}))


def test_partial_pair_blocks_without_accepted_prediction(running, monkeypatch):
    worker, store, run_id = running
    begin_modeling(worker, store, run_id)
    async def incomplete(target, reference, candidate, output_dir, **kwargs):
        output_dir.mkdir(parents=True)
        (output_dir / "partial.cif").write_text("partial artifact for integrity test")
        return {"status": "incomplete", "reason": "Candidate pending", "jobs": [
            {"status": "completed"}, {"status": "pending", "request_id": "pending-proof"}]}
    monkeypatch.setattr(providers, "compare_binders", incomplete)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "blocked"
    assert run["actions"][-1]["state"] == "unknown"
    assert len(run["evidence"]) == 1
    latest = run["decisions"][-1]
    assert latest["rd_handoff"]["modeling"]["status"] == "incomplete"
    assert len(latest["claims"]) == 1
    artifact = latest["rd_handoff"]["modeling"]["artifacts"][0]
    assert artifact["sha256"] == hashlib.sha256(b"partial artifact for integrity test").hexdigest()
    assert run["usage"]["model_calls"] == 2
    assert run["usage"]["input_tokens"] == 100
    # Partial artifacts must remain inspectable without being accepted as evidence.
    from fastapi.testclient import TestClient
    from app import main
    monkeypatch.setattr(main, "RUNTIME", w.RUNTIME)
    with TestClient(main.create_app(store, embedded=False)) as client:
        downloaded = client.get(artifact["url"])
    assert downloaded.status_code == 200
    assert downloaded.content == b"partial artifact for integrity test"


def test_complete_molecular_update_does_not_recount_rosalind(running, monkeypatch):
    worker, store, run_id = running
    begin_modeling(worker, store, run_id)
    async def complete(*args, **kwargs):
        return {"status": "completed", "jobs": [{"status": "completed"}, {"status": "completed"}], "artifacts": []}
    monkeypatch.setattr(providers, "compare_binders", complete)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "completed"
    assert len(run["evidence"]) == 2
    assert run["usage"]["model_calls"] == 2
    assert run["usage"]["output_tokens"] == 20
    assert "metadata" not in run["decisions"][-1]
    handoff = run["decisions"][-1]["rd_handoff"]
    assert handoff["candidates"][0]["sequence_sha256"] == hashlib.sha256(b"DF").hexdigest()
    assert handoff["reference"]["sequence_sha256"] == hashlib.sha256(b"DE").hexdigest()
    assert handoff["target"]["sequence_sha256"] == hashlib.sha256(b"AC").hexdigest()
    assert handoff["candidates"][0]["source_note"] == "Test reference accession and candidate design provenance."
    assert handoff["candidates"][0]["id"] != run["decisions"][0]["rd_handoff"]["candidates"][0]["id"]
    assert handoff["candidates"][0]["name"] == "Supplied candidate binding-domain construct"


def test_failed_model_metadata_and_usage_preserved_once(running, monkeypatch):
    worker, store, run_id = running
    async def fail(*args, **kwargs):
        raise providers.ProviderError("Validated output failed", metadata=model_metadata())
    monkeypatch.setattr(providers, "investigate", fail)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "failed"
    assert run["actions"][-1]["state"] == "failed"
    assert run["actions"][-1]["provider_metadata"]["requests"][0]["request_id"] == "req-proof"
    assert run["usage"]["model_calls"] == 2
    assert run["usage"]["input_tokens"] == 100
    # Reconciliation of the same receipt does not charge the model twice.
    worker.provider_failure(run_id, run["actions"][-1]["id"], providers.ProviderError("Again", metadata=model_metadata()))
    assert store.get(run_id)["usage"]["model_calls"] == 2


def test_cancellation_preserves_unknown_request_and_usage(running, monkeypatch):
    worker, store, run_id = running
    async def cancelled(*args, **kwargs):
        store.mutate(run_id, lambda r: r.update(cancel_requested=True))
        exc = asyncio.CancelledError()
        exc.metadata = model_metadata()
        exc.metadata["requests"].append({"status": "dispatched", "number": 3})
        exc.metadata["dispatched_requests"] = 3
        raise exc
    monkeypatch.setattr(providers, "investigate", cancelled)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "cancelled"
    assert run["actions"][-1]["state"] == "unknown"
    assert run["usage"]["model_calls"] == 3
    assert run["actions"][-1]["provider_metadata"]["requests"][-1]["status"] == "dispatched"


def test_new_revision_counts_only_new_model_receipt(running, monkeypatch):
    worker, store, run_id = running
    initial = decision()
    initial["metadata"] = model_metadata()
    worker.publish(run_id, initial)
    store.enqueue_revision(run_id, "feedback", {"decision_version": 1, "idempotency_key": uuid.uuid4().hex, "text": "Consider the contradictory source."})
    async def reassess(case, hypothesis, evidence, emit, cancelled, **kwargs):
        assert case["revision_context"]["scientist_input"]["text"] == "Consider the contradictory source."
        value = decision()
        value["metadata"] = {**model_metadata(), "dispatched_requests": 1, "usage": {"input_tokens": 25, "output_tokens": 5}}
        return value
    monkeypatch.setattr(providers, "investigate", reassess)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "completed"
    assert run["usage"]["model_calls"] == 3
    assert run["usage"]["input_tokens"] == 125
    assert run["hypothesis"]["text"] == "Original wording."


def test_demo_feedback_then_outcome_completes_three_versions(running):
    worker, store, run_id = running
    store.mutate(run_id, lambda r: r.update(mode="demo"))
    asyncio.run(worker.execute(run_id))
    first = store.get(run_id)
    assert first["status"] == "completed"
    first_hash = first["decisions"][0]["sha256"]
    store.enqueue_revision(run_id, "feedback", {"decision_version": 1, "idempotency_key": uuid.uuid4().hex,
                                                 "text": "Include a target-retention control."})
    asyncio.run(worker.execute(run_id))
    second = store.get(run_id)
    assert second["status"] == "completed"
    handoff = second["decisions"][-1]["rd_handoff"]
    store.enqueue_revision(run_id, "outcome", {"decision_version": 2, "idempotency_key": uuid.uuid4().hex,
                                                "experiment_id": handoff["experiment_id"], "candidate_id": handoff["candidates"][0]["id"],
                                                "endpoint": "Test readout", "value": 1.2, "unit": "arbitrary units",
                                                "notes": "Demonstration value only; not a real measurement."})
    asyncio.run(worker.execute(run_id))
    final = store.get(run_id)
    assert final["status"] == "completed"
    assert len(final["decisions"]) == 3
    assert final["decisions"][0]["sha256"] == first_hash
    assert "1.2 arbitrary units" in final["decisions"][-1]["changes"][0]
    assert final["hypothesis"]["text"] == "Original wording."
    assert final["usage"]["model_calls"] == 0


def test_custom_demo_hypothesis_does_not_inherit_original_design(running):
    worker, store, run_id = running
    supplied = "A different user-supplied hypothesis with a different experimental objective."
    def customize(run):
        run["mode"] = "demo"
        run["hypothesis"].update(text=supplied, sha256=hashlib.sha256(supplied.encode()).hexdigest())
    store.mutate(run_id, customize)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    final = run["decisions"][-1]
    assert run["status"] == "completed"
    assert final["assessment"] == "not_evaluable"
    assert final["rd_handoff"]["objective"] == supplied
    assert final["rd_handoff"]["status"] == "blocked"
    assert final["rd_handoff"]["candidates"] == []
    assert final["rd_handoff"]["modeling"]["status"] == "blocked"
    assert final["next_experiment"]["title"] != run["case_snapshot"]["demo_decision"]["next_experiment"]["title"]
    assert all(claim["kind"] == "case_context" for claim in final["claims"])


def test_cancel_wins_during_incomplete_modeling_publication(running, monkeypatch):
    worker, store, run_id = running
    begin_modeling(worker, store, run_id)
    async def incomplete(*args, **kwargs):
        return {"status": "incomplete", "reason": "Candidate pending", "jobs": [{"status": "pending"}]}
    monkeypatch.setattr(providers, "compare_binders", incomplete)
    original_mutate = store.mutate
    def cancellation_at_publication(identifier, operation):
        if operation.__name__ == "incomplete":
            original_mutate(identifier, lambda run: run.update(cancel_requested=True))
        return original_mutate(identifier, operation)
    monkeypatch.setattr(store, "mutate", cancellation_at_publication)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "cancelled"
    assert len(run["decisions"]) == 1
    assert run["actions"][-1]["state"] == "unknown"


def test_real_sdk_team_passes_durable_worker_handoff_and_skill_gates(running, monkeypatch):
    worker, store, run_id = running
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_MODEL", "gpt-6-astra")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch)
    asyncio.run(worker.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "completed", json.dumps({"events":run["events"][-6:], "actions":run["actions"][-1:]}, indent=2)
    assert len(run["handoffs"]) == 9
    active_roles = {product["sender"] for product in run["handoffs"] if product["model_called"]}
    assert {receipt["role"] for receipt in run["skill_receipts"] if receipt["skill_id"] == "discovery-planning"} == active_roles
    receipts = {x["id"]: x for x in run["skill_receipts"]}
    for product in run["handoffs"]:
        assert product["skill_receipt_ids"]
        assert all(receipts[sid]["role"] == product["sender"] for sid in product["skill_receipt_ids"])
    molecular = next(product for product in run["handoffs"] if product["sender"] == "molecular_scientist")
    bio = next(product for product in run["handoffs"] if product["sender"] == "bioinformatician")
    assert bio["id"] in molecular["input_versions"]["upstream_handoff_ids"]
    assert "molecular_scientist" in bio["recipient"]
    assert run["usage"]["model_calls"] == len(calls)
    assert run["decisions"][-1]["metadata"]["requested_model"] == "gpt-6-astra"
