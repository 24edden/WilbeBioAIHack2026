"""End-to-end service check. Live is the default; no silent offline fallback."""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8080")
    parser.add_argument("--mode", choices=["live", "demo"], default="live")
    parser.add_argument("--case", default="cd19-car-t")
    parser.add_argument("--output", type=Path, default=Path("runtime/smoke-export.json"))
    args = parser.parse_args()

    def request(path, body=None):
        req = urllib.request.Request(args.url.rstrip("/")+path,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=150) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"HTTP {exc.code}: {exc.read().decode()}")

    health = request("/api/health")
    if not health["worker_alive"]:
        raise SystemExit("Worker is not running.")
    if args.mode == "live" and health["capabilities"]["rosalind"]["status"] != "verified":
        # Explicit invocation of this live smoke test authorizes its small probe.
        probe = request("/api/capabilities/probe", {"provider": "rosalind"})
        if probe["status"] != "verified":
            raise SystemExit("Selected-model gate failed: " + probe.get("detail", probe["status"]))
    case = next(item for item in request("/api/cases") if item["id"] == args.case)
    run = request("/api/runs", {"case_id": case["id"], "hypothesis": case["hypothesis"],
                               "source_name": case["hypothesis_source"]["name"], "mode": args.mode,
                               "idempotency_key": uuid.uuid4().hex})
    print(f"Run {run['id']} started in {args.mode} mode.", flush=True)
    started = time.monotonic()
    last_event = 0
    while run["status"] in ("queued", "running"):
        for event in run["events"]:
            if event["id"] > last_event:
                last_event = event["id"]
                print(f"{event['agent']}: {event['title']}", flush=True)
        if time.monotonic()-started > 1260:
            raise SystemExit("Smoke test stopped waiting; inspect the persisted run. No repeat submitted.")
        time.sleep(.5)
        run = request("/api/runs/"+run["id"])
    exported = request(f"/api/runs/{run['id']}/export.json")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(exported, indent=2))
    print(json.dumps({"run_id": run["id"], "status": run["status"], "mode": run["mode"],
                      "usage": run["usage"], "evidence": len(run["evidence"]), "decisions": len(run["decisions"]),
                      "export": str(args.output)}))
    if run["status"] != "completed":
        raise SystemExit(run.get("error") or "Run did not complete.")
    if args.mode == "live" and run["usage"]["model_calls"] == 0:
        raise SystemExit("Live run has no observed model requests.")


if __name__ == "__main__":
    main()
