"""Offline proposal contracts; these helpers never execute provider requests."""
import copy

import pytest

from app import discovery_planning as planning, followups
from app.store import digest

SOURCE = {"path": "sources/example.tsv", "sha256": "a" * 64}
CASE = {"id": "case-one", "source_manifest": [SOURCE]}
EVIDENCE = [{"id": "source-observation", "source": {"sha256": "b" * 64}}]
RECIPE = {"id": "registered-comparison", "kind": "data_analysis", "title": "Recompute the contrast",
          "input_sources": [SOURCE], "prerequisites": ["Pinned source table"]}
NVIDIA = {**RECIPE, "id": "registered-structure", "kind": "bionemo_public_structure",
          "title": "Compare qualified monomers"}
HYPOTHESIS = "The user's exact hypothesis.\n"


def proposal(**changes):
    arguments = dict(role="bioinformatician", case=CASE, hypothesis=HYPOTHESIS, evidence=EVIDENCE,
                     recipes=[RECIPE, NVIDIA], bionemo_status="configured", analysis_id=RECIPE["id"],
                     scientific_question="Does the source contrast distinguish the proposed explanations?",
                     rationale="Recompute the source contrast before assigning a direction of effect.",
                     decision_it_could_change="Which mechanism should receive experimental follow-up.",
                     evidence_ids=[EVIDENCE[0]["id"]])
    arguments.update(changes)
    return planning.build_proposal(**arguments)


@pytest.fixture
def registry(monkeypatch):
    def catalog(case_id):
        return [copy.deepcopy(RECIPE), copy.deepcopy(NVIDIA)] if case_id == CASE["id"] else []
    monkeypatch.setattr(followups, "approved_catalog", catalog)


def test_registered_options_are_proposal_only_and_tolerate_minimal_catalog_metadata():
    options = planning.planning_options(CASE, EVIDENCE, [RECIPE, NVIDIA], "configured")
    assert [item["readiness"] for item in options] == ["unperformed", "unperformed"]
    assert all(item["execution"] == planning.EXECUTION for item in options)
    assert options[0]["recipe_sha256"] == digest(RECIPE)
    minimal = planning.planning_options({"id": "case-one"}, EVIDENCE,
                                        [{"id": "minimal", "kind": "data_analysis"}], "missing")[0]
    assert minimal["input_sources"] == []
    assert minimal["title"] == "minimal" and minimal["readiness"] == "unperformed"


@pytest.mark.parametrize("manifest, provider, expected_count", [
    ([], "configured", 1),
    ([{**SOURCE, "sha256": "c" * 64}], "configured", 1),
    ([SOURCE], "missing", 1),
    ([], "missing", 2),
])
def test_source_and_provider_readiness_are_explicit(manifest, provider, expected_count):
    option = planning.planning_options({**CASE, "source_manifest": manifest}, EVIDENCE, [NVIDIA], provider)[0]
    assert option["readiness"] == "needs_inputs"
    assert len(option["readiness_reasons"]) == expected_count
    assert option["already_completed_evidence_ids"] == []


def test_binder_prerequisites_do_not_hide_a_public_structure_recipe():
    case = {**CASE, "molecular_inputs": {}, "missing_inputs": ["No exact CAR binder sequence"]}
    option = planning.planning_options(case, EVIDENCE, [NVIDIA], "verified")[0]
    assert option["readiness"] == "unperformed"
    item = proposal(case=case, analysis_id=NVIDIA["id"])
    assert item["owner"] == "molecular_scientist"
    assert item["proposing_role"] == "bioinformatician"


def test_build_and_handoff_preserve_exact_source_versions_and_identity(registry):
    item = proposal()
    assert item == proposal()
    assert item["input_versions"]["hypothesis_sha256"] == digest(HYPOTHESIS)
    assert item["input_versions"]["evidence_versions"] == {"source-observation": "b" * 64}
    assert item["input_versions"]["source_versions"] == {SOURCE["path"]: SOURCE["sha256"]}
    assert item["status"] == "proposed" and item["qualification"] == "unperformed"
    assert planning.validate_proposal(item, CASE, EVIDENCE, digest(HYPOTHESIS), "bioinformatician") == item
    assert proposal(role="statistician")["id"] != item["id"]
    assert proposal(hypothesis=HYPOTHESIS.rstrip())["id"] != item["id"]


