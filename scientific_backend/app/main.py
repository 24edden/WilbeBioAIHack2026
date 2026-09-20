from __future__ import annotations
import asyncio
import copy
import hashlib
import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import ROOT, RUNTIME
from .store import Store, Conflict, digest, now
from .worker import Worker
from . import __version__


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    @field_validator("*")
    @classmethod
    def nonblank(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError("Text fields must contain non-whitespace content.")
        return value


class CreateRun(StrictInput):
    case_id: str = Field(max_length=100)
    hypothesis: str = Field(min_length=10, max_length=24000)
    source_name: str = Field(default="User message", min_length=1, max_length=300)
    mode: Literal["demo", "live"] = "live"
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=100)
    molecular_inputs: dict | None = None
    required_analysis_ids: list[str] = Field(default_factory=list, max_length=8)
    evaluation_lesson_id: str | None = Field(default=None, max_length=100)

    @field_validator("hypothesis")
    @classmethod
    def meaningful(cls, value):
        if len(value.strip()) < 10:
            raise ValueError("Supply the hypothesis you want investigated.")
        return value

    @field_validator("molecular_inputs")
    @classmethod
    def qualify_inputs(cls, value):
        if value is None:
            return value
        # Reuse the exact-sequence boundary, excluding operation-owned fields.
        validated = Modeling.model_validate({**value, "decision_version": 1})
        return {k: v for k, v in validated.model_dump().items() if k not in ("decision_version", "idempotency_key")}


class Feedback(StrictInput):
    decision_version: int = Field(ge=1)
    text: str = Field(min_length=3, max_length=6000)
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=100)


class FollowupRequest(StrictInput):
    decision_version: int = Field(ge=1)
    recommendation_id: str = Field(min_length=1, max_length=150)
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=100)


class SynthesisContinuationRequest(StrictInput):
    source_operation_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=100)


class ResearchBriefRequest(StrictInput):
    decision_version: int = Field(ge=1, strict=True)
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=100)


class Outcome(StrictInput):
    decision_version: int = Field(ge=1)
    experiment_id: str = Field(min_length=1, max_length=100)
    candidate_id: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, max_length=200)
    value: float = Field(strict=True, allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=100)
    notes: str = Field(min_length=3, max_length=6000)
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=100)


class Modeling(StrictInput):
    decision_version: int = Field(ge=1)
    target_sequence: str = Field(min_length=15, max_length=1800)
    reference_binder: str = Field(min_length=15, max_length=900)
    candidate_binder: str = Field(min_length=15, max_length=900)
    target_retained: Literal[True]
    source_note: str = Field(min_length=10, max_length=6000)
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=100)

    @field_validator("target_sequence", "reference_binder", "candidate_binder")
    @classmethod
    def sequence(cls, value):
        value = "".join(value.split()).upper()
        if len(value) < 15:
            raise ValueError("Protein sequences must contain at least 15 amino acids after whitespace removal.")
        if not set(value).issubset(set("ACDEFGHIKLMNPQRSTVWY")):
            raise ValueError("Use an exact protein sequence with standard amino-acid letters and no FASTA header.")
        return value


class Probe(StrictInput):
    provider: Literal["rosalind", "bionemo"]


class LessonProposal(StrictInput):
    origin_run_id: str = Field(min_length=1, max_length=100)
    decision_version: int = Field(ge=1)
    procedure: str = Field(min_length=10, max_length=4000)
    conditions: str = Field(min_length=10, max_length=2000)
    scope_case_ids: list[str] = Field(min_length=1, max_length=20)
    excluded_case_ids: list[str] = Field(min_length=1, max_length=20)
    author: str = Field(min_length=1, max_length=200)


class LessonReview(StrictInput):
    approved: bool
    reviewer: str = Field(min_length=1, max_length=200)
    notes: str = Field(min_length=10, max_length=3000)


class LessonEvaluation(StrictInput):
    baseline_run_id: str = Field(min_length=1, max_length=100)
    candidate_run_id: str = Field(min_length=1, max_length=100)
    out_of_scope_run_id: str = Field(min_length=1, max_length=100)
    quality_passed: bool
    evaluator: str = Field(min_length=1, max_length=200)
    notes: str = Field(min_length=10, max_length=4000)


