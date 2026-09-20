"""Durable scientific work products; vendor orchestration is explicitly mocked."""
import asyncio
import copy
import hashlib
import json
import uuid

import pytest

from app import analysis_tools, providers, worker as workflow
from app.cases import get_case
from app.store import Conflict, Store, digest


@pytest.fixture
def live_context(tmp_path, monkeypatch):
    from governance_fixtures import pin_legacy_manual_policy
    monkeypatch.setattr(workflow, "DEMO_DELAY", 0)
    monkeypatch.setattr(workflow, "RUNTIME", tmp_path / "runtime")
    store = Store(tmp_path / "work-products.sqlite")
    case = get_case("cd19-car-t")
    payload = {"case_id": case["id"], "hypothesis": case["hypothesis"], "source_name": "Pinned Brev hypothesis",
               "mode": "live", "idempotency_key": uuid.uuid4().hex}
    run = store.create(case, payload)
    pin_legacy_manual_policy(store, run["id"])
    return workflow.Worker(store), store, run["id"], case


def canonical_result_hash(values):
    raw = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def work_product(run, *, evidence_ids=None):
    evidence = run["evidence"]
    ids = evidence_ids or [e["id"] for e in evidence]
    packet = [next(e for e in evidence if e["id"] == eid) for eid in ids]
    return {"sender": "bioinformatician", "recipient": ["statistician"], "case_id": run["case_id"],
            "question": "Which source identity exclusions affect the next analysis?",
            "method": "Read the pinned source table and report exact barcode exclusions.",
            "result_status": "completed", "result": "Runtime source QC is available for review.",
            "limitations": ["Reporter-library observations do not adjudicate an individual patient's failure."],
            "decision_it_could_change": "Whether variant-level attribution can include unmatched barcodes.",
            "claims": [{"text": "The joined and unmatched barcode counts are source-derived.", "evidence_ids": ["ANALYSIS-CD19-QC"], "kind": "observation"}],
            "input_versions": {"hypothesis_sha256": run["hypothesis"]["sha256"],
                               "evidence_sha256": hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
                               "evidence_ids": ids, "evidence_versions": {e["id"]: e["source"]["sha256"] for e in packet},
                               "upstream_handoff_ids": []}}


def final_decision(case, extra_id=None):
    value = copy.deepcopy(case["demo_decision"])
    if extra_id:
        value["claims"].append({"text": "Runtime barcode qualification identified explicit unmatched identities.", "evidence_ids": [extra_id], "kind": "observation"})
    return value


def test_derived_evidence_and_work_product_are_durable_before_callback_returns(live_context, monkeypatch):
    worker, store, run_id, case = live_context
    output = analysis_tools.analyze_case(case["id"], "cd19-barcode-qc")
    observed = []
    async def investigate(*args, **callbacks):
        assert "demo_decision" not in args[0]
        assert args[1] == case["hypothesis"]
        await callbacks["accept_evidence"](output)
        saved = Store(store.path).get(run_id)
        accepted = next(e for e in saved["evidence"] if e["id"] == output["id"])
        assert accepted == output
        assert accepted["source"]["sha256"] == canonical_result_hash(accepted["values"])
        raw_hashes = {e["source"]["sha256"] for e in case["evidence"]}
        assert all(s["sha256"] in raw_hashes for s in accepted["values"]["input_sources"])
        receipt = await callbacks["accept_handoff"](work_product(saved))
        assert receipt["accepted"] is True
        durable = Store(store.path).get(run_id)["handoffs"][-1]
        assert durable["id"] == receipt["id"]
        assert durable["case_id"] == case["id"]
        assert durable["operation_id"] == saved["operation"]["id"]
        observed.append(durable)
        return final_decision(case, output["id"])
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "completed", result.get("error")
    assert len(observed) == 1
    assert any(output["id"] in c["evidence_ids"] for c in result["decisions"][-1]["claims"])


