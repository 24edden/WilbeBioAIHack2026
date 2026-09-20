"""Required analyses are reviewed after durable acceptance; no vendor calls."""
import asyncio
import copy
import json

import pytest

from app import config as _config  # Initialize private config before the isolation fixture clears it.
from app import analysis_tools as a, providers as p
import test_providers as transport
from test_providers import isolated


def planned_transport(monkeypatch, bio_plan):
    """Reuse the SDK mock while giving bioinformatics an explicit review plan."""
    install_client = transport.fake_clients

    def install_plan(monkeypatch, handler):
        def scripted(request):
            body = json.loads(request.content)
            default_response = handler(request)
            if "ROLE: bioinformatician." not in body["instructions"]:
                return default_response
            outputs = [item for item in body["input"] if item.get("type") == "function_call_output"]
            if body.get("tools") and len(outputs) < len(bio_plan):
                name, arguments = bio_plan[len(outputs)]
                return transport.response([transport.function(name, arguments, len(outputs) + 1)])
            return transport.response([transport.message(transport.specialist_brief("bioinformatician"))])
        install_client(monkeypatch, scripted)

    monkeypatch.setattr(transport, "fake_clients", install_plan)
    return transport.team_transport(monkeypatch)


def preexecuted_inputs(*, two=False, case_id="case-1"):
    source = {"path": "study/samples.csv", "sha256": "b" * 64}
    case = {"id": case_id, "source_manifest": [source], "required_analysis_ids": ["test-analysis"]}
    records = [{"id": "e1"}]
    analyses = [("test-analysis", "ANALYSIS-TEST")]
    if two:
        analyses.append(("followup-analysis", "ANALYSIS-SECOND"))
        case["required_analysis_ids"].append("followup-analysis")
    for analysis_id, evidence_id in analyses:
        record = transport.derived(evidence_id)
        record["values"].update(analysis_id=analysis_id, case_id=case_id, input_sources=[source.copy()])
        rehash(record)
        records.append(record)
    return case, records


