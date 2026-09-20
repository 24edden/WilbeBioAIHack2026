"""Navigation must preserve a draft without submitting it or mutating a past run."""

from copy import deepcopy
import importlib
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest


FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


@pytest.fixture
def wizard(monkeypatch):
    monkeypatch.setenv("TRACE_START_SCREEN", "classic")
    monkeypatch.syspath_prepend(str(FRONTEND))
    adapters = importlib.import_module("ui.adapters")
    event_type = importlib.import_module("ui.events").Event
    st.cache_data.clear()

    class Source:
        requests = None
        failure = False
        incomplete = False

        def __init__(self):
            self.requests = []

        def capabilities(self, backend):
            return {
                "run_mode": "mock", "model_overrides_supported": False,
                "specialist_roles": [{"id": "clinical", "label": "Clinical"},
                                     {"id": "literature", "label": "Literature"}],
                "required_roles": ["orchestrator", "critic"],
                "defaults": {"specialists": ["clinical", "literature"]},
            }

        def events(self, request):
            self.requests.append(request)
            if self.failure:
                raise RuntimeError("Backend unavailable")
            yield event_type(type="run_started", run_id="flow-test", ts=1000,
                             payload={"question": request.question, "config": deepcopy(request.config)})
            yield event_type(type="agent_spawned", run_id="flow-test", ts=1100,
                             agent_id="clinical-1", agent_role="clinical")
            if not self.incomplete:
                yield event_type(type="run_complete", run_id="flow-test", ts=1200,
                                 payload={"verdict": "Review complete", "confidence": 0.6})

    source = Source()
    monkeypatch.setattr(adapters, "source_for", lambda mode: source)
    app = AppTest.from_file(str(FRONTEND / "app.py"), default_timeout=10).run()
    assert not app.exception
    yield app, source
    st.cache_data.clear()


def advance_with_sample(app):
    app.radio(key="draft_mode").set_value("Live").run()
    app.toggle(key="draft_sample").set_value(True).run()
    app.button(key="evidence_next").click().run()
    assert not app.exception


def test_setup_reveals_one_stage_and_back_keeps_question_and_agents(wizard):
    app, source = wizard
    assert app.session_state["stage"] == "evidence"
    assert len(app.text_area) == 1 and not app.multiselect
    assert not next(e for e in app.expander if e.label == "Research question").proto.expanded
    assert not source.requests
    advance_with_sample(app)
    assert app.session_state["stage"] == "question"
    app.text_area(key="draft_question").set_value("Which observations support this hypothesis?")
    app.multiselect(key="draft_specialists").set_value(["clinical"])
    app.button(key="question_back").click().run()
    assert app.session_state["stage"] == "evidence"
    assert len(app.text_area) == 1 and not app.multiselect
    assert not next(e for e in app.expander if e.label == "Research question").proto.expanded
    assert app.toggle(key="draft_sample").value
    app.button(key="evidence_next").click().run()
    assert app.text_area(key="draft_question").value == "Which observations support this hypothesis?"
    assert app.multiselect(key="draft_specialists").value == ["clinical"]
    assert not source.requests and not app.exception


def test_start_submits_once_and_edit_does_not_change_previous_run(wizard):
    app, source = wizard
    advance_with_sample(app)
    app.text_area(key="draft_question").set_value("Original research question")
    app.multiselect(key="draft_specialists").set_value(["clinical"])
    app.button(key="start_run").click().run()
    assert app.session_state["stage"] == "results"
    assert len(source.requests) == 1
    assert len(app.text_area) == 1 and not app.multiselect
    assert not next(e for e in app.expander if e.label == "Research question").proto.expanded
    original = source.requests[0]
    assert original.question == "Original research question"
    assert original.config["specialists"] == ["clinical"]
    app.run()
    assert len(source.requests) == 1
    app.button(key="results_edit").click().run()
    assert app.session_state["stage"] == "question"
    app.text_area(key="draft_question").set_value("Revised research question").run()
    app.multiselect(key="draft_specialists").set_value(["literature"]).run()
    assert original.question == "Original research question"
    assert original.config["specialists"] == ["clinical"]
    assert app.session_state["run"].question == "Original research question"
    assert len(source.requests) == 1 and not app.exception
    # Navigation can arrive in the same rerun as a final uncommitted text edit.
    app.text_area(key="draft_question").set_value("Keep the latest edit")
    app.button(key="view_previous_result").click().run()
    assert app.session_state["stage"] == "results"
    app.button(key="results_edit").click().run()
    assert app.text_area(key="draft_question").value == "Keep the latest edit"
    assert len(source.requests) == 1


