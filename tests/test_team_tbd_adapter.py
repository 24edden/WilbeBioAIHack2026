"""Security and faithful mapping checks; no scientific jobs are submitted."""
import hashlib
import json
import os
from pathlib import Path

import httpx
import pytest

from frontend.ui.team_tbd_adapter import Capsule, LiveSource, SCHEMA


def capsule_fixture(tmp_path):
    run = {"id": "sample", "events": [{"title": "Recorded"}], "evidence": [],
           "usage": {"model_calls": 2}, "status": "completed"}
    files = {
        "export.json": {"run": run}, "view.json": {"run_id": "sample"},
        "artifact-index.json": {"schema_version": SCHEMA, "package_id": "test", "artifacts": []},
    }
    manifest = {"schema_version": SCHEMA, "package_id": "test", "files": [],
                "entrypoints": {"artifact_index": "artifact-index.json"},
                "runs": [{"run_id": "sample", "raw_export_path": "export.json", "view_path": "view.json"}]}
    for name, value in files.items():
        data = json.dumps(value).encode()
        (tmp_path / name).write_bytes(data)
        manifest["files"].append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return Capsule(tmp_path)


def test_capsule_load_and_integrity(tmp_path):
    capsule = capsule_fixture(tmp_path)
    assert capsule.load("sample")["events"][0]["title"] == "Recorded"
    data = (tmp_path / "export.json").read_bytes()
    (tmp_path / "export.json").write_bytes(data.replace(b"Recorded", b"Modified"))
    with pytest.raises(ValueError, match="SHA-256"):
        capsule.load("sample")


@pytest.mark.parametrize("path", ["../export.json", "/export.json", "a/../export.json", "%2e%2e/export.json", "https://x", "a\\b", "export.json?x", "unknown.json"])
def test_capsule_refuses_untrusted_paths(tmp_path, path):
    with pytest.raises(ValueError):
        capsule_fixture(tmp_path).read_bytes(path)


def test_capsule_refuses_symlinks_and_manifest_tampering(tmp_path):
    capsule = capsule_fixture(tmp_path)
    (tmp_path / "export.json").unlink()
    (tmp_path / "export.json").symlink_to(tmp_path / "view.json")
    with pytest.raises(ValueError, match="symlink"):
        capsule.load("sample")
    with pytest.raises(ValueError, match="Manifest SHA-256"):
        Capsule(tmp_path, "0" * 64)


@pytest.mark.parametrize("base", ["https://example.com", "http://localhost:8081", "http://127.0.0.1@evil.test", "http://127.0.0.1:8081/api", "http://127.0.0.1:8081?x"])
def test_live_refuses_non_loopback_origins(base):
    with pytest.raises(ValueError):
        LiveSource(base)


def test_live_refuses_redirects():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(302, headers={"Location": "http://example.com"})))
    with pytest.raises(ValueError, match="redirect"):
        LiveSource("http://127.0.0.1:8081", client).load("sample")


def test_live_mapping_recorded_artifacts_and_hashes():
    payload = b"verified coordinates"
    url = "/api/runs/sample/artifacts/action/prediction.cif"
    preview = "/api/runs/sample/structure-preview/action/prediction.cif"
    artifact = {"url": url, "preview_url": preview, "sha256": hashlib.sha256(payload).hexdigest()}
    run = {"id": "sample", "usage": {"model_calls": 8}, "events": [], "evidence": [],
           "followup_operations": [{"status": "failed", "result_status": "completed", "artifacts": [artifact], "provider_receipts": [{"status": "completed"}]}],
           "research_briefs": [{"content": {"headline": "Saved conclusion"}, "provider_metadata": {"requested_model": "gpt-6-astra"}}]}
    calls = []

    def transport(request):
        calls.append(request.method)
        if request.url.path.endswith("export.json"):
            return httpx.Response(200, json={"run": run})
        return httpx.Response(200, content=payload)

    source = LiveSource("http://127.0.0.1:8081", httpx.Client(transport=httpx.MockTransport(transport)))
    result = source.load("sample")
    assert result["view"]["findings"]["headline"] == "Saved conclusion"
    assert result["view"]["usage"] == {"model_calls": 8}
    assert result["view"]["followup_operations"][0]["status"] == "failed"
    assert source.artifact_bytes(artifact) == payload
    assert source.artifact_bytes({"url": preview}) == payload
    with pytest.raises(ValueError, match="not recorded"):
        source.artifact_bytes({"url": "/api/runs/other/artifacts/action/prediction.cif"})
    source._artifacts[url]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        source.artifact_bytes(artifact)
    assert set(calls) == {"GET"}


def test_actual_capsule_when_configured():
    root = os.environ.get("TEAM_TBD_TEST_CAPSULE") or os.environ.get("TEAM_TBD_CAPSULE")
    if not root:
        pytest.skip("Set TEAM_TBD_CAPSULE for private frozen-data verification")
    capsule = Capsule(Path(root))
    assert len(capsule.runs) == 12
    for metadata in capsule.runs:
        result = capsule.load(metadata["run_id"])
        assert result["run"]["id"] == metadata["run_id"]
        assert result["view"]["usage"] == result["run"]["usage"]
        for artifact in result["artifacts"]:
            if artifact.get("path"):
                capsule.artifact_bytes(artifact)
