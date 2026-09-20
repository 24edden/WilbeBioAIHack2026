"""Pure acceptance checks for scoped hypothesis states and useful continuation.

These checks establish identity, evidence provenance and execution eligibility.
They cannot prove that a reviewer's scientific interpretation is correct.
"""
from __future__ import annotations

import copy
import re

from .discovery_planning import planning_options
from .provider_schemas import HypothesisGovernance
from .store import digest

SCHEMA = "team-tbd-hypothesis-governance"
VERSION = 1
INTERPRETATION_SCOPE = "reviewer_judgment; contract_validation_is_not_scientific_proof"
METADATA_FIELDS = frozenset({"schema", "version", "hypothesis_sha256", "evidence_sha256",
                             "evidence_versions", "accepted_evidence_versions", "recipe_versions",
                             "interpretation_scope"})
IDENTITY_FIELDS = ("statement", "origin", "source_quote", "scope", "scope_type")
CITATION_FIELDS = ("supporting_evidence_ids", "contradicting_evidence_ids", "test_evidence_ids")
UNAVAILABLE_STATUSES = frozenset({"missing", "blocked", "failed", "unavailable", "pending", "incomplete"})


def _text(value, label, maximum, *, empty=False):
    if not isinstance(value, str) or len(value) > maximum or (not empty and not value.strip()):
        raise ValueError(f"{label} must be {'0' if empty else '1'}–{maximum} characters of meaningful text.")
    return value


def _identifier(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,79}", value):
        raise ValueError(label + " must be a stable identifier of at most 80 safe characters.")
    return value


def _identifiers(value, label, maximum=16):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f"{label} must be a list of at most {maximum} identifiers.")
    if any(not isinstance(item, str) or not item.strip() or len(item) > 200 for item in value):
        raise ValueError(label + " contains an invalid identifier.")
    if len(value) != len(set(value)):
        raise ValueError(label + " must not contain duplicate identifiers.")
    return value


def _evidence(evidence):
    if not isinstance(evidence, list) or len(evidence) > 512:
        raise ValueError("Accepted evidence must be a list of at most 512 records.")
    records, versions = {}, {}
    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError("Accepted evidence must contain source records.")
        evidence_id = _text(item.get("id"), "Evidence ID", 200)
        source = item.get("source")
        checksum = source.get("sha256") if isinstance(source, dict) else None
        if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
            raise ValueError("Every accepted evidence record must carry its exact source SHA-256.")
        if evidence_id in records:
            raise ValueError("Accepted evidence IDs must be unique.")
        records[evidence_id], versions[evidence_id] = item, checksum
    return records, versions


def _prediction(record):
    values = record.get("values", {})
    return (record.get("kind") == "prediction"
            or (isinstance(values, dict) and bool(values.get("structural_recipe_id"))))


def _usable(record):
    values = record.get("values", {})
    if record.get("kind") in UNAVAILABLE_STATUSES | {"gap", "limitation"}:
        return False
    statuses = [record.get("status"), record.get("result_status")]
    if isinstance(values, dict):
        statuses.extend([values.get("status"), values.get("result_status")])
    return not any(isinstance(status, str) and status in UNAVAILABLE_STATUSES for status in statuses)


def _substantive_rationale(item):
    # A length check only excludes placeholders; semantic sufficiency belongs to
    # independent scientific review, not a guessed numerical confidence cutoff.
    if len(item["rationale"].strip()) < 30:
        raise ValueError("Probable or ruled-out states require a substantive scoped rationale.")


def _validate_state(item, records):
    if item["status"] == "possible":
        return
    _substantive_rationale(item)
    biological = item["scope_type"] == "biological"

    def supported(ids):
        return any(_usable(records[eid]) and (not biological or not _prediction(records[eid])) for eid in ids)

    if item["status"] == "probable":
        if not supported(item["supporting_evidence_ids"]):
            raise ValueError("Probable requires accepted support; prediction-only evidence cannot establish a biological probability judgment.")
    else:
        if not item["contradicting_evidence_ids"] or not item["test_evidence_ids"]:
            raise ValueError("Clearly ruled out requires contradictory evidence and a performed falsification test.")
        if not supported(item["contradicting_evidence_ids"]) or not supported(item["test_evidence_ids"]):
            raise ValueError("Missing data or prediction-only evidence cannot establish a biological exclusion.")
        _text(item["falsification_test"], "Performed falsification test", 1200)
        _text(item["falsification_result"], "Falsification result", 1600)


def _previous_governance(previous):
    if previous is None:
        return None
    if not isinstance(previous, dict):
        raise ValueError("Previous governance must be a preserved structured decision.")
    if "governance" in previous or "prior_governance" in previous:
        current = previous.get("governance")
        previous = current if current is not None else previous.get("prior_governance")
    if previous is None:
        return None
    if not isinstance(previous, dict) or not isinstance(previous.get("hypotheses"), list):
        raise ValueError("Previous governance lacks its preserved hypothesis ledger.")
    return previous


