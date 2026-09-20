"""Durable AI sequence discovery with source qualification and review."""
from __future__ import annotations

import copy
import json
import uuid

from .scientific_skills import load_skill
from .brief_operations import input_identity as base_input_identity
from .store import Conflict, digest, now


def input_identity(run):
    return {**base_input_identity(run), "research_briefs": digest(run.get("research_briefs", []))}


def instruction_identity():
    return {f"{role}:{skill_id}": load_skill(skill_id, role)["sha256"]
            for role in ("molecular_scientist", "reviewer")
            for skill_id in (role, "rosalind-informed-workflow", "research-interpretation", "molecular-interpretation", "bionemo-boltz2", "uniprot-skill", "rcsb-pdb-skill")}


def update_sequence_operation(run, **changes):
    for entry in run.get("sequence_discovery_operations", []):
        if entry["id"] == run["operation"]["id"]:
            entry.update(changes)
            return


def enqueue_sequence_discovery(store, run_id, payload):
    if (set(payload) != {"decision_version", "idempotency_key"}
            or type(payload.get("decision_version")) is not int
            or payload["decision_version"] < 1
            or not isinstance(payload.get("idempotency_key"), str)
            or not 1 <= len(payload["idempotency_key"].strip()) <= 100):
        raise Conflict("Select the current decision and supply one request key.")
    from .providers import selected_model
    with store.transaction() as db:
        existing = store.dedupe(db, run_id + ":sequence-discovery", payload["idempotency_key"], payload)
        if existing is not None:
            return existing
        run = store.get(run_id, db)
        if run["mode"] != "live":
            raise Conflict("AI sequence discovery requires a live investigation.")
        if run["status"] in {"queued", "running"}:
            raise Conflict("Wait for the current operation to finish.")
        if not run["decisions"] or run["decisions"][-1]["version"] != payload["decision_version"]:
            raise Conflict("Reload the latest accepted decision before requesting sequence discovery.")
        if any(item["state"] in {"unknown", "submitting"} for item in run.get("actions", [])):
            raise Conflict("An external action remains unresolved; reconcile it before another model request.")
        source_products = {item.get("sender"): item["id"] for item in run.get("handoffs", [])
                           if item.get("acceptance_status") == "accepted" and item.get("id")}
        entry = {"id": uuid.uuid4().hex, **payload, "created_at": now(), "status": "queued",
                 "origin": "scientist_sequence_discovery_request", "model": selected_model(),
                 "reused_handoff_ids": list(source_products.values()),
                 "input_versions": input_identity(run), "instruction_hashes": instruction_identity(),
                 "source_decision_sha256": run["decisions"][-1]["sha256"]}
        run.setdefault("sequence_discovery_operations", []).append(copy.deepcopy(entry))
        run.update(status="queued", stage="sequence_discovery", error=None, cancel_requested=False,
                   operation={"kind": "sequence_discovery", "id": entry["id"], "input": copy.deepcopy(entry)})
        store.append_event(run, "Scientist", "AI sequence discovery requested",
                           "Molecular science will search public protein and structure sources, verify exact constructs and prepare a reviewed comparison draft. No NVIDIA prediction is submitted by this action.",
                           "queued", "sequence_discovery")
        store.save(db, run)
        store.record_request(db, run_id + ":sequence-discovery", payload["idempotency_key"], payload, run_id)
        return run


def validate_sequence_inputs(run):
    from .providers import selected_model
    operation = run["operation"]
    if operation["kind"] != "sequence_discovery":
        raise Conflict("This operation does not authorize sequence discovery.")
    entry = operation["input"]
    if entry["input_versions"] != input_identity(run):
        raise Conflict("The source results changed after sequence discovery was requested.")
    if entry["instruction_hashes"] != instruction_identity() or entry["model"] != selected_model():
        raise Conflict("Sequence discovery instructions or configured model changed after selection.")
    if entry["source_decision_sha256"] != run["decisions"][-1]["sha256"]:
        raise Conflict("The selected scientific decision changed.")
    return entry