def test_same_derived_evidence_is_idempotent_but_changed_version_rejected(live_context, monkeypatch):
    worker, store, run_id, case = live_context
    output = analysis_tools.analyze_case(case["id"], "cd19-barcode-qc")
    async def investigate(*args, **callbacks):
        await callbacks["accept_evidence"](output)
        await callbacks["accept_evidence"](copy.deepcopy(output))
        altered = copy.deepcopy(output)
        altered["values"]["joined_barcodes"] = 1
        altered["source"]["sha256"] = canonical_result_hash(altered["values"])
        with pytest.raises((ValueError, Conflict)):
            await callbacks["accept_evidence"](altered)
        return final_decision(case, output["id"])
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "completed", result.get("error")
    assert sum(e["id"] == output["id"] for e in result["evidence"]) == 1


@pytest.mark.parametrize("tamper", ["derived_hash", "input_source_hash", "case_identity", "analysis_identity"])
def test_derived_evidence_must_match_recipe_case_and_pinned_source_versions(live_context, monkeypatch, tamper):
    worker, store, run_id, case = live_context
    output = analysis_tools.analyze_case(case["id"], "cd19-barcode-qc")
    if tamper == "derived_hash":
        output["source"]["sha256"] = "0" * 64
    elif tamper == "input_source_hash":
        output["values"]["input_sources"][0]["sha256"] = "0" * 64
    elif tamper == "case_identity":
        output["values"]["case_id"] = "bcma-gse164551"
    else:
        output["values"]["analysis_id"] = "alk-assay-extraction"
    if tamper != "derived_hash":
        output["source"]["sha256"] = canonical_result_hash(output["values"])
    async def investigate(*args, **callbacks):
        with pytest.raises((ValueError, Conflict)):
            await callbacks["accept_evidence"](output)
        assert output["id"] not in {e["id"] for e in store.get(run_id)["evidence"]}
        return final_decision(case)
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "completed", result.get("error")


@pytest.mark.parametrize("tamper", ["case_identity", "unknown_citation", "empty_citation", "hypothesis_version", "source_version", "unauthorized_route"])
def test_work_product_rejects_wrong_identity_version_citation_or_route(live_context, monkeypatch, tamper):
    worker, store, run_id, case = live_context
    output = analysis_tools.analyze_case(case["id"], "cd19-barcode-qc")
    async def investigate(*args, **callbacks):
        await callbacks["accept_evidence"](output)
        product = work_product(store.get(run_id))
        if tamper == "case_identity":
            product["case_id"] = "bcma-gse164551"
        elif tamper == "unknown_citation":
            product["claims"][0]["evidence_ids"] = ["NOT-ACCEPTED"]
        elif tamper == "empty_citation":
            product["claims"][0]["evidence_ids"] = []
        elif tamper == "hypothesis_version":
            product["input_versions"]["hypothesis_sha256"] = "0" * 64
        elif tamper == "source_version":
            product["input_versions"]["evidence_versions"][output["id"]] = "0" * 64
        else:
            product["recipient"] = ["external_unregistered_agent"]
        receipt = await callbacks["accept_handoff"](product)
        assert receipt["accepted"] is False
        assert store.get(run_id)["handoffs"] == []
        return final_decision(case)
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "completed", result.get("error")


def test_missing_molecular_inputs_blocks_without_vendor_dispatch(live_context, monkeypatch):
    worker, store, run_id, case = live_context
    dispatches = []
    async def forbidden(*args, **kwargs):
        dispatches.append(True)
        raise AssertionError("Unqualified inputs must not dispatch a NIM call")
    monkeypatch.setattr(providers, "compare_binders", forbidden)
    async def investigate(*args, **callbacks):
        receipt = await callbacks["request_molecular"]({"rationale": "Check whether target-retained comparison is qualified."})
        assert receipt["status"] == "blocked"
        assert "not been supplied" in receipt["reason"]
        assert all(a["kind"] != "agent-directed-bionemo-comparison" for a in store.get(run_id)["actions"])
        return final_decision(case)
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "completed", result.get("error")
    assert not dispatches
    assert result["decisions"][-1]["rd_handoff"]["modeling"]["status"] == "blocked"
    assert not any(e["kind"] == "prediction" for e in result["evidence"])


