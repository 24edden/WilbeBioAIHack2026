"""Synthesis recovery contracts through the real SDK and mocked HTTP only.

No model or NVIDIA request leaves the test process. Accepted specialist work is
historical; only synthesis/review are allowed to make new model requests.
"""
import asyncio
import copy
import json
import re

import httpx
import pytest

from app import providers as p
from test_providers import (
    fake_clients, message, response, team_transport, isolated,
)


def test_synthesis_allowance_is_enforced_at_the_http_boundary(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-synthesis-key-never-send")
    session = p.ModelSession()
    request = lambda cap: httpx.Request("POST", "https://api.openai.com/v1/responses", json={
        "model": p.MODEL, "max_output_tokens": cap})
    session.active_role = "statistician"
    with pytest.raises(p.ProviderError, match="configured agent limit"):
        asyncio.run(session.before_request(request(48000)))
    assert session.dispatched == 0
    session.active_role = "coordinator"
    asyncio.run(session.before_request(request(48000)))
    session.active_role = "reviewer"
    with pytest.raises(p.ProviderError, match="configured agent limit"):
        asyncio.run(session.before_request(request(48001)))
    assert session.dispatched == 1
    assert session.records[0]["agent"] == "coordinator"
    assert session.records[0]["max_output_tokens"] == 48000


def test_synthesis_reserves_its_full_allowance_under_enforced_budget(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-synthesis-key-never-send")
    monkeypatch.setenv("TEAM_TBD_BUDGET_MODE", "enforced")
    session = p.ModelSession()
    session.active_role = "reviewer"
    session.output_tokens = 252001
    request = httpx.Request("POST", "https://api.openai.com/v1/responses", json={
        "model": p.MODEL, "max_output_tokens": 48000})
    with pytest.raises(p.ProviderError, match="Insufficient remaining output-token budget"):
        asyncio.run(session.before_request(request))
    assert session.dispatched == 0


@pytest.mark.parametrize("role", ["coordinator", "reviewer"])
def test_synthesis_json_repair_uses_synthesis_capacity_with_real_sdk(monkeypatch, role):
    monkeypatch.setenv("OPENAI_API_KEY", "test-synthesis-key-never-send")
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return response([message({"evidence_id": "e1", "tool_observation": "observed:e1"})])
    fake_clients(monkeypatch, handler)
    async def run():
        session = p.ModelSession()
        session.active_role = role
        try:
            value = await p._parse_or_repair("malformed-json", p.ProbeOutput, typed=False,
                model=session.model(), max_tokens=session.output_allowance(),
                timeout_seconds=session.request_timeout + 30)
            return value, session.metadata()
        finally:
            await session.close()
    value, metadata = asyncio.run(run())
    assert value.evidence_id == "e1"
    assert len(calls) == 1
    assert calls[0]["max_output_tokens"] == 48000
    assert calls[0]["reasoning"]["effort"] == "high"
    assert not calls[0].get("tools")
    assert metadata["requests"][0]["agent"] == role
    assert metadata["dispatched_requests"] == 1


@pytest.mark.parametrize("checkpoint", [None, {}, {"schema": "team-tbd-synthesis-checkpoint-1", "sha256": "invalid"}])
def test_invalid_checkpoint_is_rejected_before_model_client_construction(monkeypatch, checkpoint):
    async def emit(*args, **kwargs):
        pass
    def forbidden_client(*args, **kwargs):
        pytest.fail("A malformed checkpoint must not construct a model transport")
    monkeypatch.setattr(p.ModelSession, "model", forbidden_client)
    with pytest.raises(p.ProviderError, match="Synthesis checkpoint rejected before model dispatch"):
        asyncio.run(p.investigate({"id": "case-1", "synthesis_checkpoint": checkpoint},
            "Exact hypothesis.", [{"id": "e1"}], emit, lambda: False))



def _ready_checkpoint(tmp_path, monkeypatch, **fixture_options):
    from app import synthesis_checkpoint as sc
    from test_synthesis_checkpoint import create_failed_synthesis, select
    store, engine, run_id, case = create_failed_synthesis(tmp_path, monkeypatch, **fixture_options)
    before = store.get(run_id)
    select(store, run_id)
    run = store.get(run_id)
    checkpoint = sc.synthesis_context(run)
    provider_case = {**run["case_snapshot"], "process_contract": run["process_contract"], "synthesis_checkpoint": checkpoint}
    return store, engine, run_id, provider_case, before


def test_checkpoint_runs_only_fresh_synthesis_and_review_through_sdk_and_worker(tmp_path, monkeypatch):
    from app import synthesis_checkpoint as sc, analysis_tools
    from test_hypothesis_continuation import governed_decision
    monkeypatch.setenv("OPENAI_API_KEY", "test-synthesis-key-never-send")
    store, engine, run_id, case, before = _ready_checkpoint(
        tmp_path, monkeypatch, with_analysis=True, with_proposal=True)
    pinned_catalog = analysis_tools.analysis_catalog
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, synthesis=True, governance=governed_decision()["governance"])
    monkeypatch.setattr(analysis_tools, "analysis_catalog", pinned_catalog)
    parsed_allowances = []
    original_parse = p._parse_or_repair
    async def capture_parse(*args, **kwargs):
        parsed_allowances.append(kwargs["max_tokens"])
        return await original_parse(*args, **kwargs)
    monkeypatch.setattr(p, "_parse_or_repair", capture_parse)
    asyncio.run(engine.execute(run_id))
    after = store.get(run_id)
    assert after["status"] == "completed", after["error"]
    assert len(after["decisions"]) == 1
    roles = [re.search(r"ROLE: ([a-z_]+)\.", call["instructions"]).group(1) for call in calls]
    assert roles == ["coordinator"] * 3 + ["reviewer"] * 3
    assert {call["max_output_tokens"] for call in calls} == {48000}
    assert parsed_allowances == [48000, 48000]
    assert after["handoffs"][:7] == before["handoffs"]
    assert [item["sender"] for item in after["handoffs"][7:]] == ["coordinator", "reviewer"]
    assert after["evidence"] == before["evidence"]
    assert after["hypothesis"] == before["hypothesis"]
    assert after["actions"][0] == before["actions"][0]
    assert persisted == []  # No analysis or molecular work is reexecuted.
    original_ids = {item["sender"]: item["id"] for item in before["handoffs"]}
    coordinator, reviewer = after["handoffs"][-2:]
    assert coordinator["input_versions"]["upstream_handoff_ids"] == [
        original_ids["translational_scientist"], original_ids["assay_scientist"]]
    assert reviewer["input_versions"]["upstream_handoff_ids"] == [coordinator["id"], original_ids["assay_scientist"]]
    new_skills = [item for item in after["skill_receipts"] if item["operation_id"] == after["operation"]["id"]]
    assert {(item["role"], item["skill_id"]) for item in new_skills} == {
        (role, skill) for role in ("coordinator", "reviewer")
        for skill in (role, "discovery-planning", "rosalind-informed-workflow", "research-interpretation", "molecular-interpretation")}
    assert not set(item["id"] for item in new_skills).intersection(item["id"] for item in before["skill_receipts"])
    metadata = after["decisions"][-1]["metadata"]
    assert metadata["actual_model_roles"] == ["coordinator", "reviewer"]
    assert metadata["reused_role_ids"] == list(sc.ROLES)
    assert metadata["work_products"][:7] == before["handoffs"]
    assert metadata["accepted_analysis_ids"] == ["ANALYSIS-TEST"]
    original_proposal = before["handoffs"][0]["followup_proposals"][0]
    assert metadata["followup_proposals"] == [original_proposal]
    assert metadata["synthesis_checkpoint"]["source_operation_id"] == before["operation"]["id"]
    assert metadata["synthesis_checkpoint"]["source_handoff_ids"] == [item["id"] for item in before["handoffs"]]
    common = {"get_case_readiness", "read_evidence", "load_scientific_skill", "list_available_followups", "propose_followup"}
    for call in calls:
        assert {item["name"] for item in call["tools"]} == common
        assert "no new analysis, reviewer diagnostics or molecular execution" in call["instructions"]
    payload = json.loads(calls[0]["input"][0]["content"])
    assert [item["id"] for item in payload["specialist_work_products"]] == [item["id"] for item in before["handoffs"]]
    assert all(item["operation_id"] == before["operation"]["id"] for item in payload["specialist_work_products"])
    assert "draft_to_repair" not in payload and "draft_to_review" not in payload
    assert payload["accepted_evidence_ids"] == ["e1", "ANALYSIS-TEST"]
    assert payload["specialist_work_products"][0]["followup_proposals"] == [original_proposal]


@pytest.mark.parametrize("role", ["coordinator", "reviewer"])
def test_checkpoint_does_not_relax_required_evidence_read_or_repair_gate(tmp_path, monkeypatch, role):
    from test_hypothesis_continuation import governed_decision
    monkeypatch.setenv("OPENAI_API_KEY", "test-synthesis-key-never-send")
    store, engine, run_id, case, before = _ready_checkpoint(tmp_path, monkeypatch)
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, synthesis=True, failed_read_role=role, governance=governed_decision()["governance"])
    with pytest.raises(p.ProviderError, match="omitted required evidence tools") as failure:
        asyncio.run(p.investigate(case, before["hypothesis"]["text"], before["evidence"], emit,
            lambda: False, accept_evidence=accept, accept_handoff=handoff))
    role_calls = [item for item in calls if f"ROLE: {role}." in item["instructions"]]
    assert len(role_calls) == 4
    assert not role_calls[-1].get("tools")  # Exactly one format/content repair, not a fresh tool retry.
    assert all(item["max_output_tokens"] == 48000 for item in calls)
    assert failure.value.metadata["work_products"][:7] == before["handoffs"]
    assert failure.value.metadata["reused_role_ids"] == case["synthesis_checkpoint"]["reused_roles"]
    assert not any(item.get("sender") == role for item in products)
    assert persisted == []
    if role == "coordinator":
        assert failure.value.metadata["actual_model_roles"] == ["coordinator"]
        assert not any("ROLE: reviewer." in item["instructions"] for item in calls)


