"""Rosalind uses Responses without weakening grounding or hiding failures."""

import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import ROSALIND_MODEL, get_settings
from app.main import app
from app.providers import build_providers
from app.providers.errors import ProviderError
from app.providers.live import LiveReasoningProvider
from app.providers.reasoning_http import ReasoningHTTP


def completed(data):
    return {
        "status": "completed",
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "role": "assistant", "status": "completed",
             "content": [{"type": "output_text", "text": json.dumps(data)}]},
        ],
    }


@pytest.fixture
def rosalind_settings(monkeypatch):
    monkeypatch.setenv("RUN_MODE", "live")
    monkeypatch.setenv("REASONING_API_KEY", "test-secret")
    monkeypatch.setenv("REASONING_MODEL", ROSALIND_MODEL)
    monkeypatch.setenv("REASONING_API", "auto")
    return get_settings()


def intercept(monkeypatch, handler):
    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport, **kwargs))


@pytest.mark.asyncio
async def test_rosalind_plan_uses_responses_without_assuming_optional_parameters(monkeypatch, rosalind_settings, sample_bundle):
    calls = []

    def reply(request):
        calls.append(request)
        return httpx.Response(200, json=completed({"tasks": [{"role": "clinical", "task": "Read labs"}]}))

    intercept(monkeypatch, reply)
    provider = build_providers(rosalind_settings).reasoning
    plan = await provider.plan("Why?", sample_bundle)
    assert plan.tasks[0].role == "clinical"
    assert len(calls) == 1
    request = calls[0]
    payload = json.loads(request.content)
    assert str(request.url) == "https://api.openai.com/v1/responses"
    assert request.headers["authorization"] == "Bearer test-secret"
    assert payload["model"] == ROSALIND_MODEL
    assert payload["store"] is False
    assert payload["max_output_tokens"] == 16000
    assert json.loads(payload["input"][0]["content"])["question"] == "Why?"
    assert "orchestrator" in payload["instructions"]
    assert not {"temperature", "reasoning", "response_format", "text", "tools"} & payload.keys()


def test_transport_selection_follows_effective_model_without_mutating_defaults(rosalind_settings):
    assert rosalind_settings.effective_reasoning_api == "responses"
    assert replace(rosalind_settings, reasoning_model="gpt-4o-mini").effective_reasoning_api == "chat_completions"
    assert replace(rosalind_settings, reasoning_api="chat_completions").effective_reasoning_api == "chat_completions"
    assert replace(rosalind_settings, reasoning_model=ROSALIND_MODEL + "-2026-09-08").effective_reasoning_api == "responses"


@pytest.mark.asyncio
async def test_chat_compatibility_uses_same_budget_and_records_measured_usage(monkeypatch, rosalind_settings):
    usage = {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}

    def reply(request):
        assert request.url.path == "/v1/chat/completions"
        assert json.loads(request.content)["max_completion_tokens"] == 16000
        return httpx.Response(200, json={
            "id": "chat-check", "model": "gpt-4o-mini", "usage": usage,
            "choices": [{"finish_reason": "stop", "message": {"content": '{"ok": true}'}}],
        })

    intercept(monkeypatch, reply)
    provider = LiveReasoningProvider(replace(rosalind_settings, reasoning_model="gpt-4o-mini"))
    assert await provider._chat("JSON", "probe") == {"ok": True}
    assert provider.usage == [{"model": "gpt-4o-mini", "api": "chat_completions", "response_id": "chat-check", "usage": usage}]


@pytest.mark.parametrize("usage", [None, {"input_tokens": 20, "output_tokens": 30, "total_tokens": 50}])
@pytest.mark.asyncio
async def test_usage_is_retained_for_incomplete_responses_and_not_estimated(monkeypatch, rosalind_settings, usage):
    body = {"status": "incomplete", "id": "resp-check", "model": ROSALIND_MODEL, "usage": usage}
    intercept(monkeypatch, lambda _: httpx.Response(200, json=body))
    provider = LiveReasoningProvider(rosalind_settings)
    with pytest.raises(ProviderError, match="incomplete"):
        await provider._chat("JSON", "probe")
    assert provider.usage[0]["usage"] == usage
    assert provider.usage[0]["response_id"] == "resp-check"


