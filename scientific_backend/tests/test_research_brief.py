"""Research interpretation contracts through real SDK, mocked transport only."""
import asyncio
import copy
import json

import httpx
import pytest
from pydantic import ValidationError

from app import providers as p
from app import research_brief as rb
from test_providers import fake_clients, message, response, isolated


def source_run():
    hypothesis = "Does target-side splicing explain the observed response?"
    return {
        "id": "run-1", "case_id": "case-1", "status": "completed",
        "hypothesis": {"text": hypothesis, "source_name": "scientist", "sha256": p._sha(hypothesis)},
        "evidence": [{"id": "e1", "kind": "observation", "summary": "The measured endpoint decreased.",
                      "values": {"paired_samples": 9, "result": 0.2, "limitation": "Different cohorts"}}],
        "decisions": [{"version": 1, "summary": "A scoped mechanism has support.", "assessment": "inconclusive",
                       "metadata": {"huge_private_transport_history": "must-not-enter-context"}}],
        "handoffs": [{"id": "h1", "sender": "statistician", "result": "A measured association is supported.",
                      "acceptance_status": "accepted", "result_status": "completed"},
                     {"id": "rejected", "sender": "molecular_scientist", "result": "Incorrect finding.", "acceptance_status": "rejected"}],
        "process_contract": {"version": "pinned-1"}, "governance_state": {"status": "stopped"},
    }


def brief():
    return {
        "headline": "Splicing is the leading study-level explanation",
        "plain_summary": "The data support a target-side mechanism. Patient-specific causation is still untested.",
        "proposed_answer": {"statement": "Target-side splicing is the leading working explanation for the measured endpoint.",
            "confidence_label": "leading_explanation", "scope": "The observed assay result", "evidence_ids": ["e1"],
            "caveat": "Matched patient functional measurements are missing.", "strongest_alternative": "Impaired effector function remains possible."},
        "findings": [{"what": "The endpoint decreased.", "why_it_matters": "This supports a target-side mechanism.", "evidence_ids": ["e1"]}],
        "role_summaries": [{"role": "statistician", "what_found": "The association is reproducible in the supplied measurements.",
                            "why_it_matters": "Association is not patient causation.", "evidence_ids": ["e1"]}],
        "decision_story": [{"decision_version": 1, "what_changed": "The measured endpoint supports the proposed mechanism.",
                            "why": "Its paired comparison moved consistently.", "next_step": "Test matched functional controls.", "evidence_ids": ["e1"]}],
        "nvidia": {"summary": "No NVIDIA prediction was available in this context.", "learned": [], "not_established": ["Binding was not measured."], "evidence_ids": [], "sequence_ids": []},
        "recommended_next_step": {"action": "Compare matched target and effector cells.", "why": "This distinguishes target loss from effector dysfunction.",
            "positive_result": "Restoration strengthens the target hypothesis.", "negative_result": "No restoration weakens it.",
            "prerequisites": ["Qualified controls"], "evidence_ids": ["e1"]},
        "modeling_draft": {"objective": "Compare qualified binders on a retained target.", "scientific_rationale": "Functional evidence must establish an appropriate comparison.",
            "target_sequence_id": None, "reference_binder_sequence_id": None, "candidate_binder_sequence_id": None,
            "qualification_note": "Exact inputs and target-retention evidence are missing.", "missing_inputs": ["Qualified target and binder sequences"], "evidence_ids": ["e1"]},
    }


def reviewed(content=None):
    return {"verdict": "accepted", "checks": {key: True for key in rb.ReviewChecks.model_fields},
            "changes": ["Separated study support from patient attribution."],
            "remaining_limitations": ["Patient causal interpretation remains untested."], "brief": content or brief()}


def audit(run=None):
    run = run or source_run()
    sequence = "ACDEFGHIKLMNPQRSTVWY"
    sha = p._sha(sequence)
    return {"run_id": run["id"], "sequence_inventory": [{"id": "sequence-" + sha[:20], "role": "target", "verified": True,
        "sequence": sequence, "sequence_sha256": sha, "length": len(sequence), "evidence_id": "e1", "target_retention_established": False}]}


def context(run=None, extra=None):
    return rb.build_brief_context(run or source_run(), {"id": "case-1"}, extra_context=extra)