def test_unresolved_agent_molecular_job_cannot_be_reported_as_completed_run(live_context, monkeypatch):
    worker, store, run_id, case = live_context
    inputs = {"target_sequence": "ACDEFGHIKLMNPQRSTVWY", "reference_binder": "ACDEFGHIKLMNPQRSTVWY", "candidate_binder": "ACDEFGHIKLMNPQRSTVWA", "target_retained": True, "source_note": "Explicitly synthetic unit-test inputs only."}
    store.mutate(run_id, lambda r: r["case_snapshot"].update(molecular_inputs=inputs))
    monkeypatch.setattr(providers, "capabilities", lambda: {"bionemo": {"status": "configured"}})
    async def incomplete(*args, **kwargs):
        return {"status": "incomplete", "reason": "Candidate job outcome unknown", "jobs": [{"status": "completed"}, {"status": "unknown"}]}
    monkeypatch.setattr(providers, "compare_binders", incomplete)
    async def investigate(*args, **callbacks):
        response = await callbacks["request_molecular"]({"rationale": "Test pending-work visibility."})
        assert response["status"] == "incomplete"
        return final_decision(case)
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    result = store.get(run_id)
    assert any(a["state"] == "unknown" for a in result["actions"])
    assert result["status"] == "blocked"
    assert not any(e["kind"] == "prediction" for e in result["evidence"])


def test_stale_agent_modeling_does_not_overwrite_newer_decision_handoff(live_context):
    worker, store, run_id, case = live_context
    def prepare(run):
        run["evidence"] = copy.deepcopy(case["evidence"])
        run["agent_modeling"] = {"status": "completed", "reason": "Old comparison", "artifacts": [], "action_id": "older-operation-agent-boltz"}
        run["operation"] = {"kind": "feedback", "id": "new-feedback-operation"}
    store.mutate(run_id, prepare)
    value = final_decision(case)
    value["rd_handoff"]["modeling"] = {"status": "completed", "reason": "Latest manual comparison", "artifacts": [], "action_id": "newer-manual-operation-boltz"}
    worker.publish(run_id, value)
    latest = store.get(run_id)["decisions"][-1]["rd_handoff"]["modeling"]
    assert latest["action_id"] == "newer-manual-operation-boltz"


def test_l1_l2_l3_keep_original_hypothesis_and_immutable_decisions(live_context, monkeypatch):
    worker, store, run_id, case = live_context
    original_hypothesis = copy.deepcopy(store.get(run_id)["hypothesis"])
    output = analysis_tools.analyze_case(case["id"], "cd19-barcode-qc")
    seen_contexts = []
    async def investigate(context, hypothesis, evidence, *args, **callbacks):
        assert hypothesis == original_hypothesis["text"]
        await callbacks["accept_evidence"](output)
        receipt = await callbacks["accept_handoff"](work_product(store.get(run_id)))
        assert receipt["accepted"] is True
        seen_contexts.append(copy.deepcopy(context.get("revision_context")))
        return final_decision(case, output["id"])
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    first = copy.deepcopy(store.get(run_id)["decisions"][0])
    store.enqueue_revision(run_id, "feedback", {"decision_version": 1, "text": "Retain the missing surface-protein measurement as a limitation.", "idempotency_key": "l2-feedback"})
    asyncio.run(worker.execute(run_id))
    second = copy.deepcopy(store.get(run_id)["decisions"][1])
    handoff = second["rd_handoff"]
    store.enqueue_revision(run_id, "outcome", {"decision_version": 2, "experiment_id": handoff["experiment_id"], "candidate_id": handoff["candidates"][0]["id"], "endpoint": "Surface recognition", "value": 30.0, "unit": "%", "notes": "Synthetic software test submission; verification pending.", "idempotency_key": "l3-outcome"})
    asyncio.run(worker.execute(run_id))
    final = Store(store.path).get(run_id)
    assert final["status"] == "completed", final.get("error")
    assert final["hypothesis"] == original_hypothesis
    assert final["decisions"][0] == first and final["decisions"][1] == second
    assert [d["version"] for d in final["decisions"]] == [1, 2, 3]
    assert seen_contexts[0] is None
    assert seen_contexts[1]["previous_decision"]["version"] == 1
    assert seen_contexts[2]["previous_decision"]["version"] == 2
    assert sum(e["id"] == output["id"] for e in final["evidence"]) == 1
    assert len(final["handoffs"]) == 3
    returned = [e for e in final["evidence"] if e["kind"] == "user_report"]
    assert len(returned) == 2
    assert all("verification pending" in e["values"]["qc"] for e in returned)
