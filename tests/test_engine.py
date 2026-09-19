"""End-to-end runs of the real orchestrator against the mock providers."""

from app.engine import run_investigation
from app.events import EventBus
from app.ingest import build_bundle
from app.models import PatientBundle, Report
from app.providers import build_providers


async def run(question: str, bundle: PatientBundle) -> tuple[Report, EventBus]:
    bus = EventBus("test-run")
    report = Report(run_id="test-run", question=question, bundle_summary=bundle.summary())
    await run_investigation(
        run_id="test-run",
        question=question,
        bundle=bundle,
        bus=bus,
        providers=build_providers(),
        report=report,
    )
    return report, bus


async def test_full_investigation_emits_the_shared_contract(sample_bundle):
    report, bus = await run("Why did this patient fail?", sample_bundle)

    types = [e.type for e in bus.history]
    assert types[0] == "run_started"
    assert types[-1] == "run_complete"
    assert bus.closed
    for required in ("agent_spawned", "agent_message", "tool_call", "tool_result", "finding"):
        assert required in types, required

    roles = {e.agent_role for e in bus.history}
    assert {"orchestrator", "genomics", "clinical", "literature", "critic"} <= roles

    # Every spawned specialist points at the orchestrator, so the UI can draw a tree.
    spawns = [e for e in bus.history if e.type == "agent_spawned"]
    assert spawns[0].agent_id == "orchestrator-0" and spawns[0].parent_id is None
    assert all(e.parent_id == "orchestrator-0" for e in spawns[1:])


async def test_every_finding_carries_provenance_and_confidence(sample_bundle):
    report, bus = await run("Why did this patient fail?", sample_bundle)

    assert report.status == "complete"
    assert report.findings
    for finding in report.findings:
        assert finding.provenance, finding.claim
        assert 0.0 <= finding.confidence <= 1.0
    assert {p.kind for f in report.findings for p in f.provenance} >= {"file", "nim", "pmid"}


async def test_open_question_lands_on_the_strongest_variant(sample_bundle):
    report, _ = await run("Why did this patient fail?", sample_bundle)

    assert report.verdict is not None
    assert not report.verdict.abstained
    assert "KRAS" in report.verdict.answer
    assert report.verdict.confidence > 0.5


async def test_specialists_communicate_through_the_blackboard(sample_bundle):
    _, bus = await run("Why did this patient fail?", sample_bundle)

    handoff = [
        e for e in bus.history
        if e.agent_role == "literature" and e.type == "agent_message"
        and "genomics" in e.payload.get("text", "").lower()
    ]
    assert handoff, "literature agent should pick up the genomics findings"
    assert handoff[0].parent_id.startswith("genomics")


async def test_contradicted_hypothesis_is_rejected_not_humoured(sample_bundle):
    question = "Did the patient fail because of the MTHFR C677T variant?"
    report, _ = await run(question, sample_bundle)

    assert report.verdict is not None
    answer = report.verdict.answer.lower()
    assert "does not support" in answer or "abstain" in answer
    contradicting = [f for f in report.findings if f.stance == "contradicts"]
    assert contradicting, "the benign MTHFR call should argue against the hypothesis"


async def test_empty_upload_abstains(sample_bundle):
    report, bus = await run("Why did this patient fail?", PatientBundle())

    assert report.verdict is not None
    assert report.verdict.abstained
    assert report.verdict.answer.startswith("ABSTAIN")
    assert [e.type for e in bus.history][-1] == "run_complete"


async def test_hypothesis_with_no_bearing_evidence_abstains(sample_files):
    notes_only = build_bundle([f for f in sample_files if f[1].endswith(".txt")])
    report, _ = await run("Did the patient fail because of BRCA2?", notes_only)

    assert report.verdict is not None
    assert report.verdict.abstained
    assert report.verdict.confidence <= 0.3


async def test_runs_are_deterministic(sample_bundle):
    first, _ = await run("Why did this patient fail?", sample_bundle)
    second, _ = await run("Why did this patient fail?", sample_bundle)

    assert first.verdict.answer == second.verdict.answer
    assert [f.claim for f in first.findings] == [f.claim for f in second.findings]
