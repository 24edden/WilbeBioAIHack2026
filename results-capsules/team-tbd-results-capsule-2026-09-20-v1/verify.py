"""Verify a frozen Team TBD capsule offline using Python's standard library."""
import argparse
import hashlib
import json
from pathlib import Path
import re

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(value):
    raw = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return sha(raw.encode())

def local(root, relative):
    if (not isinstance(relative, str) or not relative or relative.startswith("/") or "\\" in relative
            or ":" in relative or re.search(r"[\x00-\x1f]", relative)
            or any(p in {"", ".", ".."} for p in relative.split("/"))):
        raise ValueError("Unsafe relative file path")
    path = root / relative
    if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file():
        raise ValueError("Missing file or symlink in capsule")
    return path

def verify(root):
    root = Path(root).resolve()
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["schema_version"] == "team-tbd-results-capsule/1.0", "Unsupported version"
    paths = [f["path"] for f in manifest["files"]]
    assert len(paths) == len(set(paths)), "Duplicate file paths"
    indexed = {f["path"]: f for f in manifest["files"]}
    for rec in indexed.values():
        raw = local(root, rec["path"]).read_bytes()
        assert len(raw) == rec["bytes"] and sha(raw) == rec["sha256"], "File integrity mismatch: " + rec["path"]
    results = json.loads(local(root, manifest["entrypoints"]["results"]).read_text())
    assert results["package_id"] == manifest["package_id"], "Package identity mismatch"
    views = {r["run_id"]: r for r in results["runs"]}
    assert len(views) == len(results["runs"]) == len(manifest["runs"]) == manifest["counts"]["runs"], "Run count mismatch"
    assert set(results["featured_run_ids"]).issubset(views), "Missing featured run"
    for item in manifest["runs"]:
        for key in ("raw_export_path", "view_path", "report_path", "event_path"):
            assert item[key] in indexed, "Run resource missing from checksum inventory"
        packet = json.loads(local(root, item["raw_export_path"]).read_text()); run = packet["run"]
        assert run["id"] == item["run_id"], "Run identity mismatch"
        assert packet["content_sha256"] == digest({"run": run, "case_manifest": packet["case_manifest"]}) == item["source_content_sha256"], "Original export mismatch"
        assert digest(run["hypothesis"]["text"]) == run["hypothesis"]["sha256"], "Hypothesis mismatch"
        evidence = {e["id"] for e in run.get("evidence", [])}
        for i, decision in enumerate(run.get("decisions", []), 1):
            assert decision["version"] == i and decision["sha256"] == digest({k: v for k, v in decision.items() if k != "sha256"}), "Decision mismatch"
            assert all(set(c.get("evidence_ids", [])).issubset(evidence) for c in decision.get("claims", [])), "Missing claim evidence"
        decisions = {d["version"]: d for d in run.get("decisions", [])}
        for field in ("research_briefs", "sequence_discoveries"):
            for index, value in enumerate(run.get(field, []), 1):
                assert value["version"] == index and value["source_decision_sha256"] == decisions[value["source_decision_version"]]["sha256"], "Addendum source mismatch"
                assert value["sha256"] == digest({k: v for k, v in value.items() if k != "sha256"}), "Addendum digest mismatch"
                for seq in value.get("sequences", []):
                    assert len(seq["sequence"]) == seq["length"] and sha(seq["sequence"].encode()) == seq["sequence_sha256"], "Sequence mismatch"
        view = json.loads(local(root, item["view_path"]).read_text())
        assert view == views[run["id"]], "Bulk/per-run view mismatch"
        for key in ("decisions", "handoffs", "research_briefs", "sequence_discoveries", "usage", "error", "evidence"):
            assert view[key] == run.get(key, [] if key not in {"usage", "error"} else ({} if key == "usage" else None)), "View changed original field: " + key
        assert view["question"] == run["hypothesis"] and view["status"] == run["status"], "View hypothesis/status mismatch"
        events = [json.loads(line) for line in local(root, item["event_path"]).read_text().splitlines()]
        assert events == run.get("events", []), "Event sequence changed"
    artifact_index = json.loads(local(root, manifest["entrypoints"]["artifact_index"]).read_text())
    assert artifact_index["package_id"] == manifest["package_id"], "Artifact index identity mismatch"
    for rec in artifact_index["artifacts"]:
        assert rec["run_id"] in views and rec in views[rec["run_id"]]["artifacts"], "Artifact run association mismatch"
        for entry in [rec] + ([rec["preview"]] if rec.get("preview") else []):
            listed = indexed[entry["path"]]
            assert listed["sha256"] == entry["sha256"] and listed["bytes"] == entry["bytes"], "Artifact receipt mismatch"
    assert len(artifact_index["artifacts"]) == manifest["counts"]["artifact_records"], "Artifact count mismatch"
    allowed = set(paths) | {"manifest.json", "SHA256SUMS"}
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    assert actual.issubset(allowed), "Unindexed files in package"
    if (root / "SHA256SUMS").exists():
        sums = {}
        for line in (root / "SHA256SUMS").read_text().splitlines():
            checksum, relative = line.split("  ", 1)
            assert relative not in sums, "Duplicate checksum entry"
            sums[relative] = checksum
            assert sha(local(root, relative).read_bytes()) == checksum, "Checksum mismatch"
        assert set(sums) == actual - {"SHA256SUMS"}, "Checksum inventory mismatch"
    return {"status": "verified", "package_id": manifest["package_id"], "files": len(indexed), "runs": len(views), "external_calls": 0}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path, nargs="?", default=Path(__file__).resolve().parent)
    print(json.dumps(verify(parser.parse_args().root)))
