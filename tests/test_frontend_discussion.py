"""Recorded argument links are exact, inspectable and never inferred from order."""
from copy import deepcopy
import importlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from frontend.ui.discussion import inspect_replies


def test_reply_chain_skips_unrelated_turns_and_preserves_original_indices():
    entries = [
        {"id": "source", "text": "Inventory", "reply_to": None},
        {"id": "proposal", "text": "Opening", "reply_to": "source"},
        {"id": "unrelated", "text": "Unrelated message"},
        {"id": "challenge", "text": "Challenge", "reply_to": "proposal"},
        {"id": "revision", "text": "Revision", "reply_to": "challenge"},
    ]
    original = deepcopy(entries)
    links = inspect_replies(entries)
    assert links[0].status == links[2].status == "unlinked"
    assert links[3].target_index == 1 and links[3].chain == (0, 1, 3)
    assert links[4].target_index == 3 and links[4].chain == (0, 1, 3, 4)
    assert entries == original


@pytest.mark.parametrize(("entries", "index", "status"), [
    ([{"id": "source"}, {"id": "reply", "reply_to": "missing"}], 1, "missing"),
    ([{"id": "source"}, {"id": "reply", "reply_to": "Source"}], 1, "missing"),
    ([{"id": "source"}, {"id": "reply", "reply_to": "source "}], 1, "missing"),
    ([{"id": "same"}, {"id": "same"}, {"id": "reply", "reply_to": "same"}], 2, "ambiguous"),
    ([{"id": "source"}, {"id": "same", "reply_to": "source"}, {"id": "same"}], 1, "ambiguous"),
    ([{"id": "self", "reply_to": "self"}], 0, "self"),
    ([{"id": "one", "reply_to": "two"}, {"id": "two", "reply_to": "one"}], 1, "cycle"),
    ([{"id": "one", "reply_to": "two"}, {"id": "two", "reply_to": "one"},
      {"id": "reply", "reply_to": "two"}], 2, "cycle"),
    ([{"id": "first", "reply_to": "later"}, {"id": "later"}], 0, "out_of_order"),
    ([{"text": "Legacy turn", "reply_to": "source"}, {"id": "source"}], 0, "legacy"),
    ([{"id": 1}, {"id": "reply", "reply_to": 1}], 1, "invalid"),
    ([{"id": "source"}, {"id": "reply", "reply_to": ["source"]}], 1, "invalid"),
    ([{"id": "source"}, {"id": "reply", "reply_to": "   "}], 1, "invalid"),
    ([{"id": "source", "reply_to": "missing"}, {"id": "reply", "reply_to": "source"}], 1, "missing"),
])
def test_unresolvable_chains_fail_plainly_without_a_substituted_argument(entries, index, status):
    link = inspect_replies(entries)[index]
    assert link.status == status and link.message
    assert link.target_index is None and link.chain == ()


@pytest.fixture
def ui(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "frontend"))
    return importlib.import_module("ui.state").RunState


def render(state):
    app = AppTest.from_string('''
import streamlit as st
from ui.components import render_discussion
if 'test_run' in st.session_state:
    render_discussion(st.session_state.test_run)
''').run()
    app.session_state["test_run"] = state
    return app.run()


def test_inspection_shows_exact_prior_text_and_preserves_all_source_details(ui):
    prior = 'Exact "claim" & caveat.\nSecond line <script>untrusted</script>.'
    state = ui(discussion=[
        {"id": "opening-1", "agent_id": "supporter-1", "phase": "opening", "alignment": "supporting",
         "text": prior, "assumptions": ["Not measured yet"], "evidence_refs": ["paper-17"],
         "open_questions": ["Which measurement distinguishes the claims?"],
         "provenance": [{"source": "paper-17", "quote": "Original quote"}]},
        {"id": "unrelated", "text": "Do not substitute this adjacent message."},
        {"id": "challenge-1", "agent_id": "challenger-1", "phase": "challenge", "alignment": "challenging",
         "text": "The comparison is absent.", "reply_to": "opening-1"},
    ])
    original = deepcopy(state)
    app = render(state)
    html = [item.value for item in app.markdown if "class='argument-trace'" in item.value]
    assert not app.exception and len(html) == 1
    assert 'turn 01 · supporter-1 · opening' in html[0]
    assert 'Source turn ID: opening-1' in html[0]
    assert 'Exact "claim" &amp; caveat.\nSecond line &lt;script&gt;untrusted&lt;/script&gt;.' in html[0]
    assert '<script>' not in html[0] and 'Do not substitute' not in html[0]
    assert 'Turn 01 · opening → Turn 03 · challenge' in html[0]
    assert '<summary>' in html[0] and not app.button
    assert any('Not measured yet' == item.value for item in app.text)
    assert any('paper-17' == item.value for item in app.text)
    assert any('Which measurement' in item.value for item in app.text)
    assert 'Original quote' in app.json[0].value
    assert any('Responds to: opening-1' == item.value for item in app.caption)
    assert any('A revision does not establish scientific correctness.' in item.value for item in app.caption)
    originals = [item.value for item in app.markdown if "class='find'" in item.value]
    assert 'Exact "claim"' in originals[0] and 'Do not substitute' in originals[1] and 'comparison is absent' in originals[2]
    assert state == original


def test_missing_legacy_and_cycle_messages_are_visible_without_fake_disclosures(ui):
    state = ui(discussion=[
        {"text": "Legacy argument"},
        {"id": "missing", "text": "Missing source", "reply_to": "not-here"},
        {"id": "loop-a", "text": "Cycle A", "reply_to": "loop-b"},
        {"id": "loop-b", "text": "Cycle B", "reply_to": "loop-a"},
    ])
    app = render(state)
    assert not app.exception
    assert not any("class='argument-trace'" in item.value for item in app.markdown)
    captions = " ".join(item.value for item in app.caption)
    assert 'no usable identifier' in captions and 'missing from this record' in captions and 'contain a cycle' in captions
    assert len(app.expander) == 4


def test_current_demo_review_resolves_its_real_opening_challenge_and_revision(ui):
    adapters = importlib.import_module("ui.adapters")
    state = ui()
    request = adapters.RunRequest(mode="Demo", question="Evaluate this idea with a comparison group.",
                                  config={"task_mode": "idea_review"})
    for event in adapters.DemoSource(mock_latency_scale=0).events(request):
        state.apply(event)
    assert state.complete
    phases = [entry['phase'] for entry in state.discussion]
    revision = phases.index('revision')
    inspection = inspect_replies(state.discussion)[revision]
    assert state.discussion[inspection.target_index]['phase'] == 'challenge'
    assert [phases[index] for index in inspection.chain] == ['input_inventory', 'opening', 'challenge', 'revision']
    app = render(state)
    assert not app.exception
    assert any('challenger-1 · challenge' in item.value for item in app.markdown)
