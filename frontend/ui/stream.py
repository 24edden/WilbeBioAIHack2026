"""Event sources: the live backend, and a fixture replay that needs no backend.

Both yield the same `Event` objects, so `app.py` has one rendering path. The
mock source exists for the same reason `RUN_MODE=mock` does on the backend: the
full visual with zero tokens, no GPU and no network.
"""

from __future__ import annotations

import json
import time
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import quote

import httpx

from .events import Event

FIXTURE_DIR = Path(os.environ.get("TRACE_FIXTURE_DIR", str(Path(__file__).resolve().parent.parent / "fixtures")))
DEFAULT_BACKEND = os.environ.get("TRACE_BACKEND_URL", "http://localhost:8000")


# -- live -----------------------------------------------------------------


def _file_ids(body: Any) -> list[str]:
    """Pull file ids out of an UploadResponse.

    The backend returns `{"files": [{"file_id": ..., "filename": ...}, ...]}`.
    The other shapes are tolerated so a backend tweak degrades instead of
    silently investigating zero files.
    """
    if isinstance(body, dict):
        entries = body.get("files")
        if isinstance(entries, list):
            ids = [
                e.get("file_id") if isinstance(e, dict) else e
                for e in entries
            ]
            return [str(i) for i in ids if i]
        if isinstance(body.get("file_ids"), list):
            return [str(i) for i in body["file_ids"]]
    if isinstance(body, list):
        return [str(i) for i in body]
    return []


@dataclass(frozen=True)
class BackendContract:
    """Change paths and wire mappings here; keep normalized Event/RunState stable."""
    upload_path: str = "/upload"
    sample_path: str = "/demo/sample-patient"
    start_path: str = "/investigate"
    events_path: str = "/events/{run_id}"
    report_path: str = "/report/{run_id}"
    capabilities_path: str = "/capabilities"
    cancel_path: str = "/runs/{run_id}/cancel"
    upload_field: str = "files"
    start_payload: Callable[[str, list[str], dict[str, Any]], Any] = lambda question, ids, config: {
        "question": question, "file_ids": ids, **({"config": config} if config else {})}
    parse_file_ids: Callable[[Any], list[str]] = _file_ids
    parse_run_id: Callable[[Any], str] = lambda body: str(body["run_id"])
    map_event: Callable[[Any], Event] = Event.from_dict
    map_capabilities: Callable[[Any], dict[str, Any]] = lambda body: body


DEFAULT_CONTRACT = BackendContract()


def _mapped_event(blob: str, contract: BackendContract) -> Event:
    try:
        event = contract.map_event(json.loads(blob))
        if not isinstance(event, Event):
            raise TypeError("map_event must return Event")
        return event
    except Exception as exc:
        return Event(type="error", payload={"message": f"Could not map backend event: {exc}"})


def upload_files(base_url: str, files: list[tuple[str, bytes]], timeout: float = 60.0, *, contract: BackendContract = DEFAULT_CONTRACT) -> list[str]:
    """POST /upload: returns file ids for the uploaded patient files."""
    payload = [(contract.upload_field, (name, data)) for name, data in files]
    resp = httpx.post(f"{base_url.rstrip('/')}{contract.upload_path}", files=payload, timeout=timeout)
    resp.raise_for_status()
    return contract.parse_file_ids(resp.json())


def load_sample_patient(base_url: str, timeout: float = 60.0, *, contract: BackendContract = DEFAULT_CONTRACT) -> list[str]:
    """POST /demo/sample-patient: loads the bundled patient server side.

    This is the stage path. No file picker, no dragging a VCF around live.
    """
    resp = httpx.post(f"{base_url.rstrip('/')}{contract.sample_path}", timeout=timeout)
    resp.raise_for_status()
    return contract.parse_file_ids(resp.json())


