"""Read public receipts for engineering checks without promoting CAR-T evidence.

The writer is scripts/verify_bionemo_service.py. This reader never contacts a
provider, follows receipt-supplied paths, exposes raw errors or changes capability
state. A completed receipt is rechecked against its bounded local artifact.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

MAX_CHECKS = 128
MAX_RECEIPT_BYTES = 64_000
MAX_ARTIFACT_BYTES = 10_000_000
SCOPE = "engineering_monomer_only"
SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,199}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
STATUSES = {"intent_recorded", "dispatched", "pending", "unknown", "failed", "completed"}


class InvalidReceipt(ValueError):
    pass


@contextmanager
def _directory(name, *, parent=None):
    descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    try:
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def _runtime_directory(path):
    """Walk from the filesystem root so an ancestor symlink cannot bypass guards."""
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.parts[1:]:
            if component in {".", ".."}:
                raise InvalidReceipt("unsafe_storage")
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


def _bytes(name, directory, maximum):
    """Open only a fixed child name, with a bound enforced before and during read."""
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
            raise InvalidReceipt("invalid_file")
        chunks, total = [], 0
        while True:
            chunk = os.read(descriptor, min(65_536, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise InvalidReceipt("file_limit")
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise InvalidReceipt("file_changed")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _identifier(value, pattern):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        return None
    if value.lower().startswith(("sk-", "nvapi-", "bearer")):
        return None
    if any(secret and secret in value for secret in (
        os.getenv("OPENAI_API_KEY"), os.getenv("NGC_API_KEY"), os.getenv("NVIDIA_API_KEY"))):
        return None
    return value


def _time(value):
    if not isinstance(value, str) or len(value) > 64:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).isoformat() if parsed.tzinfo else None
    except ValueError:
        return None


def _unverified(reason, check_id=None):
    result = {"status": "unverified", "scope": "unverified", "model": "mit/boltz2",
              "monomer_service_verified": False, "matched_comparison_verified": False,
              "cart_hypothesis_tested": False, "artifacts": [], "reason_code": reason}
    safe_id = _identifier(check_id, SAFE_ID)
    if safe_id:
        result["check_id"] = safe_id
    return result


def _public_receipt(receipt, check_id, directory, expected_path):
    if not isinstance(receipt, dict) or receipt.get("check_id") != check_id:
        raise InvalidReceipt("receipt_identity")
    if receipt.get("scope") != SCOPE or receipt.get("model") != "mit/boltz2":
        raise InvalidReceipt("receipt_scope")
    if receipt.get("matched_comparison_verified") is not False or receipt.get("cart_hypothesis_tested") is not False:
        raise InvalidReceipt("receipt_scope")
    status = receipt.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise InvalidReceipt("receipt_status")
    result = {**_unverified("not_verified", check_id), "status": status, "scope": SCOPE}
    for field in ("created_at", "dispatched_at", "finished_at", "response_received_at"):
        timestamp = _time(receipt.get(field))
        if timestamp:
            result[field] = timestamp
    request_id = _identifier(receipt.get("request_id"), SAFE_REQUEST_ID)
    if request_id:
        result["request_id"] = request_id
    if status != "completed":
        if receipt.get("monomer_service_verified") is not False:
            raise InvalidReceipt("receipt_verification")
        return result

    validation = receipt.get("validation")
    if (receipt.get("monomer_service_verified") is not True or not isinstance(validation, dict)
            or validation.get("exact_sequence_match") is not True
            or validation.get("coordinates_finite") is not True
            or validation.get("alpha_carbon_coverage_complete") is not True
            or validation.get("chain_ids") != ["A"] or validation.get("models") != 1):
        raise InvalidReceipt("receipt_validation")
    sequence_hash = receipt.get("sequence_sha256")
    if not isinstance(sequence_hash, str) or not SHA256.fullmatch(sequence_hash) or validation.get("sequence_sha256") != sequence_hash:
        raise InvalidReceipt("receipt_validation")
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 1 or not isinstance(artifacts[0], dict):
        raise InvalidReceipt("receipt_artifact")
    artifact = artifacts[0]
    if (artifact.get("name") != "prediction.cif" or artifact.get("media_type") != "chemical/x-mmcif"
            or artifact.get("path") not in ("prediction.cif", str(expected_path))):
        raise InvalidReceipt("receipt_artifact_path")
    claimed_hash = artifact.get("sha256")
    if not isinstance(claimed_hash, str) or not SHA256.fullmatch(claimed_hash):
        raise InvalidReceipt("receipt_artifact")
    data = _bytes("prediction.cif", directory, MAX_ARTIFACT_BYTES)
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != claimed_hash or not data.lstrip().startswith(b"data_"):
        raise InvalidReceipt("artifact_mismatch")
    score = receipt.get("confidence_score")
    if score is not None and (type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1):
        raise InvalidReceipt("receipt_confidence")
    result.update(monomer_service_verified=True, reason_code="validated_engineering_artifact",
                  artifacts=[{"name": "prediction.cif", "sha256": actual_hash, "media_type": "chemical/x-mmcif"}])
    if score is not None:
        result["confidence_score"] = score
    return result


def latest_bionemo_check(runtime: Path) -> dict | None:
    """Return the newest local check, never silently falling back after tampering.

    No more than 128 directory entries, one 64 KB receipt and one 10 MB artifact
    are considered. Only directories/files opened without following symlinks are
    used. Missing engineering state returns None; unsafe or invalid state returns
    an explicitly unverified result, without paths, exception text or secrets.
    """
    runtime = Path(runtime).absolute()
    check_id = None
    try:
        with _runtime_directory(runtime) as runtime_fd:
            with _directory("engineering", parent=runtime_fd) as engineering_fd:
                candidates = []
                with os.scandir(engineering_fd) as entries:
                    for index, entry in enumerate(entries):
                        if index >= MAX_CHECKS:
                            raise InvalidReceipt("check_limit")
                        if not SAFE_ID.fullmatch(entry.name):
                            continue
                        if entry.is_symlink():
                            raise InvalidReceipt("unsafe_storage")
                        if not entry.is_dir(follow_symlinks=False):
                            continue
                        with _directory(entry.name, parent=engineering_fd) as directory:
                            try:
                                metadata = os.stat("receipt.json", dir_fd=directory, follow_symlinks=False)
                            except FileNotFoundError:
                                continue
                            if not stat.S_ISREG(metadata.st_mode):
                                raise InvalidReceipt("unsafe_storage")
                            candidates.append((metadata.st_mtime_ns, entry.name))
                if not candidates:
                    return None
                _, check_id = max(candidates)
                with _directory(check_id, parent=engineering_fd) as directory:
                    raw = _bytes("receipt.json", directory, MAX_RECEIPT_BYTES)
                    receipt = json.loads(raw)
                    return _public_receipt(receipt, check_id, directory,
                                           runtime / "engineering" / check_id / "prediction.cif")
    except FileNotFoundError:
        return _unverified("missing_artifact", check_id) if check_id else None
    except InvalidReceipt as exc:
        return _unverified(str(exc), check_id)
    except (OSError, ValueError, TypeError, RecursionError):
        return _unverified("invalid_or_unsafe_receipt", check_id)


def bionemo_download(runtime: Path, check_id: str) -> tuple[dict, bytes]:
    """Serve only a named verified engineering artifact, rechecking returned bytes."""
    if _identifier(check_id, SAFE_ID) is None:
        raise InvalidReceipt("receipt_identity")
    runtime = Path(runtime).absolute()
    with _runtime_directory(runtime) as root:
        with _directory("engineering", parent=root) as engineering:
            with _directory(check_id, parent=engineering) as directory:
                receipt = json.loads(_bytes("receipt.json", directory, MAX_RECEIPT_BYTES))
                public = _public_receipt(receipt, check_id, directory, runtime / "engineering" / check_id / "prediction.cif")
                if public.get("monomer_service_verified") is not True:
                    raise InvalidReceipt("not_verified")
                data = _bytes("prediction.cif", directory, MAX_ARTIFACT_BYTES)
                if hashlib.sha256(data).hexdigest() != public["artifacts"][0]["sha256"]:
                    raise InvalidReceipt("artifact_changed")
                return public, data
