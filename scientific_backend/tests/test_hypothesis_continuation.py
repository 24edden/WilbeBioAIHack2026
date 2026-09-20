"""Offline durable hypothesis continuation; no model or vendor transport is used."""
import asyncio
import copy
import hashlib
import json
import uuid

import pytest

from app import analysis_tools, followups, providers, worker
from app.store import Conflict, Store, digest
from test_providers import decision


SOURCE = {"path": "sources/continuation/table.tsv", "sha256": "b" * 64}
RECIPES = [{"id": name, "title": name + " registered comparison", "input_sources": [SOURCE],
            "followup_only": True} for name in ("first-analysis", "second-analysis", "unchosen-analysis")]
HYPOTHESIS = "Original hypothesis, with exact wording and provenance.\n"


def recommendation(analysis_id):
    return {"kind": "data_analysis", "analysis_id": analysis_id, "title": "Test " + analysis_id,
            "rationale": "Distinguish the retained explanation using the registered source comparison.",
            "decision_it_could_change": "Whether the explanation remains possible in the specified assay scope.",
            "prerequisites": ["Pinned source table"], "evidence_ids": ["e1"], "status": "ready"}


def governed_decision(next_id=None, stop_reason="needs_data"):
    value = decision()
    value["followups"] = [recommendation(next_id)] if next_id else []
    value["governance"] = {
        "hypotheses": [{"hypothesis_id": "primary", "statement": "A source-specific mechanism may explain the observation.",
                        "origin": "user", "source_quote": "", "scope": "Only the supplied experimental system",
                        "scope_type": "biological", "status": "possible",
                        "rationale": "The accepted source remains compatible with this explanation but does not establish it.",
                        "supporting_evidence_ids": ["e1"], "contradicting_evidence_ids": [], "test_evidence_ids": [],
                        "falsification_test": "", "falsification_result": "", "next_analysis_ids": [next_id] if next_id else [],
                        "blocker": "" if next_id else "The remaining distinction requires an unavailable measurement."}],
        "next_action_id": next_id, "target_hypothesis_ids": ["primary"] if next_id else [],
        "continuation_reason": "The selected source comparison can discriminate the current explanation." if next_id else
                               "The approved computations are insufficient to distinguish the remaining biological possibilities.",
        "stop_reason": "continue" if next_id else stop_reason,
    }
    return value


def analysis_record(analysis_id):
    values = {"case_id": "case-1", "analysis_id": analysis_id, "input_sources": [SOURCE], "contrast": 3.0}
    checksum = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return {"id": "ANALYSIS-" + analysis_id.upper(), "title": analysis_id, "kind": "derived",
            "summary": "Registered source comparison produced a contrast of 3.",
            "source": {"name": "Offline synthetic source", "url": "https://example.org/test", "locator": analysis_id, "sha256": checksum},
            "values": values}


def pin_policy(run, enabled=True):
    contract = copy.deepcopy(run["process_contract"])
    contract["hypothesis_governance"] = {"enabled": enabled, "auto_continue": enabled}
    contract.pop("sha256", None)
    run["process_contract"] = {**contract, "sha256": digest(contract)}


@pytest.fixture
def harness(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda _: copy.deepcopy(RECIPES))
    monkeypatch.setattr(worker, "RUNTIME", tmp_path / "runtime")
    monkeypatch.setattr(providers, "effective_model_limits", lambda: {"budget_mode": "advisory"})
    store = Store(tmp_path / "state.sqlite")
    case = {"id": "case-1", "title": "Continuation test", "hypothesis": HYPOTHESIS, "source_manifest": [SOURCE],
            "evidence": [{"id": "e1", "kind": "measured", "title": "Source observation", "summary": "Synthetic test observation",
                          "source": {"name": "Test source", "url": "https://example.org/test", "locator": "table", "sha256": "b" * 64}}]}
    run = store.create(case, {"idempotency_key": uuid.uuid4().hex, "hypothesis": HYPOTHESIS,
                              "source_name": "scientist.md", "mode": "live"})
    def prepare(current):
        current["evidence"] = copy.deepcopy(case["evidence"])
        pin_policy(current)
    store.mutate(run["id"], prepare)
    return store, worker.Worker(store), run["id"]


