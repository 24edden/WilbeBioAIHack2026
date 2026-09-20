"""Portable application-boundary evaluations, independent of model self-grading.

Evaluations verify identity, provenance, dependencies and bounded execution. They
do not score biological truth. A blocked work product can pass its contract while
explicitly recording that its scientific question remains unanswered. Receipts
are appended in the same transaction as accepted work, or before rejection is
returned to the sender, so repair history survives a process restart.
"""
from __future__ import annotations

import hashlib
import json
import uuid

from .store import digest, now

EVALUATION_SCHEMA = "team-tbd-stage-evaluation-1"


def _strings(value, *, nonempty=False):
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(isinstance(x, str) and x.strip() for x in value)
            and len(value) == len(set(value)))


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def evaluate_handoff(product, run):
    """Return a check receipt, without mutating state or trusting model identities."""
    checks = []

    def check(name, passed, detail):
        checks.append({"id": name, "passed": bool(passed), "detail": detail})
        return bool(passed)

    contract = run["process_contract"]
    policy = contract.get("stage_policy", {})
    product = product if isinstance(product, dict) else {}
    role = product.get("sender") if isinstance(product.get("sender"), str) else "unregistered"
    previous = [r for r in run.get("stage_evaluations", [])
                if r["stage"] == "handoff:" + role and r["operation_id"] == run["operation"]["id"]]
    attempt = len(previous) + 1
    maximum = policy.get("max_handoff_attempts_per_role", 2)
    check("attempt_budget", attempt <= maximum and not any(r["verdict"] == "accepted" for r in previous),
          "At most an initial submission and one repair; accepted products cannot be replaced within an operation.")
    complete = check("required_fields", all(k in product for k in contract["handoff_required"]),
                     "Work product must contain every pinned handoff field.")
    if complete:
        check("meaningful_content", all(_text(product.get(k)) for k in ("question", "method", "result", "decision_it_could_change"))
              and _strings(product.get("limitations"), nonempty=True),
              "Question, method, result and affected decision must be meaningful; limitations must be explicit.")
        check("case_identity", product["case_id"] == run["case_id"], "Work product belongs to this case.")
        check("result_status", product["result_status"] in policy.get("result_statuses", ["completed", "blocked", "inconclusive"]),
              "Completed, blocked and inconclusive work are distinct statuses.")
        routes = {r["id"]: r["recipients"] for r in contract["roles"]}
        routes.update(contract.get("additional_routes", {}))
        check("authorized_route", _strings(product["recipient"], nonempty=True)
              and set(product["recipient"]).issubset(routes.get(role, [])),
              "Sender and recipients must follow registered role routes.")
        versions = product["input_versions"] if isinstance(product["input_versions"], dict) else {}
        check("hypothesis_version", versions.get("hypothesis_sha256") == run["hypothesis"]["sha256"],
              "Pin the exact original hypothesis hash.")
        records = {e["id"]: e for e in run["evidence"]}
        ids = versions.get("evidence_ids")
        valid_ids = _strings(ids) and set(ids).issubset(records)
        check("evidence_identity", valid_ids, "Input evidence IDs must be unique and already accepted.")
        if valid_ids:
            packet = [records[eid] for eid in ids]
            checksum = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
            check("evidence_versions", versions.get("evidence_sha256") == checksum
                  and versions.get("evidence_versions") == {e["id"]: e["source"]["sha256"] for e in packet},
                  "Input packet digest and every source hash must match accepted records.")
        claims = product["claims"]
        check("claim_citations", isinstance(claims, list) and all(
            isinstance(c, dict) and _text(c.get("text")) and _strings(c.get("evidence_ids"), nonempty=True)
            and valid_ids and set(c["evidence_ids"]).issubset(ids) for c in claims),
            "Every stated claim must cite nonempty accepted evidence from its declared input packet.")
        if "followup_proposals" in product:
            from .discovery_planning import validate_proposal
            proposals = product["followup_proposals"]
            valid_proposals = isinstance(proposals, list) and len(proposals) <= 3
            try:
                if valid_proposals:
                    proposal_ids = []
                    for proposal in proposals:
                        validate_proposal(proposal, run["case_snapshot"], run["evidence"],
                                          run["hypothesis"]["sha256"], role)
                        if not valid_ids or not set(proposal["evidence_ids"]).issubset(ids):
                            raise ValueError("Proposal evidence is outside this work product.")
                        proposal_ids.append(proposal["id"])
                    valid_proposals = len(proposal_ids) == len(set(proposal_ids))
            except (ValueError, KeyError, TypeError):
                valid_proposals = False
            check("followup_proposals", valid_proposals,
                  "Proposals must retain registered recipe, role, case and exact accepted input versions; no execution implied.")
        upstream = {h["id"]: h for h in run.get("handoffs", []) if h["operation_id"] == run["operation"]["id"]}
        upstream_ids = versions.get("upstream_handoff_ids")
        valid_upstream = _strings(upstream_ids) and set(upstream_ids).issubset(upstream)
        check("upstream_identity", valid_upstream, "Upstream products must be accepted in this operation.")
        required_roles = policy.get("required_upstream", {}).get(role, [])
        check("stage_dependencies", valid_upstream and set(required_roles).issubset(
            {upstream[i]["sender"] for i in upstream_ids} if valid_upstream else set()),
            "Required upstream roles must be explicitly consumed; blocked branches remain visible.")
        if product.get("model_called"):
            receipts = {s["id"]: s for s in run.get("skill_receipts", [])
                        if s["role"] == role and s["operation_id"] == run["operation"]["id"]}
            selected = product.get("skill_receipt_ids")
            valid_skills = _strings(selected, nonempty=True) and set(selected).issubset(receipts)
            check("skill_receipts", valid_skills, "Model work requires persisted current role-specific skill receipts.")
            if valid_skills:
                expected = {receipts[s]["skill_id"]: {"version": receipts[s]["version"], "sha256": receipts[s]["sha256"]} for s in selected}
                check("skill_versions", product.get("skill_versions") == expected and role in expected,
                      "Skill version and hash must match loaded instructions, including this role's skill.")
    accepted = all(c["passed"] for c in checks)
    failed = [c["id"] for c in checks if not c["passed"]]
    return {"schema": EVALUATION_SCHEMA, "stage": "handoff:" + role, "verdict": "accepted" if accepted else "rejected",
            "result_status": product.get("result_status", "invalid"), "attempt": attempt,
            "repair_allowed": not accepted and attempt < maximum and not any(r["verdict"] == "accepted" for r in previous),
            "checks": checks, "reason": "Contract accepted; scientific conclusions remain subject to review." if accepted else "Failed checks: " + ", ".join(failed),
            "scientific_validity": "not_established_by_contract_checks"}


def record_evaluation(run, evaluation, *, subject_sha256=None):
    """Call within Store.mutate: persisted alongside the boundary's state change."""
    receipt = {**evaluation, "id": "eval-" + uuid.uuid4().hex, "run_id": run["id"],
               "operation_id": run["operation"]["id"], "created_at": now(),
               "process_contract_sha256": run["process_contract"]["sha256"],
               "hypothesis_sha256": run["hypothesis"]["sha256"], "subject_sha256": subject_sha256}
    receipt["sha256"] = digest(receipt)
    run.setdefault("stage_evaluations", []).append(receipt)
    return receipt


def boundary_receipt(stage, verdict, result_status, detail):
    """Receipt for an existing validator or terminal state; no synthetic scoring."""
    return {"schema": EVALUATION_SCHEMA, "stage": stage, "verdict": verdict,
            "result_status": result_status, "checks": [{"id": stage, "passed": verdict == "accepted", "detail": detail}],
            "reason": detail, "repair_allowed": False, "scientific_validity": "not_established_by_contract_checks"}
