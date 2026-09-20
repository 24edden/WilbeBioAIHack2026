"""Server-side control transport for the durable Team TBD scientific service.

Only explicit loopback origins are accepted. Requests are never retried, redirected,
or replaced with mock work. A caller owns each request key and must keep that key
and the exact payload until its outcome is known. Scientific validation and
execution remain entirely in the authoritative service.
"""
from __future__ import annotations

import copy
import json
import re
from typing import Any

import httpx

from .team_tbd_adapter import LiveSource, MAX_BYTES


class APIError(RuntimeError):
    """An explicit server rejection or a failed read, with no provider claims."""

    def __init__(self, status_code: int | None, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class UncertainWriteError(APIError):
    """The service may have persisted this intent; do not create another key."""

    def __init__(self, operation: str, idempotency_key: str | None):
        self.operation = operation
        self.idempotency_key = idempotency_key
        message = "The request outcome is unknown. Refresh the saved run before taking another action."
        if idempotency_key:
            message += " Keep this exact request and its existing request key; no automatic retry was made."
        else:
            message += " This control has no request key; do not automatically repeat it."
        super().__init__(None, message)


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError("Invalid API identifier")
    return value


_PAYLOAD_FIELDS = {
    "create": ({"case_id", "hypothesis", "source_name", "mode", "idempotency_key",
                "molecular_inputs", "required_analysis_ids", "evaluation_lesson_id"},
               {"case_id", "hypothesis", "source_name", "mode", "idempotency_key"}),
    "feedback": ({"decision_version", "text", "idempotency_key"}, {"decision_version", "text", "idempotency_key"}),
    "outcomes": ({"decision_version", "experiment_id", "candidate_id", "endpoint", "value", "unit", "notes", "idempotency_key"},
                 {"decision_version", "experiment_id", "candidate_id", "endpoint", "value", "unit", "notes", "idempotency_key"}),
    "modeling": ({"decision_version", "target_sequence", "reference_binder", "candidate_binder", "target_retained", "source_note", "idempotency_key"},
                 {"decision_version", "target_sequence", "reference_binder", "candidate_binder", "target_retained", "source_note", "idempotency_key"}),
    "research-briefs": ({"decision_version", "idempotency_key"}, {"decision_version", "idempotency_key"}),
    "sequence-discoveries": ({"decision_version", "idempotency_key"}, {"decision_version", "idempotency_key"}),
    "followups": ({"decision_version", "recommendation_id", "idempotency_key"}, {"decision_version", "recommendation_id", "idempotency_key"}),
    "continue-synthesis": ({"source_operation_id", "idempotency_key"}, {"source_operation_id", "idempotency_key"}),
}


def _payload(operation: str, payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("A structured request is required")
    allowed, required = _PAYLOAD_FIELDS[operation]
    if set(payload) - allowed or required - set(payload):
        raise ValueError("Request fields do not match the scientific service contract")
    key = payload.get("idempotency_key")
    if not isinstance(key, str) or not key.strip() or len(key) > 100:
        raise ValueError("Keep one nonblank request key (at most 100 characters) for this exact request")
    if "decision_version" in payload and (type(payload["decision_version"]) is not int or payload["decision_version"] < 1):
        raise ValueError("Select the exact current decision version")
    # A defensive copy ensures no caller edit can change an in-flight request.
    # Do not strip, normalize or rephrase the original question or source name.
    result = copy.deepcopy(payload)
    json.dumps(result, allow_nan=False)
    return result


class TeamTBDClient(LiveSource):
    """Finite GET polling and explicit writes to the scientific /api/runs contract."""

    def _request(self, method: str, path: str, payload: dict | None = None) -> bytes:
        if not path.startswith("/api/") or any(c in path for c in "\\%?#") or any(p in (".", "..") for p in path.split("/")):
            raise ValueError("Invalid API path")
        write = method != "GET"
        key = payload.get("idempotency_key") if payload else None
        client = self._client or httpx.Client(timeout=30, trust_env=False, follow_redirects=False)
        try:
            options: dict[str, Any] = {"follow_redirects": False, "headers": {"Origin": self.base, "Accept": "application/json"}}
            if payload is not None:
                options["json"] = payload
            with client.stream(method, self.base + path, **options) as response:
                if 300 <= response.status_code < 400:
                    if write:
                        raise UncertainWriteError(path, key)
                    raise APIError(response.status_code, "Scientific service redirects are forbidden.")
                if response.status_code >= 500 and write:
                    raise UncertainWriteError(path, key)
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        if write:
                            raise UncertainWriteError(path, key)
                        raise APIError(response.status_code, "Scientific service response exceeds the read limit.")
                    chunks.append(chunk)
                body = b"".join(chunks)
                if response.status_code >= 400:
                    try:
                        detail = json.loads(body).get("detail", "Scientific service rejected the request.")
                    except (ValueError, AttributeError):
                        detail = "Scientific service rejected the request."
                    if not isinstance(detail, str):
                        # Validation locations/messages are safe; never echo rejected inputs.
                        detail = "; ".join(str(item.get("msg", "Invalid request")) for item in detail if isinstance(item, dict)) if isinstance(detail, list) else "Invalid request."
                    raise APIError(response.status_code, detail[:2000])
                return body
        except httpx.HTTPError as exc:
            if write:
                raise UncertainWriteError(path, key) from exc
            raise APIError(None, "The scientific service could not be reached. Check its configured connection.") from exc
        finally:
            if self._client is None:
                client.close()

    def _get(self, path: str) -> bytes:
        return self._request("GET", path)

    def _json(self, path: str):
        try:
            return json.loads(self._get(path))
        except (ValueError, UnicodeError) as exc:
            raise APIError(None, "The scientific service returned an invalid response.") from exc

    def _write(self, operation: str, payload: dict | None, run_id: str | None = None) -> dict:
        if payload is not None:
            payload = _payload(operation, payload)
        path = "/api/runs" if operation == "create" else f"/api/runs/{_identifier(run_id)}/{operation}"
        raw = self._request("POST", path, payload)
        try:
            result = json.loads(raw)
            if not isinstance(result, dict) or not isinstance(result.get("id"), str) or not isinstance(result.get("status"), str):
                raise ValueError("Missing run identity or status")
            if run_id is not None and result["id"] != run_id:
                raise ValueError("Run identity mismatch")
            if operation == "create" and (result.get("hypothesis", {}).get("text") != payload["hypothesis"]
                                           or result.get("hypothesis", {}).get("source_name") != payload["source_name"]
                                           or result.get("case_id") != payload["case_id"]
                                           or result.get("mode") != payload["mode"]):
                raise ValueError("Original hypothesis provenance mismatch")
            return result
        except (ValueError, UnicodeError, AttributeError) as exc:
            raise UncertainWriteError(path, payload.get("idempotency_key") if payload else None) from exc

    def health(self) -> dict:
        return self._json("/api/health")

    def cases(self) -> list[dict]:
        return self._json("/api/cases")

    def case(self, case_id: str) -> dict:
        return self._json(f"/api/cases/{_identifier(case_id)}")

    def datasets(self) -> list[dict]:
        return self._json("/api/datasets")

    def dataset(self, dataset_id: str) -> dict:
        return self._json(f"/api/datasets/{_identifier(dataset_id)}")

    def process_contract(self) -> dict:
        return self._json("/api/process-contract")

    def skills(self) -> dict:
        return self._json("/api/skills")

    def get_run(self, run_id: str) -> dict:
        run = self._json(f"/api/runs/{_identifier(run_id)}")
        if not isinstance(run, dict) or run.get("id") != run_id:
            raise APIError(None, "Scientific service run identity mismatch.")
        return run

    def events(self, run_id: str, after: int = 0) -> list[dict]:
        """Poll durable events without holding an unbounded Streamlit SSE request."""
        if type(after) is not int or after < 0:
            raise ValueError("Event cursor must be a nonnegative integer")
        return [event for event in self.get_run(run_id).get("events", []) if event["id"] > after]

    def followups(self, run_id: str) -> dict:
        return self._json(f"/api/runs/{_identifier(run_id)}/followups")

    def synthesis_checkpoint(self, run_id: str) -> dict:
        return self._json(f"/api/runs/{_identifier(run_id)}/synthesis-checkpoint")

    def create_run(self, payload: dict) -> dict:
        return self._write("create", payload)

    def cancel(self, run_id: str) -> dict:
        return self._write("cancel", None, run_id)

    def resume(self, run_id: str) -> dict:
        return self._write("resume", None, run_id)

    def feedback(self, run_id: str, payload: dict) -> dict:
        return self._write("feedback", payload, run_id)

    def outcome(self, run_id: str, payload: dict) -> dict:
        return self._write("outcomes", payload, run_id)

    def modeling(self, run_id: str, payload: dict) -> dict:
        return self._write("modeling", payload, run_id)

    def research_brief(self, run_id: str, payload: dict) -> dict:
        return self._write("research-briefs", payload, run_id)

    def sequence_discovery(self, run_id: str, payload: dict) -> dict:
        return self._write("sequence-discoveries", payload, run_id)

    def followup(self, run_id: str, payload: dict) -> dict:
        return self._write("followups", payload, run_id)

    def continue_synthesis(self, run_id: str, payload: dict) -> dict:
        return self._write("continue-synthesis", payload, run_id)


def available_controls(run: dict, health: dict, checkpoint: dict | None = None) -> dict[str, str | None]:
    """UI hints only: None means locally eligible; the service revalidates every write."""
    active = run.get("status") in {"running", "queued"}
    decision = bool(run.get("decisions"))
    unresolved = any(a.get("state") in {"unknown", "submitting"} for a in run.get("actions", []))
    operation_id = run.get("operation", {}).get("id", "")
    failed = bool(operation_id) and any(a.get("state") == "failed" and a.get("id", "").startswith(operation_id) for a in run.get("actions", []))
    base = ("Wait for the current operation to finish." if active else
            "An external action remains unresolved; reconcile it before requesting more work." if unresolved else
            "A saved decision is required." if not decision else None)
    live = base or ("This action requires a live investigation." if run.get("mode") != "live" else None)
    completed = live or ("A completed current decision is required." if run.get("status") != "completed" else None)
    modeling = completed or ("Configure the supported NVIDIA service on the backend first." if health.get("capabilities", {}).get("bionemo", {}).get("status") not in {"configured", "verified"} else None)
    handoff = run.get("decisions", [{}])[-1].get("rd_handoff", {}) if decision else {}
    outcome = base or ("This decision has no experiment and candidate identifiers for a measured return." if not handoff.get("experiment_id") or not handoff.get("candidates") else None)
    resume = ("Only stopped runs can be resumed." if run.get("status") not in {"paused", "cancelled", "failed", "budget_exhausted", "blocked"} else
              "An external action remains unresolved; it cannot be submitted twice." if unresolved else
              "The current provider attempt failed and cannot be replayed. Inspect synthesis continuation or start an explicitly new investigation." if failed else None)
    return {"cancel": None if active else "There is no active operation to cancel.", "resume": resume,
            "feedback": base, "outcome": outcome, "modeling": modeling,
            "research_brief": live, "sequence_discovery": live,
            "followup": completed or ("This run was cancelled." if run.get("cancel_requested") else None),
            "continue_synthesis": None if checkpoint and checkpoint.get("eligible") is True else (checkpoint or {}).get("reason", "Inspect saved synthesis recovery eligibility first.")}
