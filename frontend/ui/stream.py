"""Event sources: the live backend, and a fixture replay that needs no backend.

Both yield the same `Event` objects, so `app.py` has one rendering path. The
mock source exists for the same reason `RUN_MODE=mock` does on the backend: the
full visual with zero tokens, no GPU and no network.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterator

import httpx

from .events import Event

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
DEFAULT_BACKEND = "http://localhost:8000"


# -- live -----------------------------------------------------------------


def upload_files(base_url: str, files: list[tuple[str, bytes]], timeout: float = 60.0) -> list[str]:
    """POST /upload: returns file_ids for the uploaded patient files."""
    payload = [("files", (name, data)) for name, data in files]
    resp = httpx.post(f"{base_url.rstrip('/')}/upload", files=payload, timeout=timeout)
    resp.raise_for_status()
    body = resp.json()
    ids = body.get("file_ids", body if isinstance(body, list) else [])
    return [str(i) for i in ids]


def start_run(base_url: str, question: str, file_ids: list[str], timeout: float = 30.0) -> str:
    """POST /investigate: returns the run_id to stream."""
    resp = httpx.post(
        f"{base_url.rstrip('/')}/investigate",
        json={"question": question, "file_ids": file_ids},
        timeout=timeout,
    )
    resp.raise_for_status()
    return str(resp.json()["run_id"])


def fetch_report(base_url: str, run_id: str, timeout: float = 30.0) -> dict[str, Any]:
    """GET /report/{run_id}: the final structured report."""
    resp = httpx.get(f"{base_url.rstrip('/')}/report/{run_id}", timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def live_stream(base_url: str, run_id: str, connect_timeout: float = 10.0) -> Iterator[Event]:
    """GET /events/{run_id}: Server-Sent Events, parsed into `Event`s.

    Hand-rolled rather than pulling an SSE library: the wire format is three
    lines of parsing and one less dependency for another team to reproduce.
    """
    url = f"{base_url.rstrip('/')}/events/{run_id}"
    # No read timeout: the stream is idle between agent steps by design.
    timeout = httpx.Timeout(None, connect=connect_timeout)
    try:
        with httpx.stream("GET", url, timeout=timeout) as resp:
            resp.raise_for_status()
            data: list[str] = []
            for line in resp.iter_lines():
                if line == "":
                    if data:
                        yield Event.from_json("\n".join(data))
                        data = []
                    continue
                if line.startswith(":"):  # keep-alive comment
                    continue
                if line.startswith("data:"):
                    data.append(line[5:].lstrip())
            if data:
                yield Event.from_json("\n".join(data))
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