def rehash(record):
    record["source"]["sha256"] = p._sha(json.dumps(
        record["values"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))


@pytest.mark.parametrize("case_id,two,with_followup", [
    ("case-1", False, False),
    ("case-1", True, False),
    ("cart-discovery", False, False),
    ("case-1", True, True),
])
def test_preexecuted_required_analysis_needs_review_not_repeat_execution(monkeypatch, case_id, two, with_followup):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-never-send")
    read_ids = ["ANALYSIS-TEST"] + (["ANALYSIS-SECOND"] if two else [])
    calls, _, persisted, products, emit, accept, handoff = planned_transport(monkeypatch, [
        ("analysis_catalog", {}), ("read_evidence", {"evidence_ids": read_ids})])
    monkeypatch.setattr(a, "analyze_case", lambda *_: pytest.fail("Preexecuted analysis must not run again"))
    case, evidence = preexecuted_inputs(two=two, case_id=case_id)
    if with_followup:
        case["followup_context"] = {"evidence_ids": ["ANALYSIS-TEST"], "previous_decision": {}}
    before_case, before_evidence = copy.deepcopy(case), copy.deepcopy(evidence)
    result = asyncio.run(p.investigate(case, "The supplied hypothesis.", evidence, emit, lambda: False,
                                      accept_evidence=accept, accept_handoff=handoff))
    assert result["summary"]
    assert persisted == []
    assert result["metadata"]["accepted_analysis_ids"] == read_ids
    assert result["metadata"]["role_evidence_reads"]["bioinformatician"] == sorted(read_ids)
    assert any(product["sender"] == "reviewer" for product in products)
    bio = next(call for call in calls if "ROLE: bioinformatician." in call["instructions"])
    assert "read_evidence for every required result" in bio["instructions"]
    if not with_followup:
        assert "do not repeat a completed recipe" in bio["instructions"]
    assert case == before_case and evidence == before_evidence


@pytest.mark.parametrize("read_ids,two,expected", [
    (None, False, "Required role tools"),
    (["e1"], False, "must read every"),
    (["ANALYSIS-TEST"], True, "ANALYSIS-SECOND"),
    (["unaccepted-evidence"], False, "Required role tools"),
    (["ANALYSIS-TEST", "unaccepted-evidence"], False, "Required role tools"),
])
def test_required_analysis_review_rejects_missing_wrong_or_partial_reads(monkeypatch, read_ids, two, expected):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-never-send")
    plan = [("analysis_catalog", {})]
    if read_ids is not None:
        plan.append(("read_evidence", {"evidence_ids": read_ids}))
    calls, _, persisted, products, emit, accept, handoff = planned_transport(monkeypatch, plan)
    case, evidence = preexecuted_inputs(two=two)
    with pytest.raises(p.ProviderError, match=expected) as failure:
        asyncio.run(p.investigate(case, "The supplied hypothesis.", evidence, emit, lambda: False,
                                 accept_evidence=accept, accept_handoff=handoff))
    assert products == [] and persisted == []
    assert all("ROLE: bioinformatician." in call["instructions"] for call in calls)
    assert not calls[-1].get("tools")  # One bounded repair; no execution retry.
    expected_reads = [] if read_ids is None or "unaccepted-evidence" in read_ids else sorted(read_ids)
    assert failure.value.metadata["role_evidence_reads"]["bioinformatician"] == expected_reads


def test_preexecuted_required_analysis_still_requires_catalog_review(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-never-send")
    _, _, _, products, emit, accept, handoff = planned_transport(monkeypatch, [
        ("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]})])
    case, evidence = preexecuted_inputs()
    with pytest.raises(p.ProviderError, match="analysis_catalog"):
        asyncio.run(p.investigate(case, "The supplied hypothesis.", evidence, emit, lambda: False,
                                 accept_evidence=accept, accept_handoff=handoff))
    assert products == []


def test_ordinary_case_still_requires_executable_analysis_tool(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-never-send")
    _, _, _, products, emit, accept, handoff = planned_transport(monkeypatch, [
        ("analysis_catalog", {}), ("read_evidence", {"evidence_ids": ["ANALYSIS-TEST"]})])
    case, evidence = preexecuted_inputs()
    case.pop("required_analysis_ids")
    with pytest.raises(p.ProviderError, match="run_case_analysis"):
        asyncio.run(p.investigate(case, "The supplied hypothesis.", evidence, emit, lambda: False,
                                 accept_evidence=accept, accept_handoff=handoff))
    assert products == []


@pytest.mark.parametrize("damage", [
    "missing", "case", "hash", "source", "empty_source", "no_sources", "unmapped_source", "kind", "duplicate",
])
def test_invalid_preexecuted_results_fail_before_model_construction(monkeypatch, damage):
    case, evidence = preexecuted_inputs()
    record = evidence[-1]
    if damage == "missing":
        evidence.pop()
    elif damage == "case":
        record["values"]["case_id"] = "another-case"
        rehash(record)
    elif damage == "hash":
        record["source"]["sha256"] = "f" * 64
    elif damage in {"source", "empty_source", "no_sources", "unmapped_source"}:
        if damage == "source":
            record["values"]["input_sources"][0]["sha256"] = "c" * 64
        elif damage == "empty_source":
            record["values"]["input_sources"] = [{}]
        elif damage == "no_sources":
            record["values"]["input_sources"] = []
        else:
            record["values"]["input_sources"][0]["path"] = "different-study.csv"
        rehash(record)
    elif damage == "kind":
        record["kind"] = "preview"
    else:
        other = copy.deepcopy(record)
        other["id"] = "ANALYSIS-DUPLICATE"
        evidence.append(other)
    monkeypatch.setattr(p, "ModelSession", lambda *_: pytest.fail("Invalid required evidence must fail before a model session"))

    async def emit(*args, **kwargs):
        pass

    with pytest.raises(p.ProviderError, match="Scientist-required analysis"):
        asyncio.run(p.investigate(case, "The supplied hypothesis.", evidence, emit, lambda: False))
