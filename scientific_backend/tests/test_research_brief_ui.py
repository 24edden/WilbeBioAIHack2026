"""Execute the production UI's interpretation and exact-input preparation boundaries."""
import copy
from pathlib import Path
from types import SimpleNamespace

from test_synthesis_presentation import run_ui


class StaticClient:
    def get(self, path):
        assert path == '/static/app.js'
        return SimpleNamespace(status_code=200, text=(Path(__file__).parents[1] / 'static/app.js').read_text())


def run():
    sequence = {'id': 'sequence-verified-target', 'role': 'target', 'label': 'wild_type',
                'sequence': 'ACDEFGHIKLMNPQRSTVWY', 'length': 20, 'verified': True,
                'sequence_sha256': 'a' * 64, 'request_id': 'real-request', 'evidence_id': 'E1',
                'provenance': {'identity_basis': 'Matched accepted provider input', 'mapping': 'Declared region'}}
    brief = {'id': 'brief-1', 'decision_version': 3, 'status': 'completed',
             'created_at': '2026-09-20T00:00:00Z', 'human_review_status': 'unreviewed',
             'content': {'headline': 'A bounded leading explanation', 'plain_summary': 'The target changed.',
                         'proposed_answer': {'statement': 'A plausible splice mechanism.',
                                             'confidence_label': 'leading_explanation', 'scope': 'Public reference model',
                                             'evidence_ids': ['E1'], 'caveat': 'Patient attribution remains unresolved.',
                                             'strongest_alternative': 'A distinct trafficking mechanism.'},
                         'findings': [{'what': 'A measured change', 'why_it_matters': 'Guides the next test.', 'evidence_ids': ['E1']}],
                         'decision_story': [{'decision_version': 3, 'what_changed': 'NVIDIA result added',
                                             'why': 'Prediction tests structural plausibility.', 'next_step': 'Use a binding assay.', 'evidence_ids': ['E1']}],
                         'nvidia': {'summary': 'A monomer comparison', 'learned': ['Two structures returned.'],
                                    'not_established': ['Binding loss was not tested.'], 'sequence_ids': [sequence['id']], 'evidence_ids': ['E1']},
                         'role_summaries': [{'role': 'molecular_scientist', 'what_found': 'Monomers only.',
                                             'why_it_matters': 'Choose an assay.', 'evidence_ids': ['E1']}],
                         'recommended_next_step': {'action': 'Binding assay', 'why': 'Distinguish explanations.',
                                                   'positive_result': 'Differential binding', 'negative_result': 'Equivalent binding'},
                         'modeling_draft': {'objective': 'Interpret the public target comparison', 'scientific_rationale': 'Test the proposed mechanism.',
                                            'qualification_note': 'Needs a qualified binder.', 'target_sequence_id': sequence['id'],
                                            'reference_binder_sequence_id': None, 'candidate_binder_sequence_id': None,
                                            'missing_inputs': ['Reference and candidate binder sequences']}},
             'molecular_audit': {'status': 'completed', 'sequence_inventory': [sequence], 'audit_sha256': 'b' * 64,
                                 'comparisons': [{'evidence_id': 'E1', 'what_this_adds': 'Exploratory geometry',
                                                   'predictions': [{'label': 'wild_type', 'request_id': 'real-request',
                                                                    'confidence': {'status': 'available', 'mean': 55, 'metric': 'pLDDT', 'native_scale': '0–100'},
                                                                    'request_audit': {'status': 'checked', 'settings': {'seed': 1}}}],
                                                   'limitations': ['No binding complex']}]}}
    return {'id': 'test-run', 'mode': 'live', 'status': 'completed', 'decisions': [{'version': 3}],
            'research_briefs': [brief], 'research_brief_operations': []}


def ui(value, expression, **extra):
    return run_ui(StaticClient(), value, expression, **extra)


def test_working_answer_displays_proposal_caveat_decisions_and_exact_inputs():
    result = ui(run(), """
renderResearchBrief(selectedDecision());
return {html:element('research-brief-content').innerHTML,
        context:element('molecular-preparation-content').innerHTML,
        status:element('research-brief-status').textContent,
        originalOpen:element('original-findings').open};
""")
    for text in ['A plausible splice mechanism.', 'Leading explanation', 'Patient attribution remains unresolved.',
                 'NVIDIA result added', 'Binding loss was not tested.', 'ACDEFGHIKLMNPQRSTVWY',
                 'real-request', 'SHA-256', 'Human review: unreviewed']:
        assert text in result['html']
    assert 'Interpret the public target comparison' in result['context']
    assert 'Human review pending' in result['status']
    assert result['originalOpen'] is False


