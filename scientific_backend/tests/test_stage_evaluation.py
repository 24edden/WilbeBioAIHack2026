"""Failure-path checks of application gates; no vendor calls or biological grading."""
import asyncio
import copy
import hashlib
import json
import uuid

import pytest

from app import providers
from app.cases import get_case
from app.process_contract import get_process_contract
from app.stage_evaluation import evaluate_handoff, record_evaluation
from app.store import Store, digest
from app.worker import Worker


@pytest.fixture
def context(tmp_path):
    from governance_fixtures import pin_legacy_manual_policy
    store = Store(tmp_path / "evaluations.sqlite")
    case = get_case("cd19-car-t")
    run = store.create(case, {"hypothesis": case["hypothesis"], "source_name": "Test source", "mode": "live", "idempotency_key": uuid.uuid4().hex})
    pin_legacy_manual_policy(store, run["id"])
    run = store.mutate(run["id"], lambda r: r.update(evidence=copy.deepcopy(case["evidence"])))
    return store, run, case


def product_for(run, role="bioinformatician", *, upstream=None, status="completed"):
    packet = run["evidence"]
    routes = {r["id"]: r["recipients"] for r in run["process_contract"]["roles"]}
    routes.update(run["process_contract"]["additional_routes"])
    return {"sender": role, "case_id": run["case_id"], "recipient": routes[role],
            "question": "Which measurements support the hypothesis?", "method": "Review scoped source records.",
            "result_status": status, "result": "Source records require their stated scope limits.",
            "limitations": ["Reporter data cannot establish patient-level causality."],
            "decision_it_could_change": "Which discriminating measurement should be acquired next.",
            "claims": [{"text": "The supplied record is available for assessment.", "evidence_ids": [packet[0]["id"]], "kind": "observation"}],
            "input_versions": {"hypothesis_sha256": run["hypothesis"]["sha256"],
                               "evidence_sha256": hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
                               "evidence_ids": [e["id"] for e in packet], "evidence_versions": {e["id"]: e["source"]["sha256"] for e in packet},
                               "upstream_handoff_ids": upstream or []}}


def failed_checks(receipt):
    return {c["id"] for c in receipt["checks"] if not c["passed"]}


@pytest.mark.parametrize("role", ["statistician", "clinical_scientist", "clinical_pharmacologist", "translational_scientist", "assay_scientist", "coordinator", "reviewer"])
def test_downstream_stages_cannot_skip_required_work_products(context, role):
    _, run, _ = context
    evaluation = evaluate_handoff(product_for(run, role), run)
    assert evaluation["verdict"] == "rejected"
    assert "stage_dependencies" in failed_checks(evaluation)


def test_blocked_upstream_is_consumed_as_missing_information_not_scientific_success(context):
    _, run, _ = context
    run["handoffs"] = [{"id": "bio-blocked", "sender": "bioinformatician", "operation_id": run["operation"]["id"], "result_status": "blocked"}]
    product = product_for(run, "statistician", upstream=["bio-blocked"], status="blocked")
    product.update(result="The supplied tables lack independent unit mapping; estimates cannot be computed.", claims=[])
    evaluation = evaluate_handoff(product, run)
    assert evaluation["verdict"] == "accepted"
    assert evaluation["result_status"] == "blocked"
    assert evaluation["scientific_validity"] == "not_established_by_contract_checks"


@pytest.mark.parametrize("field,value,failed", [
    ("question", " ", "meaningful_content"), ("limitations", [], "meaningful_content"),
    ("result_status", "confident", "result_status"), ("claims", [{"text": "Unsupported claim", "evidence_ids": []}], "claim_citations"),
    ("input_versions", [], "hypothesis_version"), ("recipient", "statistician", "authorized_route"),
])
def test_malformed_work_products_are_rejected_without_a_boundary_crash(context, field, value, failed):
    _, run, _ = context
    product = product_for(run)
    product[field] = value
    evaluation = evaluate_handoff(product, run)
    assert evaluation["verdict"] == "rejected"
    assert failed in failed_checks(evaluation)


