"""Typed recommendations become executable only through this case-bound registry.

No model-supplied paths, code, sequence, endpoint or arbitrary parameters cross
this boundary. Existing evidence and decisions are retained on the same run.
"""
from __future__ import annotations

import copy
import uuid

from .store import Conflict, digest, now


def approved_catalog(case_id: str) -> list[dict]:
    from .analysis_tools import analysis_catalog
    entries = [{**item, "kind": "data_analysis", "title": item.get("title", item["id"]),
                "prerequisites": item.get("prerequisites", ["Pinned source files must pass identity and hash checks."])}
               for item in analysis_catalog(case_id)]
    try:
        from .structural_followups import catalog
    except ModuleNotFoundError as exc:
        if exc.name != "app.structural_followups":
            raise
    else:
        entries.extend(catalog(case_id))
    if len({item["id"] for item in entries}) != len(entries):
        raise ValueError("Follow-up registry contains duplicate recipe identifiers.")
    return entries


def validate_story(insights, recommendations, evidence_ids, recipes):
    """Validate model-readable content before it is attached to a decision."""
    allowed = {item["id"]: item for item in recipes}
    if not isinstance(insights, list) or len(insights) > 4:
        raise ValueError("Return at most four concise findings.")
    for insight in insights:
        for key, limit in (("title", 120), ("finding", 500), ("why_it_matters", 400), ("next_step", 400)):
            if not isinstance(insight.get(key), str) or not insight[key].strip() or len(insight[key]) > limit:
                raise ValueError("Finding text is missing or exceeds its concise field limit: " + key)
        citations = insight.get("evidence_ids")
        if not citations or not isinstance(citations, list) or not set(citations).issubset(evidence_ids):
            raise ValueError("Every finding must cite accepted evidence; missing citations or IDs outside this run are rejected.")
    if not isinstance(recommendations, list) or len(recommendations) > 4:
        raise ValueError("Return at most four registered follow-up recommendations.")
    seen = set()
    for item in recommendations:
        recipe = allowed.get(item.get("analysis_id"))
        if not recipe or item.get("kind") != recipe["kind"]:
            raise ValueError("Follow-up recommendation must identify a registered recipe for this case.")
        if item["analysis_id"] in seen:
            raise ValueError("Do not repeat the same follow-up recipe.")
        seen.add(item["analysis_id"])
        for key, limit in (("title", 120), ("rationale", 700), ("decision_it_could_change", 500)):
            if not isinstance(item.get(key), str) or not item[key].strip() or len(item[key]) > limit:
                raise ValueError("Follow-up text is missing or too long: " + key)
        if not isinstance(item.get("prerequisites"), list) or len(item["prerequisites"]) > 6 or any(
                not isinstance(value, str) or not value.strip() or len(value) > 300 for value in item["prerequisites"]):
            raise ValueError("Follow-up prerequisites must be concise explicit strings.")
        if item.get("requested_status", item.get("status")) not in {"ready", "needs_inputs"}:
            raise ValueError("Follow-up readiness must be ready or needs_inputs.")
        citations = item.get("evidence_ids")
        if not citations or not isinstance(citations, list) or not set(citations).issubset(evidence_ids):
            raise ValueError("Follow-up rationale must cite accepted evidence.")


