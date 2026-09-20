"""Explicit recovery of known failed coordinator synthesis from accepted work.

A checkpoint is constructed from server state, never a caller-supplied work
product. It authorizes reuse of seven accepted specialist products only. The
coordinator and reviewer must run afresh; unknown external work never qualifies.
"""
from __future__ import annotations

import copy
import json
import uuid

from .stage_evaluation import evaluate_handoff
from .store import Conflict, digest, now

SCHEMA = "team-tbd-synthesis-checkpoint-1"
ROLES = ("bioinformatician", "statistician", "clinical_scientist", "clinical_pharmacologist",
         "molecular_scientist", "translational_scientist", "assay_scientist")
SERVER_HANDOFF_FIELDS = {"run_id", "operation_id", "accepted_at", "acceptance_status", "acceptance_evaluation_id"}


def _case_inputs(case):
    return {key: value for key, value in case.items() if key not in {
        "demo_decision", "process_contract", "synthesis_checkpoint", "revision_context", "followup_context"}}


def _current_skills():
    from .scientific_skills import load_skill, skill_catalog
    catalog = skill_catalog()
    if not catalog or len({item["id"] for item in catalog}) != len(catalog):
        raise Conflict("The current scientific skill registry is invalid.")
    for item in catalog:
        load_skill(item["id"], item["roles"][0])  # Checks actual current instruction bytes.
    return catalog


def _validate_inputs(checkpoint, case, hypothesis, evidence, contract):
    from .cases import get_case
    from .process_contract import get_process_contract
    versions = checkpoint["input_versions"]
    if digest(hypothesis) != versions["hypothesis_sha256"]:
        raise Conflict("The checkpoint's original hypothesis changed.")
    if digest(_case_inputs(case)) != versions["case_snapshot_sha256"]:
        raise Conflict("The checkpoint's case snapshot changed.")
    if digest(evidence) != versions["evidence_sha256"]:
        raise Conflict("The checkpoint's accepted evidence changed.")
    body = {key: value for key, value in contract.items() if key != "sha256"}
    if (contract.get("sha256") != digest(body) or contract.get("sha256") != versions["process_contract_sha256"]
            or get_process_contract()["sha256"] != contract["sha256"]):
        raise Conflict("The process contract differs from the checkpoint's pinned process.")
    current = get_case(case["id"])  # Hash-qualifies the actual pinned compact source files.
    if (digest(current.get("source_manifest", [])) != versions["source_manifest_sha256"]
            or digest(case.get("source_manifest", [])) != versions["source_manifest_sha256"]):
        raise Conflict("The checkpoint's source versions differ from the current qualified sources.")
    catalog = _current_skills()
    if digest(catalog) != versions["skill_catalog_sha256"]:
        raise Conflict("Scientific skills changed after this checkpoint was created.")
    from .scientific_skills import load_skill
    for receipt in checkpoint["source_skill_receipts"]:
        skill = load_skill(receipt["skill_id"], receipt["role"])
        if receipt["sha256"] != skill["sha256"] or receipt["version"] != skill["version"]:
            raise Conflict("Previously applied scientific skills changed; accepted specialist work cannot be reused.")


def _verify_receipt(receipt):
    return receipt.get("sha256") == digest({key: value for key, value in receipt.items() if key != "sha256"})