def start_run(base_url: str, question: str, file_ids: list[str], timeout: float = 30.0, *, contract: BackendContract = DEFAULT_CONTRACT, config: dict[str, Any] | None = None) -> str:
    """POST /investigate: returns the run_id to stream."""
    resp = httpx.post(
        f"{base_url.rstrip('/')}{contract.start_path}",
        json=contract.start_payload(question, file_ids, config or {}),
        timeout=timeout,
    )
    resp.raise_for_status()
    return contract.parse_run_id(resp.json())


def fetch_capabilities(base_url: str, *, contract: BackendContract = DEFAULT_CONTRACT) -> dict[str, Any]:
    resp = httpx.get(base_url.rstrip('/') + contract.capabilities_path, timeout=5.0)
    resp.raise_for_status()
    body = contract.map_capabilities(resp.json())
    if not isinstance(body, dict):
        raise ValueError("Capabilities mapping must return an object")
    return body


def cancel_run(base_url: str, run_id: str, *, contract: BackendContract = DEFAULT_CONTRACT) -> dict[str, Any]:
    resp = httpx.post(base_url.rstrip('/') + contract.cancel_path.format(run_id=quote(run_id, safe="")), timeout=15.0)
    resp.raise_for_status()
    return resp.json()


def fetch_report(base_url: str, run_id: str, timeout: float = 30.0, *, contract: BackendContract = DEFAULT_CONTRACT) -> dict[str, Any]:
    """GET /report/{run_id}: the final structured report."""
    resp = httpx.get(base_url.rstrip('/') + contract.report_path.format(run_id=quote(run_id, safe="")), timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def live_stream(base_url: str, run_id: str, connect_timeout: float = 10.0, *, contract: BackendContract = DEFAULT_CONTRACT, should_stop: Callable[[], bool] | None = None) -> Iterator[Event]:
    """GET /events/{run_id}: Server-Sent Events, parsed into `Event`s.

    Hand-rolled rather than pulling an SSE library: the wire format is three
    lines of parsing and one less dependency for another team to reproduce.
    """
    url = base_url.rstrip('/') + contract.events_path.format(run_id=quote(run_id, safe=""))
    # No read timeout: the stream is idle between agent steps by design.
    timeout = httpx.Timeout(120.0, connect=connect_timeout)
    try:
        with httpx.stream("GET", url, timeout=timeout) as resp:
            resp.raise_for_status()
            data: list[str] = []
            for line in resp.iter_lines():
                if should_stop and should_stop():
                    return
                if line == "":
                    if data:
                        yield _mapped_event("\n".join(data), contract)
                        data = []
                    continue
                if line.startswith(":"):  # keep-alive comment
                    continue
                if line.startswith("data:"):
                    data.append(line[5:].lstrip())
            if data:
                yield _mapped_event("\n".join(data), contract)
    except httpx.HTTPError as exc:
        yield Event(
            type="error",
            run_id=run_id,
            payload={"message": f"stream failed ({type(exc).__name__}): {exc}"},
        )


# -- mock -----------------------------------------------------------------


def list_fixtures() -> list[Path]:
    return sorted(FIXTURE_DIR.glob("*.json"))


def load_fixture(path: str | Path) -> list[Event]:
    blob = json.loads(Path(path).read_text(encoding="utf-8"))
    raws = blob.get("events", blob) if isinstance(blob, dict) else blob
    return [Event.from_dict(r) for r in raws]


def mock_stream(
    path: str | Path,
    speed: float = 1.0,
    max_gap_s: float = 1.2,
) -> Iterator[Event]:
    """Replay a fixture, sleeping the real inter-event gaps so it animates.

    `speed` scales playback; `max_gap_s` caps any single pause so a fixture with
    a long think-time never stalls a live demo.
    """
    events = load_fixture(path)
    speed = max(speed, 0.05)
    previous: int | None = None
    for ev in events:
        if previous is not None:
            gap = max(0.0, (ev.ts - previous) / 1000.0) / speed
            time.sleep(min(gap, max_gap_s))
        previous = ev.ts
        yield ev