def test_context_freezes_original_and_accepts_only_latest_accepted_handoffs():
    run = source_run()
    old = copy.deepcopy(run)
    c = context(run)
    assert c["original_hypothesis"] == run["hypothesis"]
    assert c["accepted_evidence"][0]["values"] == run["evidence"][0]["values"]
    assert c["handoff_history"]["included_latest_roles"] == ["statistician"]
    assert "must-not-enter-context" not in json.dumps(c)
    assert "Incorrect finding" not in json.dumps(c)
    c["accepted_evidence"][0]["values"]["paired_samples"] = 100
    assert run == old


def test_context_keeps_last_three_decisions_and_latest_role_once():
    run = source_run()
    run["decisions"] = [{"version": v, "summary": f"Decision {v}"} for v in range(1, 6)]
    run["handoffs"].append({"id": "h2", "sender": "statistician", "result": "The latest result", "acceptance_status": "accepted"})
    c = context(run)
    assert c["decision_history"] == {"total_versions": 5, "included_versions": [3, 4, 5]}
    assert c["latest_accepted_role_products"][0]["id"] == "h2"


@pytest.mark.parametrize("change,error", [
    (lambda r: r["hypothesis"].update(text="changed"), "hypothesis hash"),
    (lambda r: r["evidence"].append(copy.deepcopy(r["evidence"][0])), "unique accepted"),
    (lambda r: r["evidence"][0].update(acceptance_status="rejected"), "rejected or pending"),
    (lambda r: r.update(decisions=[]), "completed versioned"),
    (lambda r: r["decisions"].append(copy.deepcopy(r["decisions"][0])), "must be unique"),
])
def test_invalid_context_rejected_before_transport(change, error):
    run = source_run()
    change(run)
    with pytest.raises(p.ProviderError, match=error):
        context(run)


def test_context_rejects_oversize_without_silent_evidence_loss():
    run = source_run()
    run["evidence"][0]["values"]["large"] = "a" * rb.MAX_CONTEXT_CHARS
    with pytest.raises(p.ProviderError, match="exceeds the bounded"):
        context(run)


def test_verified_sequences_remain_server_side_and_hash_checked():
    value = audit()
    c = context(extra={"molecular_audit": value})
    assert "sequence" not in c["molecular_audit"]["sequence_inventory"][0]
    assert value["sequence_inventory"][0]["sequence"]
    value["sequence_inventory"][0]["sequence"] += "A"
    with pytest.raises(p.ProviderError, match="do not match"):
        context(extra={"molecular_audit": value})


@pytest.mark.parametrize("change,error", [
    (lambda b: b["proposed_answer"].update(evidence_ids=["invented"]), "missing, unaccepted"),
    (lambda b: b["decision_story"][0].update(decision_version=2), "supplied decision versions"),
    (lambda b: b["role_summaries"][0].update(role="clinical_scientist"), "accepted role products"),
    (lambda b: b["modeling_draft"].update(target_sequence_id="invented"), "unverified sequence"),
    (lambda b: b["modeling_draft"].update(missing_inputs=[]), "disclose missing"),
    (lambda b: b["nvidia"].update(sequence_ids=["invented"]), "unverified sequence"),
    (lambda b: b.update(plain_summary="ACDEFGHIKLMNPQRSTVWYACDEFGHIKLMNPQ"), "sequence bytes"),
])
def test_output_acceptance_rejects_fabricated_lineage_or_sequences(change, error):
    b = brief()
    change(b)
    with pytest.raises(p.ProviderError, match=error):
        rb.validate_brief(b, context())


def test_target_isoform_cannot_be_used_as_binder_and_retention_cannot_be_asserted():
    value = audit()
    c = context(extra={"molecular_audit": value})
    b = brief()
    b["modeling_draft"]["target_sequence_id"] = value["sequence_inventory"][0]["id"]
    assert rb.validate_brief(b, c)["modeling_draft"]["target_sequence_id"]
    b["modeling_draft"]["candidate_binder_sequence_id"] = value["sequence_inventory"][0]["id"]
    with pytest.raises(p.ProviderError, match="confused target and binder"):
        rb.validate_brief(b, c)
    b["modeling_draft"]["target_retained"] = True
    with pytest.raises(ValidationError, match="Extra inputs"):
        rb.ResearchBrief.model_validate(b)


