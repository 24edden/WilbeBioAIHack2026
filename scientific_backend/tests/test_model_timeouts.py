"""Timeout contracts over the real Agents/OpenAI SDK with mocked HTTP only.

No test waits for a real timeout duration or submits work to a provider.
"""
import asyncio
import json

import httpx
import pytest

from app import providers as p
from test_providers import fake_clients, message, response, team_transport


@pytest.fixture(autouse=True)
def timeout_environment(monkeypatch, tmp_path):
    for key in (
        "OPENAI_BASE_URL", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID", "ROSALIND_MODEL",
        "TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "TEAM_TBD_AGENT_TIMEOUT_SECONDS",
        "TEAM_TBD_BUDGET_MODE", "TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS", "TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS",
        "TEAM_TBD_MAX_MODEL_REQUESTS", "TEAM_TBD_MAX_TOOL_CALLS",
        "TEAM_TBD_MAX_INPUT_TOKENS", "TEAM_TBD_MAX_OUTPUT_TOKENS",
        "NGC_API_KEY", "NVIDIA_API_KEY", "BOLTZ2_NIM_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-timeout-key-never-send")
    monkeypatch.setenv("TEAM_TBD_MODEL", "gpt-6-astra")
    monkeypatch.setenv("ROSALIND_CAPABILITIES_FILE", str(tmp_path / "capabilities.json"))


def test_timeout_defaults_are_visible_and_independent_of_advisory_budgets():
    limits = p.effective_model_limits()
    assert limits["model_request_timeout_seconds"] == 600
    assert limits["agent_timeout_seconds"] == 1800
    assert limits["budget_mode"] == "advisory"


@pytest.mark.parametrize("name,value", [
    ("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "59"),
    ("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "1801"),
    ("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "120.5"),
    ("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", ""),
    ("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "infinite"),
    ("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "119"),
    ("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "7201"),
    ("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "1800.0"),
    ("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "-1"),
    ("TEAM_TBD_AGENT_TIMEOUT_SECONDS", ""),
])
def test_invalid_timeout_setting_fails_before_constructing_transport(monkeypatch, name, value):
    opened = []
    def transport_must_not_open(*args, **kwargs):
        opened.append(True)
        raise AssertionError("Invalid settings must fail before constructing a network client.")
    monkeypatch.setattr(p.httpx, "AsyncClient", transport_must_not_open)
    monkeypatch.setenv(name, value)
    with pytest.raises(p.ProviderError, match=name):
        p.ModelSession()
    assert opened == []


@pytest.mark.parametrize("request_timeout,agent_timeout", [(600, 600), (600, 629), (1800, 1800)])
def test_agent_wait_must_leave_request_completion_margin(monkeypatch, request_timeout, agent_timeout):
    monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", str(request_timeout))
    monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", str(agent_timeout))
    with pytest.raises(p.ProviderError, match="at least 30 seconds"):
        p.ModelSession()


@pytest.mark.parametrize("request_timeout,agent_timeout", [(60, 120), (600, 630), (1800, 7200)])
def test_valid_timeout_boundaries_are_accepted(monkeypatch, request_timeout, agent_timeout):
    monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", str(request_timeout))
    monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", str(agent_timeout))
    limits = p.effective_model_limits()
    assert limits["model_request_timeout_seconds"] == request_timeout
    assert limits["agent_timeout_seconds"] == agent_timeout


def test_session_snapshot_reaches_actual_sdk_http_timeout_extensions_without_retry(monkeypatch):
    from agents import Agent, RunConfig, Runner
    monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "180")
    monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "600")
    session = p.ModelSession()
    # An operator change after construction cannot alter this operation's timeouts.
    monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "300")
    monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "1500")
    requests = []
    def handler(request):
        requests.append(request)
        return response([message({"evidence_id": "e1", "tool_observation": "observed:e1"})])
    fake_clients(monkeypatch, handler)
    async def run():
        try:
            agent = Agent(name="Timeout transport probe", model=session.model(), output_type=p.ProbeOutput,
                          model_settings=p._model_settings(session.model_id, 2048))
            assert session.clients[0].max_retries == 0
            return await Runner.run(agent, "Return the supplied source identity.",
                                    run_config=RunConfig(tracing_disabled=True))
        finally:
            await session.close()
    result = asyncio.run(run())
    assert result.final_output.evidence_id == "e1"
    assert len(requests) == 1
    assert requests[0].extensions["timeout"] == {"connect": 15, "read": 180, "write": 180, "pool": 180}
    assert session.metadata()["budgets"]["model_request_timeout_seconds"] == 180
    assert session.metadata()["budgets"]["agent_timeout_seconds"] == 600
    assert p.effective_model_limits()["model_request_timeout_seconds"] == 300


def test_all_role_bounds_use_the_session_snapshot_and_molecular_floor(monkeypatch):
    monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "180")
    monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "600")
    calls, events, persisted, products, emit, accept, handoff = team_transport(monkeypatch)
    bounds = []
    original_parse = p._parse_or_repair
    parse_waits = []
    async def capture_bound(coro, cancelled, timeout):
        bounds.append(timeout)
        monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "300")
        monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "1500")
        return await coro
    async def capture_parse(*args, **kwargs):
        parse_waits.append(kwargs["timeout_seconds"])
        return await original_parse(*args, **kwargs)
    monkeypatch.setattr(p, "_bounded", capture_bound)
    monkeypatch.setattr(p, "_parse_or_repair", capture_parse)
    result = asyncio.run(p.investigate({"id": "case-1", "exposure_data": {"available": True}},
        "Exact hypothesis.", [{"id": "e1"}], emit, lambda: False,
        accept_evidence=accept, accept_handoff=handoff))
    role_order = [product["sender"] for product in products]
    assert len(role_order) == 9 and len(bounds) == 9
    assert dict(zip(role_order, bounds)) == {
        role: 900 if role == "molecular_scientist" else 600 for role in role_order}
    assert parse_waits == [210] * 9
    assert result["metadata"]["budgets"]["agent_timeout_seconds"] == 600
    assert result["metadata"]["budgets"]["model_request_timeout_seconds"] == 180


