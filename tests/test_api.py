import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def read_stream(client, run_id, limit=400):
    """Consume the SSE stream until the run completes."""
    events = []
    with client.stream("GET", f"/events/{run_id}") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            events.append(json.loads(line[len("data: "):]))
            if events[-1]["type"] == "run_complete" or len(events) >= limit:
                break
    return events


def test_health_reports_the_run_mode(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["run_mode"] == "mock"


def test_sample_patient_loads_three_parsed_files(client):
    files = client.post("/demo/sample-patient").json()["files"]
    assert {f["kind"] for f in files} == {"vcf", "labs", "notes"}
    assert all(f["n_records"] > 0 for f in files)


def test_upload_parses_and_counts_records(client):
    response = client.post(
        "/upload",
        files=[
            ("files", ("labs.csv", "test,value,ref_low,ref_high\nCEA,9,0,5\n", "text/csv")),
            ("files", ("notes.txt", "Progression on treatment.", "text/plain")),
        ],
    )
    assert response.status_code == 200
    kinds = {f["kind"]: f["n_records"] for f in response.json()["files"]}
    assert kinds == {"labs": 1, "notes": 1}


def test_investigate_rejects_an_empty_question(client):
    assert client.post("/investigate", json={"question": "  ", "file_ids": []}).status_code == 400


def test_investigate_rejects_unknown_files(client):
    response = client.post(
        "/investigate", json={"question": "Why did this patient fail?", "file_ids": ["nope"]}
    )
    assert response.status_code == 404


def test_unknown_run_is_a_404(client):
    assert client.get("/events/does-not-exist").status_code == 404
    assert client.get("/report/does-not-exist").status_code == 404


def test_end_to_end_upload_investigate_stream_report(client):
    file_ids = [f["file_id"] for f in client.post("/demo/sample-patient").json()["files"]]

    run_id = client.post(
        "/investigate",
        json={"question": "Why did this patient fail?", "file_ids": file_ids},
    ).json()["run_id"]

    events = read_stream(client, run_id)
    assert events[0]["type"] == "run_started"
    assert events[-1]["type"] == "run_complete"
    assert {e["run_id"] for e in events} == {run_id}

    # The schema the frontend renders from.
    for event in events:
        assert set(event) == {"type", "ts", "run_id", "agent_id", "agent_role",
                              "parent_id", "payload"}
    assert events == sorted(events, key=lambda e: e["ts"])

    report = client.get(f"/report/{run_id}").json()
    assert report["status"] == "complete"
    assert report["verdict"]["abstained"] is False
    assert "KRAS" in report["verdict"]["answer"]
    assert report["findings"] and all(f["provenance"] for f in report["findings"])

    logged = client.get(f"/events/{run_id}/log").json()
    assert [e["ts"] for e in logged] == [e["ts"] for e in events]

    listed = client.get("/runs").json()
    assert listed[0]["run_id"] == run_id and listed[0]["status"] == "complete"


def test_a_late_subscriber_still_sees_the_whole_run(client):
    file_ids = [f["file_id"] for f in client.post("/demo/sample-patient").json()["files"]]
    run_id = client.post(
        "/investigate",
        json={"question": "Why did this patient fail?", "file_ids": file_ids},
    ).json()["run_id"]

    first = read_stream(client, run_id)      # drains the run to completion
    replay = read_stream(client, run_id)     # connects after it is over
    assert [e["ts"] for e in replay] == [e["ts"] for e in first]
