"""Offline checkpoint recovery: trusted reuse, distinct actions, no vendor calls."""
import asyncio
import copy
import hashlib
import json
import uuid

import pytest

from app import cases, process_contract, providers, scientific_skills, synthesis_checkpoint as sc, worker
from app.stage_evaluation import evaluate_handoff, record_evaluation
from app.store import Conflict, Store, digest, now
from test_hypothesis_continuation import governed_decision


def create_failed_synthesis(tmp_path, monkeypatch, *, with_analysis=False, with_proposal=False):
    """Reusable SDK/API fixture with real acceptance and pinned local skills."""
    store = Store(tmp_path / "state.sqlite")
    engine = worker.Worker(store)
    case = {"id": "case-1", "title": "Offline synthesis checkpoint", "hypothesis": "Preserve the exact starting hypothesis.\n",
            "source_manifest": [{"path": "sources/test.tsv", "sha256": "a" * 64}],
            "evidence": [{"id": "e1", "kind": "measured", "title": "Synthetic observation", "summary": "One synthetic observation.",
                          "source": {"name": "Synthetic fixture", "url": "", "locator": "row one", "sha256": "a" * 64}}]}
    monkeypatch.setattr(cases, "get_case", lambda case_id: copy.deepcopy(case))
    from app import analysis_tools
    recipes = [{"id": name, "title": name, "input_sources": case["source_manifest"]}
               for name in (("test-analysis", "followup-analysis") if with_analysis or with_proposal else ())]
    monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda _: copy.deepcopy(recipes))
    monkeypatch.setattr(worker, "RUNTIME", tmp_path / "runtime")
    run = store.create(case, {"idempotency_key": uuid.uuid4().hex, "hypothesis": case["hypothesis"],
                              "source_name": "original-scientist.md", "mode": "live"})
    run_id, operation_id = run["id"], run["operation"]["id"]
    def prepare(current):
        current["status"] = "running"
        current["evidence"] = copy.deepcopy(case["evidence"])
        if with_analysis:
            values = {"case_id": case["id"], "analysis_id": "test-analysis", "input_sources": case["source_manifest"], "contrast": 3}
            current["evidence"].append({"id": "ANALYSIS-TEST", "title": "Synthetic derived comparison", "kind": "derived",
                "summary": "A synthetic registered comparison yielded 3.", "values": values,
                "source": {"name": "Synthetic test analysis", "url": "", "locator": "test-analysis", "sha256": digest(values)}})
        current["skill_receipts"] = []
        products = {}
        for role in sc.ROLES:
            skill_ids = [role, "discovery-planning"]
            if role == "molecular_scientist":
                skill_ids.append("bionemo-boltz2")
            receipts = []
            for skill_id in skill_ids:
                skill = scientific_skills.load_skill(skill_id, role)
                receipt = {"id": operation_id + "-skill-" + role + "-" + skill_id,
                           "skill_id": skill_id, "name": skill["name"], "role": role,
                           "version": skill["version"], "sha256": skill["sha256"],
                           "operation_id": operation_id, "loaded_at": now(), "origin": skill["origin"]}
                current["skill_receipts"].append(receipt)
                receipts.append(receipt)
            evidence = current["evidence"]
            product = {"id": "temporary-" + role, "sender": role,
                       "recipient": next(item["recipients"] for item in current["process_contract"]["roles"] if item["id"] == role),
                       "case_id": case["id"], "created_at": now(), "model_called": True, "model": providers.selected_model(),
                       "skill_receipt_ids": [item["id"] for item in receipts],
                       "skill_versions": {item["skill_id"]: {"version": item["version"], "sha256": item["sha256"]} for item in receipts},
                       "input_versions": {"hypothesis_sha256": current["hypothesis"]["sha256"],
                           "evidence_ids": [item["id"] for item in evidence], "evidence_versions": {item["id"]: item["source"]["sha256"] for item in evidence},
                           "evidence_sha256": hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
                           "upstream_handoff_ids": [products[required]["id"] for required in current["process_contract"]["stage_policy"]["required_upstream"][role]]},
                       "followup_proposals": [], "question": "What does the scoped source establish?", "method": "Read accepted synthetic source.",
                       "result_status": "inconclusive", "result": "The synthetic evidence does not establish a biological cause.",
                       "limitations": ["Synthetic fixture; no clinical inference."], "decision_it_could_change": "The next discriminating analysis.",
                       "claims": [{"text": "The source contains a synthetic observation.", "evidence_ids": ["e1"], "kind": "observation"}]}
            if with_proposal and role == "bioinformatician":
                from app.discovery_planning import build_proposal
                from app.followups import approved_catalog
                product["followup_proposals"] = [build_proposal(role=role, case=case, hypothesis=case["hypothesis"],
                    evidence=evidence, recipes=approved_catalog(case["id"]), bionemo_status="not_configured", analysis_id="followup-analysis",
                    scientific_question="Could the registered comparison distinguish the retained explanation?",
                    rationale="The accepted source leaves a specific contrast unresolved.",
                    decision_it_could_change="Which mechanism warrants the next experiment.",
                    evidence_ids=["ANALYSIS-TEST"] if with_analysis else ["e1"])]
            evaluation = evaluate_handoff(product, current)
            assert evaluation["verdict"] == "accepted", evaluation
            receipt = record_evaluation(current, evaluation, subject_sha256=digest(product))
            product.update(id=operation_id + "-handoff-" + role, run_id=run_id, operation_id=operation_id,
                           accepted_at=now(), acceptance_status="accepted", acceptance_evaluation_id=receipt["id"])
            current["handoffs"].append(product)
            products[role] = product
        # Coordinator loaded its instructions but never returned accepted output.
        for skill_id in ("coordinator", "discovery-planning"):
            skill = scientific_skills.load_skill(skill_id, "coordinator")
            current["skill_receipts"].append({"id": operation_id + "-skill-coordinator-" + skill_id, "skill_id": skill_id,
                "name": skill["name"], "role": "coordinator", "version": skill["version"], "sha256": skill["sha256"],
                "operation_id": operation_id, "loaded_at": now(), "origin": skill["origin"]})
    store.mutate(run_id, prepare)
    action_id = operation_id + "-rosalind"
    store.begin_action(run_id, action_id, "research-model-investigation", {
        "hypothesis_sha256": run["hypothesis"]["sha256"], "evidence_ids": ["e1"], "model": providers.selected_model()})
    current = store.get(run_id)
    metadata = {"provider": "openai", "requested_model": providers.selected_model(), "returned_models": [providers.selected_model()],
                "reasoning_effort": "high", "usage": {"input_tokens": 100, "output_tokens": 8000}, "dispatched_requests": 1,
                "requests": [{"number": 1, "agent": "coordinator", "status": "incomplete", "http_status": 200,
                              "request_id": "offline-request", "response_id": "offline-response", "max_output_tokens": 8000,
                              "returned_model": providers.selected_model(),
                              "incomplete_details": {"reason": "max_output_tokens"}}],
                "work_products": [{key: value for key, value in product.items() if key not in sc.SERVER_HANDOFF_FIELDS}
                                  for product in current["handoffs"]], "accepted_analysis_ids": ["ANALYSIS-TEST"] if with_analysis else [], "molecular_receipts": []}
    engine.provider_failure(run_id, action_id, providers.ProviderError("Known incomplete coordinator response", status="budget_exhausted", metadata=metadata))
    store.mutate(run_id, lambda item: item.update(status="budget_exhausted", stage="stopped", error="Output limit reached"))
    return store, engine, run_id, case


