"""Quiet activity paints retain scoped help identity without omitting any graph."""
from contextlib import nullcontext
from html import escape
import re

from streamlit.testing.v1 import AppTest

from frontend.ui import help as H


class HelpSink:
    def __init__(self):
        self.markup = []

    def container(self):
        return nullcontext()

    def html(self, markup):
        self.markup.append(markup)


def tip_id(markup):
    return re.search(r'aria-describedby="([^"]+)"', markup).group(1)


def test_scoped_help_is_identical_across_quiet_paints_and_scopes_are_distinct(monkeypatch):
    sink = HelpSink()
    monkeypatch.setattr(H, 'st', sink)
    for _ in range(30):
        H.widget(lambda label: None, 'Agent network', help='Inspect agents.', help_key='live:one:network')
    assert len(sink.markup) == 30 and len(set(sink.markup)) == 1
    first = sink.markup[0]
    for scope in ('live:one:messages', 'live:two:network', 'replay:one:network'):
        H.widget(lambda label: None, 'Agent network', help='Inspect agents.', help_key=scope)
    assert len({tip_id(markup) for markup in sink.markup}) == 4
    assert f'id="{tip_id(first)}" role="tooltip"' in first
    assert f'position-anchor:--{tip_id(first)}' in first


def test_changed_help_updates_text_with_safe_identity_and_native_render_semantics(monkeypatch):
    sink = HelpSink()
    monkeypatch.setattr(H, 'st', sink)
    calls = []

    def render(label, **kwargs):
        calls.append((label, kwargs))
        return 'rendered value'

    key = 'view:"<> & unicode α'
    result = H.widget(render, 'Question', key='native-question', help='<old & text>',
                      help_label='Question "details"', help_key=key)
    H.widget(render, 'Question', key='native-question', help='<new & text>',
             help_label='Question "details"', help_key=key)
    assert result == 'rendered value'
    assert calls == [('Question', {'key': 'native-question'})] * 2
    assert tip_id(sink.markup[0]) == tip_id(sink.markup[1])
    assert re.fullmatch(r'[a-zA-Z0-9-]+', tip_id(sink.markup[0]))
    assert escape('<old & text>') in sink.markup[0] and escape('<new & text>') in sink.markup[1]
    assert '<new & text>' not in sink.markup[1]
    assert 'Question &quot;details&quot;' in sink.markup[0]
    assert 'aria-live=' not in sink.markup[0]


def test_unscoped_duplicate_controls_keep_unique_ids_and_help_key_is_not_a_widget_kwarg(monkeypatch):
    sink = HelpSink()
    monkeypatch.setattr(H, 'st', sink)
    calls = []
    for _ in range(2):
        H.widget(lambda label: None, 'Same label', help='Same text')
    assert tip_id(sink.markup[0]) != tip_id(sink.markup[1])
    assert H.widget(lambda label, **kwargs: calls.append(kwargs), 'No help', help_key='unused') is None
    assert calls == [{}] and len(sink.markup) == 2


def test_every_activity_paint_keeps_graph_and_scoped_tips_with_new_events_visible():
    script = '''
import streamlit as st
from frontend.ui.events import Event
from frontend.ui.layout import paint_live
from frontend.ui.state import RunState
if 'activity_state' not in st.session_state:
    state = RunState()
    state.apply(Event(type='run_started', run_id='same-backend-id', payload={'question': 'Quiet run', 'config': {'run_mode': 'mock'}}))
    state.apply(Event(type='agent_spawned', agent_id='one', agent_role='clinical'))
    st.session_state.activity_state = state
paint_live(st.session_state.activity_state, st.empty(), help_scope='live:local-one')
paint_live(st.session_state.activity_state, st.empty(), recording=True, help_scope='replay:local-one')
'''
    app = AppTest.from_string(script).run()
    assert not app.exception
    initial = [item.proto.body for item in app.get('html')]
    assert len(initial) == 6 and len({tip_id(markup) for markup in initial}) == 6
    assert len(app.get('graphviz_chart')) == 2
    first_dot = app.get('graphviz_chart')[0].proto.spec
    for _ in range(3):
        app.run()
        assert [item.proto.body for item in app.get('html')] == initial
        assert len(app.get('graphviz_chart')) == 2
        assert app.get('graphviz_chart')[0].proto.spec == first_dot
    from frontend.ui.events import Event
    app.session_state['activity_state'].apply(Event(type='agent_spawned', agent_id='two', agent_role='literature', parent_id='one'))
    app.run()
    assert 'two' in app.get('graphviz_chart')[0].proto.spec
    assert app.get('graphviz_chart')[0].proto.spec != first_dot
    assert [item.proto.body for item in app.get('html')] == initial
    assert not app.exception
