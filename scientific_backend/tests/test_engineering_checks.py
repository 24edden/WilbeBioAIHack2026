"""Receipt integrity and public-data checks; no vendor request is performed."""
import hashlib
import json
import os

import pytest

from app import engineering_checks as checks


def make_check(runtime, check_id="engineering-one", *, status="completed"):
    directory = runtime / "engineering" / check_id
    directory.mkdir(parents=True)
    artifact = directory / "prediction.cif"
    artifact.write_bytes(b"data_engineering\n# bounded receipt-reader fixture\n")
    receipt = {
        "check_id": check_id, "status": status, "scope": "engineering_monomer_only", "model": "mit/boltz2",
        "created_at": "2026-09-19T12:00:00+00:00", "finished_at": "2026-09-19T12:01:00+00:00",
        "request_id": "987c13a3-c8e5-4261-b411-8224a3a3f9cf", "confidence_score": 0.87,
        "monomer_service_verified": status == "completed", "matched_comparison_verified": False,
        "cart_hypothesis_tested": False, "sequence_sha256": "a" * 64,
        "validation": {"exact_sequence_match": True, "coordinates_finite": True,
                       "alpha_carbon_coverage_complete": True, "models": 1, "chain_ids": ["A"],
                       "sequence_sha256": "a" * 64},
        "artifacts": [{"name": "prediction.cif", "path": str(artifact), "media_type": "chemical/x-mmcif",
                       "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}],
    }
    path = directory / "receipt.json"
    path.write_text(json.dumps(receipt))
    return directory, receipt, path


def test_missing_engineering_state_returns_none(tmp_path):
    assert checks.latest_bionemo_check(tmp_path) is None


def test_validated_check_is_public_and_never_claims_cart_qualification(tmp_path):
    directory, receipt, path = make_check(tmp_path)
    receipt.update(detail="raw private error /home/private and nvapi-test-secret", endpoint="https://private.example",
                   headers={"Authorization": "Bearer nvapi-test-secret"})
    path.write_text(json.dumps(receipt))
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "completed"
    assert result["monomer_service_verified"] is True
    assert result["matched_comparison_verified"] is False
    assert result["cart_hypothesis_tested"] is False
    assert result["confidence_score"] == 0.87
    assert result["artifacts"][0]["sha256"] == receipt["artifacts"][0]["sha256"]
    assert result["request_id"] == receipt["request_id"]
    public = json.dumps(result)
    for forbidden in (str(directory), "private", "nvapi-test-secret", "Authorization", "endpoint", '"path"'):
        assert forbidden not in public


def test_newest_failed_check_does_not_reuse_older_success(tmp_path):
    _, _, older = make_check(tmp_path, "older")
    _, _, newer = make_check(tmp_path, "newer", status="failed")
    os.utime(older, ns=(1_000_000, 1_000_000))
    os.utime(newer, ns=(2_000_000, 2_000_000))
    result = checks.latest_bionemo_check(tmp_path)
    assert result["check_id"] == "newer"
    assert result["status"] == "failed"
    assert result["monomer_service_verified"] is False
    assert result["artifacts"] == []


def test_artifact_tamper_cannot_retain_verified_status(tmp_path):
    directory, _, _ = make_check(tmp_path)
    (directory / "prediction.cif").write_bytes(b"data_changed\n")
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "unverified"
    assert result["reason_code"] == "artifact_mismatch"
    assert result["monomer_service_verified"] is False
    assert result["artifacts"] == []


@pytest.mark.parametrize("field,value", [
    ("exact_sequence_match", False), ("exact_sequence_match", "true"),
    ("coordinates_finite", False), ("alpha_carbon_coverage_complete", False),
    ("sequence_sha256", "b" * 64), ("chain_ids", ["A", "B"]),
])
def test_invalid_validation_flags_are_unverified(tmp_path, field, value):
    _, receipt, path = make_check(tmp_path)
    receipt["validation"][field] = value
    path.write_text(json.dumps(receipt))
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "unverified"
    assert result["monomer_service_verified"] is False


@pytest.mark.parametrize("field,value", [
    ("scope", "cart_matched_comparison"), ("matched_comparison_verified", True),
    ("cart_hypothesis_tested", True), ("check_id", "different"),
    ("confidence_score", float("nan")), ("confidence_score", 1.1),
])
def test_invalid_scope_identity_or_confidence_is_unverified(tmp_path, field, value):
    _, receipt, path = make_check(tmp_path)
    receipt[field] = value
    path.write_text(json.dumps(receipt))
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "unverified"
    assert not result["monomer_service_verified"]
    assert not result["matched_comparison_verified"]
    assert not result["cart_hypothesis_tested"]


@pytest.mark.parametrize("artifact_path", ["../../outside.cif", "/etc/passwd", "nested/prediction.cif"])
def test_receipt_paths_cannot_redirect_artifact_read(tmp_path, artifact_path):
    _, receipt, path = make_check(tmp_path)
    receipt["artifacts"][0]["path"] = artifact_path
    path.write_text(json.dumps(receipt))
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "unverified"
    assert result["reason_code"] == "receipt_artifact_path"
    assert artifact_path not in json.dumps(result)


@pytest.mark.parametrize("name", ["prediction.cif", "receipt.json"])
def test_receipt_and_artifact_symlinks_are_rejected(tmp_path, name):
    directory, _, _ = make_check(tmp_path)
    item = directory / name
    outside = tmp_path / ("outside-" + name)
    item.rename(outside)
    item.symlink_to(outside)
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "unverified"
    assert result["monomer_service_verified"] is False
    assert str(outside) not in json.dumps(result)


@pytest.mark.parametrize("target", ["runtime", "engineering", "check"])
def test_directory_symlinks_are_rejected(tmp_path, target):
    runtime = tmp_path / "runtime"
    directory, _, _ = make_check(runtime)
    source = {"runtime": runtime, "engineering": runtime / "engineering", "check": directory}[target]
    outside = tmp_path / "outside"
    source.rename(outside)
    source.symlink_to(outside, target_is_directory=True)
    result = checks.latest_bionemo_check(runtime)
    assert result["status"] == "unverified"
    assert result["monomer_service_verified"] is False


def test_runtime_ancestor_symlink_is_rejected(tmp_path):
    runtime = tmp_path / "actual-parent" / "runtime"
    make_check(runtime)
    alias = tmp_path / "alias-parent"
    alias.symlink_to(runtime.parent, target_is_directory=True)
    result = checks.latest_bionemo_check(alias / "runtime")
    assert result["status"] == "unverified"
    assert result["monomer_service_verified"] is False


def test_oversized_receipt_and_artifact_are_rejected(tmp_path, monkeypatch):
    _, _, path = make_check(tmp_path)
    with monkeypatch.context() as limited:
        limited.setattr(checks, "MAX_RECEIPT_BYTES", 10)
        assert checks.latest_bionemo_check(tmp_path)["status"] == "unverified"
    with monkeypatch.context() as limited:
        limited.setattr(checks, "MAX_ARTIFACT_BYTES", 10)
        assert checks.latest_bionemo_check(tmp_path)["status"] == "unverified"
    path.write_text('{"status":')
    assert checks.latest_bionemo_check(tmp_path)["status"] == "unverified"


def test_directory_inventory_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(checks, "MAX_CHECKS", 2)
    for number in range(3):
        make_check(tmp_path, "check-" + str(number))
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "unverified"
    assert result["reason_code"] == "check_limit"


def test_secret_or_malformed_metadata_is_not_exposed(tmp_path, monkeypatch):
    _, receipt, path = make_check(tmp_path, status="pending")
    monkeypatch.setenv("NVIDIA_API_KEY", "private-test-credential")
    receipt.update(request_id="private-test-credential", finished_at="/home/private/secret")
    path.write_text(json.dumps(receipt))
    result = checks.latest_bionemo_check(tmp_path)
    assert result["status"] == "pending"
    assert "request_id" not in result
    assert "finished_at" not in result
    assert result["artifacts"] == []


def test_download_returns_only_verified_bytes_and_public_receipt(tmp_path):
    directory, receipt, _ = make_check(tmp_path)
    public, data = checks.bionemo_download(tmp_path,'engineering-one')
    assert data == (directory/'prediction.cif').read_bytes()
    assert 'path' not in public['artifacts'][0]
    (directory/'prediction.cif').write_bytes(b'data_changed\n')
    with pytest.raises(checks.InvalidReceipt):
        checks.bionemo_download(tmp_path,'engineering-one')
    with pytest.raises(checks.InvalidReceipt):
        checks.bionemo_download(tmp_path,'../outside')
