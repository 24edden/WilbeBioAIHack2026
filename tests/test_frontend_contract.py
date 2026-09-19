"""Exercise the real API event stream through the frontend's state reducer."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from frontend.ui.events import Event
from frontend.ui.state import RunState


@pytest.mark.parametrize(
    "question,use_sample,abstained",
    [
        ("Why did this patient fail?", True, False),
        ("Did the patient fail because of MTHFR C677T?", True, False),
        ("Why did this patient fail?", False, True),
    ],
)
def test_backend_stream_renders_the_same_verdict_as_report(question, use_sample, abstained):
    with TestClient(app) as client:
        file_ids = []
        if use_sample:
            response = client.post("/demo/sample-patient")
            response.raise_for_status()
            file_ids = [item["file_id"] for item in response.json()["files"]]
        response = client.post(
            "/investigate", json={"question": question, "file_ids": file_ids}
        )
        response.raise_for_status()
        run_id = response.json()["run_id"]
        state = RunState()
        with client.stream("GET", f"/events/{run_id}") as stream:
            stream.raise_for_status()
            for line in stream.iter_lines():
                if line.startswith("data:"):
                    event = Event.from_json(line[5:].strip())
                    assert event.known_type
                    state.apply(event)

        report = client.get(f"/report/{run_id}").json()
        assert state.complete and not state.errors
        assert state.run_id == run_id
        assert state.question == question
        assert state.verdict == report["verdict"]["answer"]
        assert state.confidence == report["verdict"]["confidence"]
        assert state.abstained == report["verdict"]["abstained"] == abstained
        assert state.active_agents == 0
        assert state.conversation
        assert all(finding.provenance for finding in state.findings)
