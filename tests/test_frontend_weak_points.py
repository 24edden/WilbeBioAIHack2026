"""Weak-point UI consumes backend assessment; it never invents an assessment."""
import importlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

FRONTEND = Path(__file__).resolve().parents[1] / 'frontend'


@pytest.fixture
def ui(monkeypatch):
    monkeypatch.syspath_prepend(str(FRONTEND))
    return importlib.import_module('ui.events').Event, importlib.import_module('ui.state').RunState


def assessment():
    return {'status': 'assessed', 'items': [{
        'id': 'wp-1', 'category': 'evidence_gap', 'title': 'Limited independent evidence',
        'rationale': 'Only one specialist contributed a finding.',
        'next_evidence': 'Add an independent evidence source.', 'finding_ids': ['finding-1'],
        'sources': [{'source': 'patient.csv', 'line': 4}],
    }]}


def renderer(state):
    app = AppTest.from_string('''
import streamlit as st
from ui.state import RunState
from ui.components import render_weak_points
render_weak_points(st.session_state.get('test_run', RunState()))
''').run()
    app.session_state['test_run'] = state
    return app.run()


def test_assessment_payload_round_trips_without_inference_or_aliasing(ui):
    Event, RunState = ui
    payload = assessment()
    state = RunState()
    state.apply(Event(type='run_complete', payload={'verdict': 'A result', 'weak_points': payload}))
    assert state.weak_points == payload
    payload['items'][0]['title'] = 'Mutated elsewhere'
    assert state.weak_points['items'][0]['title'] == 'Limited independent evidence'
    app = renderer(state)
    assert not app.exception
    assert any('1 weak point reported' in caption.value for caption in app.caption)
    assert any('Limited independent evidence' in item.value for item in app.markdown)
    assert app.code[0].value == 'finding-1'
    assert 'patient.csv' in app.json[0].value


@pytest.mark.parametrize('payload', [{}, {'weak_points': None}, {'weak_points': {'status': 'assessed', 'items': ['invalid']}}])
def test_old_or_malformed_assessment_is_explicitly_not_assessed(ui, payload):
    Event, RunState = ui
    state = RunState()
    state.apply(Event(type='run_complete', payload=payload))
    assert state.weak_points == {'status': 'not_assessed', 'items': []}
    app = renderer(state)
    assert not app.exception
    assert any('Not assessed' in info.value for info in app.info)
    assert not app.code and not app.json


def test_assessed_empty_is_distinct_from_missing_assessment(ui):
    Event, RunState = ui
    state = RunState()
    state.apply(Event(type='run_complete', payload={'weak_points': {'status': 'assessed', 'items': []}}))
    app = renderer(state)
    assert any('No weak points were returned' in info.value for info in app.info)
    assert not any('Not assessed' in info.value for info in app.info)

def test_real_demo_assessment_reaches_state_and_results_without_remapping(ui):
    _, RunState = ui
    adapters = importlib.import_module('ui.adapters')
    request = adapters.RunRequest(mode='Demo', question='Why did treatment fail?', sample=True,
                                  config={'specialists': ['clinical']})
    events = list(adapters.DemoSource(mock_latency_scale=0).events(request))
    completed = next(event for event in events if event.type == 'run_complete')
    state = RunState()
    for event in events:
        state.apply(event)
    assert state.complete
    assert state.weak_points == completed.payload['weak_points']
    assert state.weak_points['status'] == 'assessed'
    assert any(item['id'] == 'limited-corroboration' for item in state.weak_points['items'])
    app = renderer(state)
    assert not app.exception
    assert any(f"{len(state.weak_points['items'])} weak points reported" in caption.value for caption in app.caption)