@pytest.fixture
def synthesis_harness(tmp_path, monkeypatch):
    return create_failed_synthesis(tmp_path, monkeypatch)


def select(store, run_id, key="explicit-recovery"):
    return sc.enqueue_synthesis_continuation(store, run_id, {
        "idempotency_key": key, "source_operation_id": store.get(run_id)["operation"]["id"]})


def test_inspect_is_read_only_and_selection_is_atomic_idempotent(synthesis_harness):
    store, _, run_id, _ = synthesis_harness
    before = store.get(run_id)
    available = sc.inspect_synthesis_checkpoint(store, run_id)
    assert available["eligible"] and available["handoff_count"] == 7
    assert store.get(run_id) == before
    selected = select(store, run_id)
    assert selected["operation"]["id"] != before["operation"]["id"]
    assert selected["operation"]["kind"] == "synthesis_continuation"
    assert selected["actions"] == before["actions"] and selected["handoffs"] == before["handoffs"]
    assert selected["skill_receipts"] == before["skill_receipts"] and selected["hypothesis"] == before["hypothesis"]
    assert selected["operation"]["input"]["reused_handoff_ids"] == [item["id"] for item in before["handoffs"]]
    same = sc.enqueue_synthesis_continuation(store, run_id, {"idempotency_key": "explicit-recovery", "source_operation_id": before["operation"]["id"]})
    assert same["synthesis_operations"] == selected["synthesis_operations"]
    assert len(same["synthesis_checkpoints"]) == len(same["synthesis_operations"]) == 1
    assert sc.synthesis_context(selected)["work_products"] == before["handoffs"]
    with pytest.raises(Conflict):
        sc.enqueue_synthesis_continuation(store, run_id, {"idempotency_key": "other-key", "source_operation_id": before["operation"]["id"]})