def test_input_missing_proposal_is_valid_and_never_claims_execution(registry):
    case = {**CASE, "source_manifest": []}
    item = proposal(case=case, analysis_id=NVIDIA["id"], bionemo_status="missing")
    checked = planning.validate_proposal(item, case, EVIDENCE, digest(HYPOTHESIS), "bioinformatician")
    assert checked["status"] == "proposed" and checked["qualification"] == "needs_inputs"
    assert checked["execution"] == planning.EXECUTION
    assert checked["input_versions"]["source_versions"][SOURCE["path"]] is None


@pytest.mark.parametrize("changes", [
    {"analysis_id": "unregistered"},
    {"evidence_ids": ["fabricated"]},
    {"evidence_ids": []},
    {"evidence_ids": ["source-observation", "source-observation"]},
    {"role": "unregistered-role"},
    {"scientific_question": " "},
    {"rationale": "x" * 701},
    {"decision_it_could_change": "x" * 501},
    {"evidence": [{"id": "source-observation", "source": {"sha256": "not-a-version"}}]},
])
def test_invalid_proposal_inputs_are_rejected(changes):
    with pytest.raises(ValueError):
        proposal(**changes)


def test_wrong_case_catalog_is_rejected_at_handoff(registry):
    item = proposal()
    with pytest.raises(ValueError, match="registered recipe"):
        planning.validate_proposal(item, {**CASE, "id": "other-case"}, EVIDENCE, digest(HYPOTHESIS), "bioinformatician")


@pytest.mark.parametrize("field, value", [
    ("id", "forged-proposal"), ("owner", "statistician"), ("proposing_role", "reviewer"),
    ("case_id", "other-case"), ("kind", "bionemo_public_structure"), ("recipe_sha256", "d" * 64),
    ("qualification", "completed"), ("status", "completed"), ("execution", "execute_now"),
    ("input_versions", {"hypothesis_sha256": "d" * 64, "evidence_versions": {"source-observation": "e" * 64}}),
])
def test_forged_server_fields_and_version_changes_are_rejected(registry, field, value):
    item = proposal()
    item[field] = value
    with pytest.raises(ValueError, match="differs"):
        planning.validate_proposal(item, CASE, EVIDENCE, digest(HYPOTHESIS), "bioinformatician")


def test_accepted_evidence_and_recipe_changes_invalidate_the_proposal(registry, monkeypatch):
    item = proposal()
    changed_evidence = [{**EVIDENCE[0], "source": {"sha256": "c" * 64}}]
    with pytest.raises(ValueError, match="differs"):
        planning.validate_proposal(item, CASE, changed_evidence, digest(HYPOTHESIS), "bioinformatician")
    monkeypatch.setattr(followups, "approved_catalog", lambda case_id: [{**RECIPE, "description": "Changed method"}])
    with pytest.raises(ValueError, match="differs"):
        planning.validate_proposal(item, CASE, EVIDENCE, digest(HYPOTHESIS), "bioinformatician")


def completed(recipe=NVIDIA, source=SOURCE):
    return {"id": "accepted-computation", "source": {"sha256": "c" * 64},
            "values": {"structural_recipe_id": recipe["id"], "input_sources": [source]}}


def test_completed_prediction_returns_existing_evidence_without_resubmission(registry):
    evidence = EVIDENCE + [completed()]
    item = proposal(evidence=evidence, analysis_id=NVIDIA["id"], bionemo_status="missing")
    assert item["status"] == "already_completed" and item["qualification"] == "completed"
    assert item["already_completed_evidence_ids"] == ["accepted-computation"]
    assert "accepted-computation" in item["evidence_ids"]
    assert planning.validate_proposal(item, CASE, evidence, digest(HYPOTHESIS), "bioinformatician") == item


def test_old_source_version_is_not_mistaken_for_completed_current_work():
    evidence = EVIDENCE + [completed(source={**SOURCE, "sha256": "d" * 64})]
    item = proposal(evidence=evidence, analysis_id=NVIDIA["id"])
    assert item["status"] == "proposed" and item["already_completed_evidence_ids"] == []


def test_catalog_and_citations_have_bounds():
    with pytest.raises(ValueError, match="64"):
        planning.planning_options(CASE, EVIDENCE, [RECIPE] * 65, "configured")
    with pytest.raises(ValueError, match="12"):
        proposal(evidence_ids=["id-" + str(i) for i in range(13)])
    with pytest.raises(ValueError, match="unique"):
        planning.planning_options(CASE, EVIDENCE, [RECIPE, RECIPE], "configured")