def test_discovery_finalization_wait_uses_request_timeout_plus_margin(monkeypatch):
    monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "180")
    monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "600")
    calls, events, persisted, products, emit, accept, handoff = team_transport(
        monkeypatch, discovery=True, extra_bio=-7)
    bounds = []
    async def capture_bound(coro, cancelled, timeout):
        bounds.append(timeout)
        return await coro
    monkeypatch.setattr(p, "_bounded", capture_bound)
    result = asyncio.run(p.investigate({"id": "cart-discovery"}, "Exact source-defined question.",
        [{"id": "e1"}], emit, lambda: False, accept_evidence=accept, accept_handoff=handoff))
    assert result["metadata"]["reviewer_completed"] is True
    assert bounds[:2] == [600, 210]
    assert bounds.count(210) == 1
    finalization = [call for call in calls if "ROLE: bioinformatician." in call["instructions"] and not call.get("tools")]
    assert len(finalization) == 1
    assert len([event for event in events if event[0][1] == "Exploration closed for handoff"]) == 1


def test_json_format_repair_uses_supplied_wait_with_real_sdk_and_mock_transport(monkeypatch):
    monkeypatch.setenv("TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS", "180")
    monkeypatch.setenv("TEAM_TBD_AGENT_TIMEOUT_SECONDS", "600")
    calls, bounds = [], []
    def handler(request):
        calls.append(request)
        return response([message({"evidence_id": "e1", "tool_observation": "observed:e1"})])
    async def capture_bound(coro, cancelled, timeout):
        bounds.append(timeout)
        return await coro
    fake_clients(monkeypatch, handler)
    monkeypatch.setattr(p, "_bounded", capture_bound)
    async def run():
        session = p.ModelSession()
        try:
            return await p._parse_or_repair("malformed-json", p.ProbeOutput, typed=False,
                model=session.model(), timeout_seconds=session.request_timeout + 30)
        finally:
            await session.close()
    result = asyncio.run(run())
    assert result.evidence_id == "e1"
    assert bounds == [210]
    assert len(calls) == 1