@pytest.mark.parametrize("change", ["unknown", "submitting", "cancelled", "missing_handoff", "accepted_coordinator", "bad_receipt", "changed_product", "wrong_final_role", "wrong_failure", "published", "changed_process", "changed_source"])
def test_ineligible_or_changed_failure_never_queues(synthesis_harness, monkeypatch, change):
    store, _, run_id, case = synthesis_harness
    def alter(run):
        if change in {"unknown", "submitting"}:
            run["actions"].append({"id": "external", "state": change})
        elif change == "cancelled":
            run["cancel_requested"] = True
        elif change == "missing_handoff":
            run["handoffs"].pop()
        elif change == "accepted_coordinator":
            run["handoffs"].append({**run["handoffs"][-1], "id": "extra", "sender": "coordinator"})
        elif change == "bad_receipt":
            run["stage_evaluations"][0]["reason"] = "Altered acceptance"
        elif change == "changed_product":
            run["handoffs"][0]["result"] = "Unaccepted replacement result"
        elif change in {"wrong_final_role", "wrong_failure"}:
            request = run["actions"][0]["provider_metadata"]["requests"][-1]
            if change == "wrong_final_role":
                request["agent"] = "reviewer"
            else:
                request["incomplete_details"]["reason"] = "other_failure"
        elif change == "published":
            run["decisions"] = [{"version": 1}]
        elif change == "changed_process":
            run["process_contract"]["version"] = "unreviewed-change"
    if change == "changed_source":
        monkeypatch.setattr(cases, "get_case", lambda _: {**case, "source_manifest": []})
    store.mutate(run_id, alter)
    before = store.get(run_id)
    assert sc.inspect_synthesis_checkpoint(store, run_id)["eligible"] is False
    with pytest.raises((Conflict, ValueError)):
        select(store, run_id)
    assert store.get(run_id) == before


@pytest.mark.parametrize("change", ["evidence", "hypothesis", "handoff", "skill_receipt", "checkpoint", "source_bytes", "skill_release", "source_action"])
def test_checkpoint_is_revalidated_at_consumption(synthesis_harness, monkeypatch, change):
    store, _, run_id, _ = synthesis_harness
    select(store, run_id)
    def alter(run):
        if change == "evidence":
            run["evidence"][0]["summary"] = "Changed observation"
        elif change == "hypothesis":
            run["hypothesis"]["source_name"] = "different provenance"
        elif change == "handoff":
            run["handoffs"][0]["result"] = "Different scientific result"
        elif change == "skill_receipt":
            run["skill_receipts"][0]["sha256"] = "d" * 64
        elif change == "checkpoint":
            run["synthesis_checkpoints"][0]["work_products"][0]["result"] = "Forged result"
        elif change == "source_action":
            run["actions"][0]["state"] = "succeeded"
    store.mutate(run_id, alter)
    if change == "source_bytes":
        monkeypatch.setattr(cases, "get_case", lambda _: (_ for _ in ()).throw(ValueError("Pinned source bytes changed")))
    elif change == "skill_release":
        original = scientific_skills.skill_catalog
        monkeypatch.setattr(scientific_skills, "skill_catalog", lambda role=None: [{**item, "version": "changed"} for item in original(role)])
    with pytest.raises((Conflict, ValueError)):
        sc.synthesis_context(store.get(run_id))


