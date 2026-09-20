"""Real Agents SDK, mocked model transport and in-memory public source adapter."""
import asyncio
import copy
import json

import httpx
import pytest
from pydantic import ValidationError

from app import providers as p, sequence_discovery as sd, sequence_sources as sources
from test_providers import fake_clients, function, message, response, isolated


def record(identifier, sequence, kind="protein", targets=None):
    return {"id": identifier, "label": identifier, "sequence": sequence, "length": len(sequence),
        "sequence_sha256": p._sha(sequence), "verified": True, "source_url": "https://example.test/" + identifier,
        "source_locator": "Offline source fixture " + identifier, "source_sha256": "a" * 64,
        "entity_type": kind, "target_accessions": targets if targets is not None else ["P00001"],
        "provenance": {"identity": "offline fixture; not biological evidence"}, "qualification": "Software fixture only."}


def records():
    return [record("target-1", "ACDEFGHIKLMNPQRSTVWYA"),
            record("binder-1", "ACDEFGHIKLMNPQRSTVWYC", "single_chain_binder"),
            record("binder-2", "ACDEFGHIKLMNPQRSTVWYD", "single_chain_binder")]


def run_record():
    text = "Find qualified target and binder records for the current mechanism."
    return {"id": "run-1", "case_id": "case-1", "hypothesis": {"text": text, "source_name": "Scientist", "sha256": p._sha(text)},
            "decisions": [{"version": 3, "summary": "Target-side mechanism is a research lead.", "assessment": "inconclusive",
                           "metadata": {"private_history": "do-not-copy"}}],
            "evidence": [{"id": "e1", "title": "Accepted assay observation", "summary": "Observed endpoint shift.", "values": {"large_table": "omit"}}],
            "research_briefs": [{"source_decision_version": 3, "content": {"headline": "Current working answer", "modeling_draft": {"scientific_rationale": "Identify a research comparator."}}}]}


def proposal(partial=False):
    selections = [{"source_id": identifier, "role": role, "rationale": "Relevant public research comparator.",
                   "qualification": "Exact verified source construct; no patient identity or superiority claim."}
                  for identifier, role in (("target-1", "target"), ("binder-1", "reference_binder"), ("binder-2", "candidate_binder"))]
    return {"summary": "Verified public inputs for a research comparison.", "scientific_rationale": "The proposed inputs address the current target-side question.",
            "qualification_note": "Target retention and functional recognition require separate evidence; no NVIDIA request was made.",
            "selections": selections[:2] if partial else selections,
            "missing_inputs": ["An exact qualified alternative single-chain binder."] if partial else []}


def reviewed(value=None):
    return {"verdict": "accepted", "checks": {key: True for key in sd.SequenceReviewChecks.model_fields},
            "changes": ["Preserved research-comparator scope."], "remaining_limitations": ["Target retention unestablished."],
            "proposal": value or proposal()}


@pytest.fixture
def fake_sources(monkeypatch):
    instances = []
    class FakeSources:
        def __init__(self, emit=None, cancelled=None):
            self.sources, self.receipts, self.calls = [], [], []
            instances.append(self)
        async def invoke(self, name, argument):
            self.calls.append((name, argument))
            self.receipts.append({"skill_id": "uniprot-skill" if "uniprot" in name else "rcsb-pdb-skill", "status": "completed",
                                  "source_sha256": "b" * 64, "endpoint": "https://example.test/" + name})
            if name == "fetch_uniprot":
                self.sources.append(records()[0])
                return self.sources[-1]
            if name == "fetch_structure":
                self.sources.extend(records()[1:])
                return {"sequences": self.sources[-2:]}
            return {"records": [{"accession": "P00001", "pdb_id": "1ABC"}]}
        async def search_uniprot(self, query): return await self.invoke("search_uniprot", query)
        async def fetch_uniprot(self, accession): return await self.invoke("fetch_uniprot", accession)
        async def search_structures(self, query): return await self.invoke("search_structures", query)
        async def fetch_structure(self, pdb_id): return await self.invoke("fetch_structure", pdb_id)
    monkeypatch.setattr(sources, "SequenceSources", FakeSources)
    real_load = sd.load_skill
    def load(skill_id, role):
        if skill_id in {"uniprot-skill", "rcsb-pdb-skill"}:
            return {"id": skill_id, "name": "Offline source skill fixture", "version": "fixture", "sha256": "c" * 64,
                    "instructions": "Use the bounded source tool; this fixture makes no network request."}
        return real_load(skill_id, role)
    monkeypatch.setattr(sd, "load_skill", load)
    return instances