def test_two_successive_chosen_actions_reassess_and_stop_with_possible_hypothesis(harness, monkeypatch):
    store, engine, run_id = harness
    original = store.get(run_id)
    computed, reviewed = [], []
    def analyze(case_id, analysis_id):
        computed.append(analysis_id)
        assert analysis_id != "unchosen-analysis"
        return analysis_record(analysis_id)
    async def review(case, hypothesis, evidence, emit, cancelled, **kwargs):
        current = store.get(run_id)
        selected = current["operation"]["input"]["analysis_id"]
        assert current["governance_state"]["status"] == "running"
        reviewed.append(selected)
        assert hypothesis == HYPOTHESIS
        assert case["followup_context"]["origin"] == "agent_governance"
        assert case["revision_context"]["scientist_input"] is None
        assert case["revision_context"]["continuation_input"]["origin"] == "agent_governance"
        assert case["followup_context"]["previous_decision"]["governance"] == current["decisions"][-1]["governance"]
        assert analysis_record(selected)["id"] in {item["id"] for item in current["evidence"]}
        return governed_decision("second-analysis" if selected == "first-analysis" else None)
    monkeypatch.setattr(analysis_tools, "analyze_case", analyze)
    monkeypatch.setattr(providers, "investigate", review)
    engine.publish(run_id, governed_decision("first-analysis"))
    first = copy.deepcopy(store.get(run_id)["decisions"][0])
    assert store.get(run_id)["status"] == "queued"
    asyncio.run(engine.execute(run_id))
    second = copy.deepcopy(store.get(run_id)["decisions"][1])
    assert store.get(run_id)["status"] == "queued"
    asyncio.run(engine.execute(run_id))
    result = store.get(run_id)
    assert computed == reviewed == ["first-analysis", "second-analysis"]
    assert result["hypothesis"] == original["hypothesis"]
    assert result["decisions"][:2] == [first, second]
    assert [item["version"] for item in result["decisions"]] == [1, 2, 3]
    assert [item["new_decision_version"] for item in result["followup_operations"]] == [2, 3]
    assert all(item["origin"] == "agent_governance" and item["status"] == "completed" for item in result["followup_operations"])
    assert result["status"] == "completed"
    assert result["governance_state"]["status"] == "stopped"
    assert result["governance_state"]["stop_reason"] == "needs_data"
    assert result["governance_state"]["hypotheses"][0]["status"] == "possible"
    assert [item["status"] for item in result["governance_transitions"]] == ["queued", "queued", "stopped"]
    assert len([item for item in result["events"] if item["type"] == "hypothesis.state"]) == 3
    assert all(action["state"] == "succeeded" for action in result["actions"])


def test_publication_queue_atomicity_idempotence_and_restart(harness, monkeypatch):
    store, engine, run_id = harness
    original_operation = store.get(run_id)["operation"]["id"]
    real_apply = followups.apply_governance_continuation
    def interrupted(run):
        real_apply(run)
        raise ValueError("Simulated interruption before commit")
    monkeypatch.setattr(followups, "apply_governance_continuation", interrupted)
    with pytest.raises(ValueError, match="before commit"):
        engine.publish(run_id, governed_decision("first-analysis"), operation_id=original_operation)
    rolled_back = store.get(run_id)
    assert not rolled_back["decisions"] and not rolled_back.get("followup_operations")
    monkeypatch.setattr(followups, "apply_governance_continuation", real_apply)
    engine.publish(run_id, governed_decision("first-analysis"), operation_id=original_operation)
    before = store.get(run_id)
    engine.publish(run_id, governed_decision("first-analysis"), operation_id=original_operation)
    store.recover()
    after = store.get(run_id)
    assert after["status"] == "queued"
    assert after["decisions"] == before["decisions"]
    assert after["followup_operations"] == before["followup_operations"]
    assert len(after["governance_transitions"]) == 1
    with pytest.raises(Conflict, match="stale operation"):
        engine.publish(run_id, governed_decision(), operation_id="unrelated-operation")
    assert len(store.get(run_id)["decisions"]) == 1


