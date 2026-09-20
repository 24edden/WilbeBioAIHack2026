"""Transport-mocked contract tests. These do not establish vendor entitlement."""
import asyncio
import io
import json
import re
from pathlib import Path

import httpx
import pytest

from app import providers as p
from app.provider_schemas import Investigation


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    for key in ("OPENAI_API_KEY", "NGC_API_KEY", "NVIDIA_API_KEY", "BOLTZ2_NIM_URL", "OPENAI_BASE_URL", "ROSALIND_MODEL", "TEAM_TBD_MODEL", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID",
                "TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", "TEAM_TBD_MAX_OUTPUT_TOKENS", "TEAM_TBD_MAX_INPUT_TOKENS", "TEAM_TBD_BUDGET_MODE", "TEAM_TBD_MAX_MODEL_REQUESTS", "TEAM_TBD_MAX_TOOL_CALLS",
                "TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "TEAM_TBD_AGENT_TIMEOUT_SECONDS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ROSALIND_CAPABILITIES_FILE", str(tmp_path / "capabilities.json"))


def fake_clients(monkeypatch, handler):
    original = httpx.AsyncClient
    class MockClient(original):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)
    monkeypatch.setattr(p.httpx, "AsyncClient", MockClient)


def decision():
    return {"summary": "Evidence does not yet discriminate the hypothesis.", "assessment": "inconclusive",
            "insights": [{"title": "Evidence remains descriptive", "finding": "The source reports an observation.",
                          "why_it_matters": "It does not discriminate competing mechanisms.", "evidence_ids": ["e1"],
                          "next_step": "Compare the proposed mechanisms using matched controls."}], "followups": [],
            "claims": [{"text": "The source reports an observation.", "evidence_ids": ["e1"], "kind": "observation"}],
            "alternatives": [{"title": "Alternative mechanism", "reason": "Not distinguished by the source."}],
            "limitations": ["No patient-level inference."],
            "next_experiment": {"title": "Discriminate mechanisms", "design": "Paired controls", "positive": "Supports", "negative": "Weakens", "inconclusive": "Repeat"},
            "rd_handoff": {"objective": "Test a candidate", "status": "proposed", "reference": "Known control",
                           "candidates": [{"id": "candidate-1", "name": "Expert-supplied candidate", "rationale": "Discriminating comparison"}],
                           "modeling": {"status": "blocked", "reason": "Qualified sequences missing", "artifacts": []},
                           "experiment_id": "experiment-1", "return_requirements": ["Measured binding with units"]}}


