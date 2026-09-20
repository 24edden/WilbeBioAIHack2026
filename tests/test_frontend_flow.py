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


def test_saved_selection_uses_identity_and_restores_exact_record_and_drafts(wizard):
    from dataclasses import replace
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    current_id = app.session_state['result_id']
    original = deepcopy(app.session_state['run'])
    request = deepcopy(app.session_state['submitted'])
    records = []
    full_question = 'Same long question prefix ' * 7 + '<exact ending>'
    for suffix, mode, status in [('one', 'Demo', 'complete'), ('two', 'Mock', 'cancelled'), ('three', 'Live', 'error')]:
        state = deepcopy(original)
        state.question, state.status = full_question, status
        records.append({'id': 'abcdefgh-' + suffix, 'run': state,
                        'request': replace(request, mode=mode, question=full_question,
                                           context={'question': 'Prior context for ' + suffix})})
    app.session_state['previous_runs'] = records
    app.session_state['followup_drafts']['abcdefgh-two'] = {
        'prompt': 'Saved recording follow-up draft', 'weak_points': {}}
    app.run()
    assert len(set(app.selectbox(key='saved_result').options)) == 3
    app.text_input(key='followup_prompt').set_value('Keep my current unsent follow-up')
    app.selectbox(key='saved_result').set_value('abcdefgh-two').run()
    assert app.session_state['result_id'] == current_id
    assert app.session_state['run'] == original and app.session_state['submitted'] == request
    assert app.session_state['followup_drafts'][current_id]['prompt'] == 'Keep my current unsent follow-up'
    assert any('Same long question prefix' in item.value and '&lt;exact ending&gt;' in item.value
               and 'Recorded playback' in item.value and 'Cancelled' in item.value for item in app.markdown)
    assert len(source.requests) == 1
    app.session_state['previous_runs'] = list(reversed(records))
    app.run()
    assert app.selectbox(key='saved_result').value == 'abcdefgh-two'
    app.button(key='open_saved_result').click().run()
    assert app.session_state['result_id'] == 'abcdefgh-two'
    assert app.session_state['run'] == records[1]['run']
    assert app.session_state['submitted'] == records[1]['request']
    assert app.text_input(key='followup_prompt').value == 'Saved recording follow-up draft'
    app.selectbox(key='saved_result').set_value(current_id).run()
    app.button(key='open_saved_result').click().run()
    assert app.session_state['run'] == original and app.session_state['submitted'] == request
    assert app.text_input(key='followup_prompt').value == 'Keep my current unsent follow-up'
    assert len(source.requests) == 1 and not app.exception


def test_saved_selection_survives_history_eviction_without_index_drift(wizard):
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    current_id = app.session_state['result_id']
    records = [{'id': f'saved-{index}', 'run': deepcopy(app.session_state['run']),
                'request': deepcopy(app.session_state['submitted'])} for index in range(5)]
    app.session_state['previous_runs'] = records
    app.session_state['saved_result'] = 0  # Migrate a prior in-session index value.
    app.run()
    assert app.selectbox(key='saved_result').value == 'saved-0'
    app.selectbox(key='saved_result').set_value('saved-4').run()
    app.button(key='open_saved_result').click().run()
    retained = app.session_state['previous_runs']
    assert len(retained) == 5 and retained[0]['id'] == 'saved-1' and retained[-1]['id'] == current_id
    assert app.session_state['result_id'] == 'saved-4'
    assert app.selectbox(key='saved_result').value in [item['id'] for item in retained if item['id'] != 'saved-4']
    assert len(source.requests) == 1 and not app.exception


def test_opening_older_activity_preserves_result_context_draft_and_source_count(wizard):
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    Message = importlib.import_module('ui.state').Message
    app.session_state['run'].timeline = [Message(index, 'agent_message', 'agent', 'research', None,
                                                f'Saved message {index}') for index in range(95)]
    original = deepcopy(app.session_state['run'])
    request = deepcopy(app.session_state['submitted'])
    app.run()
    key = f"result_activity:{app.session_state['result_id']}"
    app.session_state[f'{key}:open'] = True
    app.run()
    assert any('Showing entries 56 to 95 of 95' in item.value for item in app.caption)
    app.text_input(key='followup_prompt').set_value('Keep this unsent follow-up while I inspect history')
    app.session_state[f'{key}:open'] = True  # AppTest does not serialize expander widget state.
    app.button(key=f'{key}:older').click().run()
    assert any('Showing entries 16 to 55 of 95' in item.value for item in app.caption)
    assert app.text_input(key='followup_prompt').value == 'Keep this unsent follow-up while I inspect history'
    assert app.session_state['run'] == original and app.session_state['submitted'] == request
    assert len(source.requests) == 1 and not app.exception


