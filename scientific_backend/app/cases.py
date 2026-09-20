"""Versioned scientific case packs with checked source bytes.

The data and curated demonstration decisions are deliberately separate from live
model output. Public measurements stay measured in either execution mode; a
curated decision is never represented as a recorded model call.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1] / "casepacks"
CASE_IDS = ("cart-discovery", "cd19-car-t", "alk-l1196m", "bcma-gse164551")


class SourceIntegrityError(ValueError):
    """A pinned input is missing or its bytes have changed."""


def verify_sources(root: Path | None = None) -> dict:
    """Verify the compact bundle before giving evidence to an investigator."""
    root = Path(root or CASE_ROOT).resolve()
    manifest = json.loads((root / "MANIFEST.json").read_text())
    checked = []
    for record in manifest["source_files"]:
        path = (root / record["path"]).resolve()
        if not path.is_relative_to(root):
            raise SourceIntegrityError("Source path escapes the case pack")
        if not path.is_file():
            raise SourceIntegrityError("Pinned source missing: " + record["path"])
        data = path.read_bytes()
        if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise SourceIntegrityError("Pinned source changed: " + record["path"])
        checked.append(record["path"])
    return {"status": "verified", "source_count": len(checked), "sources": checked}


def get_case(case_id: str) -> dict:
    """Return a fresh case dictionary; refuse unknown IDs and altered evidence."""
    if case_id not in CASE_IDS:
        raise KeyError(case_id)
    integrity = verify_sources()
    manifest = json.loads((CASE_ROOT / "MANIFEST.json").read_text())
    if case_id == "cart-discovery":
        from .data_catalog import discovery_case
        case = discovery_case()
        case["source_integrity"] = {**case["source_integrity"], **integrity, "raw_datasets": "catalog-unverified; selected files are hash-verified before analysis"}
        from .gse28460_analysis import source_manifest
        case["source_manifest"] = manifest["source_files"] + source_manifest()
        return case
    contents = (CASE_ROOT / (case_id + ".json")).read_bytes()
    expected = next(item["sha256"] for item in manifest["case_files"] if item["path"] == case_id + ".json")
    if hashlib.sha256(contents).hexdigest() != expected:
        raise SourceIntegrityError("Derived case packet changed: " + case_id)
    case = json.loads(contents)
    if case["id"] != case_id:
        raise SourceIntegrityError("Case identity does not match its selected ID")
    known_ids = {item["id"] for item in case["evidence"]}
    if case["evidence_count"] != len(known_ids) or len(known_ids) != len(case["evidence"]):
        raise SourceIntegrityError("Evidence identity/count mismatch")
    for claim in case["demo_decision"]["claims"]:
        if not claim["evidence_ids"] or not set(claim["evidence_ids"]).issubset(known_ids):
            raise SourceIntegrityError("Curated claim has unresolved evidence references")
    case["source_integrity"] = integrity
    case["source_manifest"] = manifest["source_files"]
    if case_id == "cd19-car-t":
        from .gse28460_analysis import source_manifest
        case["source_manifest"] = case["source_manifest"] + source_manifest()
    return case


def list_cases() -> list[dict]:
    """Expose selection cards without repeating every source record."""
    fields = ("id", "title", "subtitle", "hypothesis", "hypothesis_source", "description", "evidence_count", "readiness", "limitations", "data_mode")
    return [{key: case[key] for key in fields} for case in (get_case(cid) for cid in CASE_IDS)]