def test_real_sdk_synthesis_and_independent_review_preserve_history(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    calls, events = [], []
    run, extra = source_run(), {"molecular_audit": audit()}
    before = copy.deepcopy((run, extra))
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        return response([message(brief() if len(calls) == 1 else reviewed())], len(calls))
    async def emit(*args, **kwargs):
        events.append((args, kwargs))
    fake_clients(monkeypatch, handler)
    result = asyncio.run(rb.generate_research_brief(run, {"id": "case-1"}, emit, extra_context=extra))
    assert (run, extra) == before
    assert len(calls) == 2
    assert all(call["reasoning"]["effort"] == "high" and call["max_output_tokens"] == 48000 and not call.get("tools") for call in calls)
    assert result["content"]["proposed_answer"]["confidence_label"] == "leading_explanation"
    assert result["human_review_status"] == "unreviewed"
    assert result["decision_version"] == 1
    assert result["provider_metadata"]["actual_model_roles"] == ["coordinator", "reviewer"]
    assert result["provider_metadata"]["usage"] == {"input_tokens": 60, "output_tokens": 20}
    assert result["provider_metadata"]["requests"][1]["request_id"] == "req_2"
    assert result["provider_metadata"]["returned_models"] == ["gpt-6-astra"]
    assert len(result["skill_receipts"]) == 8
    assert all(item["name"] and item["loaded_at"] for item in result["skill_receipts"])
    assert result["model_review"]["verdict"] == "accepted"
    assert result["context_sha256"] == rb._sha(context(run, extra))
    assert result["sha256"] == rb._sha({key: val for key, val in result.items() if key != "sha256"})
    assert any("AI review" in args[1] for args, kwargs in events)


def test_invalid_citations_get_one_explicit_correction_then_fail(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    calls = []
    bad = brief()
    bad["proposed_answer"]["evidence_ids"] = ["fabricated"]
    def handler(request):
        calls.append(json.loads(request.content))
        return response([message(bad)], len(calls))
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError, match="missing, unaccepted") as err:
        asyncio.run(rb.generate_research_brief(source_run(), {"id": "case-1"}))
    assert len(calls) == 2
    assert "acceptance_feedback" in calls[-1]["input"][0]["content"]
    assert err.value.metadata["acceptance_repairs"] == 1
    assert err.value.metadata["actual_model_roles"] == ["coordinator"]


def test_reviewer_must_pass_every_check(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    calls = []
    review = reviewed()
    review["checks"]["prediction_limits_preserved"] = False
    def handler(request):
        calls.append(json.loads(request.content))
        return response([message(brief() if len(calls) == 1 else review)], len(calls))
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError, match="reviewer rejected"):
        asyncio.run(rb.generate_research_brief(source_run(), {"id": "case-1"}))
    assert len(calls) == 3


def test_explicit_schema_unsupported_switches_only_same_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(400, json={"error": {"message": "json_schema structured output is not supported", "type": "invalid_request_error"}})
        return response([message(brief() if len(calls) == 2 else reviewed())], len(calls))
    fake_clients(monkeypatch, handler)
    result = asyncio.run(rb.generate_research_brief(source_run(), {"id": "case-1"}))
    assert len(calls) == 3
    assert {c["model"] for c in calls} == {p.MODEL}
    assert result["provider_metadata"]["typed_output"] is False


def test_timeout_is_unknown_and_never_retried(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("timeout", request=request)
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError) as err:
        asyncio.run(rb.generate_research_brief(source_run(), {"id": "case-1"}))
    assert len(calls) == 1
    assert err.value.status == "unknown"
    assert err.value.reason_code == "model_request_timeout"
    assert err.value.metadata["failure"]["automatic_retry"] is False


def test_auth_error_does_not_retry_or_substitute(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(403, json={"error": {"message": "Model access denied", "type": "permission_error"}})
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError):
        asyncio.run(rb.generate_research_brief(source_run(), {"id": "case-1"}))
    assert len(calls) == 1


def test_invalid_source_rejected_before_model_session(monkeypatch):
    monkeypatch.setattr(p, "ModelSession", lambda *a, **k: pytest.fail("Transport must not be created"))
    run = source_run()
    run["hypothesis"]["text"] = "tampered"
    with pytest.raises(p.ProviderError, match="hypothesis hash"):
        asyncio.run(rb.generate_research_brief(run, {"id": "case-1"}))


@pytest.mark.parametrize("text", [
    "Sequence checksum " + "a" * 64,
    "Reference sequence-10a724e985733a905f02 completed.",
    "The provider returned req_live_model_123.",
    "The response was resp_saved_123.",
    "Prediction 07f57391-aa22-412f-8735-0420c6e1b0de returned.",
])
def test_readable_narrative_rejects_machine_provenance_dumps(text):
    b = brief()
    b["nvidia"]["learned"] = [text]
    with pytest.raises(p.ProviderError, match="hash or machine identifier"):
        rb.validate_brief(b, context())


def test_hypothesis_labels_stay_out_of_narrative_but_biological_symbols_are_allowed():
    b = brief()
    b["findings"][0]["what"] = "H1 remains the most useful lead."
    c = context()
    c["governance_state"] = {"hypotheses": [{"hypothesis_id": "H1"}]}
    with pytest.raises(p.ProviderError, match="internal hypothesis or evidence label"):
        rb.validate_brief(b, c)
    # A real scientific symbol is not forbidden when it is not a case ledger ID.
    assert rb.validate_brief(b, context())["findings"][0]["what"]


def test_evidence_codes_stay_in_structured_citations():
    run = source_run()
    run["evidence"][0]["id"] = "ANALYSIS-OBSERVED"
    b = brief()
    def replace(node):
        if isinstance(node, dict):
            for key, val in node.items():
                if key == "evidence_ids":
                    node[key] = ["ANALYSIS-OBSERVED"] if val else []
                else:
                    replace(val)
        elif isinstance(node, list):
            for val in node:
                replace(val)
    replace(b)
    assert rb.validate_brief(b, context(run))["proposed_answer"]["evidence_ids"] == ["ANALYSIS-OBSERVED"]
    b["findings"][0]["what"] += " See ANALYSIS-OBSERVED."
    with pytest.raises(p.ProviderError, match="internal hypothesis or evidence label"):
        rb.validate_brief(b, context(run))


@pytest.mark.parametrize("section,key,limit", [
    ("nvidia", "summary", 45),
    ("proposed_answer", "statement", 60),
    ("recommended_next_step", "action", 40),
    ("recommended_next_step", "why", 35),
])
def test_practical_narrative_word_caps(section, key, limit):
    b = brief()
    b[section][key] = "a " * (limit + 1)
    with pytest.raises(p.ProviderError, match=f"exceeds {limit} words"):
        rb.validate_brief(b, context())


def test_nvidia_bullets_and_prerequisites_are_short_and_limited():
    b = brief()
    b["nvidia"]["learned"] = ["a " * 36]
    with pytest.raises(p.ProviderError, match="exceeds 35 words"):
        rb.validate_brief(b, context())
    b["nvidia"]["learned"] = ["A concise takeaway."] * 5
    with pytest.raises(ValidationError, match="at most 4"):
        rb.validate_brief(b, context())
    b = brief()
    b["recommended_next_step"]["prerequisites"] = ["a " * 26]
    with pytest.raises(p.ProviderError, match="exceeds 25 words"):
        rb.validate_brief(b, context())
    b["recommended_next_step"]["prerequisites"] = ["Qualified controls"] * 5
    with pytest.raises(ValidationError, match="at most 4"):
        rb.validate_brief(b, context())


def test_independent_reviewer_must_pass_readability(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    calls = []
    review = reviewed()
    review["checks"]["plain_language_and_decision_relevance"] = False
    def handler(request):
        calls.append(json.loads(request.content))
        return response([message(brief() if len(calls) == 1 else review)], len(calls))
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError, match="reviewer rejected"):
        asyncio.run(rb.generate_research_brief(source_run(), {"id": "case-1"}))
    assert len(calls) == 3
    assert "scientific lesson instead of a receipt inventory" in calls[-1]["instructions"]


def required_studies(count=1):
    run = source_run()
    case = {"id": run["case_id"], "required_analysis_ids": []}
    run["required_analysis_operations"] = []
    for index in range(count):
        analysis_id, evidence_id = f"paired-study-{index}", f"study-evidence-{index}"
        case["required_analysis_ids"].append(analysis_id)
        run["evidence"].append({"id": evidence_id, "kind": "observation", "acceptance_status": "accepted",
            "summary": "The additional treatment cohort showed no consistent endpoint change.",
            "values": {"cohort": "Conventional treatment", "paired_samples": 11, "result": 0.01,
                       "limitations": ["Different treatment exposure from the original experiment."]}})
        run["required_analysis_operations"].append({"analysis_id": analysis_id,
            "action_id": f"required-action-{index}", "status": "completed", "evidence_id": evidence_id})
    return run, case


def required_finding(evidence_ids):
    return {"what": "The additional conventional-treatment cohort showed no consistent endpoint change.",
        "why_it_matters": "This leaves the original experimental explanation unchanged and limits generalization across treatments.",
        "evidence_ids": evidence_ids}


def test_required_study_context_includes_only_completed_accepted_pinned_operations():
    run, case = required_studies()
    operation = run["required_analysis_operations"][0]
    run["required_analysis_operations"] += [
        {**operation, "action_id": "pending", "status": "running"},
        {**operation, "action_id": "failed", "status": "failed"},
        {**operation, "action_id": "not-required", "analysis_id": "model-selected-analysis"},
        {**operation, "action_id": "unaccepted", "evidence_id": "not-in-accepted-evidence"},
    ]
    before = copy.deepcopy((run, case))
    c = rb.build_brief_context(run, case)
    assert c["required_study_coverage"] == [operation]
    assert c["accepted_evidence"][1]["values"] == run["evidence"][1]["values"]
    assert rb.build_brief_context(run, {"id": case["id"]})["required_study_coverage"] == []
    c["required_study_coverage"][0]["action_id"] = "mutated-copy"
    assert (run, case) == before


@pytest.mark.parametrize("other_section", ["proposed_answer", "recommended_next_step", "modeling_draft"])
def test_required_study_citation_outside_findings_does_not_satisfy_coverage(other_section):
    run, case = required_studies()
    b = brief()
    b[other_section]["evidence_ids"].append("study-evidence-0")
    b["proposed_answer"]["caveat"] = "The additional cohort lacks patient-matched functional measurements."
    with pytest.raises(p.ProviderError, match="Missing finding evidence: study-evidence-0"):
        rb.validate_brief(b, rb.build_brief_context(run, case))


def test_eight_required_studies_fit_existing_concise_finding_fields():
    run, case = required_studies(8)
    b = brief()
    b["findings"] = [required_finding([item["evidence_id"]]) for item in run["required_analysis_operations"]]
    c = rb.build_brief_context(run, case)
    assert len(rb.validate_brief(b, c)["findings"]) == 8
    b["findings"][0]["what"] = "a " * 41
    with pytest.raises(p.ProviderError, match="exceeds 40 words"):
        rb.validate_brief(b, c)


def test_related_required_results_can_be_grouped_with_all_evidence_references():
    run, case = required_studies(2)
    b = brief()
    b["findings"].append(required_finding(["study-evidence-0", "study-evidence-1"]))
    assert rb.validate_brief(b, rb.build_brief_context(run, case))["findings"][-1]["evidence_ids"] == [
        "study-evidence-0", "study-evidence-1"]


def test_missing_required_finding_gets_visible_correction_before_independent_review(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    run, case = required_studies()
    before = copy.deepcopy((run, case))
    fixed = brief()
    fixed["findings"].append(required_finding(["study-evidence-0"]))
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        value = brief() if len(calls) == 1 else fixed if len(calls) == 2 else reviewed(fixed)
        return response([message(value)], len(calls))

    fake_clients(monkeypatch, handler)
    result = asyncio.run(rb.generate_research_brief(run, case))
    assert len(calls) == 3
    first_context = json.loads(calls[0]["input"][0]["content"])["accepted_context"]
    assert first_context["required_study_coverage"] == run["required_analysis_operations"]
    correction = json.loads(calls[1]["input"][0]["content"])
    assert "study-evidence-0" in correction["acceptance_feedback"]
    assert "observed result and the cohort or experimental scope" in calls[0]["instructions"]
    assert "citation attached to unrelated prose" in calls[-1]["instructions"]
    assert result["model_review"]["checks"]["required_study_results_explained"] is True
    assert result["input_versions"]["required_study_coverage_sha256"] == rb._sha(first_context["required_study_coverage"])
    assert result["provider_metadata"]["acceptance_repairs"] == 1
    assert (run, case) == before


def test_reviewer_rejects_required_citation_with_insufficient_result_explanation(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-research-brief-never-send")
    run, case = required_studies()
    b = brief()
    # Presence of a reference is mechanically valid, but not a scientific explanation.
    b["findings"][0]["evidence_ids"].append("study-evidence-0")
    review = reviewed(b)
    review["checks"]["required_study_results_explained"] = False
    review["remaining_limitations"] = ["The additional cohort result and its implication were not explained."]
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        return response([message(b if len(calls) == 1 else review)], len(calls))

    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError, match="reviewer rejected"):
        asyncio.run(rb.generate_research_brief(run, case))
    assert len(calls) == 3