def _validate_products(checkpoint, case, hypothesis, evidence, contract):
    products = checkpoint["work_products"]
    if (len(products) != 7 or {item.get("sender") for item in products} != set(ROLES)
            or len({item.get("id") for item in products}) != 7
            or checkpoint.get("source_handoff_ids") != [item["id"] for item in products]):
        raise Conflict("Synthesis recovery requires exactly seven complete accepted specialist products.")
    receipts = {item["id"]: item for item in checkpoint["acceptance_receipts"]}
    skills = checkpoint["source_skill_receipts"]
    if len({item["id"] for item in skills}) != len(skills):
        raise Conflict("Checkpoint skill receipt IDs are duplicated.")
    validation_run = {"id": checkpoint["run_id"], "case_id": case["id"], "case_snapshot": case,
                      "hypothesis": {"sha256": digest(hypothesis)}, "evidence": evidence, "process_contract": contract,
                      "operation": {"id": checkpoint["source_operation_id"]}, "handoffs": products,
                      "skill_receipts": skills, "stage_evaluations": []}
    for product in products:
        receipt = receipts.get(product.get("acceptance_evaluation_id"), {})
        if (product.get("run_id") != checkpoint["run_id"] or product.get("operation_id") != checkpoint["source_operation_id"]
                or product.get("acceptance_status") != "accepted" or not _verify_receipt(receipt)
                or receipt.get("operation_id") != checkpoint["source_operation_id"]
                or receipt.get("run_id") != checkpoint["run_id"]
                or receipt.get("stage") != "handoff:" + product["sender"] or receipt.get("verdict") != "accepted"
                or receipt.get("process_contract_sha256") != contract["sha256"]
                or receipt.get("hypothesis_sha256") != digest(hypothesis)):
            raise Conflict("A specialist product lacks its exact accepted provenance receipt.")
        evaluation = evaluate_handoff(product, validation_run)
        if evaluation["verdict"] != "accepted":
            raise Conflict("A saved specialist product no longer satisfies its pinned contract: " + evaluation["reason"])
    if {item["id"]: digest(item) for item in products} != checkpoint["input_versions"]["handoff_sha256"]:
        raise Conflict("Checkpoint specialist product versions changed.")
    assay = next(item for item in products if item["sender"] == "assay_scientist")
    if set(assay["input_versions"]["evidence_ids"]) != {item["id"] for item in evidence}:
        raise Conflict("Accepted evidence changed after the specialist stages finished.")


def validate_provider_checkpoint(checkpoint, case, hypothesis, evidence):
    """Recheck the server-created context before model transport or upstream reuse."""
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != SCHEMA:
        raise Conflict("Unrecognized synthesis checkpoint.")
    if checkpoint.get("sha256") != digest({key: value for key, value in checkpoint.items() if key != "sha256"}):
        raise Conflict("Synthesis checkpoint content changed.")
    if checkpoint.get("reused_roles") != list(ROLES) or checkpoint.get("molecular_receipts") != []:
        raise Conflict("Checkpoint reuse scope differs from the seven accepted specialist stages.")
    contract = case.get("process_contract")
    if not isinstance(contract, dict):
        raise Conflict("Checkpoint context must carry the exact pinned process contract.")
    _validate_inputs(checkpoint, case, hypothesis, evidence, contract)
    _validate_products(checkpoint, case, hypothesis, evidence, contract)
    if not set(checkpoint["accepted_analysis_ids"]).issubset({item["id"] for item in evidence}):
        raise Conflict("Checkpoint analysis IDs are not accepted evidence.")
    return copy.deepcopy(checkpoint)


def _known_failure(run, action):
    if run["mode"] != "live" or run["decisions"] or run["status"] not in {"failed", "budget_exhausted"}:
        raise Conflict("Synthesis recovery requires a stopped live investigation with no published decision.")
    if run.get("cancel_requested"):
        raise Conflict("A cancelled investigation cannot start synthesis recovery.")
    if any(item["state"] in {"unknown", "submitting"} for item in run["actions"]):
        raise Conflict("An external action remains unresolved; synthesis recovery is not allowed.")
    if (action["state"] != "failed" or action["kind"] != "research-model-investigation"
            or action["id"] != run["operation"]["id"] + "-rosalind"):
        raise Conflict("The failed action does not belong to the current research operation.")
    metadata = action.get("provider_metadata", {})
    requests = metadata.get("requests", [])
    if (not requests or any(item.get("status") not in {"completed", "incomplete", "failed"} for item in requests)
            or requests[-1].get("agent") != "coordinator" or requests[-1].get("http_status") != 200
            or requests[-1].get("status") != "incomplete"
            or requests[-1].get("incomplete_details", {}).get("reason") != "max_output_tokens"
            or not requests[-1].get("request_id") or not requests[-1].get("response_id")):
        raise Conflict("Only a known coordinator response truncated at its output limit can use this checkpoint.")
    from .providers import selected_model
    if (metadata.get("requested_model") != selected_model()
            or metadata.get("returned_models") != [selected_model()]
            or requests[-1].get("returned_model") != selected_model()):
        raise Conflict("Synthesis recovery must retain the same explicitly configured model.")
    return metadata


