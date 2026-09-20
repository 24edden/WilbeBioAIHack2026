"""Task-aware UI uses actual engine metadata and preserves directed handoffs."""
import importlib
from pathlib import Path


def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'frontend'))
    return [importlib.import_module('ui.' + name) for name in ('adapters', 'state', 'events', 'graph', 'icons')]


def test_demo_auto_review_metadata_and_discussion(monkeypatch):
    adapters, states, _, graph, icons = modules(monkeypatch)
    source = adapters.DemoSource(mock_latency_scale=0)
    assert len(source.capabilities('')['review_roles']) == 3
    state = states.RunState()
    events = list(source.events(adapters.RunRequest(mode='Demo', sample=True,
        question='Evaluate this idea: use a blinded pilot to test the assay.', config={'task_mode': 'auto'})))
    for event in events:
        state.apply(event)
    assert state.task_mode == 'idea_review'
    assert len(state.agents) == 5
    assert not state.findings
    assert state.discussion == events[-1].payload['discussion']
    assert [entry['phase'] for entry in state.discussion] == ['input_inventory', 'opening', 'challenge', 'revision', 'summary']
    assert next(agent for agent in state.agents.values() if agent.role == 'supporter').alignment == 'supporting'
    assert next(agent for agent in state.agents.values() if agent.role == 'challenger').skills == ['challenge']
    assert 'Support (' in graph.build_dot(state)
    assert icons.svg_icon('challenge') != icons.svg_icon('unknown')
    assert '<script>' not in icons.svg_icon('<script>')


def test_message_recipient_can_spawn_later(monkeypatch):
    _, states, events, graph, _ = modules(monkeypatch)
    state = states.RunState()
    state.apply(events.Event(type='agent_spawned', agent_id='supporter-0', agent_role='supporter', payload={'alignment':'supporting'}))
    state.apply(events.Event(type='agent_message', agent_id='supporter-0', parent_id='critic-0', payload={'text':'Review this revision'}))
    assert ('supporter-0', 'critic-0') in state.edges
    state.apply(events.Event(type='agent_spawned', agent_id='critic-0', agent_role='critic'))
    dot = graph.build_dot(state)
    assert '"supporter-0" -> "critic-0"' in dot
    assert 'Support (1)' in dot


def test_actual_catalog_task_controls_and_review_result(monkeypatch):
    monkeypatch.setenv("TRACE_START_SCREEN", "classic")
    adapters, states, _, _, _ = modules(monkeypatch)
    from streamlit.testing.v1 import AppTest
    import streamlit as st
    st.cache_data.clear()
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'frontend' / 'app.py')).run()
    app.button(key='evidence_next').click().run()
    assert app.selectbox(key='draft_task_mode').value == 'auto'
    assert not app.multiselect
    app.selectbox(key='draft_task_mode').set_value('idea_review').run()
    assert app.session_state['draft']['config'] == {'task_mode': 'idea_review'}
    assert not app.exception
    app.selectbox(key='draft_task_mode').set_value('investigation').run()
    assert app.multiselect(key='draft_specialists').value
    st.cache_data.clear()
