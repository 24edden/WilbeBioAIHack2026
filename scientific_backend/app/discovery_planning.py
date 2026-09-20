"""Case-bound proposals, with no execution or provider transport.

Only accepted role handoffs may share proposals downstream. Configuration is a
planning observation; execution independently rechecks provider and source state.
"""
from __future__ import annotations

import copy
import re

from .store import digest

EXECUTION = "proposal_only; reviewed governance selects under pinned auto_continue policy, or scientist selects follow-up"
ROLES = frozenset({"bioinformatician", "statistician", "clinical_scientist",
                  "clinical_pharmacologist", "molecular_scientist",
                  "translational_scientist", "assay_scientist", "coordinator", "reviewer"})
KINDS = frozenset({"data_analysis", "bionemo_public_structure"})
MAX_CITATIONS = 12


def _text(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{label} must contain 1–{maximum} characters.")
    return value


def _hash(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError(label + " must be an exact SHA-256 value.")
    return value


def _list(value, label, maximum):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f"{label} must be a list of at most {maximum} items.")
    return value


def _sources(value, label, maximum=64):
    result = {}
    for item in _list(value, label, maximum):
        if not isinstance(item, dict):
            raise ValueError(label + " must contain source records.")
        path = _text(item.get("path"), label + " path", 500)
        checksum = _hash(item.get("sha256"), label + " hash")
        if path in result:
            raise ValueError(label + " has duplicate source paths.")
        result[path] = checksum
    return result


def _evidence_index(evidence):
    records = {}
    for item in _list(evidence, "Accepted evidence", 512):
        if not isinstance(item, dict):
            raise ValueError("Accepted evidence must contain records.")
        evidence_id = _text(item.get("id"), "Accepted evidence ID", 200)
        if evidence_id in records:
            raise ValueError("Accepted evidence IDs must be unique.")
        records[evidence_id] = item
    return records


def _recipe_index(recipes):
    result = {}
    for item in _list(recipes, "Approved recipes", 64):
        if not isinstance(item, dict):
            raise ValueError("Approved recipes must contain records.")
        recipe_id = _text(item.get("id"), "Recipe ID", 160)
        if recipe_id in result or item.get("kind") not in KINDS:
            raise ValueError("Approved recipes require unique IDs and registered kinds.")
        result[recipe_id] = item
    return result


def _already_completed(records, recipe, required):
    completed = []
    for evidence_id, item in records.items():
        values = item.get("values", {})
        if not isinstance(values, dict) or recipe["id"] not in {
                values.get("analysis_id"), values.get("structural_recipe_id")}:
            continue
        # Another source version is not completion for this registered recipe.
        # Legacy recipes with no input declarations retain accepted-ID behavior.
        actual = _sources(values.get("input_sources", []), "Evidence input sources")
        if any(actual.get(path) != checksum for path, checksum in required.items()):
            continue
        completed.append(evidence_id)
    return completed[:MAX_CITATIONS]


def planning_options(case: dict, evidence: list[dict], recipes: list[dict], bionemo_status: str) -> list[dict]:
    """Describe bounded registered methods without executing them."""
    _text(case.get("id"), "Case ID", 160)
    _text(bionemo_status, "BioNeMo configuration status", 80)
    pinned = _sources(case.get("source_manifest", []), "Case source manifest", maximum=512)
    records = _evidence_index(evidence)
    options = []
    for recipe in _recipe_index(recipes).values():
        required = _sources(recipe.get("input_sources", []), "Recipe input sources")
        prerequisites = [_text(item, "Recipe prerequisite", 300) for item in
                         _list(recipe.get("prerequisites", []), "Recipe prerequisites", 12)]
        reasons = []
        for path, checksum in required.items():
            if path not in pinned:
                reasons.append("Source is absent from this case's pinned manifest: " + path)
            elif pinned[path] != checksum:
                reasons.append("Pinned source version differs from the registered recipe: " + path)
        if recipe["kind"] == "bionemo_public_structure" and bionemo_status not in {"configured", "verified"}:
            reasons.append("A NVIDIA credential or supported NIM configuration is required; no inference was submitted.")
        completed = _already_completed(records, recipe, required)
        if completed:
            readiness = "completed"
            reasons = ["Accepted evidence already records this recipe for the same registered input versions; reuse it rather than resubmitting."]
        else:
            readiness = "needs_inputs" if reasons else "unperformed"
        options.append({
            "id": recipe["id"], "kind": recipe["kind"],
            "title": _text(recipe.get("title", recipe["id"]), "Recipe title", 300),
            "description": str(recipe.get("description", "Registered source-qualified follow-up."))[:1600],
            "prerequisites": prerequisites,
            "input_sources": [{"path": path, "sha256": checksum} for path, checksum in required.items()],
            "recipe_sha256": digest(recipe), "readiness": readiness,
            "already_completed_evidence_ids": completed, "readiness_reasons": reasons,
            "execution": EXECUTION,
        })
    return options


def _make_proposal(*, role, case, hypothesis_sha256, evidence, recipes, bionemo_status,
                   analysis_id, scientific_question, rationale, decision_it_could_change, evidence_ids):
    if role not in ROLES:
        raise ValueError("The proposing role is not registered.")
    _hash(hypothesis_sha256, "Hypothesis version")
    _text(analysis_id, "Analysis ID", 160)
    options = {item["id"]: item for item in planning_options(case, evidence, recipes, bionemo_status)}
    option = options.get(analysis_id)
    if option is None:
        raise ValueError("Proposal must name a registered recipe for this case.")
    scientific_question = _text(scientific_question, "Scientific question", 500)
    rationale = _text(rationale, "Proposal rationale", 700)
    decision_it_could_change = _text(decision_it_could_change, "Decision it could change", 500)
    citations = _list(evidence_ids, "Proposal evidence IDs", MAX_CITATIONS)
    if not citations:
        raise ValueError("Proposal must cite accepted evidence.")
    for value in citations:
        _text(value, "Proposal evidence ID", 200)
    if len(citations) != len(set(citations)):
        raise ValueError("Proposal evidence IDs must be unique.")
    records = _evidence_index(evidence)
    if not set(citations).issubset(records):
        raise ValueError("Proposal must cite accepted evidence from this case.")
    if option["readiness"] == "completed":
        # The harness does not retain this response as a new proposal.
        citations = list(dict.fromkeys(citations + option["already_completed_evidence_ids"]))[:MAX_CITATIONS]
        first_completed = option["already_completed_evidence_ids"][0]
        if first_completed not in citations:
            citations[-1] = first_completed
    versions = {}
    for evidence_id in citations:
        source = records[evidence_id].get("source") or {}
        versions[evidence_id] = _hash(source.get("sha256"), "Cited evidence source version")
    pinned = _sources(case.get("source_manifest", []), "Case source manifest", maximum=512)
    return {
        "id": "proposal-" + digest([role, case["id"], hypothesis_sha256, analysis_id, option["recipe_sha256"]])[:24],
        "status": "already_completed" if option["readiness"] == "completed" else "proposed",
        "qualification": option["readiness"], "case_id": case["id"], "proposing_role": role,
        "owner": "molecular_scientist" if option["kind"] == "bionemo_public_structure" else "bioinformatician",
        "analysis_id": analysis_id, "kind": option["kind"], "title": option["title"],
        "scientific_question": scientific_question, "rationale": rationale,
        "decision_it_could_change": decision_it_could_change, "evidence_ids": list(citations),
        "input_versions": {"hypothesis_sha256": hypothesis_sha256, "evidence_versions": versions,
                           "source_versions": {source["path"]: pinned.get(source["path"])
                                               for source in option["input_sources"]}},
        "recipe_sha256": option["recipe_sha256"], "prerequisites": option["prerequisites"],
        "readiness_reasons": option["readiness_reasons"],
        "already_completed_evidence_ids": option["already_completed_evidence_ids"],
        "bionemo_status": bionemo_status, "execution": EXECUTION,
    }


def build_proposal(*, role, case, hypothesis, evidence, recipes, bionemo_status, analysis_id,
                   scientific_question, rationale, decision_it_could_change, evidence_ids) -> dict:
    """Bind a role recommendation to accepted evidence and a registered method."""
    _text(hypothesis, "Original hypothesis", 24_000)
    return _make_proposal(role=role, case=case, hypothesis_sha256=digest(hypothesis), evidence=evidence,
                          recipes=recipes, bionemo_status=bionemo_status, analysis_id=analysis_id,
                          scientific_question=scientific_question, rationale=rationale,
                          decision_it_could_change=decision_it_could_change, evidence_ids=evidence_ids)


def validate_proposal(proposal, case, evidence, hypothesis_sha256, role) -> dict:
    """Recheck identities at handoff acceptance, granting no execution authority.

    Configuration is the recorded planning observation, not a promise that a
    later request works. Incomplete inputs are valid proposals, not fake success.
    """
    from .followups import approved_catalog

    if not isinstance(proposal, dict):
        raise ValueError("Proposal must be a structured record.")
    expected = _make_proposal(
        role=role, case=case, hypothesis_sha256=hypothesis_sha256, evidence=evidence,
        recipes=approved_catalog(case["id"]), bionemo_status=proposal.get("bionemo_status"),
        analysis_id=proposal.get("analysis_id"), scientific_question=proposal.get("scientific_question"),
        rationale=proposal.get("rationale"), decision_it_could_change=proposal.get("decision_it_could_change"),
        evidence_ids=proposal.get("evidence_ids"),
    )
    if proposal != expected:
        raise ValueError("Proposal identity, registered recipe, input version or qualification differs from its accepted context.")
    return copy.deepcopy(expected)