@pytest.mark.parametrize("body,match", [
    ({"status": "incomplete", "output": completed({"ok": True})["output"]}, "incomplete"),
    ({"status": "failed", "error": {"message": "sensitive"}}, "did not complete"),
    ({"status": "completed", "output": []}, "no assistant text"),
    ({"status": "completed", "output": [{"type": "message", "role": "assistant", "content": [{"type": "refusal", "refusal": "sensitive"}]}]}, "declined"),
    ({"status": "completed", "output": [{"type": "reasoning", "text": '{"ok": true}'}]}, "no assistant text"),
    ([], "unexpected response shape"),
])
@pytest.mark.asyncio
async def test_incomplete_refused_or_malformed_responses_do_not_become_findings(monkeypatch, rosalind_settings, body, match):
    intercept(monkeypatch, lambda _: httpx.Response(200, json=body))
    with pytest.raises(ProviderError, match=match):
        await LiveReasoningProvider(rosalind_settings)._chat("JSON", "probe")


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
@pytest.mark.asyncio
async def test_http_failures_are_actionable_and_do_not_echo_secrets_or_fallback(monkeypatch, rosalind_settings, status):
    calls = []

    def fail(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": "test-secret; private patient record"}})

    intercept(monkeypatch, fail)
    with pytest.raises(ProviderError, match=f"HTTP {status}") as error:
        await LiveReasoningProvider(rosalind_settings)._chat("JSON", "probe")
    assert "test-secret" not in str(error.value)
    assert "private patient" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_timeout_does_not_leak_request_or_fallback(monkeypatch, rosalind_settings):
    def fail(request):
        raise httpx.ReadTimeout("private patient data", request=request)

    intercept(monkeypatch, fail)
    with pytest.raises(ProviderError, match="timed out") as error:
        await ReasoningHTTP(rosalind_settings).complete("JSON", "probe")
    assert "private patient data" not in str(error.value)


@pytest.mark.asyncio
async def test_access_lookup_is_read_only(monkeypatch, rosalind_settings):
    calls = []

    def reply(request):
        calls.append(request)
        return httpx.Response(200, json={"id": ROSALIND_MODEL})

    intercept(monkeypatch, reply)
    await ReasoningHTTP(rosalind_settings).check_access()
    assert len(calls) == 1
    assert calls[0].method == "GET"
    assert calls[0].url.path == f"/v1/models/{ROSALIND_MODEL}"
    assert calls[0].content == b""


def test_rosalind_override_flows_through_run_and_capabilities(monkeypatch, rosalind_settings):
    # The server starts with another default. An existing frontend model field
    # selects Rosalind for this run, including the correct transport.
    monkeypatch.setenv("REASONING_MODEL", "gpt-4o-mini")
    calls = []

    def reply(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert request.url.path == "/v1/responses"
        assert payload["model"] == ROSALIND_MODEL
        system = payload["instructions"]
        if "orchestrator" in system:
            data = {"tasks": [{"role": "clinical", "task": "Review uploaded labs"}]}
        elif "critic agent" in system:
            data = {"answer": "No grounded conclusion", "rationale": "No claims", "confidence": 0.1}
        else:
            data = {"message": "Evidence is insufficient", "claims": []}
        return httpx.Response(200, json=completed(data))

    intercept(monkeypatch, reply)
    with TestClient(app) as client:
        capabilities = client.get("/capabilities").json()
        assert capabilities["reasoning_api"] == "chat_completions"
        file_ids = [item["file_id"] for item in client.post("/demo/sample-patient").json()["files"]]
        response = client.post("/investigate", json={
            "question": "What evidence is missing?",
            "file_ids": file_ids,
            "config": {"specialists": ["clinical"], "reasoning_model": ROSALIND_MODEL},
        })
        response.raise_for_status()
        run_id = response.json()["run_id"]
        frames = client.get(f"/events/{run_id}").text
        events = [json.loads(line[6:]) for line in frames.splitlines() if line.startswith("data: ")]
        assert not [event for event in events if event["type"] == "error"]
        report = client.get(f"/report/{run_id}").json()
        assert report["config"]["reasoning_model"] == ROSALIND_MODEL
        assert report["config"]["reasoning_api"] == "responses"
        assert report["verdict"]["abstained"] is True
        assert events[0]["payload"]["config"]["reasoning_api"] == "responses"
        assert client.get("/capabilities").json()["defaults"]["reasoning_model"] == "gpt-4o-mini"
        assert "test-secret" not in frames
    assert len(calls) >= 2


@pytest.mark.parametrize("key,value", [
    ("REASONING_API", "invented"),
    ("REASONING_TIMEOUT_SECONDS", "nan"),
    ("REASONING_TIMEOUT_SECONDS", "0"),
    ("REASONING_MAX_OUTPUT_TOKENS", "-1"),
])
def test_invalid_transport_settings_fail_early(monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        get_settings()