def _qualified(item, recipe, run, version, *, origin):
    result = {key: copy.deepcopy(item.get(key)) for key in (
        "kind", "analysis_id", "title", "rationale", "decision_it_could_change", "prerequisites", "evidence_ids")}
    requested = item.get("requested_status", item.get("status", "ready"))
    result.update(id=f"{run['id'][:8]}-v{version}-followup-{digest([recipe['kind'], recipe['id']])[:12]}",
                  origin=origin, requested_status=requested, recipe_sha256=digest(recipe),
                  status="ready", executable=True, reason="Registered recipe; inputs are validated again before execution.")
    already = [e["id"] for e in run["evidence"] if e.get("values", {}).get("analysis_id") == recipe["id"]
               or e.get("values", {}).get("structural_recipe_id") == recipe["id"]]
    pinned = {source["path"]: source["sha256"] for source in run["case_snapshot"].get("source_manifest", [])}
    requires_fresh_sources = any(pinned.get(source["path"]) != source["sha256"] for source in recipe.get("input_sources", []))
    if requires_fresh_sources:
        result.update(status="needs_inputs", executable=False,
                      reason="This recipe requires source versions added after this investigation. Start a fresh investigation to pin the current data; this run's source snapshot is preserved.")
    elif already:
        result.update(status="completed", executable=False, evidence_ids=list(dict.fromkeys((result["evidence_ids"] or []) + already)),
                      reason="This recipe already has accepted evidence for the pinned input version.")
    elif requested == "needs_inputs":
        result.update(status="needs_inputs", executable=False, reason="The recommendation identifies unresolved prerequisites.")
    elif recipe["kind"] == "bionemo_public_structure":
        from .providers import capabilities
        if capabilities()["bionemo"]["status"] not in {"configured", "verified"}:
            result.update(status="needs_inputs", executable=False, reason="Configure a NVIDIA credential or supported NIM service before execution.")
    if run["mode"] != "live":
        result.update(status="unavailable", executable=False, reason="Executable follow-ups require a live investigation.")
    elif run["status"] in {"running", "queued"}:
        result.update(status="running", executable=False, reason="Wait for the current operation to finish.")
    elif run["status"] != "completed":
        result.update(status="unavailable", executable=False, reason="A completed current decision is required.")
    return result


def normalize_decision_story(decision, run):
    recommendations = decision.get("followups", [])
    insights = decision.get("insights", [])
    recipes = approved_catalog(run["case_id"]) if recommendations else []
    validate_story(insights, recommendations, {e["id"] for e in run["evidence"]}, recipes)
    decision["insights"] = [{**item, "origin": item.get("origin", "model_generated")} for item in insights]
    by_id = {item["id"]: item for item in recipes}
    # Publication is about to finish this operation; the request endpoint rechecks current state.
    publication_run = {**run, "status": "completed"}
    decision["followups"] = [_qualified(item, by_id[item["analysis_id"]], publication_run, decision["version"],
                                        origin=item.get("origin", "model_recommendation")) for item in recommendations]


def available_followups(run):
    decision = run["decisions"][-1] if run["decisions"] else None
    if decision is None:
        return {"run_id": run["id"], "decision_version": None, "followups": [], "operations": run.get("followup_operations", [])}
    recipes = approved_catalog(run["case_id"])
    recommended = {item["analysis_id"]: item for item in decision.get("followups", [])}
    actions = []
    for recipe in recipes:
        item = recommended.get(recipe["id"])
        origin = "model_recommendation" if item else "registered_catalog"
        if item is None:
            item = {"kind": recipe["kind"], "analysis_id": recipe["id"], "title": recipe["title"],
                    "rationale": recipe.get("description", "Registered source-data analysis."),
                    "decision_it_could_change": "Review whether this source-backed result changes the current assessment.",
                    "prerequisites": recipe.get("prerequisites", []), "evidence_ids": [], "status": "ready"}
        actions.append(_qualified(item, recipe, run, decision["version"], origin=origin))
    return {"run_id": run["id"], "decision_version": decision["version"], "followups": actions,
            "operations": copy.deepcopy(run.get("followup_operations", []))}


def enqueue_followup(store, run_id, payload):
    """Same run, exact decision, one active operation, immutable request identity."""
    with store.transaction() as db:
        existing = store.dedupe(db, run_id + ":followup", payload["idempotency_key"], payload)
        if existing:
            return existing
        run = store.get(run_id, db)
        if run["status"] != "completed" or run["mode"] != "live" or not run["decisions"]:
            raise Conflict("Follow-ups require a completed live investigation; wait for active work to finish.")
        decision = run["decisions"][-1]
        if decision["version"] != payload["decision_version"]:
            raise Conflict("The decision changed. Reload its current follow-up recommendations.")
        recommendation = next((item for item in available_followups(run)["followups"] if item["id"] == payload["recommendation_id"]), None)
        if not recommendation or not recommendation["executable"]:
            raise Conflict("This follow-up is not currently executable for the selected decision.")
        _queue_selected(run, payload, recommendation, origin="scientist_selection")
        store.save(db, run)
        store.record_request(db, run_id + ":followup", payload["idempotency_key"], payload, run_id)
        return run


