"""Claims must resolve to actual tool evidence, including across uploaded files."""

import pytest

from app.agents.base import Blackboard, RunContext
from app.agents.clinical import ClinicalAgent
from app.agents.genomics import GenomicsAgent
from app.agents.literature import LiteratureAgent
from app.events import EventBus
from app.ingest import build_bundle, parse_labs
from app.providers import build_providers
from app.providers.base import ClaimDraft, ReasoningStep


def context(bundle):
    return RunContext(run_id="grounding", question="Why did treatment fail?", bundle=bundle,
                      bus=EventBus("grounding"), providers=build_providers(), blackboard=Blackboard())


@pytest.mark.parametrize("agent_type", [GenomicsAgent, LiteratureAgent, ClinicalAgent])
async def test_unmatched_model_claims_are_withheld(agent_type, sample_bundle, monkeypatch):
    ctx = context(sample_bundle)
    ctx.blackboard.expect(set())

    async def invented(*args, **kwargs):
        return ReasoningStep("Review", [ClaimDraft("Invented claim", confidence=0.99,
            detail={"label": "NONEXISTENT", "pmid": "000000", "name": "fake", "source_line": 999})])

    monkeypatch.setattr(ctx.providers.reasoning, "step", invented)
    agent = agent_type("test-agent", "Investigate", ctx)
    await agent.run()
    assert not agent.findings
    assert not [e for e in ctx.bus.history if e.type == "error"]
    assert any("Withheld" in e.payload.get("text", "") for e in ctx.bus.history)


async def test_genomics_cites_each_variants_actual_upload():
    bundle = build_bundle([
        ("one", "first.vcf", "12\t25398284\trs121913529\tC\tT\t.\tPASS\tGENE=KRAS;CSQ=p.Gly12Asp"),
        ("two", "second.vcf", "1\t97915614\trs3918290\tC\tT\t.\tPASS\tGENE=DPYD;CSQ=c.1905+1G>A"),
    ])
    agent = GenomicsAgent("genomics-1", "Investigate", context(bundle))
    await agent.run()
    assert len(agent.findings) == 2
    assert {f.detail["gene"]: f.provenance[0].ref for f in agent.findings} == {
        "KRAS": "first.vcf", "DPYD": "second.vcf"}


async def test_clinical_provenance_uses_original_note_lines_and_lab_files():
    bundle = build_bundle([
        ("one", "first.csv", "test,value,date\nCEA,1,2026-01-01\n"),
        ("two", "second.csv", "test,value,date\nCEA,9,2026-02-01\n"),
        ("notes", "notes.txt", "# History\n\nFine.\n\n# Treatment\n\nGrade 3 neutropenia.\n"),
    ])
    agent = ClinicalAgent("clinical-1", "Investigate", context(bundle))
    await agent.run()
    trend = next(f for f in agent.findings if f.detail.get("name") == "CEA")
    assert {p.ref for p in trend.provenance} == {"first.csv", "second.csv"}
    toxicity = next(f for f in agent.findings if f.detail.get("terms"))
    assert all(p.ref == "notes.txt" and p.locator == "line 7" for p in toxicity.provenance)


def test_nonfinite_lab_values_are_unknown_and_json_serializable():
    labs = parse_labs("test,value,ref_high\nCEA,NaN,5\nCEA,inf,5\n")
    assert all(lab.value is None and lab.flag == "unknown" for lab in labs)


def test_multiline_csv_keeps_physical_source_lines():
    labs = parse_labs('test,value,unit\nCEA,1,"ng\n/mL"\nCEA,9,ng/mL\n')
    assert [lab.source_line for lab in labs] == [2, 4]


async def test_same_variant_in_two_files_retains_each_source():
    row = "12\t25398284\trs121913529\tC\tT\t.\tPASS\tGENE=KRAS;CSQ=p.Gly12Asp"
    bundle = build_bundle([("one", "first.vcf", row), ("two", "second.vcf", row)])
    agent = GenomicsAgent("genomics-1", "Investigate", context(bundle))
    await agent.run()
    assert len(agent.findings) == 2
    assert {f.provenance[0].ref for f in agent.findings} == {"first.vcf", "second.vcf"}
