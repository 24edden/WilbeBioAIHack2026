from copy import deepcopy
import importlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from frontend.ui.outcomes import STREAM_ENDED, outcome_notice
from frontend.ui.state import RunState


@pytest.mark.parametrize('status,abstained,kind,title', [
    ('complete', False, 'complete', 'Result ready'),
    ('complete', True, 'abstained', 'Finished without a supported conclusion'),
    ('cancelled', True, 'cancelled', 'Investigation stopped'),
    ('error', False, 'error', 'Investigation ended with an error'),
    ('unknown-status', False, 'unknown', 'Run ended'),
])
def test_explicit_terminal_outcome_controls_notice_without_mutating_the_record(status, abstained, kind, title):
    state = RunState(complete=True, status=status, abstained=abstained)
    original = deepcopy(state)
    notice = outcome_notice(state, active=False)
    assert notice.kind == kind and notice.title == title and notice.target == 'results'
    assert state == original
    assert outcome_notice(state, active=True) is None
    assert outcome_notice(state, active=False, replaying=True) is None


def test_no_final_event_is_distinct_from_known_errors_or_confirmed_cancellation():
    ended = outcome_notice(RunState(errors=[STREAM_ENDED]), active=False)
    assert ended.kind == 'incomplete' and ended.title == 'No final result received'
    assert ended.target == 'investigation' and ended.action_label == 'View activity'
    error = outcome_notice(RunState(errors=['Backend unavailable', STREAM_ENDED]), active=False)
    assert error.kind == 'error' and 'no final result arrived' in error.detail
    assert 'cancel' not in error.detail.lower()
    stopped = outcome_notice(RunState(complete=True, status='cancelled'), active=False)
    assert stopped.action_label == 'View outcome'
    assert 'Partial findings remain available' not in stopped.detail


def test_prior_recoverable_error_does_not_override_a_completed_result():
    notice = outcome_notice(RunState(complete=True, status='complete', errors=['One tool failed']), active=False)
    assert notice.kind == 'complete' and 'also recorded errors' in notice.detail


def test_recording_notice_cannot_claim_new_analysis():
    notice = outcome_notice(RunState(complete=True, status='complete'), active=False, recording=True)
    assert notice.title.startswith('Recorded outcome:') and notice.action_label == 'View recording'
    assert 'not new analysis' in notice.detail


def test_outcome_markup_escapes_untrusted_status_and_keeps_action_outside_live_region(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'frontend'))
    app = AppTest.from_string('''
from ui.state import RunState
from ui.outcomes import outcome_notice, render_outcome_notice
state = RunState(complete=True, status='<script>bad</script>')
render_outcome_notice(outcome_notice(state, active=False), key='view')
''').run()
    assert not app.exception
    html = app.markdown[0].value
    assert "role='status'" in html and "aria-live='polite'" in html
    assert '&lt;script&gt;bad&lt;/script&gt;' in html and '<script>' not in html
    assert '<button' not in html and app.button(key='view').label == 'View outcome'


@pytest.mark.parametrize('status,abstained,expected', [
    ('error', False, 'Run ended with an error'),
    ('unknown-status', False, 'Run ended'),
    ('cancelled', False, 'Cancelled'),
    ('complete', True, 'Abstained'),
])
@pytest.mark.parametrize('task_mode', ['investigation', 'idea_review'])
def test_terminal_verdict_never_uses_success_label_for_unsuccessful_or_unknown_outcome(monkeypatch, status, abstained, expected, task_mode):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'frontend'))
    app = AppTest.from_string('''
import streamlit as st
from ui.components import render_verdict
if 'record' in st.session_state:
    render_verdict(st.session_state.record)
''').run()
    states = importlib.import_module('ui.state')
    app.session_state['record'] = states.RunState(complete=True, status=status, abstained=abstained, verdict='Recorded output', task_mode=task_mode)
    app.run()
    html = '\n'.join(item.value for item in app.markdown)
    assert expected in html and '✔ Verdict' not in html
    assert 'Recorded output' in html and not app.exception
