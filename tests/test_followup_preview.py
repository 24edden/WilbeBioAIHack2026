from copy import deepcopy
from html import unescape
import importlib
import json
from pathlib import Path
import re

import pytest
from streamlit.testing.v1 import AppTest

from frontend.ui.followup import ContextInspection, context_for, weak_point_question
from frontend.ui.followup_preview import preview_html
from frontend.ui.state import Finding, RunState


def oversized_record():
    return RunState(run_id='original', question='q' * 4100, verdict='v' * 3100,
        findings=[Finding(f'agent-{index}', 'clinical', f'claim-{index} ' + 'x' * 720, .5,
                          [{'ref': f'{index}-{source}', 'quote': 'z' * 650} for source in range(4)])
                  for index in range(10)],
        weak_points={'status': 'assessed', 'items': [
            {'kind': 'k' * 110, 'rationale': f'gap-{index} ' + 'w' * 520} for index in range(8)]},
        discussion=[{'role': 'r' * 110, 'text': f'turn-{index} ' + 'd' * 620} for index in range(6)])


def payload_from_html(markup):
    exact = markup.split('<summary>Exact prior-context payload</summary>', 1)[1]
    content = re.search("<div class='argument-trace-text'>(.*?)</div>", exact, re.S).group(1)
    return json.loads(unescape(content))


def test_exact_payload_counts_selection_and_all_character_caps_are_inspectable():
    state = oversized_record()
    original = deepcopy(state)
    inspection = ContextInspection(state)
    assert inspection.counts() == {'findings': (8, 10), 'weak_points': (6, 8), 'discussion': (4, 6),
                                   'references': (24, 32), 'references_in_omitted_findings': 8}
    markup = preview_html(inspection)
    assert payload_from_html(markup) == context_for(state) == inspection.payload
    assert inspection.payload['findings'][0]['claim'].startswith('claim-0')
    assert inspection.payload['findings'][-1]['claim'].startswith('claim-7')
    assert inspection.payload['discussion'][0]['text'].startswith('turn-2')
    shortened = {label: (kept, available) for label, kept, available in inspection.shortened()}
    assert shortened['Prior question'] == (4000, 4100)
    assert shortened['Prior conclusion'] == (3000, 3100)
    assert shortened['Finding 1 claim'][0] == 700
    assert shortened['Finding 1, source reference 1'] == (600, len(json.dumps(state.findings[0].provenance[0], ensure_ascii=False)))
    assert shortened['Weak point 1 kind'][0] == 100
    assert shortened['Weak point 1 description'][0] == 500
    assert shortened['Discussion turn 3 role'][0] == 100
    assert shortened['Discussion turn 3 text'][0] == 600
    assert '24 of 32 source references attached to the included findings' in markup
    assert '8 further source references belong to omitted findings' in markup
    assert 'not included in this prior-context payload' in markup
    assert 'separate from your new question' in markup and 'characters, not tokens' in markup
    assert state == original


def test_short_exact_boundary_unicode_and_legacy_fallback_fields_are_not_misreported():
    reference = {'quote': 'é' * 587}  # Exact size is measured from the actual serializer.
    state = RunState(question='q' * 4000, verdict='v' * 3000,
                     findings=[Finding('a', 'clinical', 'c' * 700, .3, [reference])],
                     weak_points={'items': [{'category': 'legacy-category', 'description': 'Old description'},
                                            {'title': 'Old title'}]},
                     discussion=[{'text': 'd' * 600}])
    inspection = ContextInspection(state)
    assert inspection.payload == context_for(state)
    shortened = inspection.shortened()
    source_size = len(json.dumps(reference, ensure_ascii=False, default=str))
    assert shortened == ([('Finding 1, source reference 1', 600, source_size)] if source_size > 600 else [])
    assert inspection.payload['weak_points'][0] == {'kind': 'legacy-category', 'description': 'Old description'}
    assert inspection.payload['weak_points'][1]['description'] == 'Old title'


def test_empty_record_and_saved_payload_have_honest_different_comparison_states():
    empty = ContextInspection(RunState())
    markup = preview_html(empty)
    assert '0 of 0 findings' in markup and empty.shortened() == []
    assert 'No retained text fields were shortened' in markup
    legacy = {'question': '<script>untrusted</script>', 'findings': [{'claim': 'A retained claim', 'source_references': ['{"partial']}]}
    original = deepcopy(legacy)
    saved = ContextInspection(payload=legacy)
    markup = preview_html(saved)
    assert payload_from_html(markup) == legacy
    assert 'Only the saved context is shown here' in markup
    assert 'omissions and shortening cannot be determined from this payload alone' in markup
    assert 'No retained text fields were shortened' not in markup
    assert 'First 8' not in markup and 'Selection follows record order' not in markup
    assert '&lt;script&gt;' in markup and '<script>' not in markup
    assert legacy == original


def test_selected_weak_point_outside_context_limit_can_still_be_in_the_new_question():
    state = oversized_record()
    selected = state.weak_points['items'][7]
    assert all('gap-7' not in item['description'] for item in ContextInspection(state).payload['weak_points'])
    assert 'gap-7' in weak_point_question(state, selected)
    assert 'not included in this prior-context payload' in preview_html(ContextInspection(state))


def test_payload_preparation_is_shared_and_huge_source_serialization_is_deferred(monkeypatch):
    module = importlib.import_module('frontend.ui.followup')
    builds = []
    original = module._build_context
    monkeypatch.setattr(module, '_build_context', lambda *args: (builds.append(True), original(*args))[1])
    inspection = ContextInspection(oversized_record())
    assert inspection.deferred and inspection.counts()['findings'] == (8, 10) and not builds
    expected = inspection.payload
    preview_html(inspection)
    preview_html(inspection)
    assert inspection.payload is expected and len(builds) == 1


def test_large_preview_is_not_prepared_until_its_panel_is_requested(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'frontend'))
    module = importlib.import_module('ui.followup')
    builds = []
    original = module._build_context
    monkeypatch.setattr(module, '_build_context', lambda *args: (builds.append(True), original(*args))[1])
    state = oversized_record()
    app = AppTest.from_string('''
import streamlit as st
from ui.followup import ContextInspection
from ui.followup_preview import render_context_preview
if 'record' in st.session_state:
    render_context_preview(ContextInspection(st.session_state.record), key='context-preview')
''').run()
    app.session_state['record'] = state
    app.run()
    assert not app.exception and not builds
    app.session_state['context-preview'] = True
    app.run()
    assert not app.exception and len(builds) == 1
    assert payload_from_html(app.markdown[0].value) == context_for(state)
