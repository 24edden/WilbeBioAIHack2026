"""Control transport contracts, safety boundaries and isolated scientific API tests."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest

from frontend.ui.team_tbd_client import APIError, TeamTBDClient, UncertainWriteError, available_controls


ORIGIN = "http://127.0.0.1:9876"
CREATE = {"case_id": "case-1", "hypothesis": "  Keep the scientist's exact question.\n", "source_name": "Original note.md\n",
          "mode": "live", "idempotency_key": "one-intent"}


def client_for(handler):
    return TeamTBDClient(ORIGIN, httpx.Client(transport=httpx.MockTransport(handler)))


@pytest.mark.parametrize("origin", ["http://localhost:8081", "http://example.com", "https://127.0.0.1:8081",
    "http://127.0.0.1:8081/other", "http://127.0.0.1:8081?secret=1", "http://user:pass@127.0.0.1", "http://127.0.0.1@evil.example"])
def test_private_loopback_origin_required(origin):
    with pytest.raises(ValueError, match="loopback"):
        TeamTBDClient(origin)


def test_create_preserves_exact_source_and_same_origin_without_overrides():
    seen = []
    def handler(request):
        seen.append(request)
        body = json.loads(request.content)
        assert body == CREATE
        assert request.headers["Origin"] == ORIGIN
        return httpx.Response(202, json={"id": "run-1", "status": "queued", "case_id": body["case_id"], "mode": body["mode"],
                                        "hypothesis": {"text": body["hypothesis"], "source_name": body["source_name"]}})
    original = copy.deepcopy(CREATE)
    result = client_for(handler).create_run(original)
    assert original == CREATE
    assert result["status"] == "queued"
    assert len(seen) == 1 and seen[0].url.path == "/api/runs"


@pytest.mark.parametrize("change", [{"model": "other"}, {"budget": 100}, {"idempotency_key": " "}, {"idempotency_key": "x" * 101}])
def test_unsupported_payload_or_missing_identity_never_sent(change):
    def forbidden(_):
        pytest.fail("Invalid payload crossed the transport boundary")
    with pytest.raises(ValueError):
        client_for(forbidden).create_run({**CREATE, **change})
    without_key = {k: v for k, v in CREATE.items() if k != "idempotency_key"}
    with pytest.raises(ValueError):
        client_for(forbidden).create_run(without_key)


@pytest.mark.parametrize("method,endpoint,payload", [
    ("feedback", "feedback", {"decision_version": 2, "text": "Original correction.\n", "idempotency_key": "feedback-1"}),
    ("outcome", "outcomes", {"decision_version": 2, "experiment_id": "exp-1", "candidate_id": "arm-1", "endpoint": "Test endpoint",
                            "value": 5.0, "unit": "units", "notes": "Unverified test return.", "idempotency_key": "outcome-1"}),
    ("modeling", "modeling", {"decision_version": 2, "target_sequence": "A" * 15, "reference_binder": "C" * 15,
                             "candidate_binder": "D" * 15, "target_retained": True, "source_note": "Verified exact inputs.", "idempotency_key": "model-1"}),
    ("research_brief", "research-briefs", {"decision_version": 2, "idempotency_key": "brief-1"}),
    ("sequence_discovery", "sequence-discoveries", {"decision_version": 2, "idempotency_key": "sequence-1"}),
    ("followup", "followups", {"decision_version": 2, "recommendation_id": "recommendation-1", "idempotency_key": "followup-1"}),
    ("continue_synthesis", "continue-synthesis", {"source_operation_id": "operation-1", "idempotency_key": "synthesis-1"}),
])
def test_mutation_paths_keep_the_pinned_decision_and_request_key(method, endpoint, payload):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.method == "POST" and request.url.path == f"/api/runs/run-1/{endpoint}"
        assert json.loads(request.content) == payload
        return httpx.Response(202, json={"id": "run-1", "status": "queued"})
    assert getattr(client_for(handler), method)("run-1", payload)["status"] == "queued"
    assert len(calls) == 1


@pytest.mark.parametrize("version", [0, -1, True, 1.0, "1"])
def test_decision_version_is_an_exact_positive_integer(version):
    with pytest.raises(ValueError, match="version"):
        client_for(lambda _: pytest.fail("Invalid decision sent")).research_brief("run-1", {"decision_version": version, "idempotency_key": "key"})


@pytest.mark.parametrize("method", ["cancel", "resume"])
def test_non_keyed_controls_send_no_invented_body(method):
    def handler(request):
        assert request.content == b""
        assert request.url.path == f"/api/runs/run-1/{method}"
        return httpx.Response(200, json={"id": "run-1", "status": "queued"})
    getattr(client_for(handler), method)("run-1")


@pytest.mark.parametrize("status", [301, 302, 307, 308, 500, 502, 503, 504])
def test_unknown_write_never_redirects_or_retries(status):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={"Location": "http://example.com/steal"}, json={"detail": "failure"})
    with pytest.raises(UncertainWriteError) as caught:
        client_for(handler).create_run(CREATE)
    assert caught.value.idempotency_key == "one-intent"
    assert len(calls) == 1


def test_timeout_preserves_uncertainty_and_original_key():
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("Unknown external state", request=request)
    with pytest.raises(UncertainWriteError) as caught:
        client_for(handler).create_run(CREATE)
    assert caught.value.idempotency_key == CREATE["idempotency_key"]
    assert len(calls) == 1


@pytest.mark.parametrize("body", [{"id": "other", "status": "queued"}, {"id": "run-1"}, ["not a run"]])
def test_bad_mutation_acknowledgement_is_uncertain(body):
    with pytest.raises(UncertainWriteError):
        client_for(lambda _: httpx.Response(202, json=body)).feedback("run-1", {"decision_version": 1, "text": "Correction", "idempotency_key": "key"})


@pytest.mark.parametrize("field,value", [("case_id", "foreign"), ("mode", "demo"), ("hypothesis", {"text": "Changed wording", "source_name": CREATE["source_name"]})])
def test_creation_acknowledgement_requires_original_study_mode_and_wording(field, value):
    body = {"id": "run-1", "status": "queued", "case_id": CREATE["case_id"], "mode": CREATE["mode"],
            "hypothesis": {"text": CREATE["hypothesis"], "source_name": CREATE["source_name"]}}
    body[field] = value
    with pytest.raises(UncertainWriteError):
        client_for(lambda _: httpx.Response(202, json=body)).create_run(CREATE)


def test_explicit_rejection_is_not_unknown_and_validation_does_not_echo_input():
    for status in (403, 409, 422, 429):
        detail = [{"loc": ["body", "text"], "msg": "Invalid text", "input": "sensitive test value"}]
        with pytest.raises(APIError) as caught:
            client_for(lambda _: httpx.Response(status, json={"detail": detail})).create_run(CREATE)
        assert type(caught.value) is APIError and caught.value.status_code == status
        assert caught.value.detail == "Invalid text"


def test_read_failures_never_fall_back_to_mock():
    client = client_for(lambda _: httpx.Response(503, json={"detail": "Temporarily unavailable"}))
    with pytest.raises(APIError, match="Temporarily unavailable"):
        client.health()
    client = client_for(lambda _: httpx.Response(200, content=b"invalid json"))
    with pytest.raises(APIError, match="invalid response"):
        client.health()


@pytest.mark.parametrize("method,path,arg", [("health", "/api/health", None), ("cases", "/api/cases", None),
    ("case", "/api/cases/case-1", "case-1"), ("datasets", "/api/datasets", None), ("dataset", "/api/datasets/data-1", "data-1"),
    ("process_contract", "/api/process-contract", None), ("skills", "/api/skills", None),
    ("followups", "/api/runs/run-1/followups", "run-1"), ("synthesis_checkpoint", "/api/runs/run-1/synthesis-checkpoint", "run-1")])
def test_read_endpoint_routing(method, path, arg):
    def handler(request):
        assert request.method == "GET" and request.url.path == path
        return httpx.Response(200, json={"result": "saved"})
    call = getattr(client_for(handler), method)
    assert (call(arg) if arg else call()) == {"result": "saved"}


def test_events_poll_saved_ids_and_do_not_invent_sse_or_stage_status():
    events = [{"id": 1, "status": "completed"}, {"id": 2, "status": "failed"}]
    def handler(request):
        assert request.url.path == "/api/runs/run-1"
        return httpx.Response(200, json={"id": "run-1", "events": events})
    assert client_for(handler).events("run-1", after=1) == [events[1]]


@pytest.mark.parametrize("identity", ["../other", "a/b", "x?query", "%2e%2e", "https://external", "a\\b"])
def test_untrusted_ids_cannot_redirect_requests(identity):
    client = client_for(lambda _: pytest.fail("Invalid identifier was sent"))
    with pytest.raises(ValueError):
        client.get_run(identity)
    with pytest.raises(ValueError):
        client.cancel(identity)


def test_controls_respect_operation_and_scientific_gates():
    run = {"mode": "live", "status": "completed", "decisions": [{"version": 2, "rd_handoff": {"experiment_id": "exp", "candidates": [{"id": "arm"}]}}],
           "actions": [], "operation": {"id": "operation"}}
    health = {"capabilities": {"bionemo": {"status": "configured"}}}
    controls = available_controls(run, health)
    assert all(controls[key] is None for key in ("feedback", "outcome", "modeling", "research_brief", "sequence_discovery", "followup"))
    assert controls["cancel"] and controls["resume"] and controls["continue_synthesis"]
    assert available_controls(run, {}, {"eligible": True})["continue_synthesis"] is None
    assert available_controls(run, {})["modeling"]
    run.update(status="failed", actions=[{"id": "operation-model", "state": "failed"}])
    assert available_controls(run, health)["resume"]
    run.update(actions=[{"id": "other-model", "state": "unknown"}])
    controls = available_controls(run, health)
    assert all(controls[key] for key in ("resume", "feedback", "outcome", "modeling", "research_brief", "sequence_discovery", "followup"))
    run.update(status="running", actions=[])
    controls = available_controls(run, health)
    assert controls["cancel"] is None and controls["feedback"]


def test_against_isolated_authoritative_api(tmp_path):
    """Run in a fresh process so legacy app imports cannot substitute another engine."""
    root = Path(__file__).resolve().parents[1]
    script = root / "tests" / "helpers" / "team_tbd_contract_probe.py"
    env = dict(os.environ, ROSALIND_RUNTIME=str(tmp_path / "runtime"), ROSALIND_EMBEDDED_WORKER="0",
               ROSALIND_CAPABILITIES_FILE=str(tmp_path / "capabilities.json"))
    # This fixture neither reads private env files nor contacts a running service.
    for key in ("OPENAI_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY", "BOLTZ2_NIM_URL"):
        env.pop(key, None)
    backend_python = root / "scientific_backend" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    interpreter = os.environ.get("TEAM_TBD_TEST_PYTHON") or (str(backend_python) if backend_python.is_file() else sys.executable)
    result = subprocess.run([interpreter, str(script)], cwd=root, env=env, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, ("The scientific contract check is required, never silently skipped. Install the scientific_backend environment "
                                  "or set TEAM_TBD_TEST_PYTHON to its Python executable.\n" + result.stdout + result.stderr)
    assert "isolated scientific API contracts passed" in result.stdout
