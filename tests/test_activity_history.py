"""Every retained timeline entry is reachable without preparing all its HTML."""
from copy import deepcopy
from html import escape
import re

import pytest
from streamlit.testing.v1 import AppTest

from frontend.ui.activity import activity_window, move_activity_cursor
from frontend.ui.events import Event
from frontend.ui.state import Message, RunState


@pytest.mark.parametrize('total', [0, 1, 40, 41, 80, 81, 98])
def test_pages_cover_exact_arrival_order_without_gaps_or_duplicates(total):
    cursor, entries = {}, []
    while True:
        window = activity_window(total, **cursor)
        entries.extend(reversed(range(window.start, window.end)))
        assert window.end - window.start <= 40
        if window.start == 0:
            break
        cursor = move_activity_cursor(cursor, 'older', total)
    assert entries == list(reversed(range(total)))
    oldest = move_activity_cursor({}, 'oldest', total)
    assert activity_window(total, **oldest).start == 0
    assert move_activity_cursor(oldest, 'newest', total) == {'page': 0, 'anchor': None}


def test_older_page_keeps_its_bounds_when_new_events_arrive_and_shorter_records_clamp():
    cursor = move_activity_cursor({}, 'older', 98)
    before, after = activity_window(98, **cursor), activity_window(103, **cursor)
    assert (before.start, before.end) == (after.start, after.end) == (18, 58)
    assert after.total == 103 and after.anchor == 98
    newest = activity_window(103, **move_activity_cursor(cursor, 'newer', 103))
    assert (newest.start, newest.end) == (63, 103)
    smaller = activity_window(12, page=99, anchor=98)
    assert (smaller.start, smaller.end, smaller.page) == (0, 12, 0)


class TrackedTimeline(list):
    def __init__(self, values):
        super().__init__(values)
        self.slices = []

    def __getitem__(self, key):
        if isinstance(key, slice):
            self.slices.append((key.start, key.stop))
        return super().__getitem__(key)


def history_state(count):
    state = RunState(run_id='shared-backend-id', raw=[Event(type='run_started', ts=1000)])
    # Equal and out-of-order timestamps must not reorder arrival ordinals.
    state.timeline = TrackedTimeline(Message(1000 + (index % 3) * 100, 'agent_message',
        f'agent-{index}', 'research', 'recipient',
        f'entry-{index:03d} αβγ <not-markup> & literal\n' + ('long text ' * 50 if index == 0 else ''))
        for index in range(count))
    return state


def render_history(state, key='record-one'):
    app = AppTest.from_string('''
import streamlit as st
from frontend.ui.activity import render_activity_history
if 'test_state' in st.session_state:
    render_activity_history(st.session_state.test_state, key=st.session_state.test_key)
''').run()
    app.session_state['test_state'], app.session_state['test_key'] = state, key
    return app.run()


def markup(app):
    return ''.join(item.value for item in app.markdown if "class='timeline-window'" in item.value)


def ordinals(app):
    return [int(value) for value in re.findall(r'Entry (\d+) ·', markup(app))]


def click_page(app, action, key='record-one'):
    # AppTest's Expander block does not serialize the browser's open widget
    # state alongside a button click. Keep that browser-owned state explicit.
    app.session_state[f'{key}:open'] = True
    return app.button(key=f'{key}:{action}').click().run()


def test_large_history_is_lazy_and_every_window_preserves_exact_text_and_order():
    state = history_state(98)
    original = deepcopy(state)
    app = render_history(state)
    assert not app.exception and not markup(app) and not state.timeline.slices
    app.session_state['record-one:open'] = True
    app.run()
    assert ordinals(app) == list(range(98, 58, -1))
    assert state.timeline.slices == [(58, 98)]
    assert any('Showing entries 59 to 98 of 98' in item.value for item in app.caption)
    assert app.button(key='record-one:newest').disabled and app.button(key='record-one:newer').disabled
    click_page(app, 'older')
    assert ordinals(app) == list(range(58, 18, -1))
    click_page(app, 'older')
    assert ordinals(app) == list(range(18, 0, -1))
    assert escape(state.timeline[0].text) in markup(app)
    assert '<not-markup>' not in markup(app)
    assert app.button(key='record-one:older').disabled and app.button(key='record-one:oldest').disabled
    click_page(app, 'newest')
    assert ordinals(app)[0] == 98
    click_page(app, 'oldest')
    assert ordinals(app)[-1] == 1
    assert state == original and not app.exception
    assert all(stop - start <= 40 for start, stop in state.timeline.slices)


def test_small_history_is_ready_locally_and_different_saved_records_do_not_share_pages():
    small = render_history(history_state(40))
    assert len(ordinals(small)) == 40 and not small.button
    assert not small.exception
    state = history_state(81)
    app = render_history(state)
    app.session_state['record-one:open'] = True
    app.run()
    click_page(app, 'oldest')
    assert ordinals(app) == [1]
    app.session_state['test_state'] = history_state(81)  # Same backend ID, distinct local record.
    app.session_state['test_key'] = 'record-two'
    app.run()
    assert not markup(app)
    app.session_state['record-two:open'] = True
    app.run()
    assert ordinals(app) == list(range(81, 41, -1))
    assert not app.exception


@pytest.mark.parametrize('count', [1, 12, 13])
def test_live_conversation_limit_and_count_do_not_change_full_message_text(count):
    app = AppTest.from_string('''
import streamlit as st
from frontend.ui.components import render_conversation
if 'test_state' in st.session_state:
    render_conversation(st.session_state.test_state)
''').run()
    state = history_state(count)
    app.session_state['test_state'] = state
    app.run()
    assert any(f'Latest {min(12, count)} of {count} agent messages' in item.value for item in app.caption)
    text = ''.join(item.value for item in app.markdown)
    assert text.count("class='msg'") == min(12, count)
    assert escape(state.timeline[-1].text) in text
    if count == 13:
        assert 'entry-000' not in text and 'entry-001' in text
    else:
        assert escape(state.timeline[0].text) in text


def test_tool_summary_disclosure_does_not_claim_to_replace_full_raw_payload():
    state = RunState()
    supplied = {'result': 'full payload ' * 80}
    state.apply(Event(type='tool_result', payload=supplied))
    assert len(state.timeline[0].text) == 120
    app = render_history(state)
    assert any('Tool arguments and results may be shortened' in item.value for item in app.caption)
    assert escape(state.timeline[0].text) in markup(app)
    assert state.raw[0].payload == supplied and not app.exception