def _build(run, action):
    metadata = _known_failure(run, action)
    if run["operation"]["kind"] == "synthesis_continuation":
        # A failed new coordinator call may be retried only as another explicit
        # operation, against the original immutable specialist checkpoint.
        if any(item["operation_id"] == run["operation"]["id"] for item in run.get("handoffs", [])):
            raise Conflict("An accepted synthesis-stage product already exists; this narrow checkpoint cannot be reused.")
        return synthesis_context(run)
    if run["operation"]["kind"] != "investigation":
        raise Conflict("This recovery path is limited to initial research synthesis.")
    operation_id = run["operation"]["id"]
    products = [item for item in run.get("handoffs", []) if item["operation_id"] == operation_id]
    if len(products) != 7 or {item["sender"] for item in products} != set(ROLES):
        raise Conflict("Exactly seven accepted specialist stages, with no accepted coordinator, are required.")
    reported = {item["id"]: item for item in metadata.get("work_products", [])}
    if len(metadata.get("work_products", [])) != 7 or set(reported) != {item["id"] for item in products} or any(
            reported[item["id"]] != {key: value for key, value in item.items() if key not in SERVER_HANDOFF_FIELDS}
            for item in products):
        raise Conflict("Saved specialist products differ from the failed action's accepted-work receipt.")
    receipts = [item for item in run.get("stage_evaluations", []) if item["id"] in {h["acceptance_evaluation_id"] for h in products}]
    skills = [item for item in run.get("skill_receipts", []) if item["operation_id"] == operation_id]
    catalog = _current_skills()
    checkpoint = {"schema": SCHEMA, "run_id": run["id"], "source_operation_id": operation_id,
        "source_action_id": action["id"], "created_at": now(), "reused_roles": list(ROLES),
        "work_products": copy.deepcopy(products), "source_handoff_ids": [item["id"] for item in products],
        "source_skill_receipts": copy.deepcopy(skills), "acceptance_receipts": copy.deepcopy(receipts),
        "accepted_analysis_ids": copy.deepcopy(metadata.get("accepted_analysis_ids", [])), "molecular_receipts": [],
        "failure_receipt": copy.deepcopy(metadata["requests"][-1]),
        "input_versions": {"hypothesis_sha256": run["hypothesis"]["sha256"],
            "hypothesis_record_sha256": digest(run["hypothesis"]), "case_snapshot_sha256": digest(_case_inputs(run["case_snapshot"])),
            "source_manifest_sha256": digest(run["case_snapshot"].get("source_manifest", [])),
            "process_contract_sha256": run["process_contract"]["sha256"], "evidence_sha256": digest(run["evidence"]),
            "skill_catalog_sha256": digest(catalog), "handoff_sha256": {item["id"]: digest(item) for item in products},
            "source_action_metadata_sha256": digest(metadata)}}
    checkpoint["id"] = "synthesis-checkpoint-" + digest([run["id"], operation_id, checkpoint["input_versions"]])[:24]
    checkpoint["sha256"] = digest(checkpoint)
    return validate_provider_checkpoint(checkpoint, {**run["case_snapshot"], "process_contract": run["process_contract"]}, run["hypothesis"]["text"], run["evidence"])


