import json

from fastapi.testclient import TestClient

from app.events import EventBus
from app.main import app
from app.models import Finding, PatientBundle, Provenance, Report, SourceFile, NoteSection
from app.weak_points import assess_weak_points


def finding(identifier, role, stance="neutral", source="notes.txt"):
    return Finding(finding_id=identifier, agent_id=f"{role}-1", agent_role=role,
        claim=f"Recorded claim {identifier}", stance=stance, confidence=0.8,
        provenance=[Provenance(kind="file", ref=source, locator="line 1")])


def bundle():
    return PatientBundle(files=[SourceFile(file_id="file-1", filename="notes.txt", kind="notes")],
                         notes=[NoteSection(text="A source observation.", source_line=1)])


def report(findings):
    return Report(run_id="test", question="Question", findings=findings, run_mode="live")


def test_unassessed_default_is_distinct_from_assessed_without_detected_items():
    result = report([finding("one", "clinical"), finding("two", "literature")])
    assert result.weak_points.status == "not_assessed"
    assessed = assess_weak_points(result, bundle(), [])
    assert assessed.status == "assessed" and assessed.items == []


def test_empty_evidence_has_concrete_gaps_without_invented_conflicts():
    assessed = assess_weak_points(report([]), PatientBundle(), [], "BRCA2")
    ids = {item.id for item in assessed.items}
    assert {"empty-input", "no-findings", "hypothesis-unaddressed"} <= ids
    assert not any(item.category == "conflicting_findings" for item in assessed.items)
    assert all(item.next_evidence for item in assessed.items)


def test_conflict_references_actual_findings_and_sources_not_invented_studies():
    findings = [finding("supports-1", "genomics", "supports"),
                finding("contradicts-1", "literature", "contradicts")]
    assessed = assess_weak_points(report(findings), bundle(), [], "named mechanism")
    conflict = next(item for item in assessed.items if item.category == "conflicting_findings")
    assert conflict.finding_ids == ["supports-1", "contradicts-1"]
    assert [source.ref for source in conflict.sources] == ["notes.txt"]
    assert "not a verified conflict" in conflict.rationale
    assert not any(source.kind == "pmid" for source in conflict.sources)


def test_neutral_or_same_direction_findings_do_not_fabricate_conflict():
    findings = [finding("one", "clinical", "supports"), finding("two", "literature", "neutral")]
    assessed = assess_weak_points(report(findings), bundle(), [], "named mechanism")
    assert not any(item.category == "conflicting_findings" for item in assessed.items)


def test_missing_source_is_explicit_and_linked():
    findings = [finding("missing", "clinical", source="not-uploaded.txt")]
    assessed = assess_weak_points(report(findings), bundle(), [])
    gap = next(item for item in assessed.items if item.category == "source_gap")
    assert gap.finding_ids == ["missing"]
    assert gap.sources[0].ref == "not-uploaded.txt"


def test_provider_error_is_not_treated_as_contradictory_evidence():
    bus = EventBus("test")
    bus.emit("error", agent_id="genomics-1", agent_role="genomics", payload={"error": "NIM unavailable"})
    assessed = assess_weak_points(report([finding("one", "clinical")]), bundle(), bus.history)
    error = next(item for item in assessed.items if item.category == "provider_failure")
    assert "genomics-1" in error.rationale
    assert error.finding_ids == []
    assert not any(item.category == "conflicting_findings" for item in assessed.items)


def test_report_and_sse_deliver_identical_assessment():
    with TestClient(app) as client:
        files = client.post("/demo/sample-patient").json()["files"]
        run_id = client.post("/investigate", json={"question": "Why did this patient fail?",
            "file_ids": [file["file_id"] for file in files]}).json()["run_id"]
        events = [json.loads(line[6:]) for line in client.get(f"/events/{run_id}").text.splitlines()
                  if line.startswith("data: ")]
        result = client.get(f"/report/{run_id}").json()
    assessment = result["weak_points"]
    assert assessment == events[-1]["payload"]["weak_points"]
    assert assessment["status"] == "assessed"
    assert any(item["id"] == "simulated-models" for item in assessment["items"])
    assert not any(item["category"] == "source_gap" for item in assessment["items"])
    finding_ids = {finding["finding_id"] for finding in result["findings"]}
    assert all(set(item["finding_ids"]) <= finding_ids for item in assessment["items"])


def test_failed_run_still_exports_the_error_assessment(monkeypatch):
    from app.providers.mock import MockReasoningProvider

    async def fail(*args, **kwargs):
        raise RuntimeError("Synthetic provider failure")

    monkeypatch.setattr(MockReasoningProvider, "plan", fail)
    with TestClient(app) as client:
        files = client.post("/demo/sample-patient").json()["files"]
        run_id = client.post("/investigate", json={"question": "Investigate", "file_ids": [f["file_id"] for f in files]}).json()["run_id"]
        events = [json.loads(line[6:]) for line in client.get(f"/events/{run_id}").text.splitlines() if line.startswith("data: ")]
        result = client.get(f"/report/{run_id}").json()
    assert result["status"] == "error"
    assert result["weak_points"] == events[-1]["payload"]["weak_points"]
    assert any(item["category"] == "provider_failure" for item in result["weak_points"]["items"])
