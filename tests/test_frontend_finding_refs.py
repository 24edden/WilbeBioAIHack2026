"""Weak points inspect exact recorded claims, never an inferred nearby finding."""
from copy import deepcopy
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from frontend.ui.events import Event
from frontend.ui.finding_refs import FindingReferenceIndex, compact_provenance
from frontend.ui.state import Finding, RunState


@pytest.mark.parametrize('stance', ['supports', 'contradicts', 'neutral'])
def test_finding_identity_stance_and_sources_survive_event_normalization(stance):
    raw = {'type': 'finding', 'agent_id': 'clinical-1', 'agent_role': 'clinical', 'payload': {
        'finding_id': 'finding-EXACT', 'finding': 'The supplied claim.', 'stance': stance,
        'provenance': [{'kind': 'file', 'ref': 'sample.csv', 'locator': 'line 7', 'quote': 'Original source text',
                        'extra_metadata': {'comparison': 'not supplied'}}],
    }}
    state = RunState()
    state.apply(Event.from_dict(raw))
    finding = state.findings[0]
    assert finding.finding_id == 'finding-EXACT' and finding.stance == stance
    assert finding.provenance == raw['payload']['provenance']
    raw['payload']['provenance'][0]['extra_metadata']['comparison'] = 'mutated externally'
    assert finding.provenance[0]['extra_metadata']['comparison'] == 'not supplied'


@pytest.mark.parametrize('stance', [None, '', 'unknown', 'SUPPORTS', 'supports ', False, [], {'supports': True}])
def test_unknown_or_malformed_stance_is_not_promoted_to_neutral(stance):
    state = RunState()
    state.apply(Event(type='finding', payload={'finding': 'A claim', 'stance': stance}))
    assert state.findings[0].stance is None and state.findings[0].finding_id is None


def test_exact_reference_resolution_ignores_confidence_order_and_handles_legacy_objects():
    original = Finding('low', 'clinical', 'The linked claim', .2, finding_id='id-low')
    adjacent = Finding('high', 'clinical', 'An unrelated high-scoring claim', .9, finding_id='id-high')
    legacy = SimpleNamespace(text='Old in-session object', confidence=.9)
    index = FindingReferenceIndex([adjacent, original, legacy])
    assert index.resolve('id-low').finding is original
    for reference in ['ID-LOW', 'id-low ', 'missing']:
        match = index.resolve(reference)
        assert match.status == 'missing' and match.finding is None
        assert 'lack IDs' in match.message
    for reference in [None, '', '   ', 1, ['id-low']]:
        assert index.resolve(reference).status == 'invalid'
    duplicate = Finding('other', 'literature', 'A different claim', .7, finding_id='id-low')
    match = FindingReferenceIndex([original, duplicate]).resolve('id-low')
    assert match.status == 'ambiguous' and match.finding is None


def test_provenance_budget_detects_large_strings_and_structures_without_serialization():
    assert compact_provenance([{'kind': 'file', 'ref': 'sample.csv', 'quote': 'Supplied excerpt'}])
    assert not compact_provenance([{'quote': 'x' * 12001}])
    assert not compact_provenance([{}] * 193)
    deeply_nested = value = {}
    for _ in range(100):
        value['next'] = {}
        value = value['next']
    assert not compact_provenance(deeply_nested)


@pytest.fixture
def ui(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'frontend'))
    return importlib.import_module('ui.components')


def render(state):
    app = AppTest.from_string('''
import streamlit as st
from ui.components import render_weak_points
if 'test_run' in st.session_state:
    render_weak_points(st.session_state.test_run)
''').run()
    app.session_state['test_run'] = state
    return app.run()


def weak_state(findings, references):
    return RunState(run_id='finding-test', question='Does the proposed explanation fit?', findings=findings,
                    weak_points={'status': 'assessed', 'items': [{
                        'title': 'Limited comparison', 'rationale': 'A control is missing.',
                        'next_evidence': 'An independent control.', 'finding_ids': references,
                        'sources': [{'ref': 'assessment-source', 'locator': 'section 2'}],
                    }]})