@pytest.mark.parametrize("change", ["missing_role", "duplicate_role", "evidence_version", "hypothesis", "skill_receipt"])
def test_saved_checkpoint_mutations_fail_before_any_sdk_call(tmp_path, monkeypatch, change):
    from app.store import digest
    store, engine, run_id, case, before = _ready_checkpoint(tmp_path, monkeypatch)
    checkpoint = case["synthesis_checkpoint"]
    hypothesis, evidence = before["hypothesis"]["text"], copy.deepcopy(before["evidence"])
    if change == "missing_role":
        checkpoint["work_products"].pop()
    elif change == "duplicate_role":
        checkpoint["work_products"][-1]["sender"] = "bioinformatician"
    elif change == "evidence_version":
        evidence[0]["source"]["sha256"] = "b" * 64
    elif change == "hypothesis":
        hypothesis += " altered"
    else:
        checkpoint["source_skill_receipts"][0]["sha256"] = "b" * 64
    # Rehashing a caller-supplied envelope cannot bypass semantic/source checks.
    checkpoint["sha256"] = digest({key: value for key, value in checkpoint.items() if key != "sha256"})
    calls = []
    fake_clients(monkeypatch, lambda request: calls.append(request))
    async def emit(*args, **kwargs):
        pass
    with pytest.raises(p.ProviderError, match="Synthesis checkpoint rejected before model dispatch"):
        asyncio.run(p.investigate(case, hypothesis, evidence, emit, lambda: False))
    assert calls == []
