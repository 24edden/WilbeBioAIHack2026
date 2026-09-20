from __future__ import annotations
import asyncio
import copy
import hashlib
import json
import uuid
from pathlib import Path

from .config import DEMO_DELAY, MAX_SECONDS, MAX_TOOL_CALLS, RUNTIME
from .store import Conflict, Store, digest, now
from .stage_evaluation import boundary_receipt, evaluate_handoff, record_evaluation


class Cancelled(Exception):
    pass


def account_provider_usage(run, action_id, metadata):
    """A provider receipt is charged once even if publication resumes after a crash."""
    receipts = run.setdefault("usage_receipts", [])
    if not metadata or action_id in receipts:
        return
    usage = metadata.get("usage", {})
    for key in ("input_tokens", "output_tokens"):
        run["usage"][key] += int(usage.get(key, 0) or 0)
    run["usage"]["model_calls"] += int(metadata.get("dispatched_requests", usage.get("model_calls", 0)) or 0)
    receipts.append(action_id)


def normalize_decision(decision, run):
    """Final publication boundary: evidence references and identity are server owned."""
    decision = copy.deepcopy(decision)
    ids = {e["id"] for e in run["evidence"]}
    required = ("summary", "assessment", "claims", "alternatives", "limitations", "next_experiment", "rd_handoff")
    for field in required:
        if field not in decision:
            raise ValueError(f"Decision missing required field: {field}")
    for claim in decision["claims"]:
        if not claim.get("evidence_ids") or not set(claim["evidence_ids"]).issubset(ids):
            raise ValueError("A claim cites missing or unaccepted evidence.")
    if not isinstance(decision["rd_handoff"], dict) or not isinstance(decision["next_experiment"], dict):
        raise ValueError("Experiment and R&D handoff must be structured records.")
    decision.update(version=len(run["decisions"])+1, created_at=now(), mode=run["mode"], operation_id=run["operation"]["id"],
                    hypothesis_sha256=run["hypothesis"]["sha256"], review_status_at_issue="unreviewed")
    decision.setdefault("changes", [])
    handoff = decision["rd_handoff"]
    handoff["experiment_id"] = f"{run['id'][:8]}-experiment-{decision['version']}"
    handoff.setdefault("candidates", [])
    for index, candidate in enumerate(handoff["candidates"]):
        candidate["id"] = f"{run['id'][:8]}-v{decision['version']}-candidate-{index+1}"
    handoff.setdefault("return_requirements", ["Candidate ID", "Experiment ID", "Endpoint", "Value and unit", "Controls and replicate/QC notes"])
    handoff.setdefault("modeling", {"status": "blocked", "reason": "Qualified exact molecular inputs required.", "artifacts": []})
    handoff.setdefault("reference", "Exact molecular reference not supplied")
    from .followups import approved_catalog, governance_policy_enabled, normalize_decision_story
    if run["operation"]["kind"] == "modeling":
        if decision.get("governance"):
            decision["prior_governance"] = decision.pop("governance")
        decision["governance"] = None  # Manual predictions do not re-evaluate hypothesis states.
    elif decision.get("governance") is not None:
        from .hypothesis_governance import validate_governance
        previous_governance = next((item.get("governance") or item.get("prior_governance")
                                    for item in reversed(run["decisions"])
                                    if item.get("governance") or item.get("prior_governance")), None)
        decision["governance"] = validate_governance(decision["governance"],
            hypothesis=run["hypothesis"]["text"], evidence=run["evidence"], recipes=approved_catalog(run["case_id"]),
            followups=decision.get("followups", []), previous=previous_governance,
            case=run["case_snapshot"])
    elif governance_policy_enabled(run):
        raise ValueError("The pinned live policy requires a validated hypothesis governance assessment before publication.")
    normalize_decision_story(decision, run)
    decision["sha256"] = digest(decision)
    return decision


def demo_decision(run):
    case = run["case_snapshot"]
    decision = copy.deepcopy(case["demo_decision"])
    if run["hypothesis"]["text"].strip() != case["hypothesis"].strip():
        # A fixture cannot adjudicate arbitrary user input. Keep the objective visible.
        decision["assessment"] = "not_evaluable"
        decision["summary"] = "Your hypothesis is preserved. This prepared walkthrough cannot adjudicate an edited hypothesis; use live mode for a model investigation."
        decision["limitations"].append("The scripted case interpretation does not assess the custom hypothesis.")
        for claim in decision["claims"]:
            claim["text"] = "Case context, not an assessment of your custom hypothesis: " + claim["text"]
            claim["kind"] = "case_context"
        decision["next_experiment"] = {
            "title": "Clarify the custom hypothesis through a live investigation",
            "design": "Investigate the preserved user hypothesis against relevant evidence before selecting a hypothesis-specific experiment.",
            "positive": "A qualified investigation identifies evidence and a discriminator supporting this exact hypothesis.",
            "negative": "A qualified investigation identifies contradictory evidence or an unsuitable proposed mechanism.",
            "inconclusive": "Relevant evidence or a discriminating experiment remains missing."}
        decision["rd_handoff"] = {
            "objective": run["hypothesis"]["text"], "status": "blocked", "reference": "No reference construct qualified for this custom hypothesis.",
            "candidates": [], "modeling": {"status": "blocked", "reason": "The scripted case cannot assess this custom objective; a live investigation and qualified molecular inputs are required.", "artifacts": []},
            "experiment_id": "", "return_requirements": ["Hypothesis-specific evidence assessment", "A qualified experimental design and registered candidate or experimental arm"]}
    decision["limitations"].append("Prepared demonstration: no GPT-Rosalind or BioNeMo inference was performed for this decision.")
    operation = run["operation"]
    if operation["kind"] in ("feedback", "outcome"):
        entry = operation["input"]
        prior = run["decisions"][-1]
        decision = copy.deepcopy(prior)
        decision.pop("sha256", None)
        decision.pop("metadata", None)
        note = entry["text"] if operation["kind"] == "feedback" else f"{entry['endpoint']}: {entry['value']} {entry['unit']}. {entry['notes']}"
        decision["changes"] = [f"Scientist {'correction' if operation['kind']=='feedback' else 'measurement'} attached to v{entry['decision_version']}: {note}"]
        decision["summary"] = "New scientist input recorded. The assessment requires review in light of this input. " + prior["summary"]
        decision["assessment"] = "unresolved"
        decision["limitations"] = list(dict.fromkeys(prior["limitations"] + ["User-submitted input is not independently verified. Demo revisions are deterministic records, not model reassessment."]))
        decision["claims"].append({"text": "A scientist supplied new information for this exact decision version; its scientific interpretation remains under review.",
                                  "evidence_ids": ["user-"+entry["id"]], "kind": "user_report"})
    return decision