def test_current_and_selected_receipts_export_saved_requests_without_opening_or_submitting(wizard):
    from dataclasses import replace
    import json
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    current_id = app.session_state['result_id']
    current = deepcopy(app.session_state['run'])
    current_request = deepcopy(app.session_state['submitted'])
    saved_request = replace(current_request, question='Exact saved submitted question', mode='Mock',
                            context={'question': 'Exact prior context αβγ'})
    app.session_state['previous_runs'] = [{'id': 'saved-receipt', 'run': deepcopy(current), 'request': saved_request}]
    app.run()
    app.session_state[f'current_receipt:{current_id}:open'] = True
    app.run()
    current_payload = next(json.loads(item.value) for item in app.json if 'trace.request-receipt' in item.value)
    assert current_payload['submitted_request']['question'] == current_request.question
    app.text_input(key='followup_prompt').set_value('An unrelated unsent follow-up')
    app.session_state['selected_receipt:saved-receipt:open'] = True
    app.run()
    selected = next(json.loads(item.value) for item in app.json
                    if 'trace.request-receipt' in item.value and 'saved-receipt' in item.value)
    assert selected['submitted_request']['question'] == saved_request.question
    assert selected['submitted_request']['prior_context'] == saved_request.context
    assert app.session_state['result_id'] == current_id and app.session_state['run'] == current
    assert app.session_state['submitted'] == current_request
    assert app.text_input(key='followup_prompt').value == 'An unrelated unsent follow-up'
    assert len(source.requests) == 1 and not app.exception


def test_slow_capability_discovery_keeps_question_and_navigation_responsive(wizard):
    from threading import Event as Signal
    from time import monotonic
    app, source = wizard
    release = Signal()
    original = source.capabilities
    calls = []
    def delayed(backend):
        calls.append(backend)
        release.wait(10)
        return original(backend)
    source.capabilities = delayed
    try:
        began = monotonic()
        app.radio(key='draft_mode').set_value('Live').run()
        app.toggle(key='draft_sample').set_value(True).run()
        app.button(key='evidence_next').click().run()
        assert monotonic() - began < 3
        assert app.session_state['stage'] == 'question'
        assert app.button(key='start_run').disabled
        app.text_area(key='draft_question').set_value('Keep editing while discovery waits').run()
        app.button(key='question_back').click().run()
        assert app.session_state['stage'] == 'evidence'
        assert len(calls) == 1 and not source.requests
        release.set()
        app.session_state['capability_lookup'].thread.join(1)
        app.button(key='evidence_next').click().run()
        assert not app.button(key='start_run').disabled
        assert app.text_area(key='draft_question').value == 'Keep editing while discovery waits'
        assert not app.exception
    finally:
        release.set()


def add_weak_points(app):
    app.session_state['run'].weak_points = {'status': 'assessed', 'items': [
        {'id': 'missing-control', 'category': 'evidence_gap', 'title': 'No comparison group',
         'rationale': 'Only treated samples were supplied.', 'next_evidence': 'A matched untreated comparison.',
         'finding_ids': ['finding-1'], 'sources': []},
        {'id': 'conflict', 'category': 'conflicting_findings', 'title': 'The accounts disagree',
         'rationale': 'Two reports name different mechanisms.', 'next_evidence': 'An independent mechanism check.',
         'finding_ids': ['finding-2'], 'sources': []},
    ]}
    app.run()