def _source_action(store, run, db=None):
    expected_id = run["operation"]["id"] + "-rosalind"
    action = next((item for item in run["actions"] if item["id"] == expected_id), None)
    if action is None:
        raise Conflict("No completed failure receipt exists for this operation.")
    if db is None:
        with store.connect() as connection:
            return _source_action(store, run, connection)
    row = db.execute("SELECT state,kind,request,result FROM actions WHERE id=? AND run_id=?", (expected_id, run["id"])).fetchone()
    if not row or row["state"] != action["state"] or row["kind"] != action["kind"]:
        raise Conflict("The action journal does not confirm this failed operation.")
    request, result = json.loads(row["request"]), json.loads(row["result"] or "null")
    if (not isinstance(result, dict) or result.get("metadata") != action.get("provider_metadata")
            or request.get("hypothesis_sha256") != run["hypothesis"]["sha256"]):
        raise Conflict("The durable action receipt differs from its original inputs or failure metadata.")
    return action


def inspect_synthesis_checkpoint(store, run_id):
    """Read-only eligibility; this does not persist a checkpoint or submit work."""
    run = store.get(run_id)
    try:
        checkpoint = _build(run, _source_action(store, run))
        return {"eligible": True, "reason": "Seven accepted specialist stages can be reused for a new coordinator and reviewer operation.",
                "source_operation_id": run["operation"]["id"], "source_action_id": run["operation"]["id"] + "-rosalind",
                "checkpoint_id": checkpoint["id"], "reused_roles": checkpoint["reused_roles"], "handoff_count": 7}
    except (ValueError, KeyError, TypeError) as exc:
        return {"eligible": False, "reason": str(exc)[:600], "source_operation_id": run["operation"]["id"],
                "source_action_id": None, "checkpoint_id": None, "reused_roles": [], "handoff_count": 0}


def enqueue_synthesis_continuation(store, run_id, payload):
    """Explicit user selection; atomic snapshot plus new action identity, never replay."""
    if set(payload) != {"idempotency_key", "source_operation_id"} or any(
            not isinstance(value, str) or not value.strip() or len(value) > 100 for value in payload.values()):
        raise Conflict("Synthesis recovery accepts only a request key and current source operation ID.")
    with store.transaction() as db:
        existing = store.dedupe(db, run_id + ":synthesis-continuation", payload["idempotency_key"], payload)
        if existing:
            return existing
        run = store.get(run_id, db)
        if run["operation"]["id"] != payload["source_operation_id"]:
            raise Conflict("The source operation changed; inspect current recovery eligibility again.")
        failed_action = _source_action(store, run, db)
        checkpoint = _build(run, failed_action)
        checkpoints = run.setdefault("synthesis_checkpoints", [])
        prior = next((item for item in checkpoints if item["id"] == checkpoint["id"]), None)
        if prior and prior != checkpoint:
            raise Conflict("An immutable checkpoint with this identity already differs.")
        if prior is None:
            checkpoints.append(copy.deepcopy(checkpoint))
        entry = {**payload, "id": uuid.uuid4().hex, "created_at": now(), "status": "queued",
                 "checkpoint_id": checkpoint["id"], "checkpoint_sha256": checkpoint["sha256"],
                 "origin": "scientist_synthesis_continuation", "reused_handoff_ids": checkpoint["source_handoff_ids"],
                 "source_action_id": failed_action["id"],
                 "source_failure_metadata_sha256": digest(failed_action["provider_metadata"])}
        run.setdefault("synthesis_operations", []).append(copy.deepcopy(entry))
        run.update(status="queued", stage="synthesis", error=None, checkpoint=0,
                   operation={"kind": "synthesis_continuation", "id": entry["id"], "input": entry})
        store.append_event(run, "Scientist", "Synthesis continuation requested",
            "Reusing seven accepted specialist products. Coordinator and reviewer will run under a new operation; the failed action remains unchanged.", "queued", "synthesis.checkpoint")
        store.save(db, run)
        store.record_request(db, run_id + ":synthesis-continuation", payload["idempotency_key"], payload, run_id)
        return run