class Worker:
    def __init__(self, store=None):
        self.store = store or Store()
        self.owner = uuid.uuid4().hex
        self.stopping = False
        self.ready = False
        self.current = None

    def budget_warning(self, run_id, category, threshold, observed):
        def record(run):
            operation_id = run["operation"]["id"]
            alerts = run.setdefault("budget_alerts", [])
            if any(a["operation_id"] == operation_id and a["category"] == category for a in alerts):
                return
            alert = {"operation_id": operation_id, "category": category, "threshold": threshold,
                     "observed": observed, "mode": "advisory", "time": now()}
            alerts.append(alert)
            self.store.append_event(run, "Harness", "Budget alert — investigation continues",
                f"{category}: observed {observed}, alert threshold {threshold}. You can stop the run.", "warning", "budget")
        self.store.mutate(run_id, record)

    def check(self, run_id):
        run = self.store.get(run_id)
        if run["cancel_requested"] or self.stopping:
            raise Cancelled()
        policy = run.get("worker_budget_policy", {})
        observed = run["usage"]["tool_calls"] - policy.get("starting_tool_calls", 0)
        threshold = policy.get("tool_calls", MAX_TOOL_CALLS)
        if observed >= threshold:
            if policy.get("mode", "advisory") == "enforced":
                raise TimeoutError("Tool-call budget exhausted.")
            self.budget_warning(run_id, "worker_tool_operations", threshold, observed)
        return run

    def provider_failure(self, run_id, action_id, exc):
        """Keep request/usage proof on failures and cancellations, without secret bodies."""
        from . import providers
        metadata = getattr(exc, "metadata", {})
        # Providers only export non-sensitive request metadata; redact defensively.
        metadata = json.loads(providers._redact(json.dumps(metadata)))
        cancelled = isinstance(exc, (Cancelled, asyncio.CancelledError))
        state = "unknown" if cancelled or getattr(exc, "status", None) == "unknown" else "failed"
        if any(record.get("status") == "dispatched" for record in metadata.get("requests", [])):
            state = "unknown"
        result = {"reason": "Local work stopped; any dispatched request may still complete." if state == "unknown" else "Provider did not return a validated complete result.",
                  "provider_status": getattr(exc, "status", "cancelled" if cancelled else "failed"), "metadata": metadata}
        self.store.end_action(run_id, action_id, state, result)
        def preserve(run):
            account_provider_usage(run, action_id, metadata)
            for action in run["actions"]:
                if action["id"] == action_id:
                    action["provider_metadata"] = metadata
        self.store.mutate(run_id, preserve)

    async def emit(self, run_id, agent, title, detail, status="completed", type="tool"):
        self.check(run_id)
        def update(run):
            self.store.append_event(run, agent, title, str(detail), status, type)
            run["last_activity"] = {"agent": agent, "title": title, "time": now(), "status": status, "type": type}
            roles = {r["id"] for r in run.get("process_contract", {}).get("roles", [])} | {"coordinator", "reviewer"}
            if agent in roles and run["status"] == "running":
                run["active_agent"] = agent
                run["stage"] = agent
                if type == "handoff" or title in {"Specialist product validated", "Specialist blocked by missing inputs", "Independent review completed"}:
                    run["active_agent"] = None
            if type == "budget" and status == "warning":
                alerts = run.setdefault("budget_alerts", [])
                if not any(a.get("operation_id") == run["operation"]["id"] and a.get("title") == title and a.get("detail") == str(detail) for a in alerts):
                    alerts.append({"operation_id": run["operation"]["id"], "category": "provider", "title": title,
                                   "detail": str(detail), "time": now(), "mode": "advisory"})
            if type == "tool":
                run["usage"]["tool_calls"] += 1
        self.store.mutate(run_id, update)

    async def heartbeat(self):
        while not self.stopping:
            if not self.store.lease(self.owner):
                self.stopping = True
                if self.current:
                    self.current.cancel()
                return
            await asyncio.sleep(5)

    async def run_forever(self):
        while not self.stopping and not self.store.lease(self.owner):
            await asyncio.sleep(2)
        if self.stopping:
            return
        self.recover()
        self.ready = True
        heartbeat = asyncio.create_task(self.heartbeat())
        try:
            while not self.stopping:
                pending = [r for r in reversed(self.store.list()) if r["status"] == "queued"]
                if not pending:
                    await asyncio.sleep(.3)
                    continue
                self.current = asyncio.create_task(self.execute(pending[0]["id"]))
                await self.current
                self.current = None
        finally:
            heartbeat.cancel()
            self.store.release(self.owner)

    def recover(self):
        """Called under the worker lease; reconcile visible continuation state too."""
        from .followups import stop_governance_operation, update_operation
        self.store.recover()
        for saved in self.store.list():
            governance_pending = (saved.get("governance_state", {}).get("status") in {"queued", "running"}
                                  and saved.get("governance_state", {}).get("operation_id") == saved["operation"]["id"])
            synthesis_pending = (saved["operation"]["kind"] == "synthesis_continuation" and any(
                item["id"] == saved["operation"]["id"] and item["status"] in {"queued", "running"}
                for item in saved.get("synthesis_operations", [])))
            brief_pending = (saved["operation"]["kind"] == "research_brief" and any(
                item["id"] == saved["operation"]["id"] and item["status"] in {"queued", "running"}
                for item in saved.get("research_brief_operations", [])))
            sequence_pending = (saved["operation"]["kind"] == "sequence_discovery" and any(
                item["id"] == saved["operation"]["id"] and item["status"] in {"queued", "running"}
                for item in saved.get("sequence_discovery_operations", [])))
            if saved["status"] in {"queued", "running", "completed"} or not (governance_pending or synthesis_pending or brief_pending or sequence_pending):
                continue
            def stopped(run):
                if run["operation"]["kind"] == "followup":
                    update_operation(run, status=run["status"], error=run.get("error"), finished_at=now())
                elif run["operation"]["kind"] == "synthesis_continuation":
                    from .synthesis_checkpoint import update_synthesis_operation
                    update_synthesis_operation(run, status=run["status"], error=run.get("error"), finished_at=now())
                elif run["operation"]["kind"] == "research_brief":
                    from .brief_operations import update_brief_operation
                    update_brief_operation(run, status=run["status"], error=run.get("error"), finished_at=now())
                elif run["operation"]["kind"] == "sequence_discovery":
                    from .sequence_operations import update_sequence_operation
                    update_sequence_operation(run, status=run["status"], error=run.get("error"), finished_at=now())
                stop_governance_operation(run)
            self.store.mutate(saved["id"], stopped)

    async def execute(self, run_id):
        from .providers import effective_model_limits
        limits = effective_model_limits()
        def start(run):
            if run["cancel_requested"]:
                run.update(status="cancelled", stage="cancelled")
                from .followups import stop_governance_operation, update_operation
                if run["operation"]["kind"] == "followup":
                    update_operation(run, status="cancelled", finished_at=now())
                elif run["operation"]["kind"] == "synthesis_continuation":
                    from .synthesis_checkpoint import update_synthesis_operation
                    update_synthesis_operation(run, status="cancelled", finished_at=now())
                elif run["operation"]["kind"] == "research_brief":
                    from .brief_operations import update_brief_operation
                    update_brief_operation(run, status="cancelled", finished_at=now())
                elif run["operation"]["kind"] == "sequence_discovery":
                    from .sequence_operations import update_sequence_operation
                    update_sequence_operation(run, status="cancelled", finished_at=now())
                stop_governance_operation(run)
            else:
                run.update(status="running", stage="qualifying", error=None)
                if run["operation"]["kind"] == "research_brief":
                    from .brief_operations import update_brief_operation
                    update_brief_operation(run, status="running", started_at=now())
                if run["operation"]["kind"] == "sequence_discovery":
                    from .sequence_operations import update_sequence_operation
                    update_sequence_operation(run, status="running", started_at=now())
                if run["operation"]["kind"] == "synthesis_continuation":
                    from .synthesis_checkpoint import update_synthesis_operation
                    update_synthesis_operation(run, status="running")
                if run["operation"]["kind"] == "followup":
                    from .followups import update_operation
                    update_operation(run, status="running")
                    if run.get("governance_state", {}).get("operation_id") == run["operation"]["id"]:
                        run["governance_state"] = {**run["governance_state"], "status": "running", "started_at": now()}
                if run.get("worker_budget_policy", {}).get("operation_id") != run["operation"]["id"]:
                    run["worker_budget_policy"] = {"operation_id": run["operation"]["id"], "mode": limits.get("budget_mode", "advisory"),
                        "seconds": MAX_SECONDS, "tool_calls": MAX_TOOL_CALLS, "starting_tool_calls": run["usage"]["tool_calls"]}
        run = self.store.mutate(run_id, start)
        if run["status"] == "cancelled":
            return
        work = None
        try:
            policy = run["worker_budget_policy"]
            if policy["mode"] == "enforced":
                await asyncio.wait_for(self.investigation(run_id), timeout=policy["seconds"])
            else:
                work = asyncio.create_task(self.investigation(run_id))
                done, _ = await asyncio.wait({work}, timeout=policy["seconds"])
                if not done:
                    self.budget_warning(run_id, "elapsed_seconds", policy["seconds"], policy["seconds"])
                await work
        except (Cancelled, asyncio.CancelledError):
            def stop(r):
                r.update(status="cancelled" if r["cancel_requested"] else "paused", stage="stopped")
                self.store.append_event(r, "Harness", "New work stopped", "No new provider submissions will be started. In-flight external work may still finish.", r["status"])
                record_evaluation(r, boundary_receipt("operation_stop", "rejected", r["status"], "New work stopped; dispatched provider actions may still complete."))
            self.store.mutate(run_id, stop)
        except TimeoutError:
            def budget_stop(r):
                r.update(status="budget_exhausted", stage="stopped", error="Run time or tool budget exhausted. Any unresolved external action will not be resubmitted.")
                record_evaluation(r, boundary_receipt("operation_stop", "rejected", "budget_exhausted", r["error"]))
                self.store.append_event(r, "Harness", "Execution budget exhausted", r["error"], "budget_exhausted", "stage.evaluation")
            self.store.mutate(run_id, budget_stop)
        except Exception as exc:
            # Keep provider exception bodies out of traces: they can contain credentials or inputs.
            category = type(exc).__name__
            message = str(exc) if isinstance(exc, (ValueError, Conflict)) else f"{category}: provider or workflow failed; inspect the capability check and local logs."
            if getattr(exc, "reason_code", None) == "model_request_timeout":
                message = "Model response timed out; the dispatched request outcome is unknown. No automatic retry was made. Accepted evidence and handoffs are preserved."
            message = message[:800]
            def fail(r):
                unresolved = any(a["state"] in ("unknown", "submitting") for a in r["actions"])
                budget_exhausted = getattr(exc, "status", None) == "budget_exhausted"
                status = "budget_exhausted" if budget_exhausted else ("blocked" if unresolved else "failed")
                detail = "Provider request, token or tool budget exhausted; accepted evidence is preserved. Any unresolved external action will not be resubmitted." if budget_exhausted else message
                r.update(status=status, error=detail, stage="stopped")
                record_evaluation(r, boundary_receipt("operation_stop", "rejected", status, detail))
                self.store.append_event(r, "Harness", "Investigation stopped", detail, status, "error")
            self.store.mutate(run_id, fail)
        finally:
            if work is not None and not work.done():
                work.cancel()
                await asyncio.gather(work, return_exceptions=True)
            self.store.mutate(run_id, lambda r: r.update(active_agent=None) if r["status"] not in {"queued", "running"} else None)
            def finish_followup(r):
                if r["operation"]["kind"] == "followup" and r["status"] not in {"queued", "running", "completed"}:
                    from .followups import stop_governance_operation, update_operation
                    update_operation(r, status=r["status"], error=r.get("error"), finished_at=now())
                    stop_governance_operation(r)
                elif r["operation"]["kind"] == "synthesis_continuation" and r["status"] not in {"queued", "running", "completed"}:
                    from .synthesis_checkpoint import update_synthesis_operation
                    update_synthesis_operation(r, status=r["status"], error=r.get("error"), finished_at=now())
                elif r["operation"]["kind"] == "research_brief" and r["status"] not in {"queued", "running", "completed"}:
                    from .brief_operations import update_brief_operation
                    update_brief_operation(r, status=r["status"], error=r.get("error"), finished_at=now())
                elif r["operation"]["kind"] == "sequence_discovery" and r["status"] not in {"queued", "running", "completed"}:
                    from .sequence_operations import update_sequence_operation
                    update_sequence_operation(r, status=r["status"], error=r.get("error"), finished_at=now())
            self.store.mutate(run_id, finish_followup)

    async def investigation(self, run_id):
        run = self.check(run_id)
        case = run["case_snapshot"]
        async def emit(agent, title, detail, status="completed", type="tool"):
            await self.emit(run_id, agent, title, detail, status, type)
        def cancelled():
            return self.stopping or self.store.get(run_id)["cancel_requested"]

        if run["operation"]["kind"] == "sequence_discovery":
            from .sequence_operations import execute_sequence_discovery
            await execute_sequence_discovery(self, run_id, emit, cancelled)
            return

        if run["operation"]["kind"] == "research_brief":
            from .brief_operations import execute_research_brief
            await execute_research_brief(self, run_id, emit, cancelled)
            return

        async def validate_and_accept_evidence(evidence):
            self.check(run_id)
            if not isinstance(evidence, dict) or not all(k in evidence for k in ("id", "title", "kind", "summary", "source", "values")):
                raise ValueError("Analysis returned an invalid evidence contract.")
            if not evidence["source"].get("sha256") or not evidence["source"].get("locator"):
                raise ValueError("Analysis evidence lacks source version or locator.")
            if len(json.dumps(evidence)) > 80000:
                raise ValueError("Analysis summary exceeds the bounded evidence packet size.")
            values = evidence["values"]
            if "structural_recipe_id" in values:
                from .structural_followups import validate_evidence
                from .followups import approved_catalog
                if values["structural_recipe_id"] not in {a["id"] for a in approved_catalog(case["id"]) if a["kind"] == "bionemo_public_structure"}:
                    raise ValueError("Structural result is outside this case's approved follow-up registry.")
                await asyncio.to_thread(validate_evidence, evidence)
                pinned = {r["path"]: r["sha256"] for r in case.get("source_manifest", [])}
                if not values.get("input_sources") or any(pinned.get(s.get("path")) != s.get("sha256") for s in values["input_sources"]):
                    raise ValueError("Structural evidence does not match this run's pinned source versions; start a fresh investigation.")
            elif str(values.get("analysis_id", "")).startswith("catalog:"):
                from .data_catalog import REGISTRY_PATH, validate_catalog_evidence
                if case["id"] != "cart-discovery" or hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest() != case["source_integrity"]["registry_sha256"]:
                    raise ValueError("Catalog evidence does not match this run's pinned registry.")
                await asyncio.to_thread(validate_catalog_evidence, evidence)
            elif "analysis_id" in values:
                from .analysis_tools import analysis_catalog
                checksum = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
                if checksum != evidence["source"]["sha256"]:
                    raise ValueError("Derived result hash does not match its content.")
                if values.get("case_id") != case["id"]:
                    raise ValueError("Derived evidence belongs to another case.")
                if values["analysis_id"] not in {a["id"] for a in analysis_catalog(case["id"])}:
                    raise ValueError("Derived analysis is outside this case's approved catalog.")
                pinned = {r["path"]: r["sha256"] for r in case.get("source_manifest", [])}
                if not values.get("input_sources") or any(pinned.get(s.get("path")) != s.get("sha256") for s in values["input_sources"]):
                    raise ValueError("Derived evidence does not match pinned source versions.")
            def accept(r):
                current = next((e for e in r["evidence"] if e["id"] == evidence["id"]), None)
                if current and digest(current) != digest(evidence):
                    raise Conflict("An analysis attempted to overwrite a pinned evidence version.")
                if not current:
                    r["evidence"].append(copy.deepcopy(evidence))
                    record_evaluation(r, boundary_receipt("evidence_acceptance", "accepted", "completed",
                                      "Evidence schema, case/recipe scope, bounded payload and pinned source/derived hashes passed the applicable source validator."), subject_sha256=digest(evidence))
                    self.store.append_event(r, "Evidence store", "Analysis result accepted", evidence["title"], type="evidence")
            self.store.mutate(run_id, accept)
            return evidence

        async def accept_evidence(evidence):
            try:
                return await validate_and_accept_evidence(evidence)
            except (ValueError, Conflict) as exc:
                self.store.mutate(run_id, lambda r: record_evaluation(r, boundary_receipt(
                    "evidence_acceptance", "rejected", "invalid", str(exc)[:500])))
                raise

        async def accept_handoff(product):
            self.check(run_id)
            response = {}
            def accept_or_return(r):
                lineage = None
                evaluation_context = r
                if r["operation"]["kind"] == "synthesis_continuation":
                    from .synthesis_checkpoint import checkpoint_evaluation_view
                    if product.get("sender") not in {"coordinator", "reviewer"}:
                        raise Conflict("Synthesis continuation cannot replace accepted specialist stages.")
                    evaluation_context, lineage = checkpoint_evaluation_view(r)
                evaluation = evaluate_handoff(product, evaluation_context)
                if lineage:
                    evaluation["checkpoint_lineage"] = lineage
                receipt = record_evaluation(r, evaluation, subject_sha256=digest(product))
                response.update(accepted=evaluation["verdict"] == "accepted", evaluation_id=receipt["id"],
                                reason=evaluation["reason"], repair_allowed=evaluation["repair_allowed"])
                if not response["accepted"]:
                    self.store.append_event(r, "Harness", "Work product returned to sender", evaluation["reason"],
                                            "blocked" if not evaluation["repair_allowed"] else "rejected", "stage.evaluation")
                    return
                accepted = copy.deepcopy(product)
                handoffs = r.setdefault("handoffs", [])
                accepted.update(id=f"{r['operation']['id']}-handoff-{len(handoffs)+1}", run_id=run_id,
                                operation_id=r["operation"]["id"], accepted_at=now(), acceptance_status="accepted",
                                acceptance_evaluation_id=receipt["id"])
                if lineage:
                    accepted["checkpoint_lineage"] = copy.deepcopy(lineage)
                handoffs.append(accepted)
                response["id"] = accepted["id"]
                self.store.append_event(r, accepted["sender"], "Work product accepted", accepted["question"], type="handoff")
            self.store.mutate(run_id, accept_or_return)
            return response

        async def request_molecular(request):
            return await self.agent_molecular(run_id, request, emit, cancelled, accept_evidence)

        async def accept_skill(request):
            from .scientific_skills import load_skill
            self.check(run_id)
            skill = load_skill(request["skill_id"], request["role"])
            if request.get("sha256", skill["sha256"]) != skill["sha256"] or request.get("version", skill["version"]) != skill["version"]:
                raise ValueError("Loaded skill differs from its current pinned version.")
            receipt = {}
            def save(r):
                receipts = r.setdefault("skill_receipts", [])
                old = next((x for x in receipts if x["skill_id"] == skill["id"] and x["role"] == request["role"] and x["operation_id"] == r["operation"]["id"]), None)
                if old:
                    if old["sha256"] != skill["sha256"] or old["version"] != skill["version"]:
                        raise Conflict("Skill changed during an active operation; start a new investigation.")
                    receipt.update(old)
                    return
                receipt.update(id=uuid.uuid4().hex, skill_id=skill["id"], name=skill["name"], version=skill["version"], sha256=skill["sha256"], role=request["role"], operation_id=r["operation"]["id"], loaded_at=now(), origin=skill["origin"])
                receipts.append(dict(receipt))
                self.store.append_event(r, request["role"], "Versioned scientific skill applied", skill["name"] + " · " + skill["version"], type="skill.loaded")
            self.store.mutate(run_id, save)
            return receipt

        if not run["evidence"]:
            self.store.mutate(run_id, lambda r: r.update(evidence=copy.deepcopy(case["evidence"])))
            await emit("Evidence curator", "Pinned source packet qualified", f"{len(case['evidence'])} evidence records loaded with exact source locators and hashes.")
        op = run["operation"]
        if op["kind"] == "investigation" and case.get("required_analysis_ids"):
            from .analysis_tools import analyze_case, analysis_catalog
            from .config import RUNTIME
            recipes = {item["id"]: item for item in analysis_catalog(case["id"])}
            for analysis_id in case["required_analysis_ids"]:
                self.check(run_id)
                if analysis_id not in recipes or recipes[analysis_id].get("followup_only"):
                    raise Conflict("A scientist-required analysis is no longer an available initial recipe.")
                action_id = op["id"] + "-required-" + digest(analysis_id)[:12]
                request = {"analysis_id": analysis_id, "case_id": case["id"], "source_manifest_sha256": digest(case.get("source_manifest", []))}
                record = self.store.begin_action(run_id, action_id, "scientist-required-analysis", request)
                if record is None:
                    await emit("bioinformatician", "Analyzing scientist-required study data", analysis_id, "running", "analysis")
                    try:
                        if analysis_id == "gse28460-paired-expression":
                            from .gse28460_analysis import analyze
                            record = await asyncio.to_thread(analyze, case_id=case["id"], output_dir=RUNTIME / "artifacts" / action_id)
                        else:
                            record = await asyncio.to_thread(analyze_case, case["id"], analysis_id)
                        self.store.end_action(run_id, action_id, "succeeded", record)
                    except BaseException:
                        self.store.end_action(run_id, action_id, "failed", {"error": "Required source analysis failed; no model result was fabricated."})
                        raise
                await accept_evidence(record)
                def attach_required(current):
                    operations = current.setdefault("required_analysis_operations", [])
                    if any(item["action_id"] == action_id for item in operations):
                        return
                    artifacts = [{"name": item["name"], "sha256": item["sha256"], "bytes": item["bytes"],
                                  "url": f"/api/runs/{run_id}/artifacts/{action_id}/{item['name']}"}
                                 for item in record.get("values", {}).get("artifacts", []) if item.get("written")]
                    operations.append({"analysis_id": analysis_id, "action_id": action_id, "status": "completed",
                                       "evidence_id": record["id"], "artifacts": artifacts, "origin": "scientist_required_study_input"})
                self.store.mutate(run_id, attach_required)
        synthesis_checkpoint = None
        if op["kind"] == "synthesis_continuation":
            from .synthesis_checkpoint import synthesis_context
            synthesis_checkpoint = synthesis_context(self.store.get(run_id))
        if op["kind"] in ("feedback", "outcome"):
            entry = op["input"]
            eid = "user-" + entry["id"]
            summary = entry["text"] if op["kind"] == "feedback" else f"{entry['endpoint']}: {entry['value']} {entry['unit']}. {entry['notes']}"
            evidence = {"id": eid, "title": "Scientist correction" if op["kind"] == "feedback" else "Returned experiment measurement", "kind": "user_report",
                        "summary": summary, "source": {"name": "Scientist submission", "url": "", "locator": f"Decision v{entry['decision_version']}; submission {entry['id']}", "sha256": digest(entry)},
                        "values": {"qc": "identity and field validation passed; scientific verification pending"}}
            def add(r):
                if eid not in {e["id"] for e in r["evidence"]}:
                    r["evidence"].append(evidence)
            self.store.mutate(run_id, add)
            await emit("Outcome curator", "Input attached to exact decision", "Identity and required fields validated. User-reported measurements remain explicitly attributed.")
        if op["kind"] == "modeling":
            await self.modeling(run_id, emit, cancelled)
            return
        followup_evidence = None
        if op["kind"] == "followup":
            followup_evidence = await self.execute_followup(run_id, emit, cancelled, accept_evidence)
        self.store.mutate(run_id, lambda r: r.update(stage="investigating"))
        if run["mode"] == "demo":
            steps = [
                ("Investigator", "Compare competing explanations", "Prepared case logic separates the supplied hypothesis from agent-derived alternatives."),
                ("Quantitative analyst", "Keep measurements in their original scope", "Read pinned extracted values and source locators; do not infer patient outcomes from an assay or library."),
                ("Molecular specialist", "Qualify the BioNeMo branch", "Exact constructs, target retention and matched controls are prerequisites; no invented structure or efficacy score."),
                ("Reviewer", "Challenge the interpretation", "Retain counterevidence, missing measurements and an experiment that distinguishes the alternatives."),
                ("R&D coordinator", "Prepare the experiment handoff", "Link the design objective, controls and return-data requirements to this decision.")]
            checkpoint = self.store.get(run_id)["checkpoint"]
            for index, step in enumerate(steps):
                if index < checkpoint:
                    continue
                await asyncio.sleep(DEMO_DELAY)
                await emit(*step, type="demo_step")
                self.store.mutate(run_id, lambda r, i=index: r.update(checkpoint=i+1))
            decision = demo_decision(self.store.get(run_id))
        else:
            from . import providers
            action_id = op["id"] + "-rosalind"
            run = self.store.get(run_id)
            action_request = {"hypothesis_sha256": run["hypothesis"]["sha256"], "evidence_ids": [e["id"] for e in run["evidence"]], "model": providers.selected_model()}
            if synthesis_checkpoint is not None:
                action_request.update(checkpoint_id=synthesis_checkpoint["id"], checkpoint_sha256=synthesis_checkpoint["sha256"],
                                      source_operation_id=synthesis_checkpoint["source_operation_id"], reused_handoff_ids=synthesis_checkpoint["source_handoff_ids"])
            prior = self.store.begin_action(run_id, action_id, "research-model-investigation", action_request)
            if prior is not None:
                decision = prior
            else:
                try:
                    context_case = copy.deepcopy(case)
                    context_case.pop("demo_decision", None)  # No reference answer in investigator context.
                    context_case["process_contract"] = run["process_contract"]
                    if synthesis_checkpoint is not None:
                        context_case["synthesis_checkpoint"] = copy.deepcopy(synthesis_checkpoint)
                    if op["kind"] in ("feedback", "outcome", "followup"):
                        from .followups import compact_previous_decision
                        context_case["revision_context"] = {"previous_decision": compact_previous_decision(run["decisions"][-1]), "scientist_input": op["input"] if op["kind"] != "followup" else None,
                            "continuation_input": op["input"] if op["kind"] == "followup" else None,
                            "instruction": "Reassess within the unchanged original objective. Explain exactly what changed."}
                    if op["kind"] == "followup":
                        context_case["followup_context"] = {"recommendation": op["input"]["recommendation"],
                            "origin": op["input"].get("origin", "scientist_selection"),
                            "previous_decision": compact_previous_decision(run["decisions"][-1]),
                            "evidence_ids": [followup_evidence["id"]], "execution_status": "completed",
                            "instruction": "Selected follow-up has executed. Review its accepted result, explain the new insight and next discriminating step. Do not repeat the same recipe."}
                    decision = await providers.investigate(context_case, run["hypothesis"]["text"], run["evidence"], emit, cancelled,
                                                          accept_evidence=accept_evidence, accept_handoff=accept_handoff,
                                                          request_molecular=request_molecular, accept_skill=accept_skill)
                    if op["kind"] == "followup":
                        decision.setdefault("changes", []).append("Executed " + op["input"]["analysis_id"] + "; accepted " + followup_evidence["id"] + "; team and reviewer reassessed decision v" + str(op["input"]["decision_version"]) + ".")
                    self.store.end_action(run_id, action_id, "succeeded", decision)
                except BaseException as exc:
                    self.provider_failure(run_id, action_id, exc)
                    raise
        self.check(run_id)
        self.publish(run_id, decision, operation_id=op["id"])

    async def execute_followup(self, run_id, emit, cancelled, accept_evidence):
        """Persist intent, execute one registered action, accept evidence, then review."""
        from .followups import approved_catalog, update_operation
        from .providers import ProviderError, _redact
        run = self.check(run_id)
        entry = run["operation"]["input"]
        recipe = next((item for item in approved_catalog(run["case_id"]) if item["id"] == entry["analysis_id"]), None)
        if not recipe or digest(recipe) != entry["recipe_sha256"]:
            raise Conflict("The registered follow-up changed after selection; select it again against the current catalog.")
        if (run["hypothesis"]["sha256"] != entry["hypothesis_sha256"]
                or run["decisions"][-1]["sha256"] != entry["decision_sha256"]
                or digest(run["case_snapshot"].get("source_manifest", [])) != entry["source_manifest_sha256"]):
            raise Conflict("Follow-up input versions no longer match the accepted request.")
        action_id = entry["id"] + "-followup"
        directory = RUNTIME / "artifacts" / action_id
        request = {key: entry[key] for key in ("analysis_id", "kind", "recipe_sha256", "decision_sha256", "hypothesis_sha256", "source_manifest_sha256")}
        prior = self.store.begin_action(run_id, action_id, "registered-followup", request)
        self.store.mutate(run_id, lambda r: update_operation(r, action_id=action_id))
        result = prior
        try:
            if result is None:
                await emit("Follow-up executor", "Executing selected follow-up", recipe["title"], "running", "followup")
                if recipe["kind"] == "data_analysis":
                    from .analysis_tools import analyze_case
                    record = await asyncio.to_thread(analyze_case, run["case_id"], recipe["id"])
                    result = {"status": "completed", "evidence": record, "artifacts": []}
                else:
                    from .structural_followups import execute
                    result = await execute(recipe["id"], output_dir=directory, emit=emit, cancelled=cancelled)
                if isinstance(result, dict):
                    receipts = [{key: job[key] for key in ("label", "model", "scope", "status", "request_id", "http_status",
                                 "sequence_sha256", "sequence_length", "confidence_score", "created_at", "finished_at") if key in job}
                                for job in result.get("jobs", []) if isinstance(job, dict)]
                    self.store.mutate(run_id, lambda r: update_operation(r, result_status=result.get("status", "unknown"), provider_receipts=receipts))
                # Only executor-returned artifacts under this durable action may be published.
                artifacts = []
                for item in (result.get("artifacts", []) if isinstance(result, dict) else []):
                    path = Path(item["path"])
                    if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
                            or not path.resolve().is_relative_to(directory.resolve()) or not path.is_file()
                            or path.suffix != ".cif" or path.stat().st_size > 10_000_000):
                        raise ValueError("Follow-up artifact is outside its registered output boundary.")
                    data = path.read_bytes()
                    if len(data) > 10_000_000 or hashlib.sha256(data).hexdigest() != item.get("sha256"):
                        raise ValueError("Follow-up artifact does not match its provider receipt.")
                    relative = path.resolve().relative_to(directory.resolve()).as_posix()
                    artifact = {key: item[key] for key in ("name", "sha256", "media_type", "label", "model", "request_id", "confidence_score", "scope") if key in item}
                    artifact.update(size=len(data), url=f"/api/runs/{run_id}/artifacts/{action_id}/{relative}",
                                    preview_url=f"/api/runs/{run_id}/structure-preview/{action_id}/{relative}")
                    artifacts.append(artifact)
                if isinstance(result, dict):
                    result["published_artifacts"] = artifacts
                self.store.mutate(run_id, lambda r: update_operation(r, artifacts=artifacts))
                self.check(run_id)
                if not isinstance(result, dict) or result.get("status") != "completed" or not isinstance(result.get("evidence"), dict):
                    state = result.get("status", "unknown") if isinstance(result, dict) else "unknown"
                    self.store.end_action(run_id, action_id, "unknown" if state in {"pending", "unknown", "incomplete"} else "failed", result)
                    raise ProviderError("Selected follow-up did not return a complete qualified result; no repeated submission or new decision was made.", status="unknown" if state in {"pending", "unknown", "incomplete"} else "failed")
                if recipe["kind"] == "bionemo_public_structure" and sorted(a["sha256"] for a in artifacts) != sorted(result["evidence"]["values"].get("artifact_hashes", [])):
                    raise ValueError("Structural evidence does not match the returned output artifacts.")
                await accept_evidence(result["evidence"])
                self.store.end_action(run_id, action_id, "succeeded", result)
            else:
                await accept_evidence(result["evidence"])
        except BaseException as exc:
            current = next(a for a in self.store.get(run_id)["actions"] if a["id"] == action_id)
            if current["state"] == "submitting":
                state = "unknown" if isinstance(exc, (Cancelled, asyncio.CancelledError)) or getattr(exc, "status", None) == "unknown" else "failed"
                self.store.end_action(run_id, action_id, state, {"reason": _redact(str(exc))[:600]})
            raise
        evidence = result["evidence"]
        self.store.mutate(run_id, lambda r: update_operation(r, status="reviewing", action_id=action_id,
                          evidence_id=evidence["id"], result_status="completed", recipe=recipe,
                          artifacts=result.get("published_artifacts", [])))
        await emit("Follow-up executor", "Follow-up evidence accepted", evidence["title"] + "; specialist and independent review starting.", "completed", "followup")
        return evidence

    async def agent_molecular(self, run_id, request, emit, cancelled, accept_evidence):
        """Specialist tool boundary: trusted intake inputs, durable intent, one submission."""
        from . import providers
        run = self.check(run_id)
        inputs = run["case_snapshot"].get("molecular_inputs")
        if not inputs or not inputs.get("target_retained"):
            return {"status": "blocked", "reason": "Qualified exact reference/candidate/target sequences and target-retained scope have not been supplied."}
        # A team re-evaluation is not authority to repeat the same external pair.
        # Exact inputs include the scientist's source note and retention assertion.
        # Also recognize earlier releases whose action IDs were operation-scoped.
        input_identity = digest(inputs)
        saved = None
        with self.store.connect() as db:
            for row in db.execute("SELECT id,state,request,result FROM actions WHERE run_id=? AND kind=? ORDER BY rowid",
                                  (run_id, "agent-directed-bionemo-comparison")):
                recorded_request = json.loads(row["request"])
                if digest(recorded_request.get("inputs")) == input_identity:
                    saved = dict(row)
                    break
        action_id = saved["id"] if saved else run_id + "-agent-boltz-" + input_identity[:24]
        if saved and saved["state"] != "succeeded":
            receipt = {"status": "blocked", "action_id": action_id, "prior_state": saved["state"],
                       "input_sha256": input_identity, "reused": True,
                       "reason": "This exact qualified molecular comparison has a prior unresolved or unsuccessful attempt; automatic resubmission is prohibited."}
            self.store.mutate(run_id, lambda r: r.update(agent_modeling={**receipt, "artifacts": [], "operation_id": run["operation"]["id"]}))
            return receipt
        if saved is None and providers.capabilities()["bionemo"]["status"] not in ("configured", "verified"):
            return {"status": "blocked", "reason": "NVIDIA key or approved local NIM is not configured."}
        directory = RUNTIME / "artifacts" / action_id
        previous = self.store.begin_action(run_id, action_id, "agent-directed-bionemo-comparison", {
            "inputs": inputs, "input_sha256": input_identity,
            "source_manifest_sha256": digest(run["case_snapshot"].get("source_manifest", [])),
            "rationale": request.get("rationale", "Qualified molecular comparison")})
        if previous is None:
            try:
                result = await providers.compare_binders(inputs["target_sequence"], inputs["reference_binder"], inputs["candidate_binder"], directory, emit=emit, cancelled=cancelled)
                state = "succeeded" if result.get("status") == "completed" else "unknown"
                self.store.end_action(run_id, action_id, state, result)
            except BaseException as exc:
                self.provider_failure(run_id, action_id, exc)
                raise
        else:
            result = previous
        self.check(run_id)
        if result.get("status") != "completed":
            self.store.mutate(run_id, lambda r: r.update(agent_modeling={"status": "incomplete", "reason": result.get("reason", "External job is unresolved."), "artifacts": [], "result": result, "action_id": action_id, "operation_id": run["operation"]["id"]}))
            return {"status": "incomplete", "action_id": action_id, "reason": result.get("reason", "An external pair member is unresolved."), "result": result}
        accepted = next((item for item in run["evidence"] if item["id"] == action_id), None)
        if accepted is not None:
            if (accepted.get("source", {}).get("sha256") != digest(result)
                    or accepted.get("values", {}).get("input_hashes") != {k: digest(inputs[k]) for k in ("target_sequence", "reference_binder", "candidate_binder")}):
                raise Conflict("The recorded molecular evidence differs from its original successful receipt.")
            await accept_evidence(copy.deepcopy(accepted))
            artifacts = copy.deepcopy(accepted["values"].get("artifacts", []))
            self.store.mutate(run_id, lambda r: r.update(agent_modeling={"status": "completed", "reason": "Reused the accepted result for the same qualified inputs; no new NVIDIA inference.",
                "artifacts": artifacts, "action_id": action_id, "operation_id": run["operation"]["id"], "reused": True}))
            return {"status": "completed", "action_id": action_id, "evidence": accepted, "artifacts": artifacts, "reused": True}
        artifacts = [{"name": p.name, "url": f"/api/runs/{run_id}/artifacts/{action_id}/{p.relative_to(directory).as_posix()}",
                      "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "size": p.stat().st_size}
                     for p in directory.rglob("*") if p.is_file() and p.suffix in (".cif", ".pdb", ".json")]
        evidence = {"id": action_id, "title": "Agent-requested BioNeMo matched binder comparison", "kind": "prediction",
                    "summary": "Validated reference and candidate binding-domain predictions against the same supplied target; no whole-cell efficacy inference.",
                    "source": {"name": "NVIDIA BioNeMo Boltz-2", "url": "https://build.nvidia.com/mit/boltz2", "locator": action_id, "sha256": digest(result)},
                    "values": {"result": result, "artifacts": artifacts, "input_hashes": {k: digest(inputs[k]) for k in ("target_sequence", "reference_binder", "candidate_binder")}}}
        await accept_evidence(evidence)
        self.store.mutate(run_id, lambda r: r.update(agent_modeling={"status": "completed", "reason": evidence["summary"], "artifacts": artifacts, "action_id": action_id, "operation_id": run["operation"]["id"]}))
        return {"status": "completed", "action_id": action_id, "evidence": evidence, "artifacts": artifacts, "reused": previous is not None}

    def publish(self, run_id, decision, *, operation_id=None):
        operation_id = operation_id or self.store.get(run_id)["operation"]["id"]
        def complete(run):
            if run["cancel_requested"]:
                raise Cancelled()
            if any(item.get("operation_id") == operation_id for item in run["decisions"]):
                return  # The decision and its queued continuation were already committed together.
            if run["operation"]["id"] != operation_id:
                raise Conflict("Publication belongs to a different or stale operation.")
            if (run.get("agent_modeling", {}).get("operation_id") == run["operation"]["id"]
                    or run.get("agent_modeling", {}).get("action_id") == run["operation"]["id"] + "-agent-boltz"):
                decision["rd_handoff"]["modeling"] = copy.deepcopy(run["agent_modeling"])
            normalized = normalize_decision(decision, run)
            run["decisions"].append(normalized)
            metadata = decision.get("metadata", {})
            if run["operation"]["kind"] != "modeling":
                account_provider_usage(run, run["operation"]["id"] + "-rosalind", metadata)
            unresolved = any(a["state"] in ("unknown", "submitting") for a in run["actions"])
            run.update(status="blocked" if unresolved else "completed", stage="decision", error="An external action remains unresolved; partial findings are available." if unresolved else None)
            if run["operation"]["kind"] == "followup":
                from .followups import update_operation
                update_operation(run, status=run["status"], new_decision_version=normalized["version"], finished_at=now())
            elif run["operation"]["kind"] == "synthesis_continuation":
                from .synthesis_checkpoint import update_synthesis_operation
                update_synthesis_operation(run, status=run["status"], new_decision_version=normalized["version"], finished_at=now())
            record_evaluation(run, boundary_receipt("decision_publication", "accepted", run["status"],
                                        "Required decision fields and accepted evidence citations passed; version, experiment and candidate IDs were assigned by the server. Scientific truth is not established by this check."),
                                        subject_sha256=normalized["sha256"])
            self.store.append_event(run, "Harness", f"Decision v{normalized['version']} ready", "Evidence references validated. Scientific review and experimental validation remain visible in the handoff.", type="completion")
            from .followups import apply_governance_continuation
            apply_governance_continuation(run)
        try:
            self.store.mutate(run_id, complete)
        except (ValueError, Conflict) as exc:
            self.store.mutate(run_id, lambda r: record_evaluation(r, boundary_receipt(
                "decision_publication", "rejected", "invalid", str(exc)[:500])))
            raise

    async def modeling(self, run_id, emit, cancelled):
        from . import providers
        run = self.check(run_id)
        inputs = run["operation"]["input"]
        action_id = run["operation"]["id"] + "-boltz"
        artifact_dir = RUNTIME / "artifacts" / action_id
        prior = self.store.begin_action(run_id, action_id, "bionemo-binder-comparison", inputs)
        if prior is None:
            try:
                result = await providers.compare_binders(inputs["target_sequence"], inputs["reference_binder"], inputs["candidate_binder"], artifact_dir, emit=emit, cancelled=cancelled)
                unresolved = any(job.get("status") in {"pending", "unknown", "dispatched"} for job in result.get("jobs", []))
                action_state = "succeeded" if result.get("status") == "completed" else ("unknown" if unresolved else "failed")
                self.store.end_action(run_id, action_id, action_state, result)
            except BaseException as exc:
                self.provider_failure(run_id, action_id, exc)
                raise
        else:
            result = prior
        self.check(run_id)
        evidence = {"id": action_id, "title": "BioNeMo matched binder predictions", "kind": "prediction", "summary": "Reference and candidate antigen-binding domains modeled against the same supplied target. Structural predictions do not establish CAR-T efficacy.",
                    "source": {"name": "NVIDIA BioNeMo Boltz-2", "url": "https://build.nvidia.com/mit/boltz2", "locator": action_id, "sha256": digest(result)}, "values": result}
        decision = copy.deepcopy(run["decisions"][-1])
        decision.pop("sha256", None)
        decision.pop("metadata", None)  # A molecular update does not spend the prior Rosalind tokens again.
        # A structural job registers the actual submitted constructs, not a generic
        # assay arm copied from the previous hypothesis-level recommendation.
        source_note = inputs.get("source_note", "Source note not present in the saved request.")
        target_hash = digest(inputs["target_sequence"])
        def construct_record(sequence, label):
            return {"name": label, "sequence_sha256": digest(sequence), "sequence_length": len(sequence),
                    "target_sequence_sha256": target_hash, "source_note": source_note, "modeling_action_id": action_id}
        handoff = decision["rd_handoff"]
        handoff["reference"] = construct_record(inputs["reference_binder"], "Supplied reference binding-domain construct")
        handoff["candidates"] = [{**construct_record(inputs["candidate_binder"], "Supplied candidate binding-domain construct"),
                                  "rationale": "Exact scientist-supplied candidate compared with the reference binder against the same fixed target."}]
        handoff["target"] = {"sequence_sha256": target_hash, "sequence_length": len(inputs["target_sequence"]),
                             "source_note": source_note, "retention_attested": inputs.get("target_retained", False)}
        handoff["objective"] = "Experimentally compare the supplied candidate and reference binding-domain constructs against the same supplied target."
        handoff["status"] = "awaiting_experimental_validation" if result.get("status") == "completed" else "modeling_incomplete"
        handoff["return_requirements"] = ["This decision's experiment ID and candidate ID", "Candidate and target sequence SHA-256 values from this handoff",
                                           "Measured endpoint, value and unit", "Matched reference control, replicates, assay provenance and QC notes"]
        artifacts = []
        for path in artifact_dir.rglob("*"):
            if path.is_file() and path.suffix in (".cif", ".pdb", ".json"):
                artifacts.append({"name": path.name, "url": f"/api/runs/{run_id}/artifacts/{action_id}/{path.relative_to(artifact_dir).as_posix()}", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size": path.stat().st_size})
        if result.get("status") != "completed":
            reason = result.get("reason", "The molecular comparison has an incomplete or unresolved member.")
            decision["rd_handoff"]["modeling"] = {"status": "incomplete", "reason": reason, "artifacts": artifacts, "result": result}
            decision["changes"] = ["Molecular comparison remains incomplete. Partial artifacts are preserved; no paired prediction was accepted as evidence."]
            def incomplete(r):
                if r["cancel_requested"]:
                    raise Cancelled()
                normalized = normalize_decision(decision, r)
                r["decisions"].append(normalized)
                r.update(status="blocked", stage="modeling", error=reason)
                record_evaluation(r, boundary_receipt("molecular_comparison", "rejected", "incomplete", reason), subject_sha256=normalized["sha256"])
                self.store.append_event(r, "BioNeMo", "Molecular comparison incomplete", reason, "blocked", "error")
            self.store.mutate(run_id, incomplete)
            return
        def accept(r):
            if action_id not in {e["id"] for e in r["evidence"]}:
                r["evidence"].append(evidence)
        self.store.mutate(run_id, accept)
        decision["rd_handoff"]["modeling"] = {"status": "completed", "reason": "Matched molecular predictions returned. No whole-cell efficacy claim.", "artifacts": artifacts, "result": result}
        decision["claims"].append({"text": evidence["summary"], "evidence_ids": [action_id], "kind": "prediction"})
        decision["changes"] = ["Added real BioNeMo reference/candidate structural comparison. Original scientific assessment remains unchanged pending experimental measurements."]
        self.publish(run_id, decision, operation_id=run["operation"]["id"])


async def main():
    await Worker().run_forever()

if __name__ == "__main__":
    asyncio.run(main())