@pytest.mark.parametrize("failure,incomplete", [(True, False), (False, True)])
def test_failed_or_truncated_run_preserves_draft_and_requires_explicit_retry(wizard, failure, incomplete):
    app, source = wizard
    advance_with_sample(app)
    app.text_area(key="draft_question").set_value("Keep this question")
    source.failure, source.incomplete = failure, incomplete
    app.button(key="start_run").click().run()
    assert app.session_state["stage"] == "investigation"
    assert app.session_state["run"].errors
    assert len(source.requests) == 1
    app.run()
    assert len(source.requests) == 1
    app.button(key="investigation_edit").click().run()
    assert app.text_area(key="draft_question").value == "Keep this question"
    assert not app.exception


def test_missing_evidence_cannot_advance(wizard):
    app, source = wizard
    app.radio(key="draft_mode").set_value("Live").run()
    app.button(key="evidence_next").click().run()
    assert app.session_state["stage"] == "evidence"
    assert not source.requests
    assert not app.exception


def test_saved_upload_bytes_survive_hidden_picker_and_can_be_removed(wizard):
    app, source = wizard
    app.radio(key="draft_mode").set_value("Live").run()
    # AppTest cannot choose a local file. Seed the same saved bytes the uploader
    # callback captures, then exercise real widget cleanup across stage changes.
    files = [("measurements.csv", b"batch,value\na,7\n")]
    app.session_state["draft"]["uploads"] = files
    app.run()
    app.button(key="evidence_next").click().run()
    assert app.session_state["stage"] == "question"
    app.button(key="question_back").click().run()
    assert app.session_state["draft"]["uploads"] == files
    app.button(key="remove_files").click().run()
    assert app.session_state["draft"]["uploads"] == []
    app.button(key="evidence_next").click().run()
    assert app.session_state["stage"] == "evidence"
    assert not source.requests and not app.exception

def test_section_headers_gate_future_steps_and_preserve_draft(wizard):
    app, source = wizard
    assert '(current)' in app.button(key='nav_evidence').label
    assert app.button(key='nav_investigation').disabled
    assert app.button(key='nav_results').disabled
    app.radio(key='draft_mode').set_value('Live').run()
    assert app.button(key='nav_question').disabled
    files = [('measurements.csv', b'batch,value\na,7\n')]
    app.session_state['draft']['uploads'] = files
    app.run()
    app.button(key='nav_question').click().run()
    assert app.session_state['stage'] == 'question'
    assert '(current)' in app.button(key='nav_question').label
    app.text_area(key='draft_question').set_value('Preserve my latest edit')
    app.multiselect(key='draft_specialists').set_value(['literature'])
    app.button(key='nav_evidence').click().run()
    assert app.session_state['draft']['uploads'] == files
    app.button(key='nav_question').click().run()
    assert app.text_area(key='draft_question').value == 'Preserve my latest edit'
    assert app.multiselect(key='draft_specialists').value == ['literature']
    assert not source.requests and not app.exception


