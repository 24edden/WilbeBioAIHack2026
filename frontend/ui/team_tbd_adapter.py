"""Read-only presentation adapters for Team TBD's private recorded research.

No provider credentials, scientific transformations, or mutation methods belong here.
The capsule and live service remain the authority for every scientific field.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx

SCHEMA = "team-tbd-results-capsule/1.0"
MAX_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 5 * 1024 * 1024


def _safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or any(c in value for c in "\\:%?#\x00"):
        raise ValueError("Invalid capsule path")
    if value.startswith("/") or any(p in ("", ".", "..") for p in value.split("/")):
        raise ValueError("Invalid capsule path")
    return value


def _verify(data: bytes, record: dict) -> bytes:
    if len(data) > MAX_BYTES:
        raise ValueError("File exceeds the read limit")
    size = record.get("bytes", record.get("size"))
    if size is not None and len(data) != size:
        raise ValueError("File size does not match its receipt")
    expected = record.get("sha256")
    if expected and hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("File SHA-256 does not match its receipt")
    return data


def _model_receipts(run: dict) -> list[dict]:
    receipts = []
    seen = set()
    for field, key in (("decisions", "metadata"), ("actions", "provider_metadata"), ("research_briefs", "provider_metadata"),
                       ("sequence_discoveries", "provider_metadata")):
        for i, item in enumerate(run.get(field, [])):
            if item.get(key):
                identity = json.dumps(item[key], sort_keys=True, separators=(",", ":"))
                if identity not in seen:
                    seen.add(identity)
                    receipts.append({"source_pointer": f"/{field}/{i}/{key}", "metadata": item[key]})
    return receipts


def recorded_artifacts(run: dict) -> list[dict]:
    """Deduplicate repeated references without upgrading any operation status."""
    records = []
    for field in ("followup_operations", "required_analysis_operations"):
        for operation in run.get(field, []):
            records.extend(operation.get("artifacts", []))
    for decision in run.get("decisions", []):
        records.extend(decision.get("rd_handoff", {}).get("modeling", {}).get("artifacts", []))
    unique = {}
    for item in records:
        if isinstance(item, dict) and item.get("url"):
            unique.setdefault(item["url"], dict(item, run_id=run["id"]))
    return list(unique.values())


def run_view(run: dict, artifacts: list[dict] | None = None) -> dict:
    """Map saved fields only; never infer scientific success from completion."""
    briefs = run.get("research_briefs", [])
    brief = briefs[-1] if briefs else {}
    return {
        "run_id": run["id"], "label": run.get("title", run["id"]),
        "status": run.get("status"), "mode": run.get("mode"), "case_id": run.get("case_id"),
        "question": run.get("hypothesis", {}), "findings": brief.get("content", {}),
        "decisions": run.get("decisions", []), "handoffs": run.get("handoffs", []),
        "checks": run.get("stage_evaluations", []), "skills": run.get("skill_receipts", []),
        "model_receipts": _model_receipts(run),
        "nvidia": ([{"source_kind": "followup_operation", "record": operation}
                    for operation in run.get("followup_operations", []) if operation.get("provider_receipts")]
                   + [{"source_kind": "decision_modeling", "record": d["rd_handoff"]["modeling"]}
                      for d in run.get("decisions", []) if d.get("rd_handoff", {}).get("modeling")]),
        "sequence_discoveries": run.get("sequence_discoveries", []),
        "research_briefs": briefs, "evidence": run.get("evidence", []),
        "followup_operations": run.get("followup_operations", []),
        "required_analysis_operations": run.get("required_analysis_operations", []),
        "governance": {"current": run.get("governance_state"), "transitions": run.get("governance_transitions", [])},
        "artifacts": artifacts if artifacts is not None else recorded_artifacts(run),
        "usage": run.get("usage", {}), "error": run.get("error"),
        "human_review_status": run.get("review_status", "unreviewed"),
        "provenance": {"source_updated_at": run.get("updated_at")},
    }


def _bundle(run: dict, view: dict, artifacts: list[dict]) -> dict:
    return {"run": run, "events": run.get("events", []), "evidence": run.get("evidence", []),
            "view": view, "artifacts": artifacts}


class Capsule:
    """Strict local reader for one immutable results capsule, never a database import."""

    def __init__(self, root: str | Path, expected_manifest_sha256: str | None = None):
        self.root = Path(root).resolve(strict=True)
        manifest_path = self.root / "manifest.json"
        if manifest_path.is_symlink():
            raise ValueError("Manifest must not be a symlink")
        with manifest_path.open("rb") as handle:
            raw = handle.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ValueError("Manifest exceeds the read limit")
        if expected_manifest_sha256 and hashlib.sha256(raw).hexdigest() != expected_manifest_sha256:
            raise ValueError("Manifest SHA-256 mismatch")
        self.manifest = json.loads(raw)
        if self.manifest.get("schema_version") != SCHEMA:
            raise ValueError("Unsupported capsule schema")
        self._files = {}
        for item in self.manifest["files"]:
            path = _safe_path(item["path"])
            if path in self._files:
                raise ValueError("Duplicate manifest file")
            if not isinstance(item.get("bytes"), int) or not 0 <= item["bytes"] <= MAX_BYTES:
                raise ValueError("Invalid manifest file size")
            if not re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")):
                raise ValueError("Invalid manifest file hash")
            self._files[path] = item
        self.runs = self.manifest["runs"]
        self._runs = {r["run_id"]: r for r in self.runs}
        if len(self._runs) != len(self.runs):
            raise ValueError("Duplicate capsule run")
        index = self.read_json(self.manifest["entrypoints"]["artifact_index"])
        if index.get("schema_version") != SCHEMA or index.get("package_id") != self.manifest.get("package_id"):
            raise ValueError("Artifact index capsule identity mismatch")
        self.artifacts = index["artifacts"]

    def read_bytes(self, path: str) -> bytes:
        path = _safe_path(path)
        if path not in self._files:
            raise ValueError("File is not listed in the capsule manifest")
        target = self.root / path
        if any(p.is_symlink() for p in (target, *target.parents) if p != self.root and self.root in p.parents):
            raise ValueError("Capsule files must not use symlinks")
        if not target.resolve(strict=True).is_relative_to(self.root):
            raise ValueError("Capsule path escapes its root")
        record = self._files[path]
        with target.open("rb") as handle:
            data = handle.read(record["bytes"] + 1)
        return _verify(data, record)

    def read_json(self, path: str):
        return json.loads(self.read_bytes(path).decode("utf-8"))

    def list_runs(self) -> list[dict]:
        return self.runs

    def load(self, run_id: str) -> dict:
        if run_id not in self._runs:
            raise ValueError("Run is not listed in this capsule")
        metadata = self._runs[run_id]
        run = self.read_json(metadata["raw_export_path"])["run"]
        view = self.read_json(metadata["view_path"])
        if run.get("id") != run_id or view.get("run_id") != run_id:
            raise ValueError("Capsule run identity mismatch")
        artifacts = [a for a in self.artifacts if a.get("run_id") == run_id]
        return _bundle(run, view, artifacts)

    def artifact_bytes(self, item: dict) -> bytes:
        match = next((a for a in self.artifacts if a.get("path") == item.get("path")
                      and a.get("run_id") == item.get("run_id")), None)
        if not match or not match.get("path"):
            raise ValueError("Artifact is not listed in this capsule")
        return _verify(self.read_bytes(match["path"]), match)


class LiveSource:
    """Server-side GET-only reader restricted to an explicit private loopback service."""

    def __init__(self, base: str, client: httpx.Client | None = None):
        parsed = urlsplit(base)
        try:
            loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
        except ValueError:
            loopback = False
        if not loopback or parsed.scheme != "http" or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("Live source must be an explicit HTTP loopback origin")
        self.base = base.rstrip("/")
        self._client = client
        self._artifacts: dict[str, dict] = {}

    def _get(self, path: str) -> bytes:
        if not path.startswith("/api/") or any(c in path for c in "\\%?#") or any(p in (".", "..") for p in path.split("/")):
            raise ValueError("Invalid API path")
        client = self._client or httpx.Client(timeout=30, trust_env=False, follow_redirects=False)
        try:
            with client.stream("GET", self.base + path, follow_redirects=False) as response:
                if 300 <= response.status_code < 400:
                    raise ValueError("Live source redirects are forbidden")
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError("Live response exceeds the read limit")
                    chunks.append(chunk)
                return b"".join(chunks)
        finally:
            if self._client is None:
                client.close()

    def list_runs(self) -> list[dict]:
        return json.loads(self._get("/api/runs"))

    def load(self, run_id: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", run_id):
            raise ValueError("Invalid run identifier")
        packet = json.loads(self._get(f"/api/runs/{run_id}/export.json"))
        run = packet["run"]
        if run.get("id") != run_id:
            raise ValueError("Live run identity mismatch")
        artifacts = recorded_artifacts(run)
        for item in artifacts:
            for key, kind in (("url", "artifacts"), ("preview_url", "structure-preview")):
                url = item.get(key)
                if url and url.startswith(f"/api/runs/{run_id}/{kind}/"):
                    self._artifacts[url] = item if key == "url" else {"url": url, "run_id": run_id}
        return _bundle(run, run_view(run, artifacts), artifacts)

    def artifact_bytes(self, item: dict) -> bytes:
        url = item.get("url", item.get("source_url"))
        if url not in self._artifacts:
            raise ValueError("Artifact is not recorded in a loaded live run")
        return _verify(self._get(url), self._artifacts[url])
