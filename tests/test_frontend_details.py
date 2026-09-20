"""Large supporting records are prepared only when the scientist requests them."""
import importlib
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


class TrackedEvents(list):
    def __init__(self, events):
        super().__init__(events)
        self.reads = 0

    def __iter__(self):
        self.reads += 1
        return super().__iter__()


@pytest.fixture
def ui(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "frontend"))
    return (importlib.import_module("ui.events"), importlib.import_module("ui.state"),
            importlib.import_module("ui.components"))


def render(function, state, module="components"):
    app = AppTest.from_string(f"""
import streamlit as st
from ui.{module} import {function}
if 'test_run' in st.session_state:
    {function}(st.session_state.test_run)
""").run()
    app.session_state["test_run"] = state
    return app.run()


def test_closed_raw_records_do_no_preparation_and_opening_preserves_full_record(ui):
    events, states, _ = ui
    state = states.RunState(run_id="large-run")
    state.raw = TrackedEvents(events.Event(type="tool_result", ts=index,
                               payload={"record": index, "text": "evidence " * 128})
                               for index in range(1000))
    app = render("render_raw_events", state, "layout")
    assert not app.exception and not app.json
    assert state.raw.reads == 0

    app.session_state["result_raw_events:large-run"] = True
    app.run()
    assert not app.exception and state.raw.reads == 1
    records = json.loads(app.json[0].value)
    assert len(records) == 1000
    assert records[-1]["payload"] == {"record": 999, "text": "evidence " * 128}

    app.session_state["result_raw_events:large-run"] = False
    app.run()
    assert not app.json and state.raw.reads == 1

    app.session_state["test_run"] = states.RunState(run_id="next-run", raw=TrackedEvents(state.raw))
    app.run()
    assert not app.exception and not app.json
    assert app.session_state["test_run"].raw.reads == 0


def test_small_provenance_is_ready_locally_and_large_provenance_is_loaded_independently(ui, monkeypatch):
    _, states, components = ui
    visited = []
    original = components._provenance_line
    monkeypatch.setattr(components, "_provenance_line", lambda item: (visited.append(item["source"]), original(item))[1])
    state = states.RunState(run_id="sources", findings=[
        states.Finding("a", "research", "Small result", .9, [{"source": "small.csv"}]),
        states.Finding("b", "research", "Large result B", .8, [{"source": f"b-{i}.csv"} for i in range(13)]),
        states.Finding("c", "research", "Large result C", .7, [{"source": f"c-{i}.csv"} for i in range(13)]),
    ])
    app = render("render_findings", state)
    assert not app.exception
    assert visited == ["small.csv"]
    assert any("Large result C" in item.value for item in app.markdown)
    assert any("small.csv" in item.value for item in app.markdown)
    assert not any("b-0.csv" in item.value or "c-0.csv" in item.value for item in app.markdown)

    app.session_state["finding_sources:sources:1"] = True
    app.run()
    assert not app.exception
    assert any("b-0.csv" in item.value for item in app.markdown)
    assert not any("c-0.csv" in item.value for item in app.markdown)


def test_large_weak_point_references_defer_records_without_hiding_the_rationale(ui):
    _, states, _ = ui
    state = states.RunState(run_id="weak", weak_points={"status": "assessed", "items": [{
        "title": "Evidence is inconsistent", "rationale": "The results disagree.",
        "next_evidence": "Check the comparison group.", "finding_ids": ["finding-1"],
        "sources": [{"source": f"record-{index}"} for index in range(13)],
    }]})
    app = render("render_weak_points", state)
    assert not app.exception and not app.json and not app.code
    assert any("The results disagree." in item.value for item in app.markdown)
    assert any("Check the comparison group." in item.value for item in app.markdown)
    app.session_state["weak_point_sources:weak:1"] = True
    app.run()
    assert not app.exception and app.code[0].value == "finding-1"
    assert len(json.loads(app.json[0].value)) == 13