def _validate_history(current, previous, versions, hypothesis_hash):
    if previous is None:
        return
    if previous.get("hypothesis_sha256") != hypothesis_hash:
        raise ValueError("Previous governance belongs to another original hypothesis.")
    previous_ids = [item.get("hypothesis_id") for item in previous["hypotheses"]]
    if len(previous_ids) != len(set(previous_ids)) or not set(previous_ids).issubset(current):
        raise ValueError("Previously tracked hypotheses cannot be duplicated or silently dropped.")
    # The full accepted snapshot avoids treating old-but-newly-cited evidence as
    # a new measurement when reopening an excluded hypothesis.
    old_versions = previous.get("accepted_evidence_versions")
    for old in previous["hypotheses"]:
        new = current[old["hypothesis_id"]]
        for field in IDENTITY_FIELDS:
            old_value = old.get(field, "biological" if field == "scope_type" else None)
            if new[field] != old_value:
                raise ValueError("A reused hypothesis ID cannot change its statement, origin, source or scope.")
        if old.get("status") == "clearly_ruled_out" and new["status"] != "clearly_ruled_out":
            cited = set().union(*(new[field] for field in CITATION_FIELDS))
            fresh = (isinstance(old_versions, dict) and
                     any(old_versions.get(eid) != versions[eid] for eid in cited))
            if not fresh or new["rationale"].strip() == str(old.get("rationale", "")).strip():
                raise ValueError("Reopening a ruled-out hypothesis requires new or changed accepted evidence and an explicit revised rationale.")


