"""FastAPI transport.

Four endpoints carry the product (`/upload`, `/investigate`, `/events`,
`/report`); the rest are conveniences for the demo. The engine is started as a
background task and the browser follows along over SSE, which is why
`/investigate` returns a `run_id` immediately rather than blocking for the
length of the investigation.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.engine import run_investigation
from app.events import Event
from app.ingest import build_bundle, sniff_kind
from app.models import (
    InvestigateRequest,
    InvestigateResponse,
    Report,
    UploadedFileInfo,
    UploadResponse,
)
from app.providers import build_providers
from app.store import files as file_store
from app.store import runs as run_store

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
HEARTBEAT_SECONDS = 15.0

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    # Stop any investigation still running so the process can exit promptly.
    for run in run_store.all():
        if run.task and not run.task.done():
            run.task.cancel()


app = FastAPI(
    lifespan=lifespan,
    title="Patient failure-investigation agents",
    version="0.1.0",
    description="Upload a patient bundle, ask why treatment failed, watch the agents work.",
)

# The Streamlit UI runs on a different port, and a judge may open it from a
# laptop on the same network. Wide-open CORS is the right call for a weekend
# demo and the wrong call for anything that outlives it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str | int]:
    settings = get_settings()
    return {
        "status": "ok",
        "run_mode": settings.run_mode,
        "runs": len(run_store.all()),
        "files": len(file_store.all()),
    }


@app.post("/upload", response_model=UploadResponse)
async def upload(files: list[UploadFile]) -> UploadResponse:
    """Accept patient files and keep the raw text; parsing happens per run so a
    fix to a parser does not require re-uploading."""
    if not files:
        raise HTTPException(status_code=400, detail="no files in the request")
    infos: list[UploadedFileInfo] = []
    for upload_file in files:
        raw = await upload_file.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")
        name = upload_file.filename or "upload.txt"
        kind = sniff_kind(name, text)
        bundle = build_bundle([("preview", name, text)])
        n_records = bundle.files[0].n_records if bundle.files else 0
        stored = file_store.add(name, text, kind, n_records)
        infos.append(
            UploadedFileInfo(
                file_id=stored.file_id, filename=name, kind=kind, n_records=n_records
            )
        )
    return UploadResponse(files=infos)


@app.post("/demo/sample-patient", response_model=UploadResponse)
async def load_sample_patient() -> UploadResponse:
    """Load the bundled sample patient. One click to a full demo, and the
    fallback if a file picker misbehaves on stage."""
    paths = sorted(SAMPLES_DIR.glob("patient-0*"))
    if not paths:
        raise HTTPException(status_code=500, detail=f"no samples found in {SAMPLES_DIR}")
    infos: list[UploadedFileInfo] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        kind = sniff_kind(path.name, text)
        bundle = build_bundle([("preview", path.name, text)])
        n_records = bundle.files[0].n_records if bundle.files else 0
        stored = file_store.add(path.name, text, kind, n_records)
        infos.append(
            UploadedFileInfo(
                file_id=stored.file_id, filename=path.name, kind=kind, n_records=n_records
            )
        )
    return UploadResponse(files=infos)


@app.post("/investigate", response_model=InvestigateResponse)
async def investigate(request: InvestigateRequest) -> InvestigateResponse:
    """Start a run and return its id. The work continues in the background."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is empty")

    missing = [f for f in request.file_ids if file_store.get(f) is None]
    if missing:
        raise HTTPException(status_code=404, detail=f"unknown file_id(s): {missing}")

    stored = file_store.many(request.file_ids)
    bundle = build_bundle([(s.file_id, s.filename, s.text) for s in stored])

    settings = get_settings()
    run = run_store.create(question, bundle, settings.run_mode)
    run.task = asyncio.create_task(
        run_investigation(
            run_id=run.run_id,
            question=question,
            bundle=bundle,
            bus=run.bus,
            providers=build_providers(settings),
            report=run.report,
        )
    )
    return InvestigateResponse(run_id=run.run_id)


def _sse(event: Event) -> str:
    """One SSE frame.

    Only a `data:` line, no `event:` name: that keeps the default `message`
    event firing, so a browser `EventSource.onmessage`, a Streamlit loop and a
    plain `curl` all read the same stream. The event type travels inside the
    JSON, per the shared schema.
    """
    return f"data: {json.dumps(event.model_dump(), separators=(',', ':'))}\n\n"


@app.get("/events/{run_id}")
async def events(run_id: str) -> StreamingResponse:
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")

    async def stream():
        # Replay is handled by the bus, so a client that connects late — which
        # is every client, since /investigate returns first — still sees the
        # whole run from the beginning.
        queue: asyncio.Queue[str] = asyncio.Queue()

        async def pump() -> None:
            async for event in run.bus.subscribe():
                await queue.put(_sse(event))
            await queue.put("")

        pump_task = asyncio.create_task(pump())
        try:
            while True:
                try:
                    frame = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"   # keeps proxies from closing an idle stream
                    continue
                if frame == "":
                    return
                yield frame
        finally:
            pump_task.cancel()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/report/{run_id}", response_model=Report)
async def report(run_id: str) -> Report:
    """The structured report. Available while the run is still going, with
    `status: running` — the UI can poll it or just wait for `run_complete`."""
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    return run.report


@app.get("/events/{run_id}/log")
async def event_log(run_id: str) -> list[Event]:
    """The whole event history as one JSON array — for tests, for the recorded
    demo, and for anyone debugging without an SSE client."""
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    return run.bus.history


@app.get("/runs")
async def list_runs() -> list[dict[str, object]]:
    return [
        {
            "run_id": run.run_id,
            "question": run.question,
            "status": run.report.status,
            "n_events": len(run.bus.history),
            "abstained": run.report.verdict.abstained if run.report.verdict else None,
        }
        for run in run_store.all()
    ]
