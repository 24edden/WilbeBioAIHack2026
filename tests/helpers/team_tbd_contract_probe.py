"""Offline subprocess fixture for the new frontend and the actual packaged API.

All cases, recipe availability, instruction identities and provider capabilities
below are synthetic test inputs. No worker executes and no vendor is contacted.
"""
import copy
import os
from pathlib import Path
import socket
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "scientific_backend"
assert (BACKEND / "app" / "main.py").is_file(), "Package the authoritative scientific backend before release"
assert not (BACKEND / ".env").exists(), "Private configuration must never be present in the source release"
assert os.environ.get("ROSALIND_RUNTIME"), "The contract test requires an isolated runtime"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))


def no_network(*args, **kwargs):
    raise AssertionError("Scientific API contract tests must not contact any network service")


socket.socket.connect = no_network

from fastapi.testclient import TestClient
from app import analysis_tools, brief_operations, cases, followups, main, providers, scientific_skills, sequence_operations
from app.store import Store, digest
from frontend.ui.team_tbd_client import APIError, TeamTBDClient, available_controls

assert Path(main.__file__).resolve().is_relative_to(BACKEND), "Do not substitute the legacy application"

ORIGIN = "http://127.0.0.1:9876"
CASE = {"id": "synthetic-case", "title": "Offline integration fixture", "hypothesis": "Exact original hypothesis.\n",
        "source_manifest": [{"path": "synthetic.tsv", "sha256": "a" * 64}], "evidence": []}
RECIPE = {"id": "synthetic-analysis", "title": "Offline comparison", "kind": "data_analysis", "input_sources": CASE["source_manifest"]}
CAPABILITIES = {"rosalind": {"status": "verified", "model": "gpt-6-astra"}, "bionemo": {"status": "configured", "model": "mit/boltz2"}}
cases.get_case = lambda case_id: copy.deepcopy(CASE) if case_id == CASE["id"] else (_ for _ in ()).throw(KeyError(case_id))
cases.list_cases = lambda: [copy.deepcopy(CASE)]
analysis_tools.analysis_catalog = lambda _: [copy.deepcopy(RECIPE)]
followups.approved_catalog = lambda _: [copy.deepcopy(RECIPE)]
providers.capabilities = lambda: copy.deepcopy(CAPABILITIES)
providers.investigate = no_network
brief_operations.instruction_identity = lambda: {"offline-fixture": "a" * 64}
sequence_operations.instruction_identity = lambda: {"offline-fixture": "a" * 64}
scientific_skills.skill_catalog = lambda: [{"id": "synthetic-skill", "name": "Offline fixture", "roles": ["reviewer"]}]
scientific_skills.verify_life_sciences_runtime = lambda: None
store = Store(Path(os.environ["ROSALIND_RUNTIME"]) / "contract.sqlite")
application = main.create_app(store=store, embedded=False)


def rejected(call, status=409):
    try:
        call()
    except APIError as exc:
        assert exc.status_code == status, exc
    else:
        raise AssertionError("The scientific API must reject this request")


def payload():
    return {"case_id": CASE["id"], "hypothesis": "  My original exact question, including whitespace.\n", "source_name": "Scientist's note.md\n",
            "mode": "live", "idempotency_key": uuid.uuid4().hex}


def decision():
    record = {"version": 1, "summary": "Synthetic saved decision; no scientific inference.", "followups": [],
              "rd_handoff": {"experiment_id": "experiment-1", "candidates": [{"id": "arm-1", "status": "planned"}]}}
    record["sha256"] = digest(record)
    return record