def test_completed_investigation_header_opens_activity_without_retry_or_submission(wizard):
    app, source = wizard
    advance_with_sample(app)
    app.button(key='start_run').click().run()
    assert app.session_state['stage'] == 'results'
    assert not app.button(key='nav_investigation').disabled
    app.button(key='nav_investigation').click().run()
    assert app.session_state['stage'] == 'investigation'
    assert not app.warning
    assert 'investigation_retry' not in [button.key for button in app.button]
    app.button(key='nav_question').click().run()
    app.text_area(key='draft_question').set_value('Next investigation draft')
    app.button(key='nav_results').click().run()
    app.button(key='nav_question').click().run()
    assert app.text_area(key='draft_question').value == 'Next investigation draft'
    assert len(source.requests) == 1 and not app.exception

def test_default_demo_accepts_prompt_and_roster_without_uploads(wizard):
    app, source = wizard
    assert app.radio(key='draft_mode').value == 'Demo'
    assert not app.get('file_uploader')
    app.button(key='evidence_next').click().run()
    assert not app.text_area(key='draft_question').disabled
    app.text_area(key='draft_question').set_value('Is the reported mechanism supported by the sample?')
    app.multiselect(key='draft_specialists').set_value(['literature'])
    app.button(key='start_run').click().run()
    assert app.session_state['stage'] == 'results'
    request = source.requests[0]
    assert request.mode == 'Demo' and request.sample and not request.uploads
    assert request.question == 'Is the reported mechanism supported by the sample?'
    assert request.config['specialists'] == ['literature']
    assert not app.exception


def test_recording_stays_fixed_separately_from_editable_demo(wizard):
    app, source = wizard
    app.radio(key='draft_mode').set_value('Mock').run()
    app.button(key='evidence_next').click().run()
    assert app.text_area(key='recorded_question').disabled
    assert not app.multiselect
    assert not source.requests

def test_global_question_editor_saves_evidence_and_results_edits_without_mutating_run(wizard):
    app, source = wizard
    app.text_area(key='draft_question').set_value('Question edited from evidence')
    app.button(key='nav_question').click().run()
    assert app.text_area(key='draft_question').value == 'Question edited from evidence'
    assert next(e for e in app.expander if e.label == 'Research question').proto.expanded
    app.button(key='start_run').click().run()
    assert app.session_state['stage'] == 'results'
    assert len(source.requests) == 1
    original = source.requests[0]
    app.text_area(key='draft_question').set_value('New question drafted beside the result')
    app.button(key='nav_investigation').click().run()
    assert app.text_area(key='draft_question').value == 'New question drafted beside the result'
    assert original.question == 'Question edited from evidence'
    assert app.session_state['run'].question == original.question
    assert len(source.requests) == 1 and not app.exception
    app.button(key='nav_question').click().run()
    assert app.text_area(key='draft_question').value == 'New question drafted beside the result'


def test_saved_recording_question_can_start_an_editable_demo_draft(wizard):
    app, source = wizard
    app.radio(key='draft_mode').set_value('Mock').run()
    recorded_question = app.text_area(key='recorded_question').value
    app.button(key='edit_recording_question').click().run()
    assert app.session_state['stage'] == 'question'
    assert app.session_state['draft']['mode'] == 'Demo'
    assert app.text_area(key='draft_question').value == recorded_question
    assert not app.text_area(key='draft_question').disabled
    assert not source.requests and not app.exception

def test_edit_and_navigation_stay_responsive_during_background_run(wizard):
    from threading import Event as Signal
    app, source = wizard
    Event = importlib.import_module('ui.events').Event
    release = Signal()
    def slow_events(request):
        source.requests.append(request)
        yield Event(type='run_started', run_id='slow', payload={'question': request.question})
        release.wait(3)
        yield Event(type='run_complete', payload={'verdict': 'Finished'})
    source.events = slow_events
    try:
        app.button(key='evidence_next').click().run()
        app.button(key='start_run').click().run()
        assert app.session_state['stage'] == 'investigation'
        assert not app.text_area(key='draft_question').disabled
        app.text_area(key='draft_question').set_value('A different next question')
        app.button(key='nav_question').click().run()
        assert app.text_area(key='draft_question').value == 'A different next question'
        assert app.button(key='start_run').disabled
        assert len(source.requests) == 1
        release.set()
        app.session_state['job'].thread.join(1)
        app.run()
        assert app.session_state['stage'] == 'question'
        app.button(key='nav_results').click().run()
        assert app.session_state['stage'] == 'results'
        assert len(source.requests) == 1 and not app.exception
    finally:
        release.set()

