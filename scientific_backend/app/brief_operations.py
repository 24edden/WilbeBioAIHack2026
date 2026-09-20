"""Explicit, durable interpretation addenda over immutable research decisions."""
from __future__ import annotations

import copy
import json
import uuid

from .scientific_skills import load_skill
from .store import Conflict, digest, now


def input_identity(run):
    return {key: digest(run.get(key)) for key in (
        "hypothesis", "evidence", "decisions", "handoffs", "case_snapshot", "process_contract", "governance_state",
        "required_analysis_operations")}


def instruction_identity():
    return {f"{role}:{skill_id}": load_skill(skill_id, role)["sha256"]
            for role in ("coordinator", "reviewer")
            for skill_id in (role, "research-interpretation", "molecular-interpretation", "bionemo-boltz2")}


def update_brief_operation(run, **changes):
    for entry in run.get("research_brief_operations", []):
        if entry["id"] == run["operation"]["id"]:
            entry.update(changes)
            return


def enqueue_research_brief(store, run_id, payload):
    if (set(payload) != {"decision_version", "idempotency_key"}
            or type(payload.get("decision_version")) is not int
            or payload["decision_version"] < 1
            or not isinstance(payload.get("idempotency_key"), str)
            or not 1 <= len(payload["idempotency_key"].strip()) <= 100):
        raise Conflict("Select the current decision and supply one request key.")
    from .providers import selected_model
    with store.transaction() as db:
        existing = store.dedupe(db, run_id + ":research-brief", payload["idempotency_key"], payload)
        if existing is not None:
            return existing
        run = store.get(run_id, db)
        if run["mode"] != "live":
            raise Conflict("Model-written interpretations require a live investigation.")
        if run["status"] in {"queued", "running"}:
            raise Conflict("Wait for the current operation to finish.")
        if not run["decisions"] or run["decisions"][-1]["version"] != payload["decision_version"]:
            raise Conflict("Reload the latest accepted decision before requesting its interpretation.")
        if any(item["state"] in {"unknown", "submitting"} for item in run.get("actions", [])):
            raise Conflict("An external action remains unresolved; reconcile it before another model request.")
        source_products = {item.get("sender"): item["id"] for item in run.get("handoffs", [])
                           if item.get("acceptance_status") == "accepted" and item.get("id")}
        entry = {"id": uuid.uuid4().hex, **payload, "created_at": now(), "status": "queued",
                 "origin": "scientist_interpretation_request", "model": selected_model(),
                 "reused_handoff_ids": list(source_products.values()),
                 "input_versions": input_identity(run), "instruction_hashes": instruction_identity(),
                 "source_decision_sha256": run["decisions"][-1]["sha256"]}
        run.setdefault("research_brief_operations", []).append(copy.deepcopy(entry))
        run.update(status="queued", stage="research_brief", error=None, cancel_requested=False,
                   operation={"kind": "research_brief", "id": entry["id"], "input": copy.deepcopy(entry)})
        store.append_event(run, "Scientist", "Clear scientific interpretation requested",
                           "A new model-written and independently AI-reviewed addendum will explain the accepted results. Historical decisions and hypothesis states remain unchanged.",
                           "queued", "research_brief")
        store.save(db, run)
        store.record_request(db, run_id + ":research-brief", payload["idempotency_key"], payload, run_id)
        return run


def validate_brief_inputs(run):
    from .providers import selected_model
    operation = run["operation"]
    if operation["kind"] != "research_brief":
        raise Conflict("This operation does not authorize a research interpretation.")
    entry = operation["input"]
    if entry["input_versions"] != input_identity(run):
        raise Conflict("The source results changed after interpretation was requested.")
    if entry["instruction_hashes"] != instruction_identity() or entry["model"] != selected_model():
        raise Conflict("Interpretation instructions or configured model changed after selection.")
    if entry["source_decision_sha256"] != run["decisions"][-1]["sha256"]:
        raise Conflict("The selected scientific decision changed.")
    return entry


async def execute_research_brief(worker, run_id, emit, cancelled):
    from .molecular_interpretation import audit_molecular_evidence
    from .research_brief import generate_research_brief
    from .worker import account_provider_usage, Cancelled
    from .stage_evaluation import boundary_receipt, record_evaluation
    from .config import RUNTIME
    import asyncio

    run = worker.check(run_id)
    entry = validate_brief_inputs(run)
    action_id = entry["id"] + "-research-brief"
    expected = {"input_versions": entry["input_versions"], "instruction_hashes": entry["instruction_hashes"],
                "model": entry["model"], "source_decision_sha256": entry["source_decision_sha256"]}
    with worker.store.connect() as db:
        saved = db.execute("SELECT kind,state,request,result FROM actions WHERE id=? AND run_id=?", (action_id, run_id)).fetchone()
    if saved:
        if saved["state"] != "succeeded":
            raise Conflict("This interpretation has an unresolved prior attempt; it will not be resubmitted.")
        request = json.loads(saved["request"])
        result = json.loads(saved["result"])
        if (saved["kind"] != "research-interpretation"
                or any(request.get(key) != value for key, value in expected.items())
                or digest(result.get("molecular_audit", {})) != request.get("molecular_audit_sha256")):
            raise Conflict("The saved interpretation does not match its frozen inputs and molecular audit.")
    else:
        audit = await asyncio.to_thread(audit_molecular_evidence, run, artifact_root=RUNTIME)
        worker.check(run_id)
        request = {**expected, "molecular_audit_sha256": digest(audit)}
        # Intent is durable before the first model submission. Unknown outcomes never replay.
        result = worker.store.begin_action(run_id, action_id, "research-interpretation", request)
    if result is None:
        try:
            result = await generate_research_brief(run, run["case_snapshot"], emit=emit, cancelled=cancelled,
                                                   extra_context={"molecular_audit": audit})
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
        validate_brief_inputs(current)
        if current["operation"]["id"] != entry["id"]:
            raise Conflict("The selected operation changed before interpretation publication.")
        briefs = current.setdefault("research_briefs", [])
        brief = next((item for item in briefs if item["operation_id"] == entry["id"]), None)
        if brief is None:
            brief = copy.deepcopy(result)
            brief.pop("sha256", None)
            brief.update(id=entry["id"] + "-brief", version=len(briefs) + 1,
                         operation_id=entry["id"], status="completed", created_at=now(),
                         source_decision_version=entry["decision_version"],
                         source_decision_sha256=entry["source_decision_sha256"],
                         human_review_status="unreviewed")
            brief["sha256"] = digest(brief)
            briefs.append(brief)
            record_evaluation(current, boundary_receipt("research_interpretation", "accepted", "completed",
                "Pinned result context, exact sequence references, evidence citations and independent AI review passed. This addendum does not modify the historical scientific decisions."),
                subject_sha256=brief["sha256"])
            worker.store.append_event(current, "reviewer", "Scientific interpretation ready",
                "A concise working answer, decision story and molecular interpretation are available; human scientific review remains pending.",
                "completed", "research_brief")
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
        update_brief_operation(current, status="completed", finished_at=now(), brief_id=brief["id"],
                               action_id=action_id, brief_version=brief["version"])
    worker.store.mutate(run_id, publish)
