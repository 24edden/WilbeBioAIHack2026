from app.agents.critic import MIN_TOP_CONFIDENCE, evidence_gate
from app.models import Finding, Provenance


def finding(role, claim, confidence, stance="neutral", cited=True):
    return Finding(
        finding_id=f"f-{claim[:6]}",
        agent_id=f"{role}-1",
        agent_role=role,
        claim=claim,
        stance=stance,
        confidence=confidence,
        provenance=[Provenance(kind="file", ref="labs.csv", locator="line 3")] if cited else [],
    )


def test_no_findings_abstains():
    gate = evidence_gate([], hypothesis=None)
    assert gate.abstain
    assert "nothing to answer" in gate.reason


def test_uncited_claims_are_not_evidence():
    gate = evidence_gate([finding("genomics", "strong claim", 0.95, cited=False)], None)
    assert gate.abstain
    assert "cites a source" in gate.reason


def test_weak_evidence_abstains_even_when_it_all_agrees():
    findings = [finding("genomics", "weak", 0.4), finding("clinical", "also weak", 0.35)]
    gate = evidence_gate(findings, hypothesis=None)
    assert gate.abstain
    assert f"{MIN_TOP_CONFIDENCE:.2f} floor" in gate.reason


def test_strong_corroborated_evidence_passes():
    findings = [finding("genomics", "strong", 0.92), finding("literature", "agrees", 0.7)]
    gate = evidence_gate(findings, hypothesis=None)
    assert not gate.abstain
    assert all(check["passed"] for check in gate.checks)


def test_hypothesis_with_balanced_evidence_abstains():
    findings = [
        finding("genomics", "for", 0.8, stance="supports"),
        finding("literature", "against", 0.8, stance="contradicts"),
    ]
    gate = evidence_gate(findings, hypothesis="MTHFR C677T")
    assert gate.abstain
    assert gate.disagreement
    assert "evenly matched" in gate.reason


def test_hypothesis_nothing_bears_on_abstains():
    findings = [finding("clinical", "unrelated context", 0.9, stance="neutral")]
    gate = evidence_gate(findings, hypothesis="MTHFR C677T")
    assert gate.abstain
    assert "either way" in gate.reason


def test_hypothesis_with_decisive_evidence_answers():
    findings = [
        finding("genomics", "against", 0.9, stance="contradicts"),
        finding("literature", "also against", 0.7, stance="contradicts"),
    ]
    gate = evidence_gate(findings, hypothesis="MTHFR C677T")
    assert not gate.abstain
    assert not gate.disagreement


def test_one_specialist_cannot_corroborate_itself():
    gate = evidence_gate([finding("genomics", "strong", 0.95),
                          finding("genomics", "same voice", 0.9)], None)
    assert gate.abstain
    assert "corroboration" in gate.reason


def test_unrelated_strong_evidence_cannot_upgrade_a_weak_hypothesis():
    gate = evidence_gate([finding("genomics", "weak", 0.1, stance="supports"),
                          finding("clinical", "unrelated", 0.95),
                          finding("literature", "context", 0.8)], "BRCA2")
    assert gate.abstain
    assert "confidence floor" in gate.reason