def test_client_cannot_supply_checkpoint_or_override_reused_products(synthesis_harness):
    store, _, run_id, _ = synthesis_harness
    for extra in ({"checkpoint": {}}, {"work_products": []}, {"source_action_id": "other"}):
        with pytest.raises(Conflict, match="only a request key"):
            sc.enqueue_synthesis_continuation(store, run_id, {"idempotency_key": "request", "source_operation_id": store.get(run_id)["operation"]["id"], **extra})
    assert not store.get(run_id).get("synthesis_checkpoints")


def test_worker_passes_validated_seven_products_and_issues_new_action(synthesis_harness, monkeypatch):
    store, engine, run_id, _ = synthesis_harness
    before = store.get(run_id)
    selected = select(store, run_id)
    calls = []
    async def synthesize(case, hypothesis, evidence, emit, cancelled, **callbacks):
        checkpoint = sc.validate_provider_checkpoint(case["synthesis_checkpoint"], case, hypothesis, evidence)
        calls.append(checkpoint)
        assert checkpoint["work_products"] == before["handoffs"]
        assert checkpoint["molecular_receipts"] == []
        assert len(store.get(run_id)["actions"]) == 2
        return governed_decision()
    monkeypatch.setattr(providers, "investigate", synthesize)
    asyncio.run(engine.execute(run_id))
    after = store.get(run_id)
    assert after["status"] == "completed", after["error"]
    assert len(calls) == 1 and len(after["decisions"]) == 1
    assert after["actions"][0] == before["actions"][0]
    assert after["actions"][1]["id"] == selected["operation"]["id"] + "-rosalind"
    assert after["actions"][1]["state"] == "succeeded"
    assert after["handoffs"] == before["handoffs"]
    assert after["synthesis_operations"][0]["status"] == "completed"
    assert after["hypothesis"] == before["hypothesis"]


def test_checkpoint_view_does_not_rewrite_original_products(synthesis_harness):
    store, _, run_id, _ = synthesis_harness
    select(store, run_id)
    original = store.get(run_id)
    view, lineage = sc.checkpoint_evaluation_view(original)
    assert all(item["operation_id"] == original["operation"]["id"] for item in view["handoffs"])
    assert all(item["operation_id"] != original["operation"]["id"] for item in original["handoffs"])
    assert lineage["reused_handoff_ids"] == [item["id"] for item in original["handoffs"]]
    assert store.get(run_id) == original


def test_new_coordinator_and_reviewer_acceptance_records_checkpoint_lineage(synthesis_harness, monkeypatch):
    store, engine, run_id, _ = synthesis_harness
    before = store.get(run_id)
    selected = select(store, run_id)
    async def review(case, hypothesis, evidence, emit, cancelled, **callbacks):
        products = {item["sender"]: item for item in case["synthesis_checkpoint"]["work_products"]}
        for role, upstream_roles in (("coordinator", ["translational_scientist", "assay_scientist"]),
                                     ("reviewer", ["coordinator", "assay_scientist"])):
            receipts = []
            for skill_id in (role, "discovery-planning"):
                receipts.append(await callbacks["accept_skill"]({"role": role, "skill_id": skill_id}))
            product = copy.deepcopy(products["assay_scientist"])
            for key in sc.SERVER_HANDOFF_FIELDS | {"id"}:
                product.pop(key, None)
            product.update(id="new-" + role, sender=role,
                           recipient=["reviewer"] if role == "coordinator" else ["scientist"],
                           skill_receipt_ids=[item["id"] for item in receipts],
                           skill_versions={item["skill_id"]: {"version": item["version"], "sha256": item["sha256"]} for item in receipts})
            product["input_versions"]["upstream_handoff_ids"] = [products[upstream]["id"] for upstream in upstream_roles]
            accepted = await callbacks["accept_handoff"](product)
            assert accepted["accepted"], accepted
            product["id"] = accepted["id"]
            products[role] = product
        return governed_decision()
    monkeypatch.setattr(providers, "investigate", review)
    asyncio.run(engine.execute(run_id))
    after = store.get(run_id)
    assert after["status"] == "completed", after["error"]
    assert after["handoffs"][:7] == before["handoffs"]
    assert [item["sender"] for item in after["handoffs"][7:]] == ["coordinator", "reviewer"]
    for product in after["handoffs"][7:]:
        assert product["operation_id"] == selected["operation"]["id"]
        assert product["checkpoint_lineage"]["source_operation_id"] == before["operation"]["id"]
        receipt = next(item for item in after["stage_evaluations"] if item["id"] == product["acceptance_evaluation_id"])
        assert receipt["checkpoint_lineage"] == product["checkpoint_lineage"]
        assert receipt["sha256"] == digest({key: value for key, value in receipt.items() if key != "sha256"})
    with store.connect() as db:
        request = json.loads(db.execute("SELECT request FROM actions WHERE id=?", (selected["operation"]["id"] + "-rosalind",)).fetchone()[0])
    assert request["checkpoint_sha256"] == selected["operation"]["input"]["checkpoint_sha256"]