with TestClient(application, base_url=ORIGIN) as transport:
    client = TeamTBDClient(ORIGIN, transport)
    assert client.health()["worker_alive"] is False
    assert client.health()["capabilities"]["rosalind"]["model"] == "gpt-6-astra"
    assert client.cases()[0]["id"] == CASE["id"]
    assert client.case(CASE["id"])["hypothesis"] == CASE["hypothesis"]
    contract = client.process_contract()
    assert len(contract["roles"]) == 7
    assert set(contract["additional_routes"]) == {"coordinator", "reviewer"}
    assert client.skills()["skills"][0]["id"] == "synthetic-skill"

    request = payload()
    first = client.create_run(request)
    assert first["hypothesis"] == {"text": request["hypothesis"], "source_name": request["source_name"], "sha256": digest(request["hypothesis"])}
    assert client.create_run(request)["id"] == first["id"]
    rejected(lambda: client.create_run({**request, "hypothesis": "A different request with the same key."}))
    assert len(client.list_runs()) == 1
    assert client.load(first["id"])["run"]["hypothesis"] == first["hypothesis"]
    assert client.events(first["id"])[0]["title"] == "Hypothesis preserved"
    assert client.events(first["id"], after=1) == []
    assert client.cancel(first["id"])["status"] == "cancelled"
    assert client.resume(first["id"])["status"] == "queued"
    client.cancel(first["id"])
    cross_origin = transport.post("/api/runs", json=payload(), headers={"Origin": "http://evil.example"})
    assert cross_origin.status_code == 403
    invalid = transport.post("/api/runs", json={**payload(), "model": "arbitrary-override"})
    assert invalid.status_code == 422
    CAPABILITIES["rosalind"]["status"] = "configured"
    rejected(lambda: client.create_run(payload()))
    CAPABILITIES["rosalind"]["status"] = "verified"

    def completed():
        run = client.create_run(payload())
        store.mutate(run["id"], lambda r: r.update(status="completed", decisions=[decision()]))
        return client.get_run(run["id"])

    run = completed()
    original = copy.deepcopy(run["decisions"])
    correction = {"decision_version": 1, "text": "An original correction.\n", "idempotency_key": "correction-1"}
    rejected(lambda: client.feedback(run["id"], {**correction, "decision_version": 2}))
    queued = client.feedback(run["id"], correction)
    assert queued["operation"]["kind"] == "feedback" and queued["hypothesis"] == run["hypothesis"]
    assert queued["decisions"] == original
    assert len(client.feedback(run["id"], correction)["feedback"]) == 1
    rejected(lambda: client.feedback(run["id"], {**correction, "idempotency_key": "different-intent"}))

    run = completed()
    outcome = {"decision_version": 1, "experiment_id": "experiment-1", "candidate_id": "arm-1", "endpoint": "Offline endpoint",
               "value": 2.0, "unit": "units", "notes": "Synthetic test return, not a biological measurement.", "idempotency_key": "outcome-1"}
    rejected(lambda: client.outcome(run["id"], {**outcome, "candidate_id": "foreign-arm"}))
    queued = client.outcome(run["id"], outcome)
    assert queued["operation"]["kind"] == "outcome" and queued["decisions"] == run["decisions"]
    assert len(client.outcome(run["id"], outcome)["outcomes"]) == 1

    run = completed()
    modeling = {"decision_version": 1, "target_sequence": "ACDEFGHIKLMNPQRST", "reference_binder": "AAAAAAAAAAAAAAA",
                "candidate_binder": "CCCCCCCCCCCCCCC", "target_retained": True, "source_note": "Synthetic sequences for routing tests only.", "idempotency_key": "modeling-1"}
    rejected(lambda: client.modeling(run["id"], {**modeling, "candidate_binder": modeling["reference_binder"]}), 422)
    rejected(lambda: client.modeling(run["id"], {**modeling, "target_retained": False}), 422)
    queued = client.modeling(run["id"], modeling)
    assert queued["operation"]["kind"] == "modeling" and queued["decisions"] == run["decisions"]
    assert client.modeling(run["id"], modeling)["operation"]["id"] == queued["operation"]["id"]

    for method, kind, field in (("research_brief", "research_brief", "research_brief_operations"),
                                ("sequence_discovery", "sequence_discovery", "sequence_discovery_operations")):
        run = completed()
        call = getattr(client, method)
        request = {"decision_version": 1, "idempotency_key": "one-" + method}
        rejected(lambda: call(run["id"], {**request, "decision_version": 2}))
        queued = call(run["id"], request)
        assert queued["operation"]["kind"] == kind and queued["decisions"] == run["decisions"]
        assert len(call(run["id"], request)[field]) == 1

    run = completed()
    selection = client.followups(run["id"])
    item = selection["followups"][0]
    assert item["executable"] is True
    request = {"decision_version": selection["decision_version"], "recommendation_id": item["id"], "idempotency_key": "one-followup"}
    rejected(lambda: client.followup(run["id"], {**request, "recommendation_id": "invented"}))
    queued = client.followup(run["id"], request)
    assert queued["operation"]["kind"] == "followup"
    assert len(client.followup(run["id"], request)["followup_operations"]) == 1
    assert client.followups(run["id"])["followups"][0]["executable"] is False

    run = completed()
    checkpoint = client.synthesis_checkpoint(run["id"])
    assert checkpoint["eligible"] is False
    assert available_controls(run, client.health(), checkpoint)["continue_synthesis"]
    rejected(lambda: client.continue_synthesis(run["id"], {"source_operation_id": run["operation"]["id"], "idempotency_key": "invalid-recovery"}))
    store.mutate(run["id"], lambda r: r.update(status="blocked", actions=[{"id": "external", "state": "unknown"}]))
    rejected(lambda: client.resume(run["id"]))
    rejected(lambda: client.research_brief(run["id"], {"decision_version": 1, "idempotency_key": "unknown-brief"}))
    rejected(lambda: client.sequence_discovery(run["id"], {"decision_version": 1, "idempotency_key": "unknown-sequence"}))
    assert all(record["usage"]["model_calls"] == 0 for record in store.list())
    assert not any(record["actions"] for record in store.list() if record["id"] != run["id"])

print("isolated scientific API contracts passed; zero provider calls")