def test_burst_is_painted_once_instead_of_once_per_event(wizard):
    app, source = wizard
    Event = importlib.import_module('ui.events').Event
    def burst(request):
        source.requests.append(request)
        yield Event(type='run_started', payload={'question': request.question})
        for index in range(100):
            yield Event(type='tool_result', ts=index, payload={'result': index})
        yield Event(type='run_complete', payload={'verdict': 'Finished'})
    source.events = burst
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    assert len(app.session_state['run'].raw) == 102
    assert app.session_state['job'].render_batches == 1
    assert len(source.requests) == 1 and not app.exception

def test_voice_applied_question_and_navigation_use_existing_draft_guards(wizard, monkeypatch):
    app, source = wizard
    voice = importlib.import_module('ui.voice')
    actions = iter([{'id': 'typed-transcript', 'type': 'dictation', 'text': 'Reviewed voice question'},
                    {'id': 'too-early', 'type': 'navigate', 'target': 'results'}, None])
    monkeypatch.setattr(voice, 'render_voice_controls', lambda *args, **kwargs: next(actions, None))
    app.run()
    assert app.text_area(key='draft_question').value == 'Reviewed voice question'
    app.run()
    assert app.session_state['stage'] == 'evidence'
    assert not source.requests
    assert any('not available yet' in info.value for info in app.info)
    app.button(key='evidence_next').click().run()
    assert app.text_area(key='draft_question').value == 'Reviewed voice question'
    assert not app.exception


def test_voice_never_rewrites_a_saved_recording_question(wizard, monkeypatch):
    app, source = wizard
    app.radio(key='draft_mode').set_value('Mock').run()
    recorded = app.text_area(key='recorded_question').value
    voice = importlib.import_module('ui.voice')
    monkeypatch.setattr(voice, 'render_voice_controls', lambda *args, **kwargs:
        {'id': 'bad-recording-edit', 'type': 'dictation', 'text': 'Replacement'})
    app.run()
    assert app.text_area(key='recorded_question').value == recorded
    assert not source.requests and not app.exception


def test_replay_never_submits_and_keeps_result_and_draft(wizard):
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    saved = deepcopy(app.session_state['run'])
    app.text_area(key='draft_question').set_value('Keep this next question')
    app.button(key='results_replay').click().run()
    assert app.session_state['stage'] == 'investigation'
    assert app.session_state['playback'] is not None
    assert app.session_state['run'] == saved
    app.button(key='replay_results').click().run()
    assert app.session_state['stage'] == 'results'
    assert app.text_area(key='draft_question').value == 'Keep this next question'
    assert len(source.requests) == 1 and not app.exception


def test_followup_reuses_submitted_evidence_and_preserves_previous_report(wizard):
    app, source = wizard
    advance_with_sample(app)
    app.text_area(key='draft_question').set_value('First question')
    app.button(key='start_run').click().run()
    app.text_input(key='followup_prompt').set_value('What evidence is missing?')
    next(button for button in app.button if button.label == 'Run follow-up').click().run()
    assert app.session_state['stage'] == 'results'
    assert len(source.requests) == 2
    submitted = app.session_state['submitted']
    assert submitted.sample and submitted.mode == 'Live'
    assert submitted.question == app.session_state['run'].question == 'What evidence is missing?'
    assert submitted.context['question'] == 'First question'
    assert 'Review complete' in source.requests[-1].question
    assert app.session_state['previous_runs'][0]['run'].question == 'First question'
    app.button(key='open_saved_result').click().run()
    assert app.session_state['run'].question == 'First question'
    assert len(source.requests) == 2 and not app.exception