def validate_governance(governance, *, hypothesis: str, evidence: list, recipes: list,
                        followups: list, previous: dict | None = None, case: dict | None = None) -> dict:
    """Validate and normalize a reviewer ledger without any provider calls.

    next_action_id is a registered analysis ID, never a generated recommendation
    ID. Raw ready recommendations may pass scientific planning validation. The
    atomic execution boundary requalifies readiness separately; an operational
    failure does not retroactively rewrite the published scientific decision.
    """
    _text(hypothesis, "Original hypothesis", 24_000)
    if isinstance(governance, HypothesisGovernance):
        raw = governance.model_dump()
    elif isinstance(governance, dict):
        raw = copy.deepcopy(governance)
    else:
        raise ValueError("Hypothesis governance must be a structured ledger.")
    supplied_metadata = {key: raw.pop(key) for key in METADATA_FIELDS if key in raw}
    result = HypothesisGovernance.model_validate(raw).model_dump()
    records, accepted_versions = _evidence(evidence)
    if not isinstance(recipes, list) or len(recipes) > 64:
        raise ValueError("Registered recipes must contain at most 64 methods.")
    by_recipe = {}
    for recipe in recipes:
        if not isinstance(recipe, dict) or not isinstance(recipe.get("id"), str) or not recipe["id"]:
            raise ValueError("Every registered recipe needs an identifier.")
        if recipe["id"] in by_recipe:
            raise ValueError("Registered recipe IDs must be unique.")
        by_recipe[recipe["id"]] = recipe
    by_hypothesis, cited_ids, analysis_ids = {}, set(), set()
    for item in result["hypotheses"]:
        hypothesis_id = _identifier(item["hypothesis_id"], "Hypothesis ID")
        if hypothesis_id in by_hypothesis:
            raise ValueError("Hypothesis IDs must be unique.")
        by_hypothesis[hypothesis_id] = item
        _text(item["statement"], "Hypothesis statement", 2400)
        _text(item["scope"], "Hypothesis scope", 700)
        _text(item["rationale"], "Hypothesis rationale", 1600)
        _text(item["source_quote"], "Source quotation", 4000, empty=True)
        _text(item["blocker"], "Explicit blocker", 1000, empty=True)
        _text(item["falsification_test"], "Falsification test", 1200, empty=True)
        _text(item["falsification_result"], "Falsification result", 1600, empty=True)
        if item["origin"] == "user":
            if hypothesis_id != "primary" and not item["source_quote"].strip():
                raise ValueError("A user-supplied alternative needs an exact source quotation.")
            if item["source_quote"] and item["source_quote"] not in hypothesis:
                raise ValueError("User source quotation must occur exactly in the original hypothesis.")
        elif item["source_quote"]:
            raise ValueError("Agent-generated alternatives cannot claim a user source quotation.")
        for field in CITATION_FIELDS:
            ids = _identifiers(item[field], field)
            if not set(ids).issubset(records):
                raise ValueError("Hypothesis states must cite only accepted evidence.")
            cited_ids.update(ids)
        next_ids = _identifiers(item["next_analysis_ids"], "Next analysis IDs", maximum=8)
        if not set(next_ids).issubset(by_recipe):
            raise ValueError("Hypothesis next analyses must name registered recipes.")
        analysis_ids.update(next_ids)
        _validate_state(item, records)
    primary = by_hypothesis.get("primary")
    if primary is None or primary["origin"] != "user":
        raise ValueError("The ledger requires the original user hypothesis under ID primary.")
    hypothesis_hash = digest(hypothesis)
    _validate_history(by_hypothesis, _previous_governance(previous), accepted_versions, hypothesis_hash)
    _text(result["continuation_reason"], "Continuation or stopping reason", 1600)
    targets = _identifiers(result["target_hypothesis_ids"], "Target hypothesis IDs")
    if not set(targets).issubset(by_hypothesis):
        raise ValueError("Continuation targets must refer to this hypothesis ledger.")

    if result["stop_reason"] == "continue":
        action = result["next_action_id"]
        if action not in by_recipe:
            raise ValueError("Continuation requires one registered next action.")
        if not targets:
            raise ValueError("Continuation needs a hypothesis to test.")
        for target in targets:
            if by_hypothesis[target]["status"] == "clearly_ruled_out" or action not in by_hypothesis[target]["next_analysis_ids"]:
                raise ValueError("The next action must test a possible or probable target that names this analysis.")
        if not isinstance(followups, list) or len(followups) > 64:
            raise ValueError("Follow-ups must be a bounded list.")
        selected = [item.model_dump() if hasattr(item, "model_dump") else item for item in followups]
        selected = [item for item in selected if isinstance(item, dict) and item.get("analysis_id") == action]
        if (len(selected) != 1 or selected[0].get("kind") != by_recipe[action].get("kind")
                or selected[0].get("status") != "ready"
                or selected[0].get("requested_status", "ready") != "ready"
                or selected[0].get("executable", True) is not True):
            raise ValueError("The next action must also be a ready final follow-up recommendation.")
        # This checks pinned sources and same-version completion only. Provider
        # authority comes from the independently qualified follow-up boundary.
        planning_case = case if case is not None else {"id": "governance-validation", "source_manifest": []}
        option = next(item for item in planning_options(planning_case, evidence, recipes, "configured") if item["id"] == action)
        if option["readiness"] != "unperformed":
            raise ValueError("Continuation requires an unperformed action with qualified source versions.")
    else:
        if result["next_action_id"] is not None or targets:
            raise ValueError("A stopped investigation cannot also queue a next action or execution targets.")
        if result["stop_reason"] == "resolved_within_scope" and any(item["status"] == "possible" for item in by_hypothesis.values()):
            raise ValueError("Unresolved possible hypotheses cannot be declared resolved within scope.")
        for item in by_hypothesis.values():
            if item["status"] == "possible" and not item["blocker"].strip():
                raise ValueError("Every unresolved possible hypothesis needs an explicit blocker before stopping.")
        if not isinstance(followups, list) or len(followups) > 64:
            raise ValueError("Follow-ups must be a bounded list.")
        nominated = set().union(*(item["next_analysis_ids"] for item in by_hypothesis.values()
                                  if item["status"] in {"possible", "probable"}))
        ready = set()
        for followup in followups:
            item = followup.model_dump() if hasattr(followup, "model_dump") else followup
            if not isinstance(item, dict):
                continue
            action = item.get("analysis_id")
            if (isinstance(action, str) and action in nominated
                    and item.get("kind") == by_recipe[action].get("kind")
                    and item.get("status") == "ready"
                    and item.get("requested_status", "ready") == "ready"
                    and item.get("executable", True) is True):
                ready.add(action)
        if ready:
            planning_case = case if case is not None else {"id": "governance-validation", "source_manifest": []}
            options = planning_options(planning_case, evidence, recipes, "configured")
            if any(item["id"] in ready and item["readiness"] == "unperformed" for item in options):
                raise ValueError("A stopped investigation still nominates a ready, unperformed hypothesis test; continue or explicitly mark its unmet prerequisites.")

    metadata = {
        "schema": SCHEMA, "version": VERSION, "hypothesis_sha256": hypothesis_hash,
        "evidence_sha256": digest(evidence),
        "evidence_versions": {eid: accepted_versions[eid] for eid in sorted(cited_ids)},
        "accepted_evidence_versions": accepted_versions,
        "recipe_versions": {aid: digest(by_recipe[aid]) for aid in sorted(analysis_ids)},
        "interpretation_scope": INTERPRETATION_SCOPE,
    }
    for key, value in supplied_metadata.items():
        if value != metadata[key]:
            raise ValueError("Governance metadata differs from its exact accepted input versions: " + key)
    return {**result, **metadata}
