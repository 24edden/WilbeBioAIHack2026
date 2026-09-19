"""User controls must affect dispatch and real provider request payloads."""

import json
from json import dumps

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


def finish(client, run_id):
    response = client.get(f"/events/{run_id}")
    response.raise_for_status()
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


@pytest.mark.parametrize("roles", [["clinical"], ["genomics", "literature"],
                                  ["genomics", "clinical", "literature"]])
@pytest.mark.parametrize("use_sample", [True, False])
def test_explicit_roster_is_dispatched_even_if_planner_omits_roles(roles, use_sample):
    with TestClient(app) as client:
        files = client.post("/demo/sample-patient").json()["files"] if use_sample else []
        response = client.post("/investigate", json={
            "question": "Why did treatment fail?", "file_ids": [f["file_id"] for f in files],
            "config": {"specialists": roles},
        })
        response.raise_for_status()
        run_id = response.json()["run_id"]
        events = finish(client, run_id)
        spawns = [e for e in events if e["type"] == "agent_spawned"]
        assert [e["agent_role"] for e in spawns] == ["orchestrator", *roles, "critic"]
        assert len({e["agent_id"] for e in spawns}) == len(spawns)
        assert events[0]["payload"]["config"]["specialists"] == roles
        report = client.get(f"/report/{run_id}").json()
        assert report["config"]["specialists"] == roles
        assert report["config"]["roster_source"] == "user"


@pytest.mark.parametrize("config", [
    {"specialists": []}, {"specialists": ["clinical", "clinical"]},
    {"specialists": ["stats"]}, {"specialists": ["critic"]},
    {"reasoning_model": " "}, {"variant_model": ""}, {"embedding_model": ""},
    {"unknown_control": 1}, {"reasoning_model": "some-model"},
])
def test_invalid_or_mock_model_controls_are_rejected(config):
    with TestClient(app) as client:
        response = client.post("/investigate", json={"question": "Investigate", "config": config})
        assert response.status_code == 422
        assert client.get("/runs").json() == []


def test_capabilities_only_expose_safe_configured_controls(monkeypatch):
    monkeypatch.setenv("REASONING_API_KEY", "do-not-expose")
    monkeypatch.setenv("BIONEMO_API_KEY", "also-secret")
    with TestClient(app) as client:
        body = client.get("/capabilities").json()
    assert body["model_overrides_supported"] is False
    assert body["required_roles"] == ["orchestrator", "critic"]
    assert {r["id"] for r in body["specialist_roles"]} == {"genomics", "clinical", "literature"}
    assert "do-not-expose" not in json.dumps(body) and "also-secret" not in json.dumps(body)
    assert not any("key" in key or "url" in key for key in body["defaults"])


def test_live_model_overrides_reach_requests_without_changing_other_runs(monkeypatch):
    monkeypatch.setenv("RUN_MODE", "live")
    monkeypatch.setenv("REASONING_API_KEY", "test-only")
    monkeypatch.setenv("REASONING_MODEL", "server-reasoning")
    monkeypatch.setenv("BIONEMO_VARIANT_MODEL", "server-variant")
    monkeypatch.setenv("BIONEMO_EMBED_MODEL", "server-embed")
    calls = []

    class ProviderHTTP:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json, headers):
            calls.append((url, json["model"]))
            if url.endswith("/chat/completions"):
                system = json["messages"][0]["content"]
                if "orchestrator" in system:
                    data = {"tasks": [{"role": "clinical", "task": "Review the uploads"}]}
                elif "critic agent" in system:
                    data = {"answer": "Insufficient evidence", "rationale": "No claims", "confidence": 0.1}
                else:
                    data = {"message": "No claims", "claims": []}
                body = {"choices": [{"message": {"content": dumps(data)}}]}
            elif url.endswith("/variant-effect"):
                body = {"score": 0.5, "id": "test-output"}
            else:
                body = {"data": [{"embedding": [1.0, 0.0]} for _ in json["input"]]}
            return httpx.Response(200, json=body)

    monkeypatch.setattr(httpx, "AsyncClient", ProviderHTTP)
    with TestClient(app) as client:
        assert client.get("/capabilities").json()["model_overrides_supported"] is True
        file_ids = [f["file_id"] for f in client.post("/demo/sample-patient").json()["files"]]
        config = {"specialists": ["genomics", "clinical", "literature"],
                  "reasoning_model": "chosen-reasoning", "variant_model": "chosen-variant",
                  "embedding_model": "chosen-embed"}
        response = client.post("/investigate", json={"question": "Investigate", "file_ids": file_ids, "config": config})
        response.raise_for_status()
        run_id = response.json()["run_id"]
        events = finish(client, run_id)
        assert not [e for e in events if e["type"] == "error"]
        assert {model for _, model in calls} == {"chosen-reasoning", "chosen-variant", "chosen-embed"}
        assert client.get(f"/report/{run_id}").json()["config"]["reasoning_model"] == "chosen-reasoning"
        calls.clear()
        second = client.post("/investigate", json={"question": "Investigate", "file_ids": file_ids}).json()["run_id"]
        finish(client, second)
        assert {model for _, model in calls} == {"server-reasoning"}
        assert client.get("/capabilities").json()["defaults"]["reasoning_model"] == "server-reasoning"