def _queue_selected(run, payload, recommendation, *, origin):
    """Mutate only inside the caller's transaction; authority never comes from payload."""
    if run.get("cancel_requested"):
        raise Conflict("The scientist cancelled this run; no new follow-up may be queued.")
    if any(action["state"] in {"unknown", "submitting"} for action in run["actions"]):
        raise Conflict("An external action remains unresolved; no follow-up may be queued.")
    decision = run["decisions"][-1]
    if (run["mode"] != "live" or run["status"] != "completed"
            or decision["version"] != payload["decision_version"]
            or recommendation["id"] != payload["recommendation_id"]
            or not recommendation.get("executable") or recommendation["status"] != "ready"):
        raise Conflict("Follow-up selection does not match the current executable decision.")
    identity = digest([run["id"], decision["sha256"], recommendation["analysis_id"],
                       recommendation["recipe_sha256"], digest(run["case_snapshot"].get("source_manifest", []))])
    entry = {key: payload[key] for key in ("decision_version", "recommendation_id", "idempotency_key")}
    entry.update(id=("governance-" + identity[:32]) if origin == "agent_governance" else uuid.uuid4().hex,
                 origin=origin, created_at=now(), status="queued",
                 analysis_id=recommendation["analysis_id"], kind=recommendation["kind"],
                 recommendation=copy.deepcopy(recommendation), recipe_sha256=recommendation["recipe_sha256"],
                 decision_sha256=decision["sha256"], hypothesis_sha256=run["hypothesis"]["sha256"],
                 source_manifest_sha256=digest(run["case_snapshot"].get("source_manifest", [])))
    run.setdefault("followup_operations", []).append(copy.deepcopy(entry))
    run.update(status="queued", stage="followup", error=None, checkpoint=0,
               operation={"kind": "followup", "id": entry["id"], "input": entry})
    from .store import Store
    Store.append_event(run, "Hypothesis governor" if origin == "agent_governance" else "Scientist",
                       "Agent-selected follow-up queued" if origin == "agent_governance" else "Follow-up requested",
                       recommendation["title"] + "; linked to decision v" + str(decision["version"]), "queued", "followup")
    return entry


def governance_policy_enabled(run):
    """Only an immutable, opted-in live process contract grants autonomous execution."""
    contract = run.get("process_contract", {})
    policy = contract.get("hypothesis_governance", {})
    body = {key: value for key, value in contract.items() if key != "sha256"}
    return (run.get("mode") == "live" and policy.get("enabled") is True
            and policy.get("auto_continue") is True and contract.get("sha256") == digest(body))