def test_weak_point_drafts_preserve_unsubmitted_text_and_survive_navigation(wizard):
    app, source = wizard
    advance_with_sample(app)
    app.button(key='start_run').click().run()
    add_weak_points(app)
    original = deepcopy(app.session_state['run'])
    submitted = deepcopy(app.session_state['submitted'])
    result_id = app.session_state['result_id']
    # No intermediate run: this is the typed, not-yet-submitted input that a form
    # would lose when an unrelated weak-point button triggers a rerun.
    app.text_input(key='followup_prompt').set_value('Keep my own unsent question')
    app.button(key='draft_weak_point:1').click().run()
    suggestion_key = f'weak_point_followup:{result_id}:1'
    suggestion = app.text_area(key=suggestion_key).value
    assert 'No comparison group' in suggestion and 'A matched untreated comparison.' in suggestion
    assert app.text_input(key='followup_prompt').value == 'Keep my own unsent question'
    assert len(source.requests) == 1
    assert app.session_state['run'] == original and app.session_state['submitted'] == submitted

    app.text_area(key=suggestion_key).set_value('An edited question about the missing control')
    app.button(key='nav_question').click().run()
    app.button(key='nav_results').click().run()
    assert app.text_area(key=suggestion_key).value == 'An edited question about the missing control'
    assert app.text_input(key='followup_prompt').value == 'Keep my own unsent question'
    app.button(key='draft_weak_point:2').click().run()
    assert app.text_area(key=suggestion_key).value == 'An edited question about the missing control'
    assert 'The accounts disagree' in app.text_area(key=f'weak_point_followup:{result_id}:2').value
    app.button(key='discard_weak_point:1').click().run()
    assert suggestion_key not in [widget.key for widget in app.text_area]
    assert app.text_input(key='followup_prompt').value == 'Keep my own unsent question'
    assert app.session_state['run'] == original and len(source.requests) == 1 and not app.exception


def test_weak_point_runs_only_after_explicit_submit_and_keeps_previous_drafts(wizard):
    app, source = wizard
    advance_with_sample(app)
    app.button(key='start_run').click().run()
    add_weak_points(app)
    previous = deepcopy(app.session_state['run'])
    previous_request = deepcopy(app.session_state['submitted'])
    result_id = app.session_state['result_id']
    app.text_input(key='followup_prompt').set_value('Original manual draft')
    app.button(key='draft_weak_point:1').click().run()
    suggestion_key = f'weak_point_followup:{result_id}:1'
    app.text_area(key=suggestion_key).set_value('What can the existing evidence say about the missing control?')
    app.button(key='run_weak_point:1').click().run()
    assert len(source.requests) == 2 and app.session_state['stage'] == 'results'
    request = app.session_state['submitted']
    assert request.question == 'What can the existing evidence say about the missing control?'
    assert request.sample == previous_request.sample and request.uploads == previous_request.uploads
    assert request.context['question'] == previous.question
    assert request.context['weak_points'][0]['description'] == 'Only treated samples were supplied.'
    assert app.session_state['previous_runs'][0]['run'] == previous
    assert app.text_input(key='followup_prompt').value == ''
    app.run()
    assert len(source.requests) == 2
    app.text_input(key='followup_prompt').set_value('Draft for the new result')
    app.button(key='open_saved_result').click().run()
    assert app.session_state['run'] == previous
    assert app.text_input(key='followup_prompt').value == 'Original manual draft'
    assert app.text_area(key=suggestion_key).value == request.question
    assert len(source.requests) == 2 and not app.exception


def test_recorded_weak_point_followup_uses_simulated_review_without_original_files(wizard):
    app, source = wizard
    app.radio(key='draft_mode').set_value('Mock').run()
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    add_weak_points(app)
    recorded = deepcopy(app.session_state['run'])
    app.button(key='draft_weak_point:1').click().run()
    assert len(source.requests) == 1
    assert any('Original source files are not reanalyzed.' in caption.value for caption in app.caption)
    app.button(key='run_weak_point:1').click().run()
    submitted = app.session_state['submitted']
    assert len(source.requests) == 2 and submitted.mode == 'Demo'
    assert submitted.config['task_mode'] == 'idea_review'
    assert not submitted.sample and not submitted.uploads and submitted.fixture is None
    assert submitted.context['question'] == recorded.question
    assert submitted.context == importlib.import_module('ui.followup').context_for(recorded)
    assert app.session_state['previous_runs'][0]['run'] == recorded
    assert not app.exception


def test_empty_suggestion_requires_a_question_and_discard_does_not_run(wizard):
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    add_weak_points(app)
    app.button(key='draft_weak_point:1').click().run()
    key = f"weak_point_followup:{app.session_state['result_id']}:1"
    app.text_area(key=key).set_value('  ')
    app.button(key='run_weak_point:1').click().run()
    assert any('Enter a follow-up question first.' in error.value for error in app.error)
    app.button(key='discard_weak_point:1').click().run()
    assert len(source.requests) == 1 and not app.exception