def test_rejected_attempt_receipts_survive_restart_and_enforce_one_repair(context, monkeypatch):
    store, initial, case = context
    calls = []
    async def investigate(*args, **callbacks):
        product = product_for(store.get(initial["id"]))
        product["question"] = ""
        for expected_repair in (True, False):
            response = await callbacks["accept_handoff"](product)
            assert response["accepted"] is False
            assert response["repair_allowed"] is expected_repair
            saved = Store(store.path).get(initial["id"])
            assert saved["stage_evaluations"][-1]["id"] == response["evaluation_id"]
        product["question"] = "Repaired, but the stage has exhausted its repair budget."
        response = await callbacks["accept_handoff"](product)
        assert response["accepted"] is False
        assert response["repair_allowed"] is False
        assert "attempt_budget" in failed_checks(store.get(initial["id"])["stage_evaluations"][-1])
        calls.append(True)
        return copy.deepcopy(case["demo_decision"])
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(Worker(store).execute(initial["id"]))
    run = Store(store.path).get(initial["id"])
    assert calls
    assert not run["handoffs"]
    assert [r["attempt"] for r in run["stage_evaluations"] if r["stage"].startswith("handoff:")] == [1, 2, 3]
    for receipt in run["stage_evaluations"]:
        assert receipt["sha256"] == digest({k: v for k, v in receipt.items() if k != "sha256"})
        assert receipt["process_contract_sha256"] == run["process_contract"]["sha256"]


def test_repair_accepts_once_and_new_operation_has_its_own_budget(context, monkeypatch):
    store, initial, case = context
    async def investigate(*args, **callbacks):
        run = store.get(initial["id"])
        product = product_for(run)
        product["method"] = ""
        assert (await callbacks["accept_handoff"](product))["repair_allowed"] is True
        product["method"] = "Source-scoped review with explicit source citations."
        accepted = await callbacks["accept_handoff"](product)
        assert accepted["accepted"] is True
        saved = Store(store.path).get(initial["id"])
        assert saved["handoffs"][-1]["acceptance_evaluation_id"] == accepted["evaluation_id"]
        assert (await callbacks["accept_handoff"](product))["accepted"] is False
        return copy.deepcopy(case["demo_decision"])
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(Worker(store).execute(initial["id"]))
    first = store.get(initial["id"])
    store.enqueue_revision(initial["id"], "feedback", {"decision_version": 1, "text": "Reconsider this source limitation.", "idempotency_key": "repair-revision"})
    asyncio.run(Worker(store).execute(initial["id"]))
    run = store.get(initial["id"])
    assert run["status"] == "completed"
    assert len(run["handoffs"]) == 2
    assert run["handoffs"][0] == first["handoffs"][0]
    assert run["handoffs"][0]["operation_id"] != run["handoffs"][1]["operation_id"]


def test_old_operation_handoff_cannot_satisfy_new_stage_dependencies(context):
    _, run, _ = context
    run["handoffs"] = [{"id": "old-bio", "sender": "bioinformatician", "operation_id": "old-operation", "result_status": "completed"}]
    evaluation = evaluate_handoff(product_for(run, "statistician", upstream=["old-bio"]), run)
    assert {"upstream_identity", "stage_dependencies"}.issubset(failed_checks(evaluation))


def test_provider_budget_failure_keeps_usage_and_budget_status(context, monkeypatch):
    store, run, _ = context
    async def exhausted(*args, **kwargs):
        error = providers.ProviderError("Token budget exhausted", status="budget_exhausted")
        error.metadata = {"dispatched_requests": 6, "usage": {"input_tokens": 163644, "output_tokens": 2500},
                          "requests": [{"request_id": "req-test", "status": "completed"}]}
        raise error
    monkeypatch.setattr(providers, "investigate", exhausted)
    asyncio.run(Worker(store).execute(run["id"]))
    saved = Store(store.path).get(run["id"])
    assert saved["status"] == "budget_exhausted"
    assert saved["usage"]["model_calls"] == 6
    assert saved["usage"]["input_tokens"] == 163644
    assert not saved["decisions"]
    receipt = saved["stage_evaluations"][-1]
    assert receipt["stage"] == "operation_stop"
    assert receipt["result_status"] == "budget_exhausted"
    assert saved["actions"][-1]["provider_metadata"]["requests"][0]["request_id"] == "req-test"


