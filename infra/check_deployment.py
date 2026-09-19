"""Exercise the deployed mock API with bundled synthetic evidence.

Run inside the UI container: python infra/check_deployment.py
Or pass a reachable API URL: python infra/check_deployment.py http://127.0.0.1:8000
"""
import json
import os
from pathlib import Path
import sys

import httpx


def check(base_url: str) -> None:
    root = Path(__file__).resolve().parents[1]
    with httpx.Client(base_url=base_url, timeout=45) as client:
        response = client.get("/capabilities")
        response.raise_for_status()
        capabilities = response.json()
        assert capabilities["run_mode"] == "mock", "Deployment check only permits mock providers"
        assert capabilities["cancellation_supported"] is True
        files = [("files", (path.name, path.read_bytes())) for path in (
            root / "samples/patient-0.vcf", root / "samples/patient-0-labs.csv",
            root / "samples/patient-0-notes.txt")]
        response = client.post("/upload", files=files)
        response.raise_for_status()
        file_ids = [item["file_id"] for item in response.json()["files"]]
        assert len(file_ids) == 3
        response = client.post("/investigate", json={
            "question": "Why did this patient's treatment fail?",
            "file_ids": file_ids,
            "config": {"specialists": ["genomics", "clinical", "literature"]},
        })
        response.raise_for_status()
        run_id = response.json()["run_id"]
        events = []
        with client.stream("GET", f"/events/{run_id}") as stream:
            stream.raise_for_status()
            for line in stream.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))
        assert events and events[-1]["type"] == "run_complete"
        assert not any(event["type"] == "error" for event in events), "Run emitted an error"
        response = client.get(f"/report/{run_id}")
        response.raise_for_status()
        report = response.json()
        assert report["status"] == "complete"
        assert report["run_mode"] == "mock"
        assert report["findings"] and report["verdict"]["answer"]
        terminal = events[-1]["payload"]
        assert terminal["metrics"] == report["metrics"]
        assert terminal["weak_points"] == report["weak_points"]
        assert terminal["status"] == report["status"]
        assert 0 < report["metrics"]["variant_peak_concurrency"] <= capabilities["execution_limits"]["variant_concurrency"]
        # Exercise a real server cancellation, including a repeat request.
        response = client.post("/investigate", json={"question": "Why did treatment fail?", "file_ids": file_ids})
        response.raise_for_status()
        cancelled_id = response.json()["run_id"]
        response = client.post(f"/runs/{cancelled_id}/cancel")
        response.raise_for_status()
        assert response.json()["status"] == "cancelled"
        repeated = client.post(f"/runs/{cancelled_id}/cancel")
        repeated.raise_for_status()
        assert repeated.json() == response.json()
        cancelled_report = client.get(f"/report/{cancelled_id}")
        cancelled_report.raise_for_status()
        assert cancelled_report.json()["status"] == "cancelled"
        cancelled_events = client.get(f"/events/{cancelled_id}/log")
        cancelled_events.raise_for_status()
        endings = [event for event in cancelled_events.json() if event["type"] == "run_complete"]
        assert len(endings) == 1 and endings[0]["payload"]["cancelled"] is True

        response = client.post("/investigate", json={
            "question": "Evaluate this idea: use a shared evidence checklist to improve reproducibility.",
            "file_ids": [], "config": {"task_mode": "auto"},
        })
        response.raise_for_status()
        review_id = response.json()["run_id"]
        review_events = []
        with client.stream("GET", f"/events/{review_id}") as stream:
            stream.raise_for_status()
            for line in stream.iter_lines():
                if line.startswith("data: "):
                    review_events.append(json.loads(line[6:]))
        response = client.get(f"/report/{review_id}")
        response.raise_for_status()
        review = response.json()
        assert review["status"] == "complete" and review["config"]["task_mode"] == "idea_review"
        assert review["discussion"] == review_events[-1]["payload"]["discussion"]
        assert [item["phase"] for item in review["discussion"]] == ["input_inventory", "opening", "challenge", "revision", "summary"]
        assert not review["findings"], "Proposal arguments must not become scientific evidence"
        roles = {event["agent_role"] for event in review_events if event["type"] == "agent_spawned"}
        assert {"research", "supporter", "challenger", "critic"} <= roles
        assert all(event["payload"].get("skills") for event in review_events if event["type"] == "agent_spawned")
        print(json.dumps({"status": "passed", "mode": "mock", "uploaded_files": len(file_ids),
                          "events": len(events), "findings": len(report["findings"]),
                          "run_id": run_id, "cancellation": "passed", "metrics": report["metrics"],
                          "idea_review": "passed", "review_run_id": review_id}))


if __name__ == "__main__":
    check(sys.argv[1] if len(sys.argv) > 1 else os.getenv("TRACE_BACKEND_URL", "http://api:8000"))