def apply_governance_continuation(run):
    """Publish-time state transition and queue are committed together by the worker.

    This function never runs a tool. The usual durable follow-up executor consumes
    the queued operation, rechecks source/recipe/decision hashes and records intent.
    """
    from .store import Store
    decision = run["decisions"][-1]
    governance = decision.get("governance")
    if not governance:
        return None
    # Re-entering publication cannot duplicate a transition or selected operation.
    existing = next((item for item in run.get("governance_transitions", [])
                     if item["decision_sha256"] == decision["sha256"]), None)
    if existing is not None:
        return copy.deepcopy(existing)
    prior = run.get("governance_state", {})
    state = {"decision_version": decision["version"], "decision_sha256": decision["sha256"],
             "hypothesis_sha256": run["hypothesis"]["sha256"], "created_at": now(),
             "status": "stopped", "stop_reason": governance["stop_reason"],
             "reason": governance["continuation_reason"], "next_analysis_id": governance["next_action_id"],
             "target_hypothesis_ids": copy.deepcopy(governance["target_hypothesis_ids"]),
             "hypotheses": copy.deepcopy(governance["hypotheses"]), "operation_id": None}
    selected = None
    if not governance_policy_enabled(run) or run["operation"]["kind"] == "modeling":
        state.update(reason="Autonomous continuation is not enabled for this operation's pinned live policy.",
                     suppression="policy_disabled")
    elif run.get("cancel_requested"):
        state.update(reason="The scientist cancelled this run; no new action was queued.", suppression="cancelled")
    elif any(action["state"] in {"unknown", "submitting"} for action in run["actions"]):
        state.update(stop_reason="provider_unresolved", reason="An external action is unresolved; automatic replay is prohibited.",
                     suppression="provider_unresolved")
    elif governance["stop_reason"] == "continue":
        recipe = next((item for item in approved_catalog(run["case_id"]) if item["id"] == governance["next_action_id"]), None)
        selected = next((item for item in decision.get("followups", []) if item["analysis_id"] == governance["next_action_id"]), None)
        attempted = [item for item in run.get("followup_operations", [])
                     if item["analysis_id"] == governance["next_action_id"]
                     and recipe is not None and item.get("recipe_sha256") == digest(recipe)
                     and item.get("source_manifest_sha256") == digest(run["case_snapshot"].get("source_manifest", []))]
        if attempted:
            state.update(stop_reason="no_informative_action", reason="This registered recipe and source version already has a durable attempt; no automatic resubmission.",
                         suppression="already_attempted", prior_operation_ids=[item["id"] for item in attempted])
        elif not recipe or recipe["kind"] not in {"data_analysis", "bionemo_public_structure"} or not selected:
            state.update(stop_reason="no_informative_action", reason="The selected action is not a supported registered recommendation.",
                         suppression="unregistered_action")
        else:
            selected = _qualified(selected, recipe, run, decision["version"], origin="agent_governance")
            if not selected["executable"] or selected["status"] != "ready":
                state.update(stop_reason="needs_data" if selected["status"] == "needs_inputs" else "no_informative_action",
                             reason=selected["reason"], suppression=selected["status"])
            else:
                payload = {"decision_version": decision["version"], "recommendation_id": selected["id"],
                           "idempotency_key": "governance-" + decision["sha256"]}
                entry = _queue_selected(run, payload, selected, origin="agent_governance")
                entry["target_hypothesis_ids"] = copy.deepcopy(governance["target_hypothesis_ids"])
                run["followup_operations"][-1]["target_hypothesis_ids"] = entry["target_hypothesis_ids"]
                state.update(status="queued", operation_id=entry["id"])
    old_statuses = {item["hypothesis_id"]: item["status"] for item in prior.get("hypotheses", [])}
    for item in governance["hypotheses"]:
        Store.append_event(run, "Hypothesis governor", item["hypothesis_id"] + ": " + item["status"],
                           "Previous: " + old_statuses.get(item["hypothesis_id"], "unassessed") + ". " + item["rationale"],
                           item["status"], "hypothesis.state")
    Store.append_event(run, "Hypothesis governor", "Investigation continues" if state["status"] == "queued" else "Investigation stopped within scope",
                       state["stop_reason"] + ": " + state["reason"], state["status"], "governance")
    run.setdefault("governance_transitions", []).append(copy.deepcopy(state))
    run["governance_state"] = copy.deepcopy(state)
    return state


def stop_governance_operation(run):
    """Record an operational interruption without changing a published assessment."""
    state = run.get("governance_state")
    if (not state or state.get("operation_id") != run["operation"]["id"]
            or state.get("status") not in {"queued", "running"}):
        return
    from .store import Store
    unresolved = any(action["state"] in {"unknown", "submitting"} for action in run["actions"])
    state = copy.deepcopy(state)
    state.update(status="stopped", created_at=now(),
                 operation_status=run["status"],
                 stop_reason="cancelled" if run.get("cancel_requested") else ("provider_unresolved" if unresolved else "execution_failed"),
                 suppression="cancelled" if run.get("cancel_requested") else "operation_failed",
                 reason="The scientist cancelled this continuation." if run.get("cancel_requested") else
                        (run.get("error") or "The selected continuation stopped before a result was published; automatic replay is prohibited."))
    run["governance_state"] = state
    run.setdefault("governance_transitions", []).append(copy.deepcopy(state))
    Store.append_event(run, "Hypothesis governor", "Autonomous continuation stopped", state["reason"], "stopped", "governance")


def update_operation(run, **changes):
    operation_id = run["operation"]["id"]
    entry = next((item for item in run.get("followup_operations", []) if item["id"] == operation_id), None)
    if entry is not None:
        entry.update(changes)


def compact_previous_decision(decision):
    return {key: copy.deepcopy(decision[key]) for key in (
        "version", "sha256", "summary", "assessment", "insights", "claims", "alternatives", "limitations", "next_experiment", "rd_handoff", "governance", "prior_governance") if key in decision}