def public_run(run, full=True):
    result = copy.deepcopy(run)
    result.pop("case_snapshot", None)
    if not full:
        for key in ("evidence", "events", "actions", "feedback", "outcomes", "operation"):
            result.pop(key, None)
        result["decision_count"] = len(result.pop("decisions"))
    return result


def report(run):
    lines = [f"# {run['title']}", "", f"Run: {run['id']} · mode: {run['mode']} · status: {run['status']}", "",
             "## Supplied hypothesis", "", run["hypothesis"]["text"], "", f"Source: {run['hypothesis']['source_name']}", f"SHA-256: {run['hypothesis']['sha256']}", ""]
    for decision in run["decisions"]:
        lines.extend([f"## Decision v{decision['version']}", "", str(decision["assessment"]), "", decision["summary"], ""])
        for insight in decision.get("insights", []):
            lines.extend(["### " + insight["title"], "", insight["finding"], "", "Why it matters: " + insight["why_it_matters"],
                          "", "Evidence: " + ", ".join(insight["evidence_ids"]), "", "Next step: " + insight["next_step"], ""])
        lines.extend(f"- {c['text']} [{', '.join(c['evidence_ids'])}]" for c in decision["claims"])
        governance = decision.get("governance")
        if governance:
            lines.extend(["", "### Hypothesis testing governance", "",
                          "Decision: " + governance["stop_reason"].replace("_", " "), "",
                          governance["continuation_reason"], ""])
            if governance.get("next_action_id"):
                lines.extend(["Selected next analysis: " + governance["next_action_id"], ""])
            for hypothesis in governance["hypotheses"]:
                lines.extend(["**" + hypothesis["hypothesis_id"] + " · " + hypothesis["status"].replace("_", " ") + "**", "",
                              hypothesis["statement"], "", "Scope: " + hypothesis["scope"], "", hypothesis["rationale"], "",
                              "Supporting evidence: " + ", ".join(hypothesis["supporting_evidence_ids"]),
                              "Counterevidence: " + ", ".join(hypothesis["contradicting_evidence_ids"]),
                              "Test evidence: " + ", ".join(hypothesis["test_evidence_ids"]), "",
                              "Falsification test: " + hypothesis["falsification_test"],
                              "Test result: " + hypothesis["falsification_result"],
                              "Next analyses: " + ", ".join(hypothesis["next_analysis_ids"]),
                              "Unresolved requirement: " + hypothesis["blocker"], ""])
        elif decision.get("prior_governance"):
            lines.extend(["", "New modeling evidence has not yet been used to reassess the prior hypothesis governance.", ""])
        if decision.get("alternatives"):
            lines.extend(["", "### Competing explanations", ""])
            for alternative in decision["alternatives"]:
                lines.extend(["**" + alternative["title"] + "**", "", alternative["reason"], ""])
        lines.extend(["", "### Limitations", ""] + [f"- {x}" for x in decision["limitations"]])
        lines.extend(["", "### Next experiment", "", json.dumps(decision["next_experiment"], indent=2), "", "### R&D handoff", "", json.dumps(decision["rd_handoff"], indent=2), ""])
        for item in decision.get("followups", []):
            lines.extend(["### Recommended follow-up: " + item["title"], "", item["rationale"], "",
                          "Decision it could change: " + item["decision_it_could_change"], "",
                          "Recipe: " + item["analysis_id"] + " · status at publication: " + item["status"], ""])
    if run.get("followup_operations"):
        lines.extend(["## Follow-up execution records", "", json.dumps(run["followup_operations"], indent=2), ""])
    if run.get("governance_state"):
        lines.extend(["## Actual continuation state", "", json.dumps(run["governance_state"], indent=2), ""])
    if run.get("synthesis_operations"):
        lines.extend(["## Explicit synthesis continuation", "",
                      "A new synthesis/review operation reused verified accepted specialist handoffs. Their original provenance remains unchanged; reuse is not a new specialist model call. Earlier failed requests remain in the execution record.",
                      "", json.dumps(run["synthesis_operations"], indent=2), ""])
    for brief in run.get("research_briefs", []):
        content = brief.get("content", {})
        answer = content.get("proposed_answer", {})
        lines.extend([f"## Working answer addendum v{brief['version']} — decision v{brief['source_decision_version']}", "",
                      "New model-written interpretation and existing-artifact audit; historical decisions are unchanged. Human scientific review is pending.", "",
                      content.get("headline", ""), "", content.get("plain_summary", ""), "",
                      "### Proposed answer", "", answer.get("statement", ""), "",
                      "Scope: " + answer.get("scope", ""), "", "Main caveat: " + answer.get("caveat", ""), "",
                      "Strongest alternative: " + answer.get("strongest_alternative", ""), ""])
        for finding in content.get("findings", []):
            lines.extend(["- " + finding["what"] + " " + finding["why_it_matters"] + " [" + ", ".join(finding["evidence_ids"]) + "]"])
        lines.extend(["", "### Why the decisions changed", ""])
        for item in content.get("decision_story", []):
            lines.extend([f"- Decision v{item['decision_version']}: {item['what_changed']} {item['why']} Next: {item['next_step']}"])
        nvidia = content.get("nvidia", {})
        lines.extend(["", "### What the NVIDIA calls added", "", nvidia.get("summary", ""), "",
                      *["- " + item for item in nvidia.get("learned", [])], "",
                      *["Not established: " + item for item in nvidia.get("not_established", [])], "",
                      "### Exact validated molecular inputs", ""])
        for sequence in brief.get("molecular_audit", {}).get("sequence_inventory", []):
            lines.extend([f"- {sequence.get('label', sequence['id'])}: {sequence['role']}, {sequence['length']} residues; SHA-256 {sequence['sequence_sha256']}",
                          "", "```text", sequence["sequence"], "```", ""])
        lines.extend(["### Interpretation provenance", "", json.dumps({key: brief.get(key) for key in (
            "sha256", "context_sha256", "source_decision_sha256", "model_review", "instruction_hashes")}, indent=2), ""])
    for discovery in run.get("sequence_discoveries", []):
        lines.extend([f"## AI sequence discovery v{discovery['version']}", "", discovery.get("summary", ""), "",
                      discovery.get("scientific_rationale", ""), "", discovery.get("qualification_note", ""), ""])
        for sequence in discovery.get("sequences", []):
            lines.extend([f"### {sequence['role']}: {sequence['label']}", "", sequence.get("qualification", ""), "",
                          f"Source: {sequence['source_url']} · {sequence['source_locator']}", "",
                          "SHA-256: " + sequence["sequence_sha256"], "", "```text", sequence["sequence"], "```", ""])
        lines.extend(["Missing inputs: " + "; ".join(discovery.get("missing_inputs", [])), "",
                      "Independent AI review: " + str(discovery.get("model_review", {}).get("verdict", "not recorded")), ""])
    for operation in run.get("required_analysis_operations", []):
        lines.extend(["## Scientist-required study analysis", "", operation["analysis_id"] + " · " + operation["status"], ""])
        for artifact in operation.get("artifacts", []):
            lines.extend([f"- [{artifact['name']}]({artifact['url']}) · SHA-256 {artifact['sha256']}"])
    lines.extend(["## Execution provenance", "", "Application: Team TBD", "", json.dumps(run["usage"], indent=2), ""])
    for receipt in run.get("skill_receipts", []):
        lines.extend([f"- Skill: {receipt['name']} · role: {receipt['role']} · version: {receipt['version']}",
                      f"  SHA-256: {receipt['sha256']} · receipt: {receipt['id']}"])
    lines.extend(["", "## Specialist work products", ""])
    for product in run.get("handoffs", []):
        lines.extend([f"### {product['sender']} → {', '.join(product['recipient'])}", "",
                      f"Status: {product['result_status']} · operation: {product['operation_id']}", "",
                      product['question'], "", product.get('result', ''), "", "Method: " + product['method'], "",
                      "Decision affected: " + product['decision_it_could_change'], "",
                      "Input versions: " + json.dumps(product['input_versions'], ensure_ascii=False), "",
                      *["- " + item for item in product['limitations']], ""])
    lines.extend(["## Stage evaluations", "", "Software acceptance checks do not establish scientific validity.", ""])
    for check in run.get("stage_evaluations", []):
        lines.extend([json.dumps(check, ensure_ascii=False, indent=2), ""])
    lines.extend(["## Evidence", ""])
    for evidence in run["evidence"]:
        source = evidence["source"]
        lines.extend([f"### {evidence['id']} · {evidence['title']}", "", evidence["summary"], "", f"Source: {source['name']} · {source['locator']}", f"SHA-256: {source['sha256']}", source.get("url", ""), ""])
    return "\n".join(lines)