def transport(monkeypatch, *, final=None, partial=False):
    calls = []
    value = proposal(partial)
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        reviewer = "ROLE: reviewer." in body["instructions"]
        if reviewer:
            return response([message(final or reviewed(value))], len(calls))
        molecular = [c for c in calls if "ROLE: molecular_scientist." in c["instructions"]]
        if len(molecular) == 1:
            return response([function("search_uniprot", {"query": "target name"}, 1), function("search_structures", {"query": "target binder"}, 2)], len(calls))
        if len(molecular) == 2:
            return response([function("fetch_uniprot", {"accession": "P00001"}, 3), function("fetch_structure", {"pdb_id": "1ABC"}, 4)], len(calls))
        return response([message(value)], len(calls))
    fake_clients(monkeypatch, handler)
    return calls


def test_context_keeps_latest_science_without_transport_or_large_tables():
    run = run_record()
    old = copy.deepcopy(run)
    context = sd.build_discovery_context(run, {"id": "case-1"})
    assert context["original_hypothesis"] == run["hypothesis"]
    assert context["latest_decision"]["version"] == 3
    assert context["latest_interpretation"]["headline"] == "Current working answer"
    assert "private_history" not in json.dumps(context)
    assert "large_table" not in json.dumps(context)
    context["accepted_findings"][0]["summary"] = "changed"
    assert run == old


@pytest.mark.parametrize("change", [
    lambda run: run["hypothesis"].update(text="changed"),
    lambda run: run.update(decisions=[]),
])
def test_invalid_context_rejected(change):
    run = run_record()
    change(run)
    with pytest.raises(p.ProviderError):
        sd.build_discovery_context(run, {"id": "case-1"})


def test_selection_copies_only_verified_exact_bytes_and_preserves_source_qualification():
    source = records()
    old = copy.deepcopy(source)
    value, selected = sd.validate_proposal(proposal(), source)
    assert selected[0]["sequence"] == source[0]["sequence"]
    assert selected[0]["source_qualification"] == "Software fixture only."
    assert sd._comparison_is_ready(selected)
    selected[0]["sequence"] = "A"
    assert source == old


@pytest.mark.parametrize("change,error", [
    (lambda v, r: v["selections"][0].update(source_id="fabricated"), "verified public source"),
    (lambda v, r: r[0].update(verified=False), "verified public source"),
    (lambda v, r: r[0].update(sequence="ACD"), "length and SHA"),
    (lambda v, r: r[0].update(source_sha256=""), "source provenance"),
    (lambda v, r: r[1].update(entity_type="antibody_chain"), "isolated antibody"),
    (lambda v, r: r[0].update(entity_type="single_chain_binder"), "target must"),
    (lambda v, r: v["selections"][1].update(role="target"), "duplicate molecular roles"),
    (lambda v, r: v["selections"][2].update(source_id="binder-1"), "distinct verified sequence"),
    (lambda v, r: r[1].update(target_accessions=["WRONG"]), "different target"),
    (lambda v, r: v.update(summary="ACDEFGHIKLMNPQRSTVWYACDEFGHIKLMN"), "not emit sequence bytes"),
])
def test_selection_rejects_fabricated_or_wrong_role_inputs(change, error):
    value, source = proposal(), records()
    change(value, source)
    with pytest.raises(p.ProviderError, match=error):
        sd.validate_proposal(value, source)


def test_partial_discovery_and_missing_target_linkage_remain_explicit():
    value = proposal(partial=True)
    _, selected = sd.validate_proposal(value, records())
    assert not sd._comparison_is_ready(selected)
    value["missing_inputs"] = []
    with pytest.raises(p.ProviderError, match="missing comparison inputs"):
        sd.validate_proposal(value, records())
    value, source = proposal(), records()
    source[2]["target_accessions"] = []
    with pytest.raises(p.ProviderError, match="missing comparison inputs"):
        sd.validate_proposal(value, source)
    value["missing_inputs"] = ["Qualified target linkage for the candidate binder."]
    _, selected = sd.validate_proposal(value, source)
    assert not sd._comparison_is_ready(selected)


@pytest.mark.parametrize("index,length", [(0, 1801), (1, 901)])
def test_selected_sequences_fit_actual_comparison_form_limits(index, length):
    source = records()
    sequence = "A" * length
    source[index].update(sequence=sequence, length=length, sequence_sha256=p._sha(sequence))
    with pytest.raises(p.ProviderError, match="supported 15"):
        sd.validate_proposal(proposal(), source)