def synthesis_context(run):
    """Validate the saved checkpoint again at consumption, with no caller authority."""
    if run["operation"]["kind"] != "synthesis_continuation":
        raise Conflict("Current operation is not an explicitly selected synthesis continuation.")
    entry = run["operation"]["input"]
    operation = next((item for item in run.get("synthesis_operations", []) if item["id"] == run["operation"]["id"]), None)
    if (not operation or any(operation.get(key) != entry.get(key) for key in (
            "checkpoint_id", "checkpoint_sha256", "source_operation_id", "source_action_id", "source_failure_metadata_sha256", "reused_handoff_ids", "origin"))
            or entry.get("origin") != "scientist_synthesis_continuation" or run["decisions"]):
        raise Conflict("The synthesis operation does not match its explicit recorded selection.")
    checkpoint = next((item for item in run.get("synthesis_checkpoints", []) if item["id"] == entry["checkpoint_id"]), None)
    if not checkpoint or checkpoint["sha256"] != entry["checkpoint_sha256"]:
        raise Conflict("The selected synthesis checkpoint is missing or changed.")
    if run.get("cancel_requested") or any(item["state"] == "unknown" or
            (item["state"] == "submitting" and item["id"] != run["operation"]["id"] + "-rosalind") for item in run["actions"]):
        raise Conflict("Cancelled or unresolved external work prevents checkpoint consumption.")
    if digest(run["hypothesis"]) != checkpoint["input_versions"]["hypothesis_record_sha256"]:
        raise Conflict("Original hypothesis identity or provenance changed.")
    current = {item["id"]: item for item in run.get("handoffs", [])}
    if any(current.get(item["id"]) != item for item in checkpoint["work_products"]):
        raise Conflict("Accepted original handoffs changed after checkpoint selection.")
    for key, expected in (("skill_receipts", checkpoint["source_skill_receipts"]), ("stage_evaluations", checkpoint["acceptance_receipts"])):
        records = {item["id"]: item for item in run.get(key, [])}
        if any(records.get(item["id"]) != item for item in expected):
            raise Conflict("Original checkpoint acceptance or skill receipts changed.")
    original_action = next((item for item in run["actions"] if item["id"] == checkpoint["source_action_id"]), None)
    if (not original_action or original_action["state"] != "failed"
            or digest(original_action.get("provider_metadata")) != checkpoint["input_versions"]["source_action_metadata_sha256"]):
        raise Conflict("Original failed action history changed after checkpoint selection.")
    failed_action = next((item for item in run["actions"] if item["id"] == entry["source_action_id"]), None)
    if (not failed_action or failed_action["state"] != "failed"
            or digest(failed_action.get("provider_metadata")) != entry["source_failure_metadata_sha256"]):
        raise Conflict("The explicitly selected failed action changed after checkpoint selection.")
    return validate_provider_checkpoint(checkpoint, {**run["case_snapshot"], "process_contract": run["process_contract"]},
                                        run["hypothesis"]["text"], run["evidence"])


def checkpoint_evaluation_view(run):
    """Temporary upstream authorization only; never rewrites stored work products."""
    checkpoint = synthesis_context(run)
    view = copy.deepcopy(run)
    allowed = set(checkpoint["source_handoff_ids"])
    for product in view["handoffs"]:
        if product["id"] in allowed:
            product["operation_id"] = run["operation"]["id"]
    lineage = {"checkpoint_id": checkpoint["id"], "checkpoint_sha256": checkpoint["sha256"],
               "source_operation_id": checkpoint["source_operation_id"], "reused_handoff_ids": checkpoint["source_handoff_ids"]}
    return view, lineage


def update_synthesis_operation(run, **changes):
    entry = next((item for item in run.get("synthesis_operations", []) if item["id"] == run["operation"]["id"]), None)
    if entry is not None:
        entry.update(changes)