def test_another_known_truncation_requires_another_explicit_new_operation(synthesis_harness, monkeypatch):
    store, engine, run_id, _ = synthesis_harness
    initial = store.get(run_id)
    first = select(store, run_id)
    original_metadata = copy.deepcopy(initial["actions"][0]["provider_metadata"])
    attempts = []
    async def incomplete(*args, **kwargs):
        attempts.append(True)
        raise providers.ProviderError("Coordinator still truncated", status="budget_exhausted", metadata=original_metadata)
    monkeypatch.setattr(providers, "investigate", incomplete)
    asyncio.run(engine.execute(run_id))
    failed = store.get(run_id)
    assert len(attempts) == 1 and failed["status"] == "budget_exhausted"
    assert failed["synthesis_operations"][0]["status"] == "budget_exhausted"
    assert sc.inspect_synthesis_checkpoint(store, run_id)["eligible"] is True
    assert len(failed["synthesis_operations"]) == 1  # No automatic retry was scheduled.
    second = select(store, run_id, key="second-explicit-selection")
    assert second["operation"]["id"] != first["operation"]["id"]
    assert len(second["synthesis_checkpoints"]) == 1
    assert len(second["synthesis_operations"]) == 2
    assert second["actions"] == failed["actions"]
    assert second["handoffs"] == initial["handoffs"]
    assert sc.synthesis_context(second)["source_operation_id"] == initial["operation"]["id"]


def test_cancelled_checkpoint_executes_no_new_model(synthesis_harness, monkeypatch):
    store, engine, run_id, _ = synthesis_harness
    select(store, run_id)
    store.mutate(run_id, lambda run: run.update(cancel_requested=True))
    async def forbidden(*args, **kwargs):
        pytest.fail("A cancelled explicit checkpoint may not dispatch synthesis")
    monkeypatch.setattr(providers, "investigate", forbidden)
    asyncio.run(engine.execute(run_id))
    after = store.get(run_id)
    assert after["status"] == "cancelled" and after["cancel_requested"] is True
    assert after["synthesis_operations"][0]["status"] == "cancelled"
    assert len(after["actions"]) == 1 and after["actions"][0]["state"] == "failed"


@pytest.mark.parametrize("intent_exists", [False, True])
def test_restart_reconciles_synthesis_operation_without_replaying_unknown_work(synthesis_harness, monkeypatch, intent_exists):
    store, engine, run_id, _ = synthesis_harness
    selected = select(store, run_id)
    def start(run):
        run["status"] = "running"
        run["synthesis_operations"][0]["status"] = "running"
    store.mutate(run_id, start)
    if intent_exists:
        store.begin_action(run_id, selected["operation"]["id"] + "-rosalind", "research-model-investigation", {
            "hypothesis_sha256": selected["hypothesis"]["sha256"], "checkpoint_id": selected["operation"]["input"]["checkpoint_id"]})
    before = store.get(run_id)
    engine.recover()
    after = store.get(run_id)
    expected = "blocked" if intent_exists else "paused"
    assert after["status"] == after["synthesis_operations"][0]["status"] == expected
    assert after["handoffs"] == before["handoffs"] and after["synthesis_checkpoints"] == before["synthesis_checkpoints"]
    assert len(after["actions"]) == len(before["actions"])
    if intent_exists:
        assert after["actions"][-1]["state"] == "unknown"
        async def forbidden(*args, **kwargs):
            pytest.fail("An unknown synthesis action cannot be resubmitted")
        monkeypatch.setattr(providers, "investigate", forbidden)
        asyncio.run(engine.execute(run_id))
        assert store.get(run_id)["status"] == "blocked"
        assert len(store.get(run_id)["actions"]) == len(before["actions"])
        assert sc.inspect_synthesis_checkpoint(store, run_id)["eligible"] is False
