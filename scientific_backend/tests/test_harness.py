"""API/workflow boundaries, with isolated SQLite and no external inference calls."""
import asyncio
import copy
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app import main as api, providers, worker as workflow
from app.cases import get_case
from app.store import Conflict, Store, digest


@pytest.fixture
def harness(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "DEMO_DELAY", 0)
    store = Store(tmp_path / "harness.sqlite")
    application = api.create_app(store=store, embedded=False)
    with TestClient(application) as client:
        yield client, store, application.state.worker


def payload(**updates):
    value = {"case_id": "cd19-car-t", "hypothesis": get_case("cd19-car-t")["hypothesis"],
             "source_name": "Selected original Brev hypothesis", "mode": "demo", "idempotency_key": uuid.uuid4().hex}
    value.update(updates)
    return value


def create(harness, **updates):
    client, store, worker = harness
    response = client.post("/api/runs", json=payload(**updates))
    assert response.status_code == 202, response.text
    return response.json()


def complete(harness, **updates):
    client, store, worker = harness
    run = create(harness, **updates)
    asyncio.run(worker.execute(run["id"]))
    result = store.get(run["id"])
    assert result["status"] == "completed", result.get("error")
    return result


def outcome_for(run, **updates):
    handoff = run["decisions"][-1]["rd_handoff"]
    value = {"decision_version": run["decisions"][-1]["version"], "experiment_id": handoff["experiment_id"],
             "candidate_id": handoff["candidates"][0]["id"], "endpoint": "Surface CD19 positive tumor cells",
             "value": 30.0, "unit": "%", "notes": "Software test input only; assay controls and biological replication not yet verified.",
             "idempotency_key": uuid.uuid4().hex}
    value.update(updates)
    return value


def test_create_retry_is_idempotent_and_changed_payload_conflicts(harness):
    client, store, _ = harness
    request = payload()
    first = client.post("/api/runs", json=request)
    second = client.post("/api/runs", json=request)
    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert len(store.list()) == 1
    altered = client.post("/api/runs", json={**request, "hypothesis": "A meaningfully changed research question."})
    assert altered.status_code == 409


def test_idempotent_create_retry_survives_full_queue(harness):
    client, store, _ = harness
    request = payload()
    first = client.post("/api/runs", json=request)
    for _ in range(9):
        create(harness)
    retry = client.post("/api/runs", json=request)
    assert retry.status_code == 202, "An exact retry must resolve before queue admission checks"
    assert retry.json()["id"] == first.json()["id"]
    assert len(store.list()) == 10
    assert client.post("/api/runs", json=payload()).status_code == 429


def test_idempotent_live_create_retry_survives_capability_change(harness, monkeypatch):
    client, store, _ = harness
    monkeypatch.setattr(providers, "capabilities", lambda: {"rosalind": {"status": "verified"}})
    request = payload(mode="live")
    first = client.post("/api/runs", json=request)
    assert first.status_code == 202
    monkeypatch.setattr(providers, "capabilities", lambda: {"rosalind": {"status": "unconfigured"}})
    retry = client.post("/api/runs", json=request)
    assert retry.status_code == 202, "An accepted run retry is not a new model dispatch"
    assert retry.json()["id"] == first.json()["id"]


def test_custom_hypothesis_is_preserved_and_not_adjudicated_by_fixture(harness):
    custom = "Test whether this new independent objective is consistent with the supplied evidence.\nKeep my wording exactly.\n"
    run = complete(harness, hypothesis=custom, source_name="scientist.md")
    assert run["hypothesis"] == {"text": custom, "source_name": "scientist.md", "sha256": digest(custom)}
    assert run["decisions"][-1]["assessment"] == "not_evaluable"
    assert "edited hypothesis" in run["decisions"][-1]["summary"]
    assert run["usage"]["model_calls"] == 0