def test_process_contract_is_pinned_without_shared_mutable_role_lists():
    first = get_process_contract()
    first["roles"][0]["recipients"].append("unregistered")
    second = get_process_contract()
    assert "unregistered" not in second["roles"][0]["recipients"]
    assert second["sha256"] == digest({k: v for k, v in second.items() if k != "sha256"})


def proposal_for(run, *, evidence_id=None):
    """Build a real registered public-structure proposal without inference."""
    from app.discovery_planning import build_proposal
    from app.followups import approved_catalog

    return build_proposal(
        role="bioinformatician", case=run["case_snapshot"],
        hypothesis=run["hypothesis"]["text"], evidence=run["evidence"],
        recipes=approved_catalog(run["case_id"]), bionemo_status="configured",
        analysis_id="cd19-exon2-structure",
        scientific_question="Could the qualified isoform change the isolated ectodomain geometry?",
        rationale="Compare public isoform structures to identify a possible structural discriminator; this does not establish CAR recognition.",
        decision_it_could_change="Whether a structural hypothesis merits a separately controlled recognition experiment.",
        evidence_ids=[evidence_id or run["evidence"][0]["id"]],
    )


def test_registered_proposal_passes_handoff_with_exact_accepted_evidence_versions(context):
    _, run, _ = context
    product = product_for(run)
    proposed = proposal_for(run)
    assert proposed["status"] == "proposed"
    assert proposed["qualification"] == "unperformed"
    product["followup_proposals"] = [proposed]
    evaluation = evaluate_handoff(product, run)
    assert evaluation["verdict"] == "accepted"
    assert any(c["id"] == "followup_proposals" and c["passed"] for c in evaluation["checks"])
    cited = proposed["evidence_ids"][0]
    accepted = next(item for item in run["evidence"] if item["id"] == cited)
    assert proposed["input_versions"]["evidence_versions"] == {cited: accepted["source"]["sha256"]}
    from app.discovery_planning import EXECUTION
    assert proposed["execution"] == EXECUTION


@pytest.mark.parametrize("tamper", ["recipe", "recipe_hash", "source", "hypothesis", "role", "owner", "case"])
def test_tampered_proposal_is_returned_without_accepting_the_handoff(context, tamper):
    _, run, _ = context
    product = product_for(run)
    proposed = proposal_for(run)
    if tamper == "recipe":
        proposed["analysis_id"] = "unregistered-prediction"
    elif tamper == "recipe_hash":
        proposed["recipe_sha256"] = "0" * 64
    elif tamper == "source":
        proposed["input_versions"]["evidence_versions"][proposed["evidence_ids"][0]] = "0" * 64
    elif tamper == "hypothesis":
        proposed["input_versions"]["hypothesis_sha256"] = "0" * 64
    elif tamper == "role":
        proposed["proposing_role"] = "reviewer"
    elif tamper == "owner":
        proposed["owner"] = "clinical_scientist"
    else:
        proposed["case_id"] = "another-case"
    product["followup_proposals"] = [proposed]
    evaluation = evaluate_handoff(product, run)
    assert evaluation["verdict"] == "rejected"
    assert failed_checks(evaluation) == {"followup_proposals"}
    assert evaluation["repair_allowed"] is True


def test_proposal_cannot_cite_accepted_evidence_outside_its_declared_handoff_packet(context):
    _, run, _ = context
    assert len(run["evidence"]) > 1
    product = product_for(run)
    product["followup_proposals"] = [proposal_for(run, evidence_id=run["evidence"][-1]["id"])]
    packet = run["evidence"][:1]
    product["input_versions"].update(
        evidence_ids=[packet[0]["id"]],
        evidence_versions={packet[0]["id"]: packet[0]["source"]["sha256"]},
        evidence_sha256=hashlib.sha256(
            json.dumps(packet, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
    )
    evaluation = evaluate_handoff(product, run)
    assert evaluation["verdict"] == "rejected"
    assert failed_checks(evaluation) == {"followup_proposals"}
    assert evaluation["repair_allowed"] is True