def test_prepare_only_verified_target_and_rationale_never_submits_nvidia_or_checks_retention():
    result = ui(run(), """
for (const id of ['modeling-target','modeling-reference','modeling-candidate','modeling-source']) element(id).value='';
element('modeling-retained').checked = true;
api = async (...args) => { calls.push(args); throw new Error('No provider submission allowed'); };
prepareModelingFromBrief();
return {target:element('modeling-target').value, reference:element('modeling-reference').value,
        candidate:element('modeling-candidate').value, source:element('modeling-source').value,
        retained:element('modeling-retained').checked, status:element('molecular-preparation-status').textContent, calls};
""")
    assert result['target'] == 'ACDEFGHIKLMNPQRSTVWY'
    assert result['reference'] == result['candidate'] == ''
    assert result['retained'] is False and result['calls'] == []
    assert 'Test the proposed mechanism.' in result['source']
    assert 'reference binder, candidate binder' in result['status']
    assert 'No NVIDIA job was submitted' in result['status']


def test_target_isoforms_cannot_be_resolved_into_binder_slots_even_if_model_selects_them():
    data = run()
    draft = data['research_briefs'][0]['content']['modeling_draft']
    draft['reference_binder_sequence_id'] = draft['candidate_binder_sequence_id'] = draft['target_sequence_id']
    result = ui(data, """
element('modeling-reference').value=''; element('modeling-candidate').value='';
prepareModelingFromBrief();
return {reference:element('modeling-reference').value, candidate:element('modeling-candidate').value};
""")
    assert result == {'reference': '', 'candidate': ''}


def test_unverified_or_invalid_sequence_bytes_never_enter_prepared_inputs():
    for change in [{'verified': False}, {'length': 999}, {'sequence_sha256': 'bad'}, {'sequence': '<img onerror=alert(1)>'}]:
        data = run()
        data['research_briefs'][0]['molecular_audit']['sequence_inventory'][0].update(change)
        result = ui(data, """
element('modeling-target').value=''; prepareModelingFromBrief();
return {inventory:briefSequenceInventory(selectedResearchBrief()), target:element('modeling-target').value};
""")
        assert result == {'inventory': [], 'target': ''}


def test_model_content_and_inventory_labels_are_html_escaped():
    data = run()
    data['research_briefs'][0]['content']['headline'] = '<img src=x onerror=alert(1)>'
    data['research_briefs'][0]['molecular_audit']['sequence_inventory'][0]['label'] = '" onmouseover="bad'
    result = ui(data, "renderResearchBrief(selectedDecision()); return element('research-brief-content').innerHTML;")
    assert '<img' not in result and '&lt;img' in result
    assert '&quot; onmouseover=&quot;bad' in result


def test_brief_is_bound_to_selected_decision_and_rejected_content_is_not_presented():
    data = run()
    data['decisions'].insert(0, {'version': 2})
    for version, reject in [(2, False), (3, True)]:
        trial = copy.deepcopy(data)
        if reject:
            trial['research_briefs'][0]['status'] = 'rejected'
        result = ui(trial, f"state.version={version}; renderResearchBrief(selectedDecision()); return {{html:element('research-brief-content').innerHTML, disabled:element('explain-results').disabled, originalOpen:element('original-findings').open}};")
        assert result['html'] == '' and result['originalOpen'] is True
        assert result['disabled'] is (version == 2)


def test_pending_operation_shows_persisted_progress_and_disables_duplicate_request():
    data = run()
    data.update(status='running', operation={'kind': 'research_brief'}, research_briefs=[])
    data['research_brief_operations'] = [{'decision_version': 3, 'status': 'running'}]
    result = ui(data, """
renderResearchBrief(selectedDecision());
return {label:element('explain-results').textContent, disabled:element('explain-results').disabled, status:element('research-brief-status').textContent};
""")
    assert result['disabled'] is True and result['label'] == 'Writing and checking…'
    assert 'separate model review' in result['status']


def test_generation_uses_version_and_stable_idempotency_key_on_uncertain_ack():
    data = run()
    data['research_briefs'] = []
    result = ui(data, """
updateStartButton = () => {}; setFormsEnabled = () => {}; toast = () => {};
renderRun = () => {}; schedulePoll = () => {}; refreshHistory = () => {};
let first = true;
api = async (path, options={}) => {
 calls.push({path, method:options.method || 'GET', body:options.body ? JSON.parse(options.body) : null});
 if (options.method === 'POST' && first) {first=false; throw new Error('Response lost');}
 return {...payload.run, status:'queued', operation:{kind:'research_brief'}};
};
await requestResearchBrief(); const retained=state.pendingKeys.size;
await requestResearchBrief();
return {calls, retained, pending:state.pendingKeys.size};
""")
    posts = [call for call in result['calls'] if call['method'] == 'POST']
    assert len(posts) == 2 and posts[0] == posts[1]
    assert posts[0]['path'] == '/api/runs/test-run/research-briefs'
    assert posts[0]['body'] == {'decision_version': 3, 'idempotency_key': 'stable-ui-request-key'}
    assert result['retained'] == 1 and result['pending'] == 0