def test_output_schema_never_accepts_a_model_generated_sequence_or_retention_boolean():
    value = proposal()
    value["selections"][0]["sequence"] = records()[0]["sequence"]
    with pytest.raises(ValidationError):
        sd.SequenceProposal.model_validate(value)
    value = proposal()
    value["target_retained"] = True
    with pytest.raises(ValidationError):
        sd.SequenceProposal.model_validate(value)


@pytest.mark.parametrize("partial", [False, True])
def test_real_sdk_discovery_and_independent_review_return_grounded_inputs(monkeypatch, fake_sources, partial):
    monkeypatch.setenv("OPENAI_API_KEY", "test-sequence-key-never-send")
    calls = transport(monkeypatch, partial=partial)
    run = run_record()
    old = copy.deepcopy(run)
    events = []
    async def emit(*args, **kwargs): events.append((args, kwargs))
    result = asyncio.run(sd.discover_sequences(run, {"id": "case-1"}, emit=emit))
    assert run == old
    assert len(calls) == 4
    assert all(call["max_output_tokens"] == (48000 if "ROLE: reviewer." in call["instructions"] else 24000) for call in calls)
    assert all(call["reasoning"]["effort"] == "high" and call["model"] == "gpt-6-astra" for call in calls)
    assert result["status"] == ("needs_inputs" if partial else "completed")
    assert len(result["sequences"]) == (2 if partial else 3)
    assert result["sequences"][0]["sequence"] == records()[0]["sequence"]
    assert result["target_retention_established"] is False and result["nvidia_submitted"] is False
    assert result["human_review_status"] == "unreviewed"
    assert result["provider_metadata"]["actual_model_roles"] == ["molecular_scientist", "reviewer"]
    assert result["provider_metadata"]["requests"][-1]["request_id"] == "req_4"
    assert result["provider_metadata"]["tool_calls"] == 4
    assert len(result["skill_receipts"]) == 14
    assert {item["skill_id"] for item in result["skill_receipts"]}.issuperset({"uniprot-skill", "rcsb-pdb-skill", "rosalind-informed-workflow"})
    assert len(result["source_receipts"]) == 4
    assert result["context_sha256"] == sd._sha(sd.build_discovery_context(run, {"id": "case-1"}))
    assert result["sha256"] == sd._sha({key: val for key, val in result.items() if key != "sha256"})
    assert len(fake_sources) == 1
    # Tool-call output gives scientific metadata/IDs, never raw execution sequences.
    for call in calls:
        for item in call["input"]:
            if item.get("type") == "function_call_output":
                assert records()[0]["sequence"] not in item["output"]


def test_failed_independent_review_gets_one_visible_correction_then_rejects(monkeypatch, fake_sources):
    monkeypatch.setenv("OPENAI_API_KEY", "test-sequence-key-never-send")
    value = reviewed()
    value["checks"]["target_and_binder_roles_qualified"] = False
    calls = transport(monkeypatch, final=value)
    with pytest.raises(p.ProviderError, match="reviewer rejected") as err:
        asyncio.run(sd.discover_sequences(run_record(), {"id": "case-1"}))
    assert len(calls) == 5
    assert not calls[-1].get("tools")
    assert err.value.metadata["acceptance_repair_roles"] == ["reviewer"]
    assert len(err.value.metadata["source_records"]) == 3


def test_unknown_model_timeout_preserves_source_receipts_without_retry(monkeypatch, fake_sources):
    monkeypatch.setenv("OPENAI_API_KEY", "test-sequence-key-never-send")
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return response([function("fetch_uniprot", {"accession": "P00001"}, 1)])
        raise httpx.ReadTimeout("timeout", request=request)
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError) as err:
        asyncio.run(sd.discover_sequences(run_record(), {"id": "case-1"}))
    assert len(calls) == 2
    assert err.value.status == "unknown"
    assert err.value.reason_code == "model_request_timeout"
    assert len(err.value.metadata["source_receipts"]) == 1
    assert len(err.value.metadata["source_records"]) == 1
    assert err.value.metadata["failure"]["automatic_retry"] is False


def test_cancel_before_sources_or_model(monkeypatch, fake_sources):
    monkeypatch.setattr(p, "ModelSession", lambda *args: pytest.fail("Cancelled operation must not open a model"))
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(sd.discover_sequences(run_record(), {"id": "case-1"}, cancelled=lambda: True))
    assert fake_sources == []