async def execute_sequence_discovery(worker, run_id, emit, cancelled):
    from .sequence_discovery import discover_sequences
    from .worker import account_provider_usage, Cancelled
    from .stage_evaluation import boundary_receipt, record_evaluation
    
    run = worker.check(run_id)
    entry = validate_sequence_inputs(run)
    action_id = entry["id"] + "-sequence-discovery"
    expected = {"input_versions": entry["input_versions"], "instruction_hashes": entry["instruction_hashes"],
                "model": entry["model"], "source_decision_sha256": entry["source_decision_sha256"]}
    with worker.store.connect() as db:
        saved = db.execute("SELECT kind,state,request,result FROM actions WHERE id=? AND run_id=?", (action_id, run_id)).fetchone()
    if saved:
        if saved["state"] != "succeeded":
            raise Conflict("This sequence discovery has an unresolved prior attempt; it will not be resubmitted.")
        request = json.loads(saved["request"])
        result = json.loads(saved["result"])
        if (saved["kind"] != "sequence-discovery"
                or any(request.get(key) != value for key, value in expected.items())):
            raise Conflict("The saved sequence discovery does not match its frozen inputs.")
    else:
        worker.check(run_id)
        request = expected
        # Intent is durable before the first model submission. Unknown outcomes never replay.
        result = worker.store.begin_action(run_id, action_id, "sequence-discovery", request)
    if result is None:
        try:
            result = await discover_sequences(run, run["case_snapshot"], emit=emit, cancelled=cancelled)
            worker.store.end_action(run_id, action_id, "succeeded", result)
        except BaseException as exc:
            worker.provider_failure(run_id, action_id, exc)
            raise
    def preserve_receipt(current):
        metadata = result.get("provider_metadata", {})
        account_provider_usage(current, action_id, metadata)
        for action in current["actions"]:
            if action["id"] == action_id:
                action["provider_metadata"] = copy.deepcopy(metadata)
    worker.store.mutate(run_id, preserve_receipt)
    worker.check(run_id)

    def publish(current):
        if current.get("cancel_requested") or worker.stopping:
            raise Cancelled()
        validate_sequence_inputs(current)
        if current["operation"]["id"] != entry["id"]:
            raise Conflict("The selected operation changed before sequence-discovery publication.")
        briefs = current.setdefault("sequence_discoveries", [])
        brief = next((item for item in briefs if item["operation_id"] == entry["id"]), None)
        if brief is None:
            brief = copy.deepcopy(result)
            brief.pop("sha256", None)
            brief.update(id=entry["id"] + "-sequences", version=len(briefs) + 1,
                         operation_id=entry["id"], created_at=now(), decision_version=entry["decision_version"],
                         source_decision_version=entry["decision_version"],
                         source_decision_sha256=entry["source_decision_sha256"],
                         human_review_status="unreviewed")
            brief["sha256"] = digest(brief)
            briefs.append(brief)
            record_evaluation(current, boundary_receipt("sequence_discovery", "accepted", "completed",
                "Pinned study context, exact retrieved sequence bytes, source identities, molecular roles and independent AI review passed. Missing comparison inputs remain explicit."),
                subject_sha256=brief["sha256"])
            worker.store.append_event(current, "reviewer", "AI sequence discovery ready",
                "Verified public sequences and their scientific context are ready for the comparison form. Incomplete roles remain empty; target retention is not asserted.",
                "completed", "sequence_discovery")
        metadata = result.get("provider_metadata", {})
        account_provider_usage(current, action_id, metadata)
        for action in current["actions"]:
            if action["id"] == action_id:
                action["provider_metadata"] = copy.deepcopy(metadata)
        for receipt in result.get("skill_receipts", []):
            record = {**receipt, "operation_id": entry["id"]}
            record["id"] = entry["id"] + "-skill-" + digest([record.get("role"), record.get("skill_id")])[:16]
            if not any(item.get("id") == record["id"] for item in current.setdefault("skill_receipts", [])):
                current["skill_receipts"].append(record)
        current.update(status="completed", stage="completed", active_agent=None, error=None)
        update_sequence_operation(current, status="completed", finished_at=now(), discovery_id=brief["id"], result_status=brief["status"],
                               action_id=action_id, discovery_version=brief["version"])
    worker.store.mutate(run_id, publish)