@pytest.mark.parametrize("timeout_type", [httpx.ReadTimeout, httpx.ConnectTimeout, httpx.PoolTimeout])
def test_sdk_request_timeout_is_unknown_safe_and_never_retried(monkeypatch, timeout_type):
    from app import followups
    monkeypatch.setattr(followups, "approved_catalog", lambda case_id: [])
    calls, events = [], []
    secret_detail = "test-timeout-key-never-send PRIVATE-TRANSPORT-DETAIL"
    def handler(request):
        calls.append(request)
        raise timeout_type(secret_detail, request=request)
    async def emit(*args, **kwargs):
        events.append((args, kwargs))
    fake_clients(monkeypatch, handler)
    with pytest.raises(p.ProviderError) as caught:
        asyncio.run(p.investigate({"id": "case-1"}, "Exact hypothesis.", [{"id": "e1"}],
            emit, lambda: False))
    error = caught.value
    assert error.status == "unknown"
    assert error.reason_code == "model_request_timeout"
    assert len(calls) == 1
    assert error.metadata["dispatched_requests"] == 1
    assert error.metadata["requests"][0]["status"] == "dispatched"
    assert error.metadata["requests"][0]["agent"] == "bioinformatician"
    failure = error.metadata["failure"]
    assert failure["type"] == "model_request_timeout"
    assert failure["request_number"] == 1 and failure["request_timeout_seconds"] == 600
    assert failure["outcome"] == "unknown" and failure["automatic_retry"] is False
    assert error.metadata["work_products"] == []
    assert error.metadata["accepted_analysis_ids"] == []
    serialized = json.dumps({"message": str(error), "metadata": error.metadata, "events": events})
    assert "test-timeout-key-never-send" not in serialized
    assert "PRIVATE-TRANSPORT-DETAIL" not in serialized
    assert "may still complete" in str(error)


def test_worker_persists_request_timeout_as_unknown_with_specific_public_message(monkeypatch, tmp_path):
    from app import followups, worker as w
    from app.store import Store
    monkeypatch.setattr(followups, "approved_catalog", lambda case_id: [])
    monkeypatch.setattr(w, "RUNTIME", tmp_path / "runtime")
    store = Store(tmp_path / "state.sqlite")
    case = {"id": "case-1", "title": "Timeout boundary", "hypothesis": "Exact hypothesis.",
            "evidence": [{"id": "e1", "title": "Source", "summary": "Qualified observation.",
                          "source": {"sha256": "b" * 64}}]}
    run = store.create(case, {"idempotency_key": "timeout-boundary", "hypothesis": case["hypothesis"],
                              "source_name": "Test scientist", "mode": "live"})
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("PRIVATE-TRANSPORT-DETAIL", request=request)
    fake_clients(monkeypatch, handler)
    asyncio.run(w.Worker(store).execute(run["id"]))
    saved = store.get(run["id"])
    assert len(calls) == 1
    assert saved["status"] == "blocked"
    assert saved["actions"][-1]["state"] == "unknown"
    assert saved["usage"]["model_calls"] == 1
    assert "Model response timed out" in saved["error"]
    assert "No automatic retry" in saved["error"]
    assert "PRIVATE-TRANSPORT-DETAIL" not in json.dumps(saved)
    assert saved["decisions"] == []
    assert saved["evidence"] == case["evidence"]
    metadata = saved["actions"][-1]["provider_metadata"]
    assert metadata["failure"]["outcome"] == "unknown"
    assert metadata["failure"]["automatic_retry"] is False