def create_app(store=None, embedded=None):
    store = store or Store()
    embedded = (os.getenv("ROSALIND_EMBEDDED_WORKER", "1") == "1") if embedded is None else embedded
    worker = Worker(store)
    from .learning import Learning
    learning = Learning(store)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(worker.run_forever()) if embedded else None
        yield
        worker.stopping = True
        if worker.current:
            worker.current.cancel()
        if task:
            try:
                await asyncio.wait_for(task, 3)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                task.cancel()

    app = FastAPI(title="Team TBD", version=__version__, lifespan=lifespan)
    app.state.store = store
    app.state.worker = worker
    app.state.probe_lock = asyncio.Lock()

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        # Same-origin writes only; service binds to localhost/private forwarded loopback.
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            from urllib.parse import urlsplit
            if urlsplit(origin).netloc != request.headers.get("host"):
                return JSONResponse({"detail": "Cross-origin writes are not permitted."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
        return response

    @app.exception_handler(Conflict)
    async def conflict_handler(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(KeyError)
    async def missing_handler(request, exc):
        return JSONResponse({"detail": "Run, case or artifact not found."}, status_code=404)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        # Do not echo arbitrary inputs, including NaN or sensitive sequence content.
        errors = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        return JSONResponse({"detail": errors}, status_code=422)

    from .cases import SourceIntegrityError

    @app.exception_handler(SourceIntegrityError)
    async def integrity_handler(request, exc):
        return JSONResponse({"detail": str(exc), "status": "blocked"}, status_code=409)

    @app.get("/api/health")
    async def health():
        from .providers import capabilities, effective_model_limits
        from .engineering_checks import latest_bionemo_check
        runs = store.list()
        with store.connect() as db:
            import time
            lease = db.execute("SELECT expires FROM leases WHERE name='worker'").fetchone()
        worker_alive = bool(lease and lease[0] > time.time())
        check = latest_bionemo_check(RUNTIME)
        if check and check.get("monomer_service_verified"):
            check["links"] = {"structure": f"/api/engineering/bionemo/{check['check_id']}/prediction.cif",
                              "receipt": f"/api/engineering/bionemo/{check['check_id']}/receipt.json",
                              "preview": f"/api/engineering/bionemo/{check['check_id']}/preview.json"}
        return {"status": "ok" if worker_alive else "degraded", "service": "Team TBD", "version": __version__, "worker_alive": worker_alive,
                "capabilities": capabilities(), "model_limits": effective_model_limits(),
                "engineering_checks": {"bionemo": check},
                "active_runs": sum(r["status"] in ("queued", "running") for r in runs), "time": now()}

    @app.get("/api/engineering/bionemo/{check_id}/{filename}")
    async def engineering_artifact(check_id: str, filename: str):
        from .engineering_checks import bionemo_download
        if filename not in {"prediction.cif", "receipt.json", "preview.json"}:
            raise HTTPException(404, "Unknown engineering artifact")
        try:
            receipt, data = bionemo_download(RUNTIME, check_id)
        except (OSError, ValueError, TypeError):
            raise HTTPException(404, "No validated engineering artifact available")
        if filename == "receipt.json":
            return JSONResponse(receipt)
        if filename == "preview.json":
            from .structure_preview import preview_from_cif
            try:
                return preview_from_cif(data, receipt=receipt, scope=receipt["scope"],
                                        cif_url=f"/api/engineering/bionemo/{check_id}/prediction.cif")
            except (ValueError, TypeError):
                raise HTTPException(409, "Structure preview did not pass validation.")
        return Response(data, media_type="chemical/x-mmcif",
                        headers={"Content-Disposition": 'attachment; filename="nvidia-engineering-monomer.cif"'})

    @app.post("/api/capabilities/probe")
    async def probe(data: Probe):
        from .providers import probe as provider_probe
        if app.state.probe_lock.locked():
            raise Conflict("A capability probe is already running.")
        async with app.state.probe_lock:
            try:
                return await asyncio.wait_for(provider_probe(data.provider), 120)
            except TimeoutError:
                raise HTTPException(504, "Capability check timed out. No automatic repeat was made.")

    @app.get("/api/cases")
    async def cases():
        from .cases import list_cases
        return list_cases()

    @app.get("/api/process-contract")
    async def process_contract():
        from .process_contract import get_process_contract
        return get_process_contract()

    @app.get("/api/skills")
    async def skills():
        from .scientific_skills import skill_catalog, verify_life_sciences_runtime
        registered = skill_catalog()
        try:
            verify_life_sciences_runtime()
            external_available = True
        except (ValueError, OSError):
            external_available = False
        for item in registered:
            if item.get("external_plugin"):
                item["available"] = external_available
        return {"skills": registered, "attribution": "Applied receipts identify actual instruction use. Team TBD Rosalind-informed guidance, installed OpenAI life-sciences tools and NVIDIA skills retain separate origins; model identity is recorded independently."}

    @app.get("/api/datasets")
    async def datasets():
        from .data_catalog import list_datasets
        return await asyncio.to_thread(list_datasets)

    @app.get("/api/datasets/{dataset_id}")
    async def dataset(dataset_id: str):
        from .data_catalog import CatalogAnalysisError, get_dataset
        try:
            return await asyncio.to_thread(get_dataset, dataset_id)
        except CatalogAnalysisError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/cases/{case_id}")
    async def case(case_id: str):
        from .cases import get_case
        packet = get_case(case_id)
        packet.pop("demo_decision", None)
        return packet

    @app.post("/api/runs", status_code=202)
    async def create(data: CreateRun):
        from .cases import get_case
        from .providers import capabilities
        payload = data.model_dump()
        with store.transaction() as db:
            existing = store.dedupe(db, "create", data.idempotency_key, payload)
            if existing:
                return public_run(existing)
        case = get_case(data.case_id)
        from .analysis_tools import analysis_catalog
        allowed = {entry["id"] for entry in analysis_catalog(data.case_id)}
        if len(set(data.required_analysis_ids)) != len(data.required_analysis_ids) or not set(data.required_analysis_ids) <= allowed:
            raise Conflict("Required analyses must be unique registered recipes for the selected study.")
        if "cd19-softmax-followup" in data.required_analysis_ids:
            raise Conflict("The softmax fit requires its separate follow-up selection.")
        if data.mode == "live" and capabilities()["rosalind"]["status"] != "verified":
            raise Conflict("The selected research model must pass the model/tool capability probe before live investigation. Configure the server key, then run Check connection.")
        if sum(r["status"] in ("running", "queued") for r in store.list()) >= 10:
            raise HTTPException(429, "The queue is full. Wait for an investigation to finish.")
        releases = learning.applicable(data.case_id, data.mode)
        candidate = learning.candidate_for_evaluation(data.evaluation_lesson_id, data.case_id, data.mode) if data.evaluation_lesson_id else None
        return public_run(store.create(case, payload, releases, candidate))

    @app.get("/api/lessons")
    async def lessons():
        return learning.list()

    @app.post("/api/lessons", status_code=201)
    async def propose_lesson(data: LessonProposal):
        from .cases import CASE_IDS
        if not set(data.scope_case_ids + data.excluded_case_ids).issubset(CASE_IDS):
            raise HTTPException(422, "Lesson scope must use known case IDs.")
        return learning.propose(data.model_dump())

    @app.post("/api/lessons/{lesson_id}/review")
    async def review_lesson(lesson_id: str, data: LessonReview):
        return learning.review(lesson_id, data.model_dump())

    @app.post("/api/lessons/{lesson_id}/evaluation")
    async def evaluate_lesson(lesson_id: str, data: LessonEvaluation):
        return learning.evaluate(lesson_id, data.model_dump())

    @app.post("/api/lessons/{lesson_id}/release")
    async def release_lesson(lesson_id: str):
        return learning.release(lesson_id)

    @app.post("/api/memory-releases/{release_id}/suspend")
    async def suspend_release(release_id: str):
        return learning.suspend(release_id)

    @app.get("/api/runs")
    async def runs():
        return [public_run(r, False) for r in store.list()]

    @app.get("/api/runs/{run_id}")
    async def run(run_id: str):
        return public_run(store.get(run_id))

    @app.get("/api/runs/{run_id}/events")
    async def events(run_id: str, request: Request):
        store.get(run_id)
        try:
            cursor = int(request.headers.get("last-event-id", "0"))
        except ValueError:
            raise HTTPException(422, "Last-Event-ID must be an integer.")
        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                run = store.get(run_id)
                for event in run["events"]:
                    if event["id"] > cursor:
                        cursor = event["id"]
                        yield f"id: {cursor}\ndata: {json.dumps(event)}\n\n"
                if run["status"] not in ("running", "queued"):
                    return
                yield ": heartbeat\n\n"
                await asyncio.sleep(1)
        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.post("/api/runs/{run_id}/cancel")
    async def cancel(run_id: str):
        def update(run):
            if run["status"] not in ("running", "queued"):
                return
            run["cancel_requested"] = True
            if run["status"] == "queued":
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
            store.append_event(run, "Scientist", "Cancellation requested", "No new work will start; an already submitted vendor job may still finish.", "requested")
        return public_run(store.mutate(run_id, update))

    @app.get("/api/runs/{run_id}/synthesis-checkpoint")
    async def synthesis_checkpoint(run_id: str):
        from .synthesis_checkpoint import inspect_synthesis_checkpoint
        return inspect_synthesis_checkpoint(store, run_id)

    @app.post("/api/runs/{run_id}/sequence-discoveries", status_code=202)
    async def sequence_discovery(run_id: str, data: ResearchBriefRequest):
        from .sequence_operations import enqueue_sequence_discovery
        return public_run(enqueue_sequence_discovery(store, run_id, data.model_dump()))

    @app.post("/api/runs/{run_id}/research-briefs", status_code=202)
    async def research_brief(run_id: str, data: ResearchBriefRequest):
        from .brief_operations import enqueue_research_brief
        return public_run(enqueue_research_brief(store, run_id, data.model_dump()))

    @app.post("/api/runs/{run_id}/continue-synthesis")
    async def continue_synthesis(run_id: str, data: SynthesisContinuationRequest):
        from .synthesis_checkpoint import enqueue_synthesis_continuation
        return public_run(enqueue_synthesis_continuation(store, run_id, data.model_dump()))

    @app.post("/api/runs/{run_id}/resume")
    async def resume(run_id: str):
        def update(run):
            if run["status"] not in ("paused", "cancelled", "failed", "budget_exhausted", "blocked"):
                raise Conflict("Only stopped runs can be resumed.")
            if any(a["state"] in ("unknown", "submitting") for a in run["actions"]):
                raise Conflict("External outcome is unknown. Reconcile it before creating an explicitly new investigation; this action will not be submitted twice.")
            operation_id = run["operation"]["id"]
            if any(a["state"] == "failed" and a["id"].startswith(operation_id) for a in run["actions"]):
                raise Conflict("This provider attempt failed. Correct the configuration and start a new investigation with a new request key; failed attempts are not silently repeated.")
            run.update(status="queued", cancel_requested=False, error=None)
            store.append_event(run, "Harness", "Resume requested", "Same hypothesis, evidence snapshot and completed action receipts retained.", "queued")
        return public_run(store.mutate(run_id, update))

    @app.post("/api/runs/{run_id}/feedback", status_code=202)
    async def feedback(run_id: str, data: Feedback):
        return public_run(store.enqueue_revision(run_id, "feedback", data.model_dump()))

    @app.get("/api/runs/{run_id}/followups")
    async def followups(run_id: str):
        from .followups import available_followups
        return available_followups(store.get(run_id))

    @app.post("/api/runs/{run_id}/followups", status_code=202)
    async def request_followup(run_id: str, data: FollowupRequest):
        from .followups import enqueue_followup
        return public_run(enqueue_followup(store, run_id, data.model_dump()))

    @app.post("/api/runs/{run_id}/outcomes", status_code=202)
    async def outcomes(run_id: str, data: Outcome):
        return public_run(store.enqueue_revision(run_id, "outcome", data.model_dump()))

    @app.post("/api/runs/{run_id}/modeling", status_code=202)
    async def modeling(run_id: str, data: Modeling):
        from .providers import capabilities
        run = store.get(run_id)
        if run["mode"] != "live":
            raise Conflict("Real molecular jobs belong to live runs. Demo mode never makes hidden inference calls.")
        if capabilities()["bionemo"]["status"] not in ("configured", "verified"):
            raise Conflict("Configure NVIDIA_API_KEY or NGC_API_KEY on the server before submitting BioNeMo jobs.")
        if data.reference_binder == data.candidate_binder:
            raise HTTPException(422, "Reference and candidate sequences are identical; supply the intended distinct design.")
        payload = data.model_dump()
        with store.transaction() as db:
            existing = store.dedupe(db, run_id+":modeling", data.idempotency_key, payload)
            if existing:
                return public_run(existing)
            run = store.get(run_id, db)
            if run["status"] != "completed" or not run["decisions"] or run["decisions"][-1]["version"] != data.decision_version:
                raise Conflict("Modeling requires the current completed decision version.")
            run.update(status="queued", stage="modeling", error=None, cancel_requested=False,
                       operation={"kind": "modeling", "id": uuid.uuid4().hex, "input": payload})
            store.append_event(run, "Molecular specialist", "Matched comparison queued", "Exact supplied target and reference/candidate binders pinned. Target retention is scientist-attested; prediction is not therapy validation.", "queued")
            store.save(db, run)
            store.record_request(db, run_id+":modeling", data.idempotency_key, payload, run_id)
        return public_run(run)

    @app.get("/api/runs/{run_id}/export.json")
    async def export(run_id: str):
        run = store.get(run_id)
        packet = {"schema_version": 1, "application_version": __version__, "exported_at": now(), "run": public_run(run), "case_manifest": run["case_snapshot"]}
        packet["content_sha256"] = digest({"run": packet["run"], "case_manifest": packet["case_manifest"]})
        return JSONResponse(packet, headers={"Content-Disposition": f'attachment; filename="team-tbd-{run_id[:8]}.json"'})

    @app.get("/api/runs/{run_id}/report.md")
    async def markdown(run_id: str):
        return PlainTextResponse(report(store.get(run_id)), media_type="text/markdown", headers={"Content-Disposition": f'attachment; filename="team-tbd-{run_id[:8]}.md"'})

    def artifact_data(run_id: str, action_id: str, file_path: str):
        run = store.get(run_id)
        if action_id not in {a["id"] for a in run["actions"]}:
            raise HTTPException(404, "Artifact action does not belong to this run.")
        url = f"/api/runs/{run_id}/artifacts/{action_id}/{file_path}"
        published = [a for d in run["decisions"] for a in d.get("rd_handoff", {}).get("modeling", {}).get("artifacts", []) if isinstance(a, dict)]
        published.extend(a for operation in run.get("followup_operations", []) for a in operation.get("artifacts", []) if isinstance(a, dict))
        published.extend(a for operation in run.get("required_analysis_operations", []) for a in operation.get("artifacts", []) if isinstance(a, dict))
        record = next((a for a in published if a.get("url") == url), None)
        if record is None:
            raise HTTPException(404, "Artifact was not published in this run's handoff.")
        base = RUNTIME / "artifacts" / action_id
        path = base / file_path
        if (path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(base.resolve())
                or not path.is_file() or path.suffix not in (".cif", ".pdb", ".json", ".tsv", ".svg") or path.stat().st_size > 20_000_000):
            raise HTTPException(404, "Artifact not found.")
        data = path.read_bytes()
        if len(data) > 20_000_000 or hashlib.sha256(data).hexdigest() != record.get("sha256"):
            raise HTTPException(409, "Artifact no longer matches its published receipt.")
        return path, data, record

    @app.get("/api/runs/{run_id}/structure-preview/{action_id}/{file_path:path}")
    async def structure_preview(run_id: str, action_id: str, file_path: str):
        from .structure_preview import preview_from_cif
        path, data, record = artifact_data(run_id, action_id, file_path)
        if path.suffix != ".cif":
            raise HTTPException(404, "Only validated CIF structures have a preview.")
        try:
            return preview_from_cif(data, receipt=record, scope=record.get("scope", "qualified_molecular_prediction"), cif_url=record["url"])
        except (ValueError, TypeError):
            raise HTTPException(409, "Structure preview did not pass validation.")

    @app.get("/api/runs/{run_id}/artifacts/{action_id}/{file_path:path}")
    async def artifact(run_id: str, action_id: str, file_path: str):
        path, data, _ = artifact_data(run_id, action_id, file_path)
        return Response(data, media_type="chemical/x-mmcif" if path.suffix == ".cif" else "application/octet-stream",
                        headers={"Content-Disposition": 'attachment; filename="' + path.name.replace('"', '') + '"', "X-Content-Type-Options": "nosniff"})

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "static" / "index.html")

    (ROOT / "static").mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    return app


app = create_app()