def test_preparation_intent_is_applied_when_generated_explanation_arrives():
    result = ui(run(), """
state.prepareMolecularRequested='test-run:3'; element('modeling-target').value='';
renderResearchBrief(selectedDecision());
return {target:element('modeling-target').value, waiting:state.prepareMolecularRequested};
""")
    assert result == {'target': 'ACDEFGHIKLMNPQRSTVWY', 'waiting': None}


def test_explanation_operation_reuses_source_handoffs_and_labels_new_interpretation_activity():
    data = run()
    data.update(status='running', active_agent='coordinator',
                operation={'id': 'explanation-op', 'kind': 'research_brief',
                           'input': {'created_at': '2026-09-20T02:00:00Z', 'reused_handoff_ids': ['bio-old', 'coord-old']}})
    data['handoffs'] = [{'id': 'bio-old', 'sender': 'bioinformatician', 'operation_id': 'science-op', 'result_status': 'supported'},
                        {'id': 'coord-old', 'sender': 'coordinator', 'operation_id': 'science-op', 'result_status': 'inconclusive'}]
    data['events'] = [{'time': '2026-09-20T01:00:00Z', 'agent': 'bioinformatician', 'type': 'agent', 'status': 'running'},
                      {'time': '2026-09-20T02:00:01Z', 'agent': 'coordinator', 'type': 'agent', 'status': 'running'}]
    result = ui(data, "return ['bioinformatician','coordinator'].map(id => roleActivity(state.run, architectureRoles.find(role => role.id === id)));")
    assert result[0]['status'] == 'Reused accepted work'
    assert result[0]['interpretation'] is False and result[0]['events'] == []
    assert result[1]['status'] == 'Explaining results' and result[1]['interpretation'] is True
    assert result[1]['reused'] is True and result[1]['latest']['operation_id'] == 'science-op'


def test_saved_brief_automatically_prepares_pristine_form_once_without_submission():
    result = ui(run(), """
for (const id of ['modeling-target','modeling-reference','modeling-candidate','modeling-source']) element(id).value='';
element('modeling-retained').checked=false;
api = async (...args) => { calls.push(args); throw new Error('No provider submission allowed'); };
renderResearchBrief(selectedDecision());
const prepared={target:element('modeling-target').value, source:element('modeling-source').value,
 key:state.preparedMolecularFor, retained:element('modeling-retained').checked};
for (const id of ['modeling-target','modeling-source']) element(id).value='';
preparePristineModelingForm(selectedResearchBrief());
return {prepared, clearedTarget:element('modeling-target').value, clearedSource:element('modeling-source').value, calls};
""")
    assert result['prepared']['target'] == 'ACDEFGHIKLMNPQRSTVWY'
    assert 'Test the proposed mechanism.' in result['prepared']['source']
    assert result['prepared']['key'] == 'test-run:3:brief-1'
    assert result['prepared']['retained'] is False and result['calls'] == []
    assert result['clearedTarget'] == result['clearedSource'] == ''


def test_automatic_preparation_preserves_any_scientist_edit_or_retention_confirmation():
    for edited in ['modeling-target', 'modeling-reference', 'modeling-candidate', 'modeling-source', 'modeling-retained']:
        result = ui(run(), """
for (const id of ['modeling-target','modeling-reference','modeling-candidate','modeling-source']) element(id).value='';
element('modeling-retained').checked=false;
if (payload.edited==='modeling-retained') element(payload.edited).checked=true;
else element(payload.edited).value='Scientist edit';
renderResearchBrief(selectedDecision());
return {values:['modeling-target','modeling-reference','modeling-candidate','modeling-source'].map(id=>element(id).value),
 retained:element('modeling-retained').checked, key:state.preparedMolecularFor || null};
""", edited=edited)
        assert result['key'] is None
        assert result['retained'] is (edited == 'modeling-retained')
        assert result['values'] == [('Scientist edit' if field == edited else '') for field in
                                     ['modeling-target', 'modeling-reference', 'modeling-candidate', 'modeling-source']]


def test_automatic_preparation_key_distinguishes_brief_versions_and_explicit_prepare_still_works():
    result = ui(run(), """
state.preparedMolecularFor='test-run:3:prior-brief';
for (const id of ['modeling-target','modeling-reference','modeling-candidate','modeling-source']) element(id).value='';
element('modeling-retained').checked=false;
preparePristineModelingForm(selectedResearchBrief());
const restored=element('modeling-target').value;
element('modeling-target').value='User-edited value';
prepareModelingFromBrief();
return {restored, explicit:element('modeling-target').value, key:state.preparedMolecularFor};
""")
    assert result == {'restored': 'ACDEFGHIKLMNPQRSTVWY', 'explicit': 'ACDEFGHIKLMNPQRSTVWY', 'key': 'test-run:3:brief-1'}
