"""A replacement backend can change its wire format without changing UI views."""

import json

import httpx

from frontend.ui.adapters import BackendSource, RunRequest
from frontend.ui.events import Event
from frontend.ui.state import RunState
from frontend.ui.stream import BackendContract, live_stream


def test_replacement_backend_maps_upload_config_catalog_and_activity(monkeypatch):
    calls = []

    def handle(request):
        calls.append(request.url.path)
        if request.url.path == "/v2/catalog":
            return httpx.Response(200, json={"workers": [{"id": "quality_control"}]})
        if request.url.path == "/v2/assets":
            assert b'name="attachments"' in request.read()
            assert b"observations.csv" in request.read()
            return httpx.Response(200, json={"assets": [{"key": "asset-7"}]})
        if request.url.path == "/v2/jobs":
            assert json.loads(request.read()) == {
                "prompt": "Check these observations",
                "assets": ["asset-7"],
                "team": {"specialists": ["quality_control"]},
            }
            return httpx.Response(200, json={"job": "job-9"})
        assert request.url.path == "/v2/activity/job-9"
        records = [
            {"event": "begin", "data": {"question": "Check these observations"}},
            {"event": "worker", "worker": "qc-1", "data": {}},
            {"event": "done", "worker": "qc-1", "data": {"verdict": "Review complete", "confidence": 0.6}},
        ]
        return httpx.Response(200, text="".join(f"data: {json.dumps(r)}\n\n" for r in records))

    contract = BackendContract(
        capabilities_path="/v2/catalog", upload_path="/v2/assets",
        start_path="/v2/jobs", events_path="/v2/activity/{run_id}",
        upload_field="attachments",
        start_payload=lambda question, ids, config: {"prompt": question, "assets": ids, "team": config},
        parse_file_ids=lambda body: [item["key"] for item in body["assets"]],
        parse_run_id=lambda body: body["job"],
        map_capabilities=lambda body: {"specialists": body["workers"]},
        map_event=lambda raw: Event(
            type={"begin": "run_started", "worker": "agent_spawned", "done": "run_complete"}[raw["event"]],
            run_id="job-9", agent_id=raw.get("worker"),
            agent_role="quality_control", payload=raw["data"],
        ),
    )
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        monkeypatch.setattr(httpx, "post", client.post)
        monkeypatch.setattr(httpx, "get", client.get)
        monkeypatch.setattr(httpx, "stream", client.stream)
        source = BackendSource(contract)
        assert source.capabilities("http://replacement.test") == {"specialists": [{"id": "quality_control"}]}
        state = RunState()
        for event in source.events(RunRequest(
            mode="Live", backend="http://replacement.test", question="Check these observations",
            uploads=[("observations.csv", b"batch,value\na,7\n")],
            config={"specialists": ["quality_control"]},
        )):
            state.apply(event)
    assert state.complete and state.verdict == "Review complete"
    assert state.agents["qc-1"].role == "quality_control"
    assert state.active_agents == 0 and not state.errors
    assert calls == ["/v2/catalog", "/v2/assets", "/v2/jobs", "/v2/activity/job-9"]


def test_bad_replacement_event_is_visible_and_does_not_drop_later_events(monkeypatch):
    contract = BackendContract(map_event=lambda raw: Event(type=raw["kind"]))
    with httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text='data: {"wrong": true}\n\ndata: {"kind": "run_complete"}\n\n')
    )) as client:
        monkeypatch.setattr(httpx, "stream", client.stream)
        events = list(live_stream("http://replacement.test", "job", contract=contract))
    assert [event.type for event in events] == ["error", "run_complete"]
    assert "Could not map backend event" in events[0].text