def test_feedback_versions_immutable_stale_input_rejected_exact_retry_accepted(harness):
    client, store, worker = harness
    run = complete(harness)
    original = copy.deepcopy(run["decisions"][0])
    correction = {"decision_version": 1, "text": "The source has no patient surface-protein measurement.", "idempotency_key": "correction-1"}
    assert client.post(f"/api/runs/{run['id']}/feedback", json=correction).status_code == 202
    asyncio.run(worker.execute(run["id"]))
    revised = store.get(run["id"])
    assert revised["decisions"][0] == original
    assert [d["version"] for d in revised["decisions"]] == [1, 2]
    assert revised["hypothesis"] == run["hypothesis"]
    assert revised["decisions"][-1]["changes"]
    stale = client.post(f"/api/runs/{run['id']}/feedback", json={**correction, "idempotency_key": "stale-new-key"})
    assert stale.status_code == 409
    repeated = client.post(f"/api/runs/{run['id']}/feedback", json=correction)
    assert repeated.status_code == 202
    assert len(store.get(run["id"])["feedback"]) == 1
    assert store.get(run["id"])["status"] == "completed"


def test_planned_arm_accepts_result_without_claiming_modeling_or_verified_measurement(harness):
    client, store, worker = harness
    run = complete(harness)
    original = copy.deepcopy(run["decisions"][0])
    arm = original["rd_handoff"]["candidates"][0]
    assert arm["type"] == "experimental_arm" and arm["status"] == "planned"
    request = outcome_for(run)
    accepted = client.post(f"/api/runs/{run['id']}/outcomes", json=request)
    assert accepted.status_code == 202, accepted.text
    asyncio.run(worker.execute(run["id"]))
    revised = store.get(run["id"])
    assert revised["decisions"][0] == original
    assert len(revised["decisions"]) == 2
    assert revised["decisions"][-1]["rd_handoff"]["modeling"]["status"] == "blocked"
    assert revised["decisions"][-1]["assessment"] == "unresolved"
    assert revised["evidence"][-1]["kind"] == "user_report"
    assert "verification pending" in revised["evidence"][-1]["values"]["qc"]
    assert revised["usage"]["model_calls"] == 0
    repeated = client.post(f"/api/runs/{run['id']}/outcomes", json=request)
    assert repeated.status_code == 202
    assert len(store.get(run["id"])["outcomes"]) == 1


@pytest.mark.parametrize("field,value", [("candidate_id", "not-in-handoff"), ("experiment_id", "different-experiment"), ("decision_version", 2)])
def test_outcome_must_resolve_current_experiment_and_arm(harness, field, value):
    client, store, _ = harness
    run = complete(harness)
    response = client.post(f"/api/runs/{run['id']}/outcomes", json=outcome_for(run, **{field: value}))
    assert response.status_code == 409
    assert store.get(run["id"])["outcomes"] == []


@pytest.mark.parametrize("field,value", [("endpoint", "   "), ("unit", "   "), ("notes", "   "), ("value", True)])
def test_malformed_outcome_fields_are_rejected(harness, field, value):
    client, store, _ = harness
    run = complete(harness)
    response = client.post(f"/api/runs/{run['id']}/outcomes", json=outcome_for(run, **{field: value}))
    assert response.status_code == 422
    assert store.get(run["id"])["outcomes"] == []