@pytest.mark.parametrize("when", ["before_publication", "after_queue"])
def test_cancellation_never_resets_or_dispatches(harness, monkeypatch, when):
    store, engine, run_id = harness
    def forbidden(*args, **kwargs):
        pytest.fail("Cancellation must prevent new executor/provider work")
    monkeypatch.setattr(analysis_tools, "analyze_case", forbidden)
    monkeypatch.setattr(providers, "investigate", forbidden)
    if when == "after_queue":
        engine.publish(run_id, governed_decision("first-analysis"))
    store.mutate(run_id, lambda run: run.update(cancel_requested=True))
    if when == "before_publication":
        with pytest.raises(worker.Cancelled):
            engine.publish(run_id, governed_decision("first-analysis"))
    asyncio.run(engine.execute(run_id))
    result = store.get(run_id)
    assert result["cancel_requested"] is True and result["status"] == "cancelled"
    assert not result["actions"]
    if when == "after_queue":
        assert result["followup_operations"][0]["status"] == "cancelled"
        assert result["governance_state"]["suppression"] == "cancelled"
        assert result["governance_state"]["stop_reason"] == "cancelled"


@pytest.mark.parametrize("action_state", ["unknown", "submitting"])
def test_unresolved_external_work_suppresses_new_autoqueue(harness, action_state):
    store, engine, run_id = harness
    store.mutate(run_id, lambda run: run["actions"].append({"id": "prior-external", "state": action_state}))
    engine.publish(run_id, governed_decision("first-analysis"))
    result = store.get(run_id)
    assert not result.get("followup_operations")
    assert len(result["decisions"]) == 1 and result["status"] == "blocked"
    assert result["governance_state"]["stop_reason"] == "provider_unresolved"
    assert result["decisions"][0]["governance"]["stop_reason"] == "continue"


@pytest.mark.parametrize("prior_status", ["failed", "cancelled", "blocked", "completed"])
def test_any_prior_attempt_same_recipe_and_sources_suppresses_replay(harness, prior_status):
    store, engine, run_id = harness
    recipe = followups.approved_catalog("case-1")[0]
    store.mutate(run_id, lambda run: run.update(followup_operations=[{
        "id": "prior-attempt", "analysis_id": recipe["id"], "recipe_sha256": digest(recipe),
        "source_manifest_sha256": digest([SOURCE]), "status": prior_status}]))
    engine.publish(run_id, governed_decision("first-analysis"))
    result = store.get(run_id)
    assert len(result["followup_operations"]) == 1
    assert result["status"] == "completed"
    assert result["governance_state"]["suppression"] == "already_attempted"
    assert result["governance_state"]["prior_operation_ids"] == ["prior-attempt"]


def test_already_accepted_analysis_cannot_be_requested_again(harness):
    store, engine, run_id = harness
    store.mutate(run_id, lambda run: run["evidence"].append(analysis_record("first-analysis")))
    with pytest.raises(ValueError, match="unperformed"):
        engine.publish(run_id, governed_decision("first-analysis"))
    assert not store.get(run_id)["decisions"]
    assert not store.get(run_id).get("followup_operations")


