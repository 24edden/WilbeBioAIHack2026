import importlib
import json
from pathlib import Path
import shutil
import subprocess
from threading import Event as Signal

import pytest
from streamlit.testing.v1 import AppTest

from frontend.ui.adapters import RunRequest
from frontend.ui.events import Event
from frontend.ui.run_clock import clock_data, measured_execution_ms
from frontend.ui.runtime import BackgroundRun
from frontend.ui.state import RunState


@pytest.mark.parametrize('value', [None, True, False, -1, float('inf'), float('nan'), '100', 10 ** 1000])
def test_invalid_or_unmeasured_backend_durations_remain_unavailable(value):
    state = RunState(complete=True, metrics={'wall_time_ms': value})
    assert measured_execution_ms(state) is None


def test_measured_duration_requires_a_terminal_run_and_keeps_zero():
    assert measured_execution_ms(RunState(metrics={'wall_time_ms': 20})) is None
    assert measured_execution_ms(RunState(complete=True, metrics={'wall_time_ms': 0})) == 0
    assert measured_execution_ms(RunState(complete=True, metrics={'wall_ms': 1250})) == 1250


def test_submission_anchor_precedes_worker_and_freezes_after_silent_completion(monkeypatch):
    runtime = importlib.import_module('frontend.ui.runtime')
    ticks = [100.0]
    monkeypatch.setattr(runtime, 'monotonic', lambda: ticks[0])
    entered, release = Signal(), Signal()
    class Silent:
        def events(self, request):
            entered.set()
            release.wait(2)
            yield Event(type='run_complete', payload={'metrics': {'wall_time_ms': 9000}})
    job = BackgroundRun(Silent(), RunRequest(mode='Demo', question='Q'))
    try:
        assert entered.wait(1) and job.submitted_at == 100.0 and job.clock_id
        ticks[0] = 110.0
        state = RunState()
        descriptor = clock_data(job, state)
        assert descriptor['active'] and descriptor['elapsedMs'] == 10000
        assert descriptor['measuredMs'] is None and not job.drain()
        assert job.submitted_at == 100.0
        ticks[0] = 112.0
        release.set()
        job.thread.join(1)
        for event in job.drain():
            state.apply(event)
        terminal = clock_data(job, state)
        assert terminal == {'runKey': descriptor['runKey'], 'active': False, 'elapsedMs': 12000, 'measuredMs': 9000}
        ticks[0] = 200.0
        assert clock_data(job, state) == terminal
        next_job = BackgroundRun(Silent(), RunRequest(mode='Demo', question='Q'))
        next_job.thread.join(1)
        assert next_job.clock_id != job.clock_id
        assert clock_data(object(), state) is None  # A worker retained through hot reload.
    finally:
        release.set()


def test_replay_stats_use_recording_span_even_when_backend_metrics_exist(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'frontend'))
    app = AppTest.from_string('''
import streamlit as st
from ui.components import render_stats
from ui.state import RunState
from ui.events import Event
state = RunState(complete=True, raw=[Event(type='run_started', ts=1000), Event(type='run_complete', ts=5000)],
                 metrics={'wall_time_ms': 2500})
render_stats(state, recording=st.session_state.get('recording', False))
''').run()
    assert not app.exception and 'Backend time' in app.markdown[0].value and '2.5s' in app.markdown[0].value
    app.session_state['recording'] = True
    app.run()
    assert 'Recording time' in app.markdown[0].value and '4.0s' in app.markdown[0].value
    assert 'Elapsed' not in app.markdown[0].value


def test_controlled_browser_clock_silence_remount_completion_and_cleanup():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for the browser lifecycle check')
    result = subprocess.run([node, str(Path(__file__).with_name('run_clock_browser_test.mjs'))],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['passed'] is True


def test_clock_accessibility_does_not_announce_each_tick():
    html = (Path(__file__).resolve().parents[1] / 'frontend/static/run_clock.html').read_text(encoding='utf-8')
    assert 'role="timer"' in html and 'aria-live="off"' in html
    assert 'Elapsed time does not indicate provider progress or health.' in html