def test_nonfinite_outcome_is_rejected(harness):
    client, store, _ = harness
    run = complete(harness)
    raw = json.dumps(outcome_for(run, value=float("nan")))
    response = client.post(f"/api/runs/{run['id']}/outcomes", content=raw, headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert not store.get(run["id"])["outcomes"]


def test_sequence_qualification_counts_normalized_residues(harness):
    client, store, _ = harness
    run = complete(harness)
    request = {"decision_version": 1, "target_sequence": "A" + " " * 14,
               "reference_binder": "ACDEFGHIKLMNPQR", "candidate_binder": "ACDEFGHIKLMNPQS",
               "target_retained": True, "source_note": "Test-only qualified source description", "idempotency_key": "bad-sequence"}
    response = client.post(f"/api/runs/{run['id']}/modeling", json=request)
    assert response.status_code == 422, "Whitespace must not satisfy sequence length requirements"


def test_queued_cancellation_prevents_work_then_resume_completes_once(harness):
    client, store, worker = harness
    run = create(harness)
    stopped = client.post(f"/api/runs/{run['id']}/cancel")
    assert stopped.json()["status"] == "cancelled"
    asyncio.run(worker.execute(run["id"]))
    assert not store.get(run["id"])["decisions"]
    assert client.post(f"/api/runs/{run['id']}/resume").status_code == 200
    asyncio.run(worker.execute(run["id"]))
    finished = store.get(run["id"])
    assert finished["status"] == "completed"
    assert len(finished["decisions"]) == 1


def test_publication_checks_cancellation_inside_transaction(harness):
    client, store, worker = harness
    run = create(harness)
    case = get_case("cd19-car-t")
    store.mutate(run["id"], lambda r: r.update(evidence=copy.deepcopy(case["evidence"]), cancel_requested=True))
    with pytest.raises(workflow.Cancelled):
        worker.publish(run["id"], case["demo_decision"])
    assert not store.get(run["id"])["decisions"]


def test_cancellation_after_provider_success_reuses_receipt_on_resume(harness, monkeypatch):
    from governance_fixtures import pin_legacy_manual_policy
    client, store, worker = harness
    case = get_case("cd19-car-t")
    run = store.create(case, payload(mode="live"))
    pin_legacy_manual_policy(store, run["id"])
    calls = []
    async def complete_and_cancel(*args, **kwargs):
        calls.append("dispatched")
        store.mutate(run["id"], lambda r: r.update(cancel_requested=True))
        return copy.deepcopy(case["demo_decision"])
    monkeypatch.setattr(providers, "investigate", complete_and_cancel)
    asyncio.run(worker.execute(run["id"]))
    stopped = store.get(run["id"])
    assert stopped["status"] == "cancelled"
    assert stopped["actions"][0]["state"] == "succeeded"
    assert not stopped["decisions"]
    assert client.post(f"/api/runs/{run['id']}/resume").status_code == 200
    asyncio.run(worker.execute(run["id"]))
    assert calls == ["dispatched"]
    assert len(store.get(run["id"])["decisions"]) == 1


def test_restart_with_unknown_external_action_blocks_resume_and_resubmit(harness):
    client, store, worker = harness
    run = create(harness)
    store.mutate(run["id"], lambda r: r.update(status="running"))
    action = run["operation"]["id"] + "-rosalind"
    store.begin_action(run["id"], action, "gpt-rosalind-investigation", {"input": "pinned"})
    restarted = Store(store.path)
    restarted.recover()
    recovered = restarted.get(run["id"])
    assert recovered["status"] == "blocked"
    assert recovered["actions"][0]["state"] == "unknown"
    assert client.post(f"/api/runs/{run['id']}/resume").status_code == 409
    with pytest.raises(Conflict):
        restarted.begin_action(run["id"], action, "gpt-rosalind-investigation", {"input": "pinned"})


def test_restart_without_external_submission_pauses_and_can_resume(harness):
    client, store, worker = harness
    run = create(harness)
    store.mutate(run["id"], lambda r: r.update(status="running"))
    Store(store.path).recover()
    assert store.get(run["id"])["status"] == "paused"
    assert client.post(f"/api/runs/{run['id']}/resume").status_code == 200
    asyncio.run(worker.execute(run["id"]))
    assert store.get(run["id"])["status"] == "completed"


def test_export_matches_visible_run_and_content_hash(harness):
    client, store, _ = harness
    run = complete(harness)
    visible = client.get(f"/api/runs/{run['id']}").json()
    export = client.get(f"/api/runs/{run['id']}/export.json").json()
    assert export["run"] == visible
    assert export["case_manifest"] == run["case_snapshot"]
    assert export["content_sha256"] == digest({"run": export["run"], "case_manifest": export["case_manifest"]})
    report = client.get(f"/api/runs/{run['id']}/report.md").text
    assert run["hypothesis"]["text"] in report
    assert run["decisions"][-1]["summary"] in report
    # A portable report must preserve the competing scientific interpretations,
    # including published support that is absent from the headline summary.
    assert "### Competing explanations" in report
    for decision in run["decisions"]:
        for alternative in decision["alternatives"]:
            assert alternative["title"] in report
            assert alternative["reason"] in report
    assert all(e["source"]["sha256"] in report for e in run["evidence"])


def test_cross_origin_write_and_case_path_rejected(harness):
    client, store, _ = harness
    response = client.post("/api/runs", json=payload(), headers={"origin": "https://unrelated.example"})
    assert response.status_code == 403
    assert not store.list()
    assert client.post("/api/runs", json=payload(case_id="../../sensitive-file")).status_code == 404