@pytest.mark.parametrize("changed", ["decision", "hypothesis", "sources", "recipe"])
def test_execution_rechecks_selected_exact_versions_without_dispatch(harness, monkeypatch, changed):
    store, engine, run_id = harness
    engine.publish(run_id, governed_decision("first-analysis"))
    if changed == "recipe":
        monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda _: [{**item, "description": "Changed method"} for item in RECIPES])
    else:
        def change(run):
            if changed == "decision":
                run["decisions"][-1]["sha256"] = "c" * 64
            elif changed == "hypothesis":
                run["hypothesis"]["sha256"] = "c" * 64
            else:
                run["case_snapshot"]["source_manifest"] = []
        store.mutate(run_id, change)
    def forbidden(*args, **kwargs):
        pytest.fail("Stale selection must fail before computation")
    monkeypatch.setattr(analysis_tools, "analyze_case", forbidden)
    monkeypatch.setattr(providers, "investigate", forbidden)
    asyncio.run(engine.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "failed"
    assert len(result["decisions"]) == 1 and not result["actions"]
    assert result["governance_state"]["status"] == "stopped"
    assert result["governance_state"]["stop_reason"] == "execution_failed"


def test_failed_analysis_is_not_replayed_on_worker_retry(harness, monkeypatch):
    store, engine, run_id = harness
    calls = []
    def fail(*args):
        calls.append(args)
        raise ValueError("Registered source QC failed")
    monkeypatch.setattr(analysis_tools, "analyze_case", fail)
    engine.publish(run_id, governed_decision("first-analysis"))
    asyncio.run(engine.execute(run_id))
    asyncio.run(engine.execute(run_id))
    result = store.get(run_id)
    assert len(calls) == 1 and len(result["actions"]) == 1
    assert result["actions"][0]["state"] == "failed"
    assert len(result["decisions"]) == 1
    assert result["governance_state"]["status"] == "stopped"


@pytest.mark.parametrize("mode", ["demo", "historical", "disabled", "tampered_policy"])
def test_nonopted_in_runs_keep_single_decision_behavior(harness, mode):
    store, engine, run_id = harness
    def alter(run):
        if mode == "demo":
            run["mode"] = "demo"
        elif mode == "disabled":
            pin_policy(run, enabled=False)
        elif mode == "tampered_policy":
            run["process_contract"]["sha256"] = "c" * 64
        else:
            run["process_contract"].pop("hypothesis_governance")
            run["process_contract"].pop("sha256")
            run["process_contract"]["sha256"] = digest(run["process_contract"])
    store.mutate(run_id, alter)
    engine.publish(run_id, decision())
    result = store.get(run_id)
    assert result["status"] == "completed" and len(result["decisions"]) == 1
    assert not result.get("followup_operations")


def test_new_live_policy_requires_governance_and_valid_current_evidence(harness):
    store, engine, run_id = harness
    with pytest.raises(ValueError, match="requires.*governance"):
        engine.publish(run_id, decision())
    invalid = governed_decision("first-analysis")
    invalid["governance"]["hypotheses"][0]["supporting_evidence_ids"] = ["invented"]
    with pytest.raises(ValueError, match="accepted evidence"):
        engine.publish(run_id, invalid)
    assert not store.get(run_id)["decisions"]
    assert not store.get(run_id).get("followup_operations")


def test_manual_selection_authority_cannot_be_set_by_payload(harness):
    store, engine, run_id = harness
    engine.publish(run_id, governed_decision())
    action = followups.available_followups(store.get(run_id))["followups"][0]
    result = followups.enqueue_followup(store, run_id, {"decision_version": 1, "recommendation_id": action["id"],
        "idempotency_key": "manual", "origin": "agent_governance", "analysis_id": "arbitrary-code"})
    entry = result["operation"]["input"]
    assert entry["origin"] == "scientist_selection"
    assert entry["analysis_id"] == "first-analysis"
    assert result["events"][-1]["agent"] == "Scientist"


@pytest.mark.parametrize("kind", ["feedback", "outcome"])
def test_new_scientist_input_can_reopen_autonomous_testing(harness, kind):
    store, engine, run_id = harness
    engine.publish(run_id, governed_decision())
    first = copy.deepcopy(store.get(run_id)["decisions"][0])
    store.mutate(run_id, lambda run: run.update(status="running", operation={"id": kind + "-new", "kind": kind}))
    engine.publish(run_id, governed_decision("first-analysis"), operation_id=kind + "-new")
    result = store.get(run_id)
    assert result["status"] == "queued" and result["decisions"][0] == first
    assert result["operation"]["input"]["origin"] == "agent_governance"


def test_modeling_keeps_prior_ledger_identity_for_later_reassessment(harness):
    store, engine, run_id = harness
    value = governed_decision(stop_reason="resolved_within_scope")
    value["governance"]["hypotheses"][0].update(
        status="clearly_ruled_out", supporting_evidence_ids=[], contradicting_evidence_ids=["e1"], test_evidence_ids=["e1"],
        falsification_test="The registered contrast assessed the specific source explanation.",
        falsification_result="The synthetic observed result contradicts the tested explanation within the stated scope.")
    engine.publish(run_id, value)
    first = copy.deepcopy(store.get(run_id)["decisions"][0])
    store.mutate(run_id, lambda run: run.update(operation={"id": "manual-modeling", "kind": "modeling"}, status="running"))
    engine.publish(run_id, first, operation_id="manual-modeling")
    modeled = copy.deepcopy(store.get(run_id)["decisions"][-1])
    assert modeled["governance"] is None
    assert modeled["prior_governance"] == first["governance"]
    assert followups.compact_previous_decision(modeled)["prior_governance"] == first["governance"]
    assert store.get(run_id)["status"] == "completed" and not store.get(run_id).get("followup_operations")
    store.mutate(run_id, lambda run: run.update(operation={"id": "later-feedback", "kind": "feedback"}, status="running"))
    with pytest.raises(ValueError, match="Reopening.*new or changed"):
        engine.publish(run_id, governed_decision(), operation_id="later-feedback")
    assert store.get(run_id)["decisions"] == [first, modeled]


MOLECULAR_INPUTS = {"target_sequence": "ACDEFGHIKLMNPQRST", "reference_binder": "CDEFGHIKLMNPQRSTV",
                    "candidate_binder": "CDEFGHIKLMNPQRSTW", "source_note": "Exact synthetic test constructs; no real inference.",
                    "target_retained": True}


def test_same_molecular_pair_is_reused_across_autonomous_team_cycles(harness, monkeypatch):
    store, engine, run_id = harness
    store.mutate(run_id, lambda run: run["case_snapshot"].update(molecular_inputs=MOLECULAR_INPUTS))
    monkeypatch.setattr(providers, "capabilities", lambda: {"bionemo": {"status": "configured"}})
    monkeypatch.setattr(analysis_tools, "analyze_case", lambda case_id, recipe: analysis_record(recipe))
    predictions, receipts = [], []
    async def compare(*args, **kwargs):
        predictions.append(args[:3])
        return {"status": "completed", "scope": "Synthetic offline comparison", "artifact": None}
    async def review(case, hypothesis, evidence, emit, cancelled, **callbacks):
        receipts.append(await callbacks["request_molecular"]({"rationale": "Review the qualified comparison."}))
        return governed_decision("second-analysis" if len(receipts) == 1 else None)
    monkeypatch.setattr(providers, "compare_binders", compare)
    monkeypatch.setattr(providers, "investigate", review)
    engine.publish(run_id, governed_decision("first-analysis"))
    asyncio.run(engine.execute(run_id))
    asyncio.run(engine.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "completed", result["error"]
    assert len(predictions) == 1 and len(receipts) == 2
    assert receipts[0]["action_id"] == receipts[1]["action_id"]
    assert receipts[1]["reused"] is True and receipts[1]["evidence"] == receipts[0]["evidence"]
    assert len([action for action in result["actions"] if action["kind"] == "agent-directed-bionemo-comparison"]) == 1
    assert len([item for item in result["evidence"] if item["kind"] == "prediction"]) == 1
    assert result["decisions"][-1]["rd_handoff"]["modeling"]["reused"] is True


@pytest.mark.parametrize("prior_state", ["unknown", "submitting", "failed"])
def test_unsuccessful_legacy_molecular_pair_is_never_automatically_resubmitted(harness, monkeypatch, prior_state):
    store, engine, run_id = harness
    store.mutate(run_id, lambda run: run["case_snapshot"].update(molecular_inputs=MOLECULAR_INPUTS))
    store.begin_action(run_id, "older-operation-agent-boltz", "agent-directed-bionemo-comparison", {"inputs": MOLECULAR_INPUTS})
    if prior_state != "submitting":
        store.end_action(run_id, "older-operation-agent-boltz", prior_state, {"status": "incomplete"})
    store.mutate(run_id, lambda run: run.update(operation={"id": "new-auto-cycle", "kind": "followup"}))
    async def forbidden(*args, **kwargs):
        pytest.fail("A prior unsuccessful attempt must prevent every new NVIDIA dispatch")
    monkeypatch.setattr(providers, "compare_binders", forbidden)
    receipt = asyncio.run(engine.agent_molecular(run_id, {"rationale": "New review."}, forbidden, lambda: False, forbidden))
    assert receipt["status"] == "blocked" and receipt["prior_state"] == prior_state
    assert receipt["action_id"] == "older-operation-agent-boltz" and receipt["reused"] is True
    assert len(store.get(run_id)["actions"]) == 1


def test_unknown_executor_outcome_stops_governance_without_retry(harness, monkeypatch):
    store, engine, run_id = harness
    attempts = []
    def unresolved(*args):
        attempts.append(args)
        raise providers.ProviderError("Outcome remains unresolved", status="unknown")
    monkeypatch.setattr(analysis_tools, "analyze_case", unresolved)
    engine.publish(run_id, governed_decision("first-analysis"))
    first_decision = copy.deepcopy(store.get(run_id)["decisions"][0])
    asyncio.run(engine.execute(run_id))
    stopped = store.get(run_id)
    assert stopped["status"] == "blocked"
    assert stopped["governance_state"]["status"] == "stopped"
    assert stopped["governance_state"]["stop_reason"] == "provider_unresolved"
    assert stopped["governance_transitions"][0]["status"] == "queued"
    assert stopped["decisions"] == [first_decision]
    asyncio.run(engine.execute(run_id))
    assert len(attempts) == 1 and len(store.get(run_id)["actions"]) == 1
    assert store.get(run_id)["actions"][0]["state"] == "unknown"


def test_restart_marks_interrupted_continuation_stopped_and_preserves_unknown_intent(harness):
    store, engine, run_id = harness
    engine.publish(run_id, governed_decision("first-analysis"))
    before = store.get(run_id)
    operation_id = before["operation"]["id"]
    store.begin_action(run_id, operation_id + "-followup", "registered-followup", {"analysis_id": "first-analysis"})
    def interrupted(run):
        run["status"] = "running"
        run["governance_state"]["status"] = "running"
    store.mutate(run_id, interrupted)
    engine.recover()
    after = store.get(run_id)
    assert after["status"] == "blocked" and after["actions"][0]["state"] == "unknown"
    assert after["governance_state"]["status"] == "stopped"
    assert after["governance_state"]["stop_reason"] == "provider_unresolved"
    assert after["followup_operations"][0]["status"] == "blocked"
    assert after["decisions"] == before["decisions"]
    assert after["governance_transitions"][0] == before["governance_transitions"][0]
    transitions = copy.deepcopy(after["governance_transitions"])
    engine.recover()
    assert store.get(run_id)["governance_transitions"] == transitions
