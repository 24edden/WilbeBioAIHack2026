import hashlib
import argparse
import asyncio
import json
import sqlite3
from pathlib import Path

from .config import RUNTIME
from .store import Store, digest


def main():
    parser = argparse.ArgumentParser(description="Rosalind Investigation service and verification")
    sub = parser.add_subparsers(dest="command", required=True)
    server = sub.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8080)
    sub.add_parser("worker")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--live-model", action="store_true")
    doctor.add_argument("--live-nim", action="store_true")
    replay = sub.add_parser("verify-export")
    replay.add_argument("path", type=Path)
    backup = sub.add_parser("backup")
    backup.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("app.main:app", host=args.host, port=args.port, workers=1)
    elif args.command == "worker":
        from .worker import main as worker_main
        asyncio.run(worker_main())
    elif args.command == "doctor":
        from .cases import list_cases, get_case
        from .providers import capabilities, probe
        cases = list_cases()
        for case in cases:
            get_case(case["id"])
        store = Store()
        with store.connect() as db:
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        result = {"database": integrity, "runtime": str(RUNTIME), "casepacks": len(cases), "capabilities": capabilities()}
        if args.live_model:
            result["model_probe"] = asyncio.run(probe("rosalind"))
        if args.live_nim:
            result["nim_probe"] = asyncio.run(probe("bionemo"))
        print(json.dumps(result, indent=2))
    elif args.command == "verify-export":
        packet = json.loads(args.path.read_text())
        if packet["content_sha256"] != digest({"run": packet["run"], "case_manifest": packet["case_manifest"]}):
            raise SystemExit("Export checksum mismatch")
        run = packet["run"]
        if run["hypothesis"]["sha256"] != digest(run["hypothesis"]["text"]):
            raise SystemExit("Hypothesis checksum mismatch")
        evidence_ids = {e["id"] for e in run["evidence"]}
        for index, decision in enumerate(run["decisions"], 1):
            decision_hash = decision["sha256"]
            body = {k: v for k, v in decision.items() if k != "sha256"}
            if decision_hash != digest(body) or decision["version"] != index:
                raise SystemExit("Decision checksum or version mismatch")
            if any(not set(c["evidence_ids"]).issubset(evidence_ids) for c in decision["claims"]):
                raise SystemExit("Missing evidence reference")
        decisions = {item["version"]: item for item in run["decisions"]}
        for index, brief in enumerate(run.get("research_briefs", []), 1):
            source = decisions.get(brief.get("source_decision_version"))
            if (brief.get("sha256") != digest({key: value for key, value in brief.items() if key != "sha256"})
                    or brief.get("version") != index or not source
                    or source["sha256"] != brief.get("source_decision_sha256")):
                raise SystemExit("Research interpretation checksum, version or source decision mismatch")
        for index, discovery in enumerate(run.get("sequence_discoveries", []), 1):
            source = decisions.get(discovery.get("source_decision_version"))
            if (discovery.get("sha256") != digest({key: value for key, value in discovery.items() if key != "sha256"})
                    or discovery.get("version") != index or not source or source["sha256"] != discovery.get("source_decision_sha256")):
                raise SystemExit("Sequence discovery checksum, version or source decision mismatch")
            for sequence in discovery.get("sequences", []):
                if sequence.get("sequence_sha256") != hashlib.sha256(sequence["sequence"].encode()).hexdigest() or sequence["length"] != len(sequence["sequence"]):
                    raise SystemExit("Discovered sequence checksum or length mismatch")
        print(json.dumps({"status": "verified", "run_id": run["id"], "mode": run["mode"], "decisions": len(run["decisions"]), "external_calls": 0}))
    elif args.command == "backup":
        if args.path.exists():
            raise SystemExit("Choose a new backup path; existing files are not overwritten.")
        args.path.parent.mkdir(parents=True, exist_ok=True)
        store = Store()
        with store.connect() as source, sqlite3.connect(args.path) as target:
            source.backup(target)
        print(f"Consistent SQLite backup saved to {args.path}. Copy runtime/artifacts alongside it for a full restore.")


if __name__ == "__main__":
    main()