def response(output, number=1):
    return httpx.Response(200, headers={"x-request-id": f"req_{number}"}, json={
        "id": f"resp_{number}", "object": "response", "created_at": 1, "model": p.selected_model(),
        "status": "completed", "output": output, "tools": [], "tool_choice": "auto", "parallel_tool_calls": True,
        "usage": {"input_tokens": 30, "output_tokens": 10, "total_tokens": 40,
                  "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}}})


def function(name, arguments, number):
    return {"id": f"fc_{number}", "call_id": f"call_{number}", "type": "function_call", "name": name,
            "arguments": json.dumps(arguments), "status": "completed"}


def message(value, number=1):
    return {"id": f"msg_{number}", "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": json.dumps(value), "annotations": []}]}


def small_cif(target="AC", binder="DE"):
    from Bio.PDB import Atom, Chain, Model, Residue, Structure, MMCIFIO
    from Bio.SeqUtils import seq3
    import numpy as np
    structure = Structure.Structure("test")
    model = Model.Model(0)
    structure.add(model)
    number = 1
    for chain_index, (cid, seq) in enumerate((("A", target), ("B", binder))):
        chain = Chain.Chain(cid)
        model.add(chain)
        for i, aa in enumerate(seq, 1):
            residue = Residue.Residue((" ", i, " "), seq3(aa).upper(), " ")
            chain.add(residue)
            residue.add(Atom.Atom("CA", np.array([i * 3., chain_index * 3., 0.]), 50., 1., " ", " CA ", number, "C"))
            number += 1
    writer = MMCIFIO()
    writer.set_structure(structure)
    out = io.StringIO()
    writer.save(out)
    return out.getvalue()


def test_configured_never_means_verified(monkeypatch):
    assert p.capabilities()["rosalind"]["status"] == "missing"
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert p.capabilities()["rosalind"]["status"] == "configured"
    p._save_capability("rosalind", {"status": "verified", "model": p.MODEL})
    assert p.capabilities()["rosalind"]["status"] == "verified"
    monkeypatch.setenv("OPENAI_API_KEY", "another-key")
    assert p.capabilities()["rosalind"]["status"] == "configured"


def test_exact_model_required(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("ROSALIND_MODEL", "other-model")
    with pytest.raises(p.ProviderError, match="never substitutes"):
        p.ModelSession()


def test_real_sdk_probe_roundtrip(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body["model"] == p.MODEL
        if len(calls) == 1:
            nonce = body["input"][0]["content"].split("=", 1)[1]
            return response([function("echo_evidence_id", {"evidence_id": nonce}, 1)])
        tool = next(item for item in body["input"] if item.get("type") == "function_call_output")
        observed = tool["output"]
        return response([message({"evidence_id": observed.removeprefix("observed:"), "tool_observation": observed})], 2)
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.probe("rosalind"))
    assert result["status"] == "verified", result
    assert result["typed_output"] is True
    assert result["metadata"]["returned_models"] == [p.MODEL]
    assert result["metadata"]["usage"]["input_tokens"] == 60
    assert result["metadata"]["requests"][0]["request_id"] == "req_1"
    assert result["metadata"]["trace_export"] is False


def test_probe_auth_failure_does_not_substitute_or_retry(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(403, json={"error": {"message": "Model access denied", "type": "permission_error"}})
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.probe("rosalind"))
    assert result["status"] == "failed"
    assert len(calls) == 1
    assert result["model"] == p.MODEL


def test_probe_explicit_typed_output_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            return httpx.Response(400, json={"error": {"message": "json_schema structured output is not supported", "type": "invalid_request_error"}})
        if len(calls) == 2:
            nonce = body["input"][0]["content"].split("=", 1)[1]
            return response([function("echo_evidence_id", {"evidence_id": nonce}, 2)], 2)
        observed = next(item["output"] for item in body["input"] if item.get("type") == "function_call_output")
        return response([message({"evidence_id": observed.removeprefix("observed:"), "tool_observation": observed})], 3)
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.probe("rosalind"))
    assert result["status"] == "verified", result
    assert result["typed_output"] is False
    assert {call["model"] for call in calls} == {p.MODEL}


def test_json_mode_has_one_bounded_format_repair(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return response([message({"evidence_id": "e1", "tool_observation": "observed:e1"})])
    fake_clients(monkeypatch, handler)
    async def run():
        session = p.ModelSession()
        try:
            value = await p._parse_or_repair('malformed-json', p.ProbeOutput, typed=False, model=session.model())
            return value
        finally:
            await session.close()
    result = asyncio.run(run())
    assert result.evidence_id == "e1"
    assert len(calls) == 1


def test_incomplete_model_response_is_not_accepted(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []
    def handler(request):
        calls.append(request)
        value = json.loads(response([]).content)
        value["status"] = "incomplete"
        value["incomplete_details"] = {"reason": "max_output_tokens"}
        return httpx.Response(200, json=value)
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.probe("rosalind"))
    assert result["status"] == "failed"
    assert len(calls) == 1
    assert result["metadata"]["requests"][0]["status"] == "incomplete"



def test_investigation_output_limit_retains_usage_and_stops_without_retry(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from app import followups
    monkeypatch.setattr(followups, "approved_catalog", lambda case_id: [])
    calls, events = [], []
    def handler(request):
        calls.append(request)
        value = json.loads(response([]).content)
        value["status"] = "incomplete"
        value["incomplete_details"] = {"reason": "max_output_tokens"}
        return httpx.Response(200, json=value)
    async def emit(agent, title, detail, status="completed", type="tool"):
        events.append((agent, title, detail, status, type))
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError, match="response output limit") as failure:
        asyncio.run(p.investigate({"id": "case-1"}, "Exact research hypothesis.", [{"id": "e1"}], emit, lambda: False))
    assert failure.value.status == "budget_exhausted"
    assert len(calls) == 1
    assert failure.value.metadata["usage"]["output_tokens"] == 10
    assert failure.value.metadata["requests"][0]["incomplete_details"]["reason"] == "max_output_tokens"
    assert any(event[0] == "model" and event[3] == "failed" for event in events)


def test_unexpected_returned_model_is_rejected(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []
    def handler(request):
        calls.append(request)
        value = json.loads(response([]).content)
        value["model"] = "gpt-other"
        return httpx.Response(200, json=value)
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.probe("rosalind"))
    assert result["status"] == "failed"
    assert len(calls) == 1
    assert result["metadata"]["returned_models"] == ["gpt-other"]
    assert result["metadata"]["requested_model"] == p.MODEL



def derived(evidence_id="ANALYSIS-TEST"):
    return {"id": evidence_id, "kind": "derived", "title": "Computed source QC", "summary": "Two source rows; no clinical inference.",
            "source": {"name": "Approved computation", "url": "https://example.org/data", "locator": "case/test-analysis", "sha256": "a" * 64},
            "values": {"row_count": 2, "input_sources": []}}


def specialist_brief(role, evidence_id="ANALYSIS-TEST"):
    return {"question": "What can the supplied evidence establish?", "method": "Review accepted tool results and sources.",
            "result_status": "blocked" if role == "molecular_scientist" else "inconclusive",
            "result": "Missing qualified constructs." if role == "molecular_scientist" else "Evidence scope limits causal inference.",
            "limitations": ["No patient outcome evidence."], "decision_it_could_change": "Which experiment can discriminate mechanisms.",
            "claims": [] if role == "molecular_scientist" else [{"text": "QC summarizes two rows.", "evidence_ids": [evidence_id], "kind": "observation"}]}


def team_transport(monkeypatch, *, followup=False, molecular=False, reject_first=None, discovery=False, extra_bio=0,
                   failed_read_role=None, reviewer_read_burst=0, selected_followup=False, public_structure=False,
                   restricted_recipe=False, proposal_scripts=None, governance=False, governance_followups=None, synthesis=False):
    from app import analysis_tools
    monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda case_id: [{"id": "test-analysis"}, {"id": "followup-analysis"}] +
                       ([{"id": "slow-followup", "followup_only": True}] if restricted_recipe else []))
    monkeypatch.setattr(analysis_tools, "analyze_case", lambda case_id, analysis_id: derived("ANALYSIS-REVIEW" if analysis_id == "followup-analysis" else "ANALYSIS-TEST"))
    calls, events, persisted, products = [], [], [], []
    plans = {
        "bioinformatician": [("analysis_catalog", {}), ("run_case_analysis", {"analysis_id": "test-analysis"})],
        "statistician": [("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]})],
        "clinical_scientist": [("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]})],
        "clinical_pharmacologist": [],
        "molecular_scientist": [("qualify_molecular_inputs", {})],
        "translational_scientist": [("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]})],
        "assay_scientist": [],
        "coordinator": [("get_case_readiness", {}), ("read_evidence", {"evidence_ids": ["e1", "ANALYSIS-TEST"]})],
        "reviewer": [("get_case_readiness", {}), ("read_evidence", {"evidence_ids": ["e1", "ANALYSIS-TEST"]})],
    }
    if synthesis:
        for role in ("coordinator", "reviewer"):
            plans[role] = [("get_case_readiness", {}), ("read_evidence", {"evidence_ids": ["e1"]})]
    if discovery:
        from app import data_catalog
        monkeypatch.setattr(data_catalog, "list_datasets", lambda: {"datasets": [{"id": "study-a", "title": "Registered source study", "files_count": 2}]})
        monkeypatch.setattr(data_catalog, "get_dataset", lambda dataset_id: {"id": dataset_id, "files": [{"id": "file-a"}, {"id": "file-b"}]})
        monkeypatch.setattr(data_catalog, "inspect_data_file", lambda file_id: {"id": file_id, "status": "available", "columns": ["sample", "value"]})
        monkeypatch.setattr(data_catalog, "analyze_data_file", lambda file_id, kind, params: derived("ANALYSIS-REVIEW" if file_id == "file-b" else "ANALYSIS-TEST"))
        plans["bioinformatician"] = [("list_datasets", {}), ("get_dataset", {"dataset_id": "study-a"}),
            ("inspect_data_file", {"file_id": "file-a"}), ("analyze_data_file", {"file_id": "file-a", "analysis_kind": "table_profile", "parameters_json": "{}"})]
        plans["bioinformatician"] += [("analyze_data_file", {"file_id": "file-extra-"+str(i), "analysis_kind": "table_profile", "parameters_json": "{}"}) for i in range(abs(extra_bio))]
    if followup:
        if discovery:
            plans["reviewer"] += [("request_data_followup", {"file_id": "file-b", "analysis_kind": "table_profile", "parameters_json": "{}", "gap": "Check independent source schema and missingness before joining cohorts."})]
        else:
            plans["reviewer"] += [("analysis_catalog", {}), ("request_followup_analysis", {"analysis_id": "followup-analysis", "gap": "A source exclusion diagnostic could change the experiment choice."})]
    if molecular:
        plans["molecular_scientist"].append(("request_molecular_comparison", {"rationale": "Exact inputs can test a structural discriminator."}))
    if selected_followup:
        plans["bioinformatician"] = [("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]})]
    if public_structure:
        plans["molecular_scientist"].append(("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]}))
    if restricted_recipe:
        plans["bioinformatician"].insert(1, ("run_case_analysis", {"analysis_id": "slow-followup"}))
        plans["reviewer"].append(("request_followup_analysis", {"analysis_id": "slow-followup", "gap": "Check the full model as a separate explicit follow-up."}))
    for role, proposals in (proposal_scripts or {}).items():
        plans[role] += [("list_available_followups", {})]
        plans[role] += [("propose_followup", arguments) for arguments in proposals]
    if failed_read_role:
        plans[failed_read_role] = [(name, {"evidence_ids": ["unaccepted-evidence"]} if name == "read_evidence" else arguments)
                                   for name, arguments in plans[failed_read_role]]
    if reviewer_read_burst:
        plans["reviewer"] += [("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]})] * reviewer_read_burst
    async def emit(*args, **kwargs):
        events.append((args, kwargs))
    async def accept(record):
        persisted.append(record)
        return record
    async def handoff(product):
        if product["sender"] == reject_first and not any(x.get("rejected") for x in products):
            products.append({"rejected": True, "submitted": json.loads(json.dumps(product))})
            return {"accepted": False, "reason": "Clarify assay scope."}
        products.append(product)
        return {"accepted": True, "id": f"durable-{len(products)}"}
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body["model"] == "gpt-6-astra"
        assert body["reasoning"]["effort"] == "high"
        role = re.search(r"ROLE: ([a-z_]+)\.", body["instructions"]).group(1)
        outputs = [item for item in body["input"] if item.get("type") == "function_call_output"]
        repairing = not body.get("tools")
        if extra_bio > 0 and role == "bioinformatician" and not outputs:
            return response([function(name, arguments, 100+i) for i, (name, arguments) in enumerate(plans[role])], len(calls))
        if reviewer_read_burst and role == "reviewer" and not outputs:
            return response([function(name, arguments, 200+i) for i, (name, arguments) in enumerate(plans[role])], len(calls))
        if not repairing and proposal_scripts and role in proposal_scripts and len(outputs) < len(plans[role]) and plans[role][len(outputs)][0] == "list_available_followups":
            # Common planning tools can be requested together. This also tests
            # duplicate proposals under normal SDK parallel tool dispatch.
            remaining = plans[role][len(outputs):]
            return response([function(name, arguments, 10000 + len(calls) * 10 + i)
                             for i, (name, arguments) in enumerate(remaining)], len(calls))
        if not repairing and len(outputs) < len(plans[role]):
            name, arguments = plans[role][len(outputs)]
            return response([function(name, arguments, len(calls))], len(calls))
        if role in {"coordinator", "reviewer"}:
            value = decision()
            if governance:
                ledger = governance(role) if callable(governance) else governance
                value["governance"] = json.loads(json.dumps(ledger))
            if governance_followups is not None:
                value["followups"] = json.loads(json.dumps(governance_followups))
            if restricted_recipe:
                value["followups"] = [{"kind": "data_analysis", "analysis_id": "slow-followup", "title": "Fit the optional full model",
                    "rationale": "The full model could test a remaining sensitivity question.", "decision_it_could_change": "Whether the observed contrast is robust.",
                    "prerequisites": ["Explicit follow-up selection"], "evidence_ids": ["e1"], "status": "ready"}]
            if role == "reviewer" and followup:
                assert "ANALYSIS-REVIEW" in [e["id"] for e in persisted]
                value["claims"].append({"text": "The review diagnostic is now available.", "evidence_ids": ["ANALYSIS-REVIEW"], "kind": "observation"})
        else:
            value = specialist_brief(role)
            if role == "molecular_scientist" and molecular:
                value.update(result_status="inconclusive", result="A molecular comparison returned; structural results remain predictions.")
            if role == "molecular_scientist" and public_structure:
                value.update(result_status="inconclusive", result="Public monomer predictions are available; CAR binding remains untested.",
                             claims=[{"text": "These public monomer predictions do not establish binding.", "evidence_ids": ["ANALYSIS-TEST"], "kind": "prediction"}])
        return response([message(value, len(calls))], len(calls))
    fake_clients(monkeypatch, handler)
    return calls, events, persisted, products, emit, accept, handoff


def governance_evidence():
    return {"id": "e1", "kind": "measured", "title": "Qualified source observation",
            "summary": "The observed assay does not distinguish the proposed mechanisms.",
            "source": {"name": "Public assay", "url": "https://example.org/assay",
                       "locator": "assay/control", "sha256": "b" * 64}, "values": {}}


def possible_governance(*, alternative=False):
    item = {"hypothesis_id": "primary", "statement": "Antigen change explains resistance.",
            "origin": "user", "source_quote": "", "scope": "The measured reporter assay; no patient attribution.",
            "scope_type": "biological", "status": "possible",
            "rationale": "Accepted measurements remain compatible with multiple mechanisms and do not establish recognition loss.",
            "supporting_evidence_ids": ["e1"], "contradicting_evidence_ids": [], "test_evidence_ids": [],
            "falsification_test": "", "falsification_result": "", "next_analysis_ids": [],
            "blocker": "Matched surface recognition measurements are absent; available source QC cannot distinguish this mechanism."}
    hypotheses = [item]
    if alternative:
        hypotheses.append({**item, "hypothesis_id": "exposure_alternative",
            "statement": "An exposure defect may coexist.", "source_quote": "An exposure defect may coexist.",
            "scope": "The supplied experimental exposure window.",
            "rationale": "The accepted records do not measure exposure over the relevant response window.",
            "blocker": "No qualified dose, concentration and sampling-time record is available for the exposure contrast."})
    return {"hypotheses": hypotheses, "next_action_id": None, "target_hypothesis_ids": [],
            "continuation_reason": "Matched recognition and exposure measurements are absent; further source QC cannot distinguish these explanations.",
            "stop_reason": "needs_data"}


def test_new_governance_policy_rejects_missing_ledger_after_one_sdk_repair(monkeypatch):
    from app.process_contract import get_process_contract
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_MODEL", "gpt-6-astra")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch)
    case = {"id": "case-1", "process_contract": get_process_contract(), "source_manifest": []}
    with pytest.raises(p.ProviderError, match="hypothesis ledger.*required") as failure:
        asyncio.run(p.investigate(case, "Antigen change explains resistance.", [governance_evidence()],
            emit, lambda: False, accept_evidence=accept, accept_handoff=handoff))
    coordinator = [call for call in calls if "ROLE: coordinator." in call["instructions"]]
    assert len(coordinator) == 4  # Readiness, evidence read, invalid output, one tools-disabled repair.
    assert not coordinator[-1].get("tools")
    assert "hypothesis ledger" in json.dumps(coordinator[-1]["input"])
    assert not any("ROLE: reviewer." in call["instructions"] for call in calls)
    assert not any(product.get("sender") == "coordinator" for product in products)
    assert [record["id"] for record in persisted] == ["ANALYSIS-TEST"]
    assert failure.value.metadata["dispatched_requests"] == len(calls)
    assert sum(event[0][1] == "Coordinator work product returned for one repair" for event in events) == 1


def test_new_governance_policy_preserves_possible_ledger_through_sdk_review(monkeypatch):
    from app.process_contract import get_process_contract
    from app.scientific_skills import load_skill
    from app.store import digest
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_MODEL", "gpt-6-astra")
    ledger = possible_governance()
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, governance=ledger)
    case = {"id": "case-1", "process_contract": get_process_contract(), "source_manifest": []}
    hypothesis = "Antigen change explains resistance."
    result = asyncio.run(p.investigate(case, hypothesis, [governance_evidence()], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    final = result["governance"]
    assert final["hypotheses"] == ledger["hypotheses"]
    assert final["hypotheses"][0]["status"] == "possible"
    assert final["stop_reason"] == "needs_data" and final["next_action_id"] is None
    assert final["hypothesis_sha256"] == digest(hypothesis)
    assert final["accepted_evidence_versions"] == {"e1": "b" * 64, "ANALYSIS-TEST": "a" * 64}
    assert result["metadata"]["reviewer_completed"] is True
    assert len(products) == 9
    for role in ("coordinator", "reviewer"):
        role_calls = [call for call in calls if f"ROLE: {role}." in call["instructions"]]
        assert len(role_calls) == 3
        payload = json.loads(role_calls[0]["input"][0]["content"])
        assert payload["hypothesis_governance"]["policy"] == case["process_contract"]["hypothesis_governance"]
        assert payload["hypothesis_governance"]["previous_governance"] is None
        skill = load_skill("discovery-planning", role)
        assert skill["instructions"] in role_calls[0]["instructions"]
        product = next(product for product in products if product.get("sender") == role)
        assert product["skill_versions"]["discovery-planning"] == {"version": skill["version"], "sha256": skill["sha256"]}
    assert not any("returned for one repair" in event[0][1] for event in events)


@pytest.mark.parametrize("retain_alternative", [True, False])
def test_sdk_governance_carries_previous_ledger_and_rejects_forgotten_ids(monkeypatch, retain_alternative):
    from app.followups import approved_catalog
    from app.hypothesis_governance import validate_governance
    from app.process_contract import get_process_contract
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_MODEL", "gpt-6-astra")
    current = possible_governance(alternative=retain_alternative)
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, selected_followup=True, governance=current)
    hypothesis = "Antigen change explains resistance. An exposure defect may coexist."
    evidence = [governance_evidence(), derived()]
    case = {"id": "case-1", "process_contract": get_process_contract(), "source_manifest": [],
            "exposure_data": {"source": "Qualified timing supplied for scoped review; no modeled exposure claim."}}
    previous = validate_governance(possible_governance(alternative=True), hypothesis=hypothesis,
        evidence=evidence, recipes=approved_catalog(case["id"]), followups=[], case=case)
    previous_snapshot = json.loads(json.dumps(previous))
    case["followup_context"] = {"execution_status": "completed", "origin": "agent_governance",
        "evidence_ids": ["ANALYSIS-TEST"], "recommendation": {"analysis_id": "test-analysis"},
        "previous_decision": {"version": 1, "summary": "Both explanations remain unresolved.", "governance": previous}}
    if retain_alternative:
        result = asyncio.run(p.investigate(case, hypothesis, evidence, emit, lambda: False,
            accept_evidence=accept, accept_handoff=handoff))
        assert {item["hypothesis_id"] for item in result["governance"]["hypotheses"]} == {"primary", "exposure_alternative"}
        assert len(products) == 9
        assert {product["sender"] for product in products if product["model_called"]} == set(result["metadata"]["roles"])
    else:
        with pytest.raises(p.ProviderError, match="silently dropped"):
            asyncio.run(p.investigate(case, hypothesis, evidence, emit, lambda: False,
                accept_evidence=accept, accept_handoff=handoff))
        coordinator = [call for call in calls if "ROLE: coordinator." in call["instructions"]]
        assert len(coordinator) == 4 and not coordinator[-1].get("tools")
        assert not any("ROLE: reviewer." in call["instructions"] for call in calls)
    seen = set()
    for call in calls:
        role = re.search(r"ROLE: ([a-z_]+)\.", call["instructions"]).group(1)
        if role in seen:
            continue
        seen.add(role)
        payload = json.loads(call["input"][0]["content"])
        assert payload["hypothesis_governance"]["previous_governance"] == previous_snapshot
        assert payload["followup_context"]["origin"] == "agent_governance"
        if role == "bioinformatician":
            assert "A reviewer-selected autonomous registered follow-up" in call["instructions"]
    if retain_alternative:
        assert seen == set(result["metadata"]["roles"])
    assert previous == previous_snapshot
    assert persisted == []  # Completed follow-up evidence is consumed without running the recipe again.


def test_sdk_governance_selects_registered_unperformed_genome_followup_without_executing(monkeypatch):
    from app import analysis_tools
    from app.process_contract import get_process_contract
    from app.store import digest
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_MODEL", "gpt-6-astra")
    genome_recipe = {"id": "genome-contrast-prototype", "title": "Compare qualified genome feature counts",
        "followup_only": True, "description": "A synthetic registered recipe used only by this transport test.",
        "prerequisites": ["Pinned genome feature table and qualified sample pairing"],
        "input_sources": [{"path": "sources/genome-features.tsv", "sha256": "d" * 64}]}
    ledger = possible_governance()
    ledger["hypotheses"][0].update(next_analysis_ids=[genome_recipe["id"]], blocker="")
    ledger.update(next_action_id=genome_recipe["id"], target_hypothesis_ids=["primary"], stop_reason="continue",
        continuation_reason="A paired feature contrast can distinguish stable from changed target measurements; failed pairing QC remains inconclusive.")
    recommendation = {"kind": "data_analysis", "analysis_id": genome_recipe["id"], "title": genome_recipe["title"],
        "rationale": "Compare paired target features with control features using the qualified table; changed versus stable measurements alter the next experimental contrast.",
        "decision_it_could_change": "Whether target change remains the next mechanism to test.",
        "prerequisites": genome_recipe["prerequisites"], "evidence_ids": ["e1"], "status": "ready"}
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, governance=ledger, governance_followups=[recommendation])
    monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda case_id: [{"id": "test-analysis"}, genome_recipe])
    executed = []
    def analysis(case_id, analysis_id):
        executed.append(analysis_id)
        assert analysis_id == "test-analysis", "The SDK must recommend, not execute, the follow-up-only genome recipe."
        record = derived()
        record["values"]["analysis_id"] = analysis_id
        return record
    monkeypatch.setattr(analysis_tools, "analyze_case", analysis)
    case = {"id": "case-1", "process_contract": get_process_contract(),
            "source_manifest": genome_recipe["input_sources"]}
    result = asyncio.run(p.investigate(case, "Antigen change explains resistance.", [governance_evidence()],
        emit, lambda: False, accept_evidence=accept, accept_handoff=handoff))
    assert result["governance"]["stop_reason"] == "continue"
    assert result["governance"]["next_action_id"] == genome_recipe["id"]
    assert result["governance"]["target_hypothesis_ids"] == ["primary"]
    assert result["followups"] == [recommendation]
    registered = {**genome_recipe, "kind": "data_analysis"}
    assert result["governance"]["recipe_versions"] == {genome_recipe["id"]: digest(registered)}
    assert executed == ["test-analysis"]
    assert [record["id"] for record in persisted] == ["ANALYSIS-TEST"]
    for role in ("coordinator", "reviewer"):
        call = next(call for call in calls if f"ROLE: {role}." in call["instructions"])
        payload = json.loads(call["input"][0]["content"])
        option = next(option for option in payload["available_followup_options"] if option["id"] == genome_recipe["id"])
        assert option["readiness"] == "unperformed"
        assert option["input_sources"] == genome_recipe["input_sources"]


def test_selected_followup_runs_team_and_reviewer_without_repeating_recipe(monkeypatch):
    from app.scientific_skills import load_skill
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, selected_followup=True)
    previous = {"version": 1, "summary": "Earlier unresolved assessment.",
                "alternatives": [{"title": "User alternative: source change", "reason": "Measured in a restricted assay."},
                                 {"title": "User alternative: response defect", "reason": "Not tested by the supplied assay."}],
                "next_experiment": {"title": "Cross source and response conditions", "design": "Measure both branches against qualified controls.",
                                    "positive": "Source-dependent effect", "negative": "Response-dependent effect", "inconclusive": "Unqualified controls"},
                "rd_handoff": {"objective": "Discriminate source change from response defect."}}
    context = {"execution_status": "completed", "evidence_ids": ["ANALYSIS-TEST"],
               "recommendation": {"analysis_id": "test-analysis"}, "previous_decision": previous}
    result = asyncio.run(p.investigate({"id": "case-1", "followup_context": context}, "My exact hypothesis.",
        [{"id": "e1"}, derived()], emit, lambda: False, accept_evidence=accept, accept_handoff=handoff))
    assert result["metadata"]["reviewer_completed"] is True
    assert len(products) == 9
    assert persisted == []  # The selected action was already durably accepted by the worker.
    bio = next(call for call in calls if "ROLE: bioinformatician." in call["instructions"])
    assert "user-selected registered follow-up" in bio["instructions"]
    assert "ANALYSIS-TEST" in json.dumps(bio["input"])
    # Parent objective, alternatives and experiment remain available to every stage
    # responsible for follow-up synthesis; a narrow result must not lose this context.
    for role in ("translational_scientist", "assay_scientist", "coordinator", "reviewer"):
        call = next(call for call in calls if f"ROLE: {role}." in call["instructions"])
        payload = json.loads(call["input"][0]["content"])
        assert payload["followup_context"] == context
        skill = load_skill(role, role)
        assert skill["instructions"] in call["instructions"]
        product = next(product for product in products if product.get("sender") == role)
        assert product["skill_versions"][role] == {"version": skill["version"], "sha256": skill["sha256"]}


def test_public_structural_followup_review_does_not_require_binder_attestation(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, selected_followup=True, public_structure=True)
    evidence = derived()
    evidence["values"] = {"structural_recipe_id": "cd19-exon2-structure", "scope": "exploratory_public_isoform_structure"}
    result = asyncio.run(p.investigate({"id": "case-1", "followup_context": {"evidence_ids": ["ANALYSIS-TEST"]}},
        "My exact hypothesis.", [{"id": "e1"}, evidence], emit, lambda: False, accept_evidence=accept, accept_handoff=handoff))
    molecular = next(product for product in products if product.get("sender") == "molecular_scientist")
    assert molecular["result_status"] == "inconclusive"
    assert molecular["claims"][0]["evidence_ids"] == ["ANALYSIS-TEST"]
    assert result["rd_handoff"]["modeling"]["status"] == "blocked"


def test_followup_only_recipes_cannot_execute_in_initial_or_reviewer_tools(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, restricted_recipe=True)
    result = asyncio.run(p.investigate({"id": "case-1"}, "My exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
                                     accept_evidence=accept, accept_handoff=handoff))
    assert result["metadata"]["reviewer_completed"] is True
    assert len(persisted) == 1
    assert [event[0][2] for event in events if event[0][1] == "Executing source-data analysis"] == ["test-analysis"]
    for role in ("bioinformatician", "reviewer"):
        final_call = [call for call in calls if f"ROLE: {role}." in call["instructions"]][-1]
        outputs = [item["output"] for item in final_call["input"] if item.get("type") == "function_call_output"]
        assert any("requires an explicit Run follow-up action" in output for output in outputs)
    bio = [call for call in calls if "ROLE: bioinformatician." in call["instructions"]][-1]
    catalogs = [json.loads(item["output"]) for item in bio["input"] if item.get("type") == "function_call_output" and item["output"].startswith("[")]
    assert catalogs and all("slow-followup" not in {entry["id"] for entry in catalog} for catalog in catalogs)
    # Recommendation/action registry remains complete; the model may recommend the explicit action.
    assert result["followups"][0]["analysis_id"] == "slow-followup"
    from app.followups import approved_catalog
    assert next(item for item in approved_catalog("case-1") if item["id"] == "slow-followup")["followup_only"] is True


def test_investigation_uses_scoped_team_and_durable_analysis(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, followup=True)
    evidence = [{"id": "e1", "title": "Approved source", "url": "https://example.org/paper", "summary": "Observation", "source": {"sha256": "b" * 64}}]
    result = asyncio.run(p.investigate({"id": "case-1"}, "My exact hypothesis.", evidence, emit, lambda: False,
                                      accept_evidence=accept, accept_handoff=handoff))
    assert 7 < len(calls) <= p.MAX_REQUESTS
    assert result["metadata"]["reviewer_completed"] is True
    assert len(result["metadata"]["work_products"]) == 9
    assert len(persisted) == 2
    assert result["metadata"]["accepted_analysis_ids"] == ["ANALYSIS-TEST", "ANALYSIS-REVIEW"]
    assert result["metadata"]["review_cycles"][0]["evidence_id"] == "ANALYSIS-REVIEW"
    assert result["claims"][0]["sources"][0]["url"] == "https://example.org/paper"
    by_role = {x["sender"]: x for x in products}
    assert by_role["clinical_scientist"]["model_called"] is True
    assert by_role["clinical_pharmacologist"]["model_called"] is False
    assert by_role["statistician"]["input_versions"]["upstream_handoff_ids"] == ["durable-1"]
    assert by_role["statistician"]["input_versions"]["evidence_versions"]["ANALYSIS-TEST"] == "a" * 64
    assert any(event[0][1] == "Reviewer requested reanalysis" for event in events)
    assert any(event[1]["type"] == "handoff" for event in events)


@pytest.mark.parametrize("mode", ["advisory", "enforced"])
def test_shared_tool_threshold_warns_or_stops_parallel_overrun_by_mode(monkeypatch, mode):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_BUDGET_MODE", mode)
    monkeypatch.setenv("TEAM_TBD_MAX_TOOL_CALLS", "60")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, reviewer_read_burst=70)
    result = asyncio.run(p.investigate({"id": "case-1"}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    assert result["metadata"]["budgets"]["tool_calls"] == 60
    assert result["metadata"]["reviewer_completed"] is True
    reviewer_calls = [call for call in calls if "ROLE: reviewer." in call["instructions"]]
    outputs = [item for item in reviewer_calls[-1]["input"] if item.get("type") == "function_call_output"]
    blocked = [item for item in outputs if "Scoped tool-call budget exhausted" in item["output"]]
    if mode == "enforced":
        assert result["metadata"]["tool_calls"] == 60
        assert blocked  # Calls beyond 60 return an explicit error and do not read evidence.
    else:
        assert result["metadata"]["tool_calls"] > 60
        assert not blocked
        assert [alert["category"] for alert in result["metadata"]["budget_alerts"]] == ["tool_calls"]
        assert sum(event[1].get("type") == "budget" and event[1].get("status") == "warning" for event in events) == 1
    actual_review_reads = sum(event[0][0] == "reviewer" and event[0][1] == "Read source evidence" for event in events)
    assert actual_review_reads == len(outputs) - len(blocked) - 1  # One completed readiness tool.


def test_molecular_specialist_uses_trusted_inputs_and_executor(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, molecular=True)
    proposals = []
    async def molecular(proposal):
        proposals.append(proposal)
        return {"status": "completed", "action_id": "durable-boltz", "evidence": [derived("PREDICTION-TEST")], "artifacts": []}
    inputs = {"target_sequence": "AC", "reference_binder": "DE", "candidate_binder": "DF", "source_note": "Scientist-qualified exact experimental constructs", "target_retained": True}
    result = asyncio.run(p.investigate({"id": "case-1", "molecular_inputs": inputs}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff, request_molecular=molecular))
    assert len(proposals) == 1
    assert proposals[0]["inputs"] == inputs
    assert proposals[0]["input_hashes"]["target_sequence"] == p._sha("AC")
    assert "PREDICTION-TEST" in [x["id"] for x in persisted]
    assert result["rd_handoff"]["modeling"]["status"] == "blocked"  # executor attaches artifacts outside model output
    assert result["metadata"]["molecular_receipts"][0]["action_id"] == "durable-boltz"


def test_rejected_work_product_gets_one_bounded_repair(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, reject_first="assay_scientist")
    result = asyncio.run(p.investigate({"id": "case-1"}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    assert len(result["metadata"]["work_products"]) == 9
    assert sum("ROLE: assay_scientist." in c["instructions"] for c in calls) == 2
    assert any(event[0][1] == "Work product returned for one repair" for event in events)


def test_rejected_coordinator_handoff_gets_one_tools_disabled_repair(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, reject_first="coordinator")
    result = asyncio.run(p.investigate({"id": "case-1"}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    coordinator_calls = [c for c in calls if "ROLE: coordinator." in c["instructions"]]
    assert len(coordinator_calls) == 4  # Two required tools, initial output, one repair.
    assert not coordinator_calls[-1].get("tools")
    assert "Clarify assay scope." in json.dumps(coordinator_calls[-1]["input"])
    assert len([product for product in products if product.get("sender") == "coordinator"]) == 1
    assert result["metadata"]["reviewer_completed"] is True
    assert any(event[0][1] == "Coordinator work product returned for one repair" for event in events)


def test_coordinator_stops_after_repair_rejection(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch)
    rejections = []

    async def reject_coordinator(product):
        if product["sender"] == "coordinator":
            rejections.append(product)
            return {"accepted": False, "reason": "Unresolved scope error."}
        return await handoff(product)

    with pytest.raises(p.ProviderError, match="Unresolved scope error"):
        asyncio.run(p.investigate({"id": "case-1"}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
            accept_evidence=accept, accept_handoff=reject_coordinator))
    assert len(rejections) == 2
    assert not any("ROLE: reviewer." in call["instructions"] for call in calls)


@pytest.mark.parametrize("role", ["statistician", "coordinator", "reviewer"])
def test_failed_evidence_read_does_not_satisfy_required_tool_gate(monkeypatch, role):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, failed_read_role=role)
    with pytest.raises(p.ProviderError, match="[Rr]equired.*tools|omitted required evidence tools") as failure:
        asyncio.run(p.investigate({"id": "case-1"}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
            accept_evidence=accept, accept_handoff=handoff))
    assert failure.value.metadata["tool_calls"] >= 3  # Failed attempts still consume capacity.
    assert not any(product.get("sender") == role for product in products)
    assert not any(event[0][0] == role and event[0][1] == "Read source evidence" for event in events)


@pytest.mark.parametrize("name,value", [
    ("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "2047"),
    ("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "64001"),
    ("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "8000.0"),
    ("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", ""),
    ("TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", "8191"),
    ("TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", "128001"),
    ("TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", "24000.0"),
    ("TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", ""),
    ("TEAM_TBD_MAX_OUTPUT_TOKENS", "15999"),
    ("TEAM_TBD_MAX_OUTPUT_TOKENS", "2000001"),
    ("TEAM_TBD_MAX_OUTPUT_TOKENS", "unlimited"),
    ("TEAM_TBD_MAX_INPUT_TOKENS", "49999"),
    ("TEAM_TBD_MAX_INPUT_TOKENS", "10000001"),
    ("TEAM_TBD_MAX_INPUT_TOKENS", "400000.0"),
    ("TEAM_TBD_MAX_INPUT_TOKENS", ""),
    ("TEAM_TBD_MAX_MODEL_REQUESTS", "0"),
    ("TEAM_TBD_MAX_MODEL_REQUESTS", "1001"),
    ("TEAM_TBD_MAX_MODEL_REQUESTS", "120.0"),
    ("TEAM_TBD_MAX_TOOL_CALLS", "0"),
    ("TEAM_TBD_MAX_TOOL_CALLS", "2001"),
    ("TEAM_TBD_MAX_TOOL_CALLS", "unlimited"),
])
def test_invalid_token_budget_configuration_fails_before_dispatch(monkeypatch, name, value):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv(name, value)
    with pytest.raises(p.ProviderError, match=name + " must be an integer"):
        p.ModelSession()


def test_configured_agent_output_allowance_applies_to_all_roles_and_repairs(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "10240")
    monkeypatch.setenv("TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", "28672")
    monkeypatch.setenv("TEAM_TBD_MAX_OUTPUT_TOKENS", "80000")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, reject_first="coordinator")
    result = asyncio.run(p.investigate({"id": "case-1"}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    for call in calls:
        role = re.search(r"ROLE: ([a-z_]+)\.", call["instructions"]).group(1)
        assert call["max_output_tokens"] == (28672 if role in {"coordinator", "reviewer"} else 10240)
    assert any("ROLE: coordinator." in call["instructions"] and not call.get("tools") for call in calls)
    assert {re.search(r"ROLE: ([a-z_]+)\.", call["instructions"]).group(1) for call in calls} == {
        "bioinformatician", "statistician", "clinical_scientist", "molecular_scientist",
        "translational_scientist", "assay_scientist", "coordinator", "reviewer"}
    assert result["metadata"]["budgets"]["agent_max_output_tokens"] == 10240
    assert result["metadata"]["budgets"]["synthesis_max_output_tokens"] == 28672
    assert result["metadata"]["budgets"]["total_output_tokens"] == 80000


def test_larger_defaults_reach_real_sdk_for_all_scientific_roles(monkeypatch):
    from app.scientific_skills import load_skill
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, reject_first="coordinator")
    result = asyncio.run(p.investigate({"id": "case-1"}, "The exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    for call in calls:
        role = re.search(r"ROLE: ([a-z_]+)\.", call["instructions"]).group(1)
        assert call["max_output_tokens"] == (48000 if role in {"coordinator", "reviewer"} else 24000)
        assert call["reasoning"]["effort"] == "high"
        assert call["model"] == "gpt-6-astra"
        workflow = load_skill("rosalind-informed-workflow", role)
        assert workflow["instructions"] in call["instructions"]
    assert any("ROLE: coordinator." in call["instructions"] and not call.get("tools") for call in calls)
    assert result["metadata"]["budgets"]["observed_input_tokens"] == 2000000
    assert result["metadata"]["budgets"]["total_output_tokens"] == 300000
    for product in products:
        if product.get("model_called"):
            workflow = load_skill("rosalind-informed-workflow", product["sender"])
            assert product["skill_versions"]["rosalind-informed-workflow"] == {
                "version": workflow["version"], "sha256": workflow["sha256"]}


def test_larger_allowance_upper_bounds_stay_within_documented_astra_output_limit(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "64000")
    monkeypatch.setenv("TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", "128000")
    session = p.ModelSession()
    assert session.output_allowance("bioinformatician") == 64000
    assert session.output_allowance("reviewer") == 128000
    assert p._model_settings(session.model_id, session.output_allowance("reviewer")).reasoning.effort == "high"


def test_request_and_tool_threshold_overrides_are_pinned_and_advisory(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_MAX_MODEL_REQUESTS", "2")
    monkeypatch.setenv("TEAM_TBD_MAX_TOOL_CALLS", "3")
    session = p.ModelSession()
    monkeypatch.setenv("TEAM_TBD_MAX_MODEL_REQUESTS", "25")
    monkeypatch.setenv("TEAM_TBD_MAX_TOOL_CALLS", "50")
    async def exercise():
        for _ in range(3):
            await session.before_request(httpx.Request("POST", "https://api.openai.com/v1/responses", json={
                "model": p.MODEL, "max_output_tokens": 24000}))
        await session.budget_threshold("tool_calls", 3, session.limits["tool_calls"], "Tool threshold reached")
    asyncio.run(exercise())
    assert session.dispatched == 3
    assert session.metadata()["budgets"]["model_requests"] == 2
    assert session.metadata()["budgets"]["tool_calls"] == 3
    assert {item["category"] for item in session.budget_alerts} == {"model_requests", "tool_calls"}


def test_output_allowance_defaults_and_total_reservation(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_BUDGET_MODE", "enforced")
    session = p.ModelSession()
    assert session.agent_max_output_tokens == 24000
    assert session.max_output_tokens == 300000
    session.output_tokens = 276001
    request = httpx.Request("POST", "https://api.openai.com/v1/responses", json={
        "model": "gpt-6-astra", "max_output_tokens": 24000})
    with pytest.raises(p.ProviderError, match="Insufficient remaining output-token budget") as failure:
        asyncio.run(session.before_request(request))
    assert failure.value.status == "budget_exhausted"
    assert session.dispatched == 0
    assert session.records == []


def test_request_cannot_exceed_configured_agent_allowance(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "4096")
    session = p.ModelSession()
    request = httpx.Request("POST", "https://api.openai.com/v1/responses", json={
        "model": "gpt-6-astra", "max_output_tokens": 4097})
    with pytest.raises(p.ProviderError, match="within the configured agent limit"):
        asyncio.run(session.before_request(request))
    assert session.dispatched == 0


def test_effective_model_limits_are_nonsecret_and_session_snapshot_is_stable(monkeypatch):
    assert p.effective_model_limits() == {
        "budget_mode": "advisory",
        "model_request_timeout_seconds": 600, "agent_timeout_seconds": 1800,
        "agent_max_output_tokens": 24000, "synthesis_max_output_tokens": 48000, "total_output_tokens": 300000,
        "observed_input_tokens": 2000000, "model_requests": 120, "tool_calls": 180}
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    session = p.ModelSession()
    monkeypatch.setenv("TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "12000")
    monkeypatch.setenv("TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS", "28000")
    monkeypatch.setenv("TEAM_TBD_MAX_INPUT_TOKENS", "650000")
    monkeypatch.setenv("TEAM_TBD_BUDGET_MODE", "enforced")
    assert p.effective_model_limits()["agent_max_output_tokens"] == 12000
    assert p.effective_model_limits()["synthesis_max_output_tokens"] == 28000
    assert session.output_allowance("coordinator") == 48000
    assert session.output_allowance("reviewer") == 48000
    assert session.output_allowance("statistician") == 24000
    assert p.effective_model_limits()["observed_input_tokens"] == 650000
    assert session.metadata()["budgets"]["agent_max_output_tokens"] == 24000
    assert session.metadata()["budgets"]["observed_input_tokens"] == 2000000
    assert session.metadata()["budgets"]["budget_mode"] == "advisory"


def test_configured_observed_input_limit_stops_next_dispatch(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_BUDGET_MODE", "enforced")
    monkeypatch.setenv("TEAM_TBD_MAX_INPUT_TOKENS", "50000")
    session = p.ModelSession()
    session.input_tokens = 50000
    # Changing the operator setting cannot change the budget of an active session.
    monkeypatch.setenv("TEAM_TBD_MAX_INPUT_TOKENS", "1000000")
    request = httpx.Request("POST", "https://api.openai.com/v1/responses", json={
        "model": "gpt-6-astra", "max_output_tokens": 8000})
    with pytest.raises(p.ProviderError, match="budget exhausted") as failure:
        asyncio.run(session.before_request(request))
    assert failure.value.status == "budget_exhausted"
    assert failure.value.metadata["budgets"]["observed_input_tokens"] == 50000
    assert session.dispatched == 0


def test_reviewer_request_capacity_extends_to_one_hundred_twenty_calls(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_BUDGET_MODE", "enforced")
    session = p.ModelSession()
    session.dispatched = 119
    session.input_tokens = 197834  # Actual broad-run usage that exceeded the prior limit.
    request = httpx.Request("POST", "https://api.openai.com/v1/responses", json={
        "model": "gpt-6-astra", "max_output_tokens": 8000})
    asyncio.run(session.before_request(request))
    assert session.dispatched == 120
    with pytest.raises(p.ProviderError, match="budget exhausted"):
        asyncio.run(session.before_request(request))
    assert len(session.records) == 1


def test_invalid_budget_mode_fails_before_dispatch(monkeypatch):
    monkeypatch.setenv("TEAM_TBD_BUDGET_MODE", "automatic")
    with pytest.raises(p.ProviderError, match="TEAM_TBD_BUDGET_MODE must be advisory or enforced"):
        p.effective_model_limits()


def test_advisory_thresholds_allow_requests_and_emit_one_warning_per_category(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    events = []
    async def emit(*args, **kwargs):
        events.append((args, kwargs))
    session = p.ModelSession(emit)
    session.input_tokens, session.output_tokens, session.dispatched = 2050000, 305000, 120
    async def dispatch_twice():
        for _ in range(2):
            await session.before_request(httpx.Request("POST", "https://api.openai.com/v1/responses", json={
                "model": "gpt-6-astra", "max_output_tokens": 8000}))
    asyncio.run(dispatch_twice())
    assert session.dispatched == 122
    assert session.metadata()["usage"] == {"input_tokens": 2050000, "output_tokens": 305000}
    assert {alert["category"] for alert in session.metadata()["budget_alerts"]} == {
        "input_tokens", "output_tokens", "model_requests"}
    assert len(session.budget_alerts) == 3
    assert sum(event[1].get("type") == "budget" and event[1].get("status") == "warning" for event in events) == 3


def test_advisory_records_crossing_usage_on_final_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TEAM_TBD_MAX_INPUT_TOKENS", "50000")
    monkeypatch.setenv("TEAM_TBD_MAX_OUTPUT_TOKENS", "16000")
    session = p.ModelSession()
    session.input_tokens, session.output_tokens = 49995, 15995
    async def roundtrip():
        request = httpx.Request("POST", "https://api.openai.com/v1/responses", json={
            "model": "gpt-6-astra", "max_output_tokens": 8000})
        await session.before_request(request)
        returned = response([])
        returned.request = request
        await session.after_response(returned)
    asyncio.run(roundtrip())
    assert session.input_tokens == 50025
    assert session.output_tokens == 16005
    assert {alert["category"] for alert in session.budget_alerts} == {"input_tokens", "output_tokens"}


def test_model_selection_scope_and_reasoning_are_explicit(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    p._save_capability("rosalind", {"status": "verified", "model": p.MODEL})
    monkeypatch.setenv("OPENAI_ORG_ID", "org-second")
    assert p.capabilities()["rosalind"]["status"] == "configured"
    monkeypatch.setenv("ROSALIND_MODEL", "gpt-rosalind-research")
    assert p.ModelSession().model_id == "gpt-rosalind-research"
    assert p._model_settings("gpt-rosalind-research", 2000).reasoning is None
    monkeypatch.setenv("TEAM_TBD_MODEL", "gpt-6-astra")
    assert p.ModelSession().model_id == "gpt-6-astra"
    assert p._model_settings("gpt-6-astra", 2000).reasoning.effort == "high"
    assert not p._matches_model("gpt-6-astra", "gpt-rosalind-research")
    assert p._matches_model("gpt-6-astra", "gpt-6-astra-2026-09-01")


def test_rejects_invented_evidence_and_model_artifacts():
    value = decision()
    with pytest.raises(p.ProviderError, match="outside this run"):
        p.validate_investigation(Investigation.model_validate(value), [])
    value["rd_handoff"]["modeling"]["status"] = "completed"
    with pytest.raises(p.ProviderError, match="completed molecular artifacts"):
        p.validate_investigation(Investigation.model_validate(value), [{"id": "e1"}])


def test_real_cif_parser_checks_chain_identity_and_geometry():
    result = p.validate_cif(small_cif(), "AC", "DE")
    assert result["chains"]["A"]["complete"]
    assert result["interface_residue_pairs_within_5_angstrom"] == 4
    with pytest.raises(p.ProviderError, match="sequence/coverage"):
        p.validate_cif(small_cif(), "AC", "DF")
    with pytest.raises(p.ProviderError):
        p.validate_cif("data_fake\n_atom_site.invalid\n", "AC", "DE")


def test_predict_records_real_artifacts(monkeypatch, tmp_path):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-key"
        assert "ligands" not in json.loads(request.content)
        return httpx.Response(200, headers={"NVCF-REQID": "vendor-id"}, json={"structures": [{"format": "mmcif", "structure": small_cif()}], "confidence_scores": [.72]})
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.predict_complex("AC", "DE", tmp_path))
    assert result["status"] == "completed"
    assert result["confidence_score"] == .72
    artifact = result["artifacts"][0]
    assert p._sha(Path(artifact["path"]).read_bytes()) == artifact["sha256"]
    assert p.capabilities()["bionemo"]["prediction_verified"] is True


def test_202_pending_preserved_no_blind_retry(monkeypatch, tmp_path):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(202, headers={"NVCF-REQID": "pending-id"}, json={"status": "pending"})
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.compare_binders("AC", "DE", "DF", tmp_path))
    assert result["status"] == "incomplete"
    assert result["jobs"][0]["status"] == "pending"
    assert result["jobs"][0]["request_id"] == "pending-id"
    assert len(calls) == 1


def test_timeout_unknown_and_no_repeat(monkeypatch, tmp_path):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("No response", request=request)
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError) as caught:
        asyncio.run(p.predict_complex("AC", "DE", tmp_path))
    assert caught.value.status == "unknown"
    assert len(calls) == 1
    jobs = list(tmp_path.glob("*/job.json"))
    assert json.loads(jobs[0].read_text())["status"] == "unknown"


def test_pair_keeps_completed_member_on_second_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    calls = []
    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, json={"structures": [{"format": "mmcif", "structure": small_cif()}], "confidence_scores": [.72]})
        return httpx.Response(422, json={"detail": "input rejected"})
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.compare_binders("AC", "DE", "DF", tmp_path))
    assert result["status"] == "incomplete"
    assert len(result["artifacts"]) == 1
    assert result["jobs"][0]["status"] == "completed"
    assert result["jobs"][1]["status"] == "failed"


def test_cancel_before_dispatch_and_invalid_sequence(monkeypatch, tmp_path):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(p.predict_complex("AC", "DE", tmp_path, cancelled=lambda: True))
    with pytest.raises(p.ProviderError, match="exact qualified"):
        asyncio.run(p.predict_complex("A C", "DE", tmp_path))
    assert not list(tmp_path.glob("*/request.json"))


def test_local_nim_doctor_is_health_only(monkeypatch):
    monkeypatch.setenv("BOLTZ2_NIM_URL", "http://127.0.0.1:8001")
    calls = []
    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert str(request.url) == "http://127.0.0.1:8001/v1/health/ready"
        return httpx.Response(200, json={"status": "ready"})
    fake_clients(monkeypatch, handler)
    result = asyncio.run(p.probe("bionemo"))
    assert len(calls) == 1
    assert result["status"] == "configured"
    assert result["health_ready"] is True
    assert result["prediction_verified"] is False


def test_cancelled_pair_retains_both_completed_and_dispatched_receipts(monkeypatch, tmp_path):
    calls = []
    async def prediction(target, binder, directory, **kwargs):
        calls.append(binder)
        if len(calls) == 1:
            return {"job_id": "first", "status": "completed", "artifacts": [{"name": "retained.cif"}]}
        exc = asyncio.CancelledError()
        exc.metadata = {"job_id": "second", "status": "unknown", "request_id": "vendor-still-running"}
        raise exc
    monkeypatch.setattr(p, "predict_complex", prediction)
    with pytest.raises(asyncio.CancelledError) as caught:
        asyncio.run(p.compare_binders("AC", "DE", "DF", tmp_path))
    saved = json.loads(next(tmp_path.glob("*/comparison.json")).read_text())
    assert saved["status"] == "incomplete"
    assert [j["status"] for j in saved["jobs"]] == ["completed", "unknown"]
    assert saved["jobs"][1]["request_id"] == "vendor-still-running"
    assert saved["artifacts"] == [{"name": "retained.cif"}]
    assert caught.value.metadata["comparison"] == saved


def test_discovery_model_selects_registered_data_and_review_diagnostic(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, discovery=True, followup=True)
    result = asyncio.run(p.investigate({"id": "cart-discovery"}, "My source-defined resistance hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    assert [e["id"] for e in persisted] == ["ANALYSIS-TEST", "ANALYSIS-REVIEW"]
    assert result["metadata"]["review_cycles"][0]["file_id"] == "file-b"
    assert result["metadata"]["review_cycles"][0]["status"] == "completed"
    bio = next(c for c in calls if "ROLE: bioinformatician." in c["instructions"])
    assert {t["name"] for t in bio["tools"]} >= {"list_datasets", "get_dataset", "inspect_data_file", "analyze_data_file"}
    assert {"run_case_analysis", "analysis_catalog"}.issubset({t["name"] for t in bio["tools"]})
    assert len(calls) <= p.MAX_REQUESTS


def test_discovery_analysis_cap_reserves_work_for_reviewer(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, discovery=True, followup=True, extra_bio=7)
    result = asyncio.run(p.investigate({"id": "cart-discovery"}, "My source-defined resistance hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    assert sum(e[0][1] == "Analyzing registered source data" and e[0][0] == "bioinformatician" for e in events) == 4
    assert result["metadata"]["reviewer_completed"] is True
    assert result["metadata"]["review_cycles"][0]["status"] == "completed"


def test_model_catalog_pages_preserve_discovery_without_oversized_context():
    value = {"id": "study", "description": "d"*6000, "files": [{"id": str(i), "name": "x", "sha256": "s"*64, "note": "n"*3000} for i in range(27)]}
    pages = [p.compact_dataset(value, offset) for offset in (0, 12, 24)]
    assert [f["id"] for page in pages for f in page["files"]] == [str(i) for i in range(27)]
    assert pages[-1]["next_offset"] is None
    assert len(json.dumps(pages[0])) < 3000
    assert len(value["files"]) == 27 and "sha256" in value["files"][0]


def test_exploration_turn_limit_finalizes_accepted_evidence_once(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch, discovery=True, extra_bio=-7)
    result = asyncio.run(p.investigate({"id": "cart-discovery"}, "My source-defined resistance hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    assert sum(e[0][1] == "Exploration closed for handoff" for e in events) == 1
    assert result["metadata"]["reviewer_completed"] is True
    assert any(not c.get("tools") and "ROLE: bioinformatician." in c["instructions"] for c in calls)


def followup_proposal_arguments(**overrides):
    """Recommendation-only mock input; never a scientific measurement."""
    return {"analysis_id": "followup-analysis",
            "scientific_question": "Does the registered source diagnostic change the observed contrast?",
            "rationale": "A source exclusion sensitivity check could distinguish the alternatives.",
            "decision_it_could_change": "Whether to prioritize the source-specific explanation for validation.",
            "evidence_ids": ["ANALYSIS-TEST"], **overrides}


def initial_role_payload(calls, role):
    call = next(call for call in calls if f"ROLE: {role}." in call["instructions"])
    return json.loads(call["input"][0]["content"])


def proposal_tool_outputs(calls, role, tool_name="propose_followup"):
    """Resolve real SDK tool outputs through their call identities."""
    body = [call for call in calls if f"ROLE: {role}." in call["instructions"]][-1]
    ids = {item["call_id"] for item in body["input"]
           if item.get("type") == "function_call" and item.get("name") == tool_name}
    return [item["output"] for item in body["input"]
            if item.get("type") == "function_call_output" and item.get("call_id") in ids]


def test_followup_proposals_reach_accepted_peers_without_executing_proposed_analysis(monkeypatch):
    from app import analysis_tools
    from app.scientific_skills import load_skill
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    arguments = followup_proposal_arguments()
    # Duplicate requests by one role must be stable, while another role may
    # independently nominate the same recipe for its own scientific question.
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, proposal_scripts={"statistician": [arguments, arguments],
                                      "clinical_scientist": [followup_proposal_arguments(
                                          scientific_question="Would the source check alter the clinical study design?")]})
    executed = []
    def execute(case_id, analysis_id):
        executed.append((case_id, analysis_id))
        assert analysis_id == "test-analysis", "Listing/proposing must not execute a follow-up"
        return derived()
    monkeypatch.setattr(analysis_tools, "analyze_case", execute)
    molecular_calls = []
    async def reject_molecular(proposal):
        molecular_calls.append(proposal)
        raise AssertionError("A recommendation must not execute molecular inference")
    result = asyncio.run(p.investigate({"id": "case-1"}, "My exact scientific hypothesis.", [{"id": "e1"}],
        emit, lambda: False, accept_evidence=accept, accept_handoff=handoff,
        request_molecular=reject_molecular))

    assert executed == [("case-1", "test-analysis")]
    assert molecular_calls == []
    assert [item["id"] for item in persisted] == ["ANALYSIS-TEST"]
    assert result["metadata"]["review_cycles"] == []
    assert result["metadata"]["molecular_receipts"] == []
    by_role = {product["sender"]: product for product in products}
    stats = by_role["statistician"]["followup_proposals"]
    clinical = by_role["clinical_scientist"]["followup_proposals"]
    assert len(stats) == len(clinical) == 1
    assert stats[0]["analysis_id"] == clinical[0]["analysis_id"] == "followup-analysis"
    for key, value in arguments.items():
        assert stats[0][key] == value
    assert stats[0] != clinical[0]
    accepted_flat = [proposal for product in result["metadata"]["work_products"]
                     for proposal in product.get("followup_proposals", [])]
    assert result["metadata"]["followup_proposals"] == accepted_flat
    assert len(accepted_flat) == 2
    # Proposal content is preserved after the source role's durable handoff and
    # survives context compaction into both synthesizer and independent reviewer.
    for role in ("coordinator", "reviewer"):
        payload = initial_role_payload(calls, role)
        peer_stats = next(product for product in payload["specialist_work_products"]
                          if product["sender"] == "statistician")
        assert peer_stats["id"] == by_role["statistician"]["id"]
        assert peer_stats["followup_proposals"] == stats
    upstream = initial_role_payload(calls, "clinical_scientist")["upstream_work_products"]
    assert next(product for product in upstream if product["sender"] == "statistician")["followup_proposals"] == stats
    duplicate_outputs = [json.loads(output) for output in proposal_tool_outputs(calls, "statistician")]
    assert len(duplicate_outputs) == 2
    assert duplicate_outputs[0] == duplicate_outputs[1] == stats[0]
    assert len(proposal_tool_outputs(calls, "statistician", "list_available_followups")) == 1
    # All model-active roles have common planning tools and pinned guidance;
    # the deterministic blocked pharmacology role is deliberately not counted.
    for role, product in by_role.items():
        if not product["model_called"]:
            continue
        call = next(call for call in calls if f"ROLE: {role}." in call["instructions"])
        tool_names = {tool["name"] for tool in call["tools"]}
        assert {"list_available_followups", "propose_followup"} <= tool_names
        planning = load_skill("discovery-planning", role)
        assert planning["instructions"] in call["instructions"]
        assert product["skill_versions"]["discovery-planning"] == {
            "version": planning["version"], "sha256": planning["sha256"]}
        if role not in {"coordinator", "reviewer"}:
            payload = initial_role_payload(calls, role)
            assert "available_followup_options" in payload
            assert "followup-analysis" in json.dumps(payload["available_followup_options"])


@pytest.mark.parametrize("rejected_role", ["assay_scientist", "coordinator", "reviewer"])
def test_valid_proposal_survives_content_repair_but_only_accepted_handoff_reaches_peers(monkeypatch, rejected_role):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    marker = "Validated sensitivity proposal must survive unrelated content repair."
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, reject_first=rejected_role,
        proposal_scripts={rejected_role: [followup_proposal_arguments(rationale=marker)]})
    result = asyncio.run(p.investigate({"id": "case-1"}, "My exact scientific hypothesis.", [{"id": "e1"}],
        emit, lambda: False, accept_evidence=accept, accept_handoff=handoff))
    rejected = next(product["submitted"] for product in products if product.get("rejected"))
    assert rejected["sender"] == rejected_role
    assert len(rejected["followup_proposals"]) == 1
    assert rejected["followup_proposals"][0]["rationale"] == marker
    repaired = next(product for product in products if product.get("sender") == rejected_role)
    assert repaired["id"] != rejected["id"]
    assert repaired["followup_proposals"] == rejected["followup_proposals"]
    assert result["metadata"]["followup_proposals"] == repaired["followup_proposals"]
    accepted = result["metadata"]["work_products"]
    assert rejected["id"] not in {product["id"] for product in accepted}
    assert repaired["id"] in {product["id"] for product in accepted}
    assert len([proposal for product in accepted for proposal in product.get("followup_proposals", [])]) == 1
    downstream = []
    if rejected_role != "reviewer":
        downstream.append(initial_role_payload(calls, "reviewer"))
    if rejected_role == "assay_scientist":
        downstream.append(initial_role_payload(calls, "coordinator"))
    for payload in downstream:
        assert rejected["id"] not in json.dumps(payload)
        source = next(product for product in payload["specialist_work_products"] if product["sender"] == rejected_role)
        assert source["id"] == repaired["id"]
        assert source["followup_proposals"] == repaired["followup_proposals"]
    role_calls = [call for call in calls if f"ROLE: {rejected_role}." in call["instructions"]]
    assert not role_calls[-1].get("tools"), "Repair must not rerun a proposing tool"
    repair_payload = json.loads(role_calls[-1]["input"][0]["content"])
    assert repair_payload["pending_followup_proposals"] == repaired["followup_proposals"]
    assert [event[0][2] for event in events if event[0][1] == "Executing source-data analysis"] == ["test-analysis"]


def test_ultimately_rejected_handoff_does_not_promote_pending_proposal(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    marker = "Proposal from an ultimately rejected assay work product."
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, proposal_scripts={"assay_scientist": [followup_proposal_arguments(rationale=marker)]})
    rejected_attempts = []
    async def refuse_assay(product):
        if product["sender"] == "assay_scientist":
            rejected_attempts.append(json.loads(json.dumps(product)))
            return {"accepted": False, "reason": "Assay result is still scientifically unsupported."}
        return await handoff(product)
    with pytest.raises(p.ProviderError, match="scientifically unsupported") as failure:
        asyncio.run(p.investigate({"id": "case-1"}, "My exact scientific hypothesis.", [{"id": "e1"}],
            emit, lambda: False, accept_evidence=accept, accept_handoff=refuse_assay))
    assert len(rejected_attempts) == 2
    assert rejected_attempts[0]["followup_proposals"] == rejected_attempts[1]["followup_proposals"]
    assert len(rejected_attempts[0]["followup_proposals"]) == 1
    assert failure.value.metadata.get("followup_proposals", []) == []
    accepted = failure.value.metadata["work_products"]
    assert all(product["sender"] != "assay_scientist" for product in accepted)
    assert marker not in json.dumps(accepted)
    assert not any("ROLE: coordinator." in call["instructions"] for call in calls)
    assert [item["id"] for item in persisted] == ["ANALYSIS-TEST"]


def test_unknown_and_fabricated_citation_proposals_do_not_enter_accepted_handoffs(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    invalid_recipe = followup_proposal_arguments(analysis_id="not-in-the-registered-catalog")
    invalid_citation = followup_proposal_arguments(evidence_ids=["invented-source-id"])
    valid = followup_proposal_arguments()
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, proposal_scripts={"assay_scientist": [invalid_recipe, invalid_citation, valid]})
    result = asyncio.run(p.investigate({"id": "case-1"}, "My exact scientific hypothesis.", [{"id": "e1"}],
        emit, lambda: False, accept_evidence=accept, accept_handoff=handoff))
    proposals = result["metadata"]["followup_proposals"]
    assert len(proposals) == 1
    assert proposals[0]["analysis_id"] == valid["analysis_id"]
    assert proposals[0]["evidence_ids"] == ["ANALYSIS-TEST"]
    assay = next(product for product in products if product.get("sender") == "assay_scientist")
    assert assay["followup_proposals"] == proposals
    accepted = json.dumps(result["metadata"]["work_products"])
    assert "invented-source-id" not in accepted
    assert "not-in-the-registered-catalog" not in accepted
    outputs = proposal_tool_outputs(calls, "assay_scientist")
    assert len(outputs) == 3
    assert all("error" in output.lower() or "reject" in output.lower() for output in outputs[:2])
    assert [item["id"] for item in persisted] == ["ANALYSIS-TEST"]
    assert [event[0][2] for event in events if event[0][1] == "Executing source-data analysis"] == ["test-analysis"]