@pytest.mark.parametrize('outcome,title,target', [
    ('complete', 'Result ready', 'results'),
    ('abstained', 'Finished without a supported conclusion', 'results'),
    ('cancelled', 'Investigation stopped', 'results'),
    ('terminal_error', 'Investigation ended with an error', 'results'),
    ('source_error', 'Investigation ended with an error', 'investigation'),
    ('stream_ended', 'No final result received', 'investigation'),
])
def test_background_outcome_notice_preserves_editing_and_requires_explicit_view(wizard, outcome, title, target):
    from threading import Event as Signal
    app, source = wizard
    Event = importlib.import_module('ui.events').Event
    release = Signal()
    def events(request):
        source.requests.append(request)
        yield Event(type='run_started', run_id='notice-test', payload={'question': request.question})
        release.wait(10)
        if outcome == 'source_error':
            raise RuntimeError('Backend unavailable')
        if outcome == 'stream_ended':
            return
        status = {'terminal_error': 'error', 'cancelled': 'cancelled'}.get(outcome, 'complete')
        yield Event(type='run_complete', payload={'status': status, 'abstained': outcome == 'abstained',
                                                  'verdict': 'Recorded outcome'})
    source.events = events
    try:
        advance_with_sample(app)
        app.button(key='start_run').click().run()
        original = deepcopy(app.session_state['submitted'])
        app.button(key='nav_question').click().run()
        app.text_area(key='draft_question').set_value('Keep this question while the run ends')
        release.set()
        app.session_state['job'].thread.join(1)
        app.run()
        assert app.session_state['stage'] == 'question'
        assert app.text_area(key='draft_question').value == 'Keep this question while the run ends'
        assert app.session_state['submitted'] == original and len(source.requests) == 1
        assert any(title in item.value and 'run-outcome-notice' in item.value for item in app.markdown)
        app.run()
        assert len(source.requests) == 1 and app.session_state['stage'] == 'question'
        key = f"view_run_outcome:{app.session_state['result_id']}"
        app.text_area(key='draft_question').set_value('Latest edit before explicitly viewing the outcome')
        app.button(key=key).click().run()
        assert app.session_state['stage'] == target
        assert app.session_state['draft']['question'] == 'Latest edit before explicitly viewing the outcome'
        assert app.session_state['submitted'] == original and len(source.requests) == 1
        app.button(key='nav_question').click().run()
        assert app.text_area(key='draft_question').value == 'Latest edit before explicitly viewing the outcome'
        assert key not in [button.key for button in app.button]
        assert not app.exception
    finally:
        release.set()


def test_saved_replay_does_not_publish_a_new_background_outcome_notice(wizard):
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    app.button(key='results_replay').click().run()
    app.button(key='nav_question').click().run()
    assert not any("<div class='run-outcome-notice'" in item.value for item in app.markdown)
    assert len(source.requests) == 1 and not app.exception


@pytest.mark.parametrize('suggested', [False, True])
def test_followup_preview_matches_the_actual_submitted_context_and_reopened_record(wizard, suggested):
    import json
    import re
    from html import unescape
    app, source = wizard
    app.button(key='evidence_next').click().run()
    app.button(key='start_run').click().run()
    add_weak_points(app)
    previous = deepcopy(app.session_state['run'])
    if suggested:
        app.button(key='draft_weak_point:2').click().run()
    previews = [item.value for item in app.markdown if '<summary>Exact prior-context payload</summary>' in item.value]
    assert len(previews) == (2 if suggested else 1)
    exact = previews[-1].split('<summary>Exact prior-context payload</summary>', 1)[1]
    previewed = json.loads(unescape(re.search("<div class='argument-trace-text'>(.*?)</div>", exact, re.S).group(1)))
    assert previewed['question'] == previous.question and len(source.requests) == 1
    assert app.session_state['run'] == previous
    if suggested:
        app.button(key='run_weak_point:2').click().run()
    else:
        app.text_input(key='followup_prompt').set_value('An explicitly submitted follow-up')
        app.button(key='run_followup').click().run()
    assert len(source.requests) == 2
    assert source.requests[-1].context == app.session_state['submitted'].context == previewed
    app.button(key='open_saved_result').click().run()
    assert app.session_state['run'] == previous
    previews = [item.value for item in app.markdown if '<summary>Exact prior-context payload</summary>' in item.value]
    exact = previews[0].split('<summary>Exact prior-context payload</summary>', 1)[1]
    assert json.loads(unescape(re.search("<div class='argument-trace-text'>(.*?)</div>", exact, re.S).group(1))) == previewed
    assert len(source.requests) == 2 and not app.exception
