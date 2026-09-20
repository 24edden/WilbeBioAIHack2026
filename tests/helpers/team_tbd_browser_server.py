"""Explicit OFFLINE browser fixture using the real API and durable store.

Start from the repository root with the scientific backend environment:
  python tests/helpers/team_tbd_browser_server.py --runtime /absolute/private/test-runtime

This fixture binds only to 127.0.0.1:8096. It blocks outgoing connections, has no
credentials, and uses no scientific worker. The deterministic completion pump is
test-only and labels every result as synthetic; zero model work is represented.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
from contextlib import asynccontextmanager
import os
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "scientific_backend"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--runtime", required=True, type=Path)
parser.add_argument("--delay", default=12, type=float)
arguments = parser.parse_args()
assert arguments.runtime.is_absolute() and not arguments.runtime.is_relative_to(BACKEND), "Use a dedicated absolute test runtime outside the backend source"
assert not (BACKEND / ".env").exists(), "Source release must not contain private configuration"
for key in ("OPENAI_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY", "BOLTZ2_NIM_URL", "OPENAI_BASE_URL"):
    os.environ.pop(key, None)
os.environ["ROSALIND_RUNTIME"] = str(arguments.runtime)
os.environ["ROSALIND_CAPABILITIES_FILE"] = str(arguments.runtime / "capabilities.json")
os.environ["ROSALIND_EMBEDDED_WORKER"] = "0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))


def no_network(*_args, **_kwargs):
    raise RuntimeError("Offline browser fixture forbids every outgoing connection and provider call")


socket.socket.connect = no_network

from app import analysis_tools, brief_operations, cases, data_catalog, followups, main, providers, scientific_skills, sequence_operations
from app.store import Store, digest, now
import uvicorn

CASE = {"id": "offline-ui-fixture", "title": "Offline integration test", "subtitle": "Synthetic browser fixture; no scientific inference",
        "hypothesis": "What can this offline software fixture demonstrate?", "hypothesis_source": "Explicit browser integration test",
        "description": "Synthetic records for checking software controls. No patient data or scientific results.", "evidence_count": 0,
        "readiness": "Offline fixture ready", "limitations": ["All results are synthetic test data."], "data_mode": "synthetic",
        "source_manifest": [{"path": "synthetic.tsv", "sha256": "a" * 64}], "evidence": []}
RECIPE = {"id": "offline-analysis", "kind": "data_analysis", "title": "Offline follow-up fixture", "input_sources": CASE["source_manifest"]}
cases.get_case = lambda case_id: copy.deepcopy(CASE) if case_id == CASE["id"] else (_ for _ in ()).throw(KeyError(case_id))
cases.list_cases = lambda: [copy.deepcopy(CASE)]
data_catalog.list_datasets = lambda: []
analysis_tools.analysis_catalog = lambda _: [copy.deepcopy(RECIPE)]
followups.approved_catalog = lambda _: [copy.deepcopy(RECIPE)]
providers.capabilities = lambda: {"rosalind": {"status": "verified", "model": "gpt-6-astra", "detail": "MOCK capability for offline UI tests; no provider calls."},
                                  "bionemo": {"status": "missing", "model": "mit/boltz2", "detail": "No NVIDIA service is used by this fixture."}}
providers.investigate = no_network
providers.probe = no_network
brief_operations.instruction_identity = lambda: {"offline-fixture": "a" * 64}
sequence_operations.instruction_identity = lambda: {"offline-fixture": "a" * 64}
scientific_skills.skill_catalog = lambda: [{"id": "offline-fixture", "name": "Synthetic browser fixture", "roles": ["reviewer"], "origin": "test_only"}]
scientific_skills.verify_life_sciences_runtime = lambda: None

store = Store(arguments.runtime / "browser.sqlite")
app = main.create_app(store=store, embedded=False)


def complete(run):
    if run.get("cancel_requested"):
        run.update(status="cancelled", stage="cancelled", active_agent=None)
        Store.append_event(run, "Offline fixture", "Test operation cancelled", "No provider work exists.", "cancelled")
        return
    version = len(run["decisions"]) + 1
    decision = {"version": version, "created_at": now(), "operation_id": run["operation"]["id"],
        "assessment": "not_evaluable", "summary": "Synthetic software integration result. No scientific inference was performed.",
        "insights": [], "followups": [], "claims": [], "alternatives": [], "limitations": ["Offline UI test data only."],
        "next_experiment": {"title": "Check interface behavior", "design": "Offline software checks", "positive": "Control works", "negative": "Software defect", "inconclusive": "Repeat the test"},
        "rd_handoff": {"objective": "Test frontend controls", "status": "proposed", "reference": "Synthetic fixture", "candidates": [{"id": "offline-arm", "name": "Synthetic test arm", "status": "planned"}],
                       "modeling": {"status": "blocked", "reason": "No molecular inference in this offline fixture.", "artifacts": []},
                       "experiment_id": "offline-experiment", "return_requirements": ["Synthetic software measurement only"]},
        "human_review_status": "unreviewed"}
    decision["sha256"] = digest(decision)
    run["decisions"].append(decision)
    run.update(status="completed", stage="completed", active_agent=None, error=None)
    Store.append_event(run, "Offline fixture", "Synthetic test complete", "A fixture decision is saved; zero scientific model or NVIDIA calls.", "completed")


async def pump():
    started = {}
    while True:
        store.lease("offline-browser-fixture", seconds=5)
        for record in store.list():
            operation = record["operation"]["id"]
            if record["status"] == "queued":
                started[operation] = time.monotonic()
                def running(run):
                    run.update(status="running", stage="offline_fixture", active_agent=None)
                    Store.append_event(run, "Offline fixture", "Synthetic operation started", "Testing the interface only; no scientific agents run.", "running")
                store.mutate(record["id"], running)
            elif record["status"] == "running" and (record.get("cancel_requested") or time.monotonic() - started.get(operation, 0) >= arguments.delay):
                store.mutate(record["id"], complete)
        await asyncio.sleep(0.25)


@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(pump())
    try:
        yield
    finally:
        task.cancel()
        store.release("offline-browser-fixture")
        try:
            await task
        except asyncio.CancelledError:
            pass


app.router.lifespan_context = lifespan
uvicorn.run(app, host="127.0.0.1", port=8096, access_log=False)
