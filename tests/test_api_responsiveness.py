"""One session preparing evidence must not block another session's API calls."""

import asyncio
from threading import Event

import httpx
import pytest

import app.main as api
from app.store import files, runs


@pytest.mark.parametrize("endpoint", ["upload", "sample", "investigate"])
async def test_health_responds_while_evidence_is_still_parsing(monkeypatch, endpoint):
    entered, release, finished = Event(), Event(), Event()
    real_build_bundle = api.build_bundle

    def held_parser(*args, **kwargs):
        entered.set()
        # Bounded fallback lets a regressed synchronous handler fail rather
        # than deadlocking the test process.
        release.wait(3)
        try:
            return real_build_bundle(*args, **kwargs)
        finally:
            finished.set()

    monkeypatch.setattr(api, "build_bundle", held_parser)
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        if endpoint == "upload":
            request = client.post("/upload", files=[("files", ("notes.txt", b"Progression on treatment."))])
        elif endpoint == "sample":
            request = client.post("/demo/sample-patient")
        else:
            evidence = files.add("notes.txt", "Progression on treatment.", "notes", 1)
            request = client.post("/investigate", json={"question": "Why did treatment fail?", "file_ids": [evidence.file_id]})
        preparing = asyncio.create_task(request)
        try:
            assert await asyncio.wait_for(asyncio.to_thread(entered.wait, 1), 2)
            health = await asyncio.wait_for(client.get("/health"), 1)
            assert health.status_code == 200
            assert health.json()["status"] == "ok"
            assert not finished.is_set(), "Health had to wait for another session's evidence parser"
        finally:
            release.set()
            response = await preparing
            for run in runs.all():
                if run.task:
                    run.task.cancel()
            await asyncio.gather(*(run.task for run in runs.all() if run.task), return_exceptions=True)
        assert response.status_code == 200
        if endpoint in {"upload", "sample"}:
            assert all(item["n_records"] > 0 for item in response.json()["files"])