def test_native_inspection_shows_exact_claim_and_all_supplied_metadata_safely(ui):
    claim = 'Exact "claim" & caveat.\n<script>untrusted</script>'
    finding = Finding('clinical-1', 'clinical', claim, .2, finding_id='claim-1', stance='contradicts', provenance=[
        {'kind': 'file', 'ref': 'sample.csv', 'locator': 'line 7', 'quote': '<img src=x onerror=bad> supplied text',
         'extra_metadata': {'method': 'reported method', 'uncertainty': ['not measured']}},
        {'source': 'legacy-paper', 'pmid': '1234', 'line': 2},
    ])
    state = weak_state([Finding('other', 'literature', 'Unrelated claim', .99, finding_id='claim-2'), finding], ['claim-1'])
    original = deepcopy(state)
    app = render(state)
    panels = [item.value for item in app.markdown if "<details class='argument-trace'>" in item.value]
    assert not app.exception and len(panels) == 1
    html = panels[0]
    assert 'Inspect finding claim-1 · clinical' in html
    assert 'Exact "claim" &amp; caveat.\n&lt;script&gt;untrusted&lt;/script&gt;' in html
    assert 'Unrelated claim' not in html and '<script>' not in html and '<img ' not in html
    for value in ['Produced by clinical-1', 'Backend-reported relation to the hypothesis: Contradicts',
                  'Source kind', 'Source reference', 'sample.csv', 'Location', 'line 7',
                  'Source excerpt supplied with this finding', '&lt;img src=x onerror=bad&gt; supplied text',
                  'extra metadata', 'reported method', 'not measured', 'legacy-paper', 'PMID', '1234']:
        assert value in html
    assert 'not whether it is correct' in html and 'not been independently verified' in html
    assert '<summary>' in html and not app.button
    assert app.code[0].value == 'claim-1' and 'assessment-source' in app.json[0].value
    assert state == original


def test_missing_duplicate_legacy_ids_and_missing_source_data_remain_explicit(ui):
    findings = [Finding('a', 'clinical', 'One claim', .4, finding_id='duplicate'),
                Finding('b', 'clinical', 'Other claim', .6, finding_id='duplicate'),
                Finding('c', 'clinical', 'Legacy claim', .5),
                Finding('d', 'clinical', 'No source attached', .5, finding_id='valid')]
    app = render(weak_state(findings, ['duplicate', 'missing<script>', 'valid']))
    html = '\n'.join(item.value for item in app.markdown)
    assert not app.exception
    assert 'Multiple findings share this ID' in html and 'No exact finding ID matches' in html and 'lack IDs' in html
    assert 'missing&lt;script&gt;' in html and '<script>' not in html
    panels = [item.value for item in app.markdown if "<details class='argument-trace'>" in item.value]
    assert len(panels) == 1 and 'Inspect finding valid' in panels[0]
    assert 'Unknown / not supplied' in panels[0] and 'No source records were attached' in panels[0]


def test_large_attached_provenance_stays_unprepared_until_reference_panel_opens(ui, monkeypatch):
    calls = []
    original = ui._finding_provenance_html
    monkeypatch.setattr(ui, '_finding_provenance_html', lambda records: (calls.append(records), original(records))[1])
    finding = Finding('a', 'clinical', 'A claim', .4, finding_id='large', provenance=[{'quote': 'x' * 20000}])
    state = weak_state([finding], ['large'])
    app = render(state)
    assert not app.exception and not calls and not app.code
    assert not any("<details class='argument-trace'>" in item.value for item in app.markdown)
    app.session_state['weak_point_sources:finding-test:1'] = True
    app.run()
    assert not app.exception and len(calls) == 1
    assert any('x' * 20000 in item.value for item in app.markdown)


def test_real_demo_finding_ids_match_the_backend_weak_point_references(ui):
    adapters = importlib.import_module('ui.adapters')
    state = RunState()
    request = adapters.RunRequest(mode='Demo', question='Why did treatment fail?', sample=True,
                                  config={'specialists': ['clinical']})
    for event in adapters.DemoSource(mock_latency_scale=0).events(request):
        state.apply(event)
    references = [ref for item in state.weak_points['items'] for ref in item.get('finding_ids', [])]
    assert references and all(FindingReferenceIndex(state.findings).resolve(ref).status == 'matched' for ref in references)
    assert all(finding.stance in ('supports', 'contradicts', 'neutral') for finding in state.findings)
    app = render(state)
    for index, item in enumerate(state.weak_points['items'], 1):
        if item.get('finding_ids'):
            app.session_state[f'weak_point_sources:{state.run_id}:{index}'] = True
    app.run()
    assert not app.exception and any('Inspect finding ' in item.value for item in app.markdown)
