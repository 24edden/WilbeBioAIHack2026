"""Production browser contracts for AI sequence discovery and applied skill attribution."""
import copy

from test_research_brief_ui import run, ui


def discovery_run():
    data = run()
    sequences = []
    for index, role in enumerate(['target', 'reference_binder', 'candidate_binder']):
        sequence = ['ACDEFGHIKLMNPQRSTVWY', 'ACDEFGHIKLMN', 'MNPQRSTVWY'][index]
        sequences.append({'id': f'seq-{index}', 'role': role, 'label': f'Qualified {role}',
                          'sequence': sequence, 'length': len(sequence), 'sequence_sha256': str(index + 1) * 64,
                          'verified': True, 'source_url': f'https://example.org/records/{index}',
                          'source_locator': f'chain {index}', 'qualification': {'status': 'qualified', 'note': 'Source identity checked'}})
    data['sequence_discoveries'] = [{'id': 'discovery-1', 'decision_version': 3, 'status': 'completed',
                                    'summary': 'Three qualified source sequences found.',
                                    'scientific_rationale': 'Test a source-backed molecular comparison.',
                                    'qualification_note': 'Clinical equivalence is unverified.', 'sequences': sequences,
                                    'missing_inputs': [], 'human_review_status': 'unreviewed'}]
    return data


def test_discovery_fills_empty_fields_and_appends_provenance_without_nvidia_submission():
    result = ui(discovery_run(), """
for (const id of ['modeling-target','modeling-reference','modeling-candidate']) element(id).value='';
element('modeling-source').value='Scientist context remains.';
element('modeling-retained').checked=false;
api=async (...args)=>{calls.push(args); throw new Error('No inference allowed');};
renderSequenceDiscovery(selectedDecision());
return {target:element('modeling-target').value, reference:element('modeling-reference').value,
 candidate:element('modeling-candidate').value, source:element('modeling-source').value,
 retained:element('modeling-retained').checked, open:element('manual-modeling').open,
 status:element('sequence-fill-status').textContent, calls};
""")
    assert result['target'] == 'ACDEFGHIKLMNPQRSTVWY'
    assert result['reference'] == 'ACDEFGHIKLMN' and result['candidate'] == 'MNPQRSTVWY'
    assert result['source'].startswith('Scientist context remains.')
    assert all(f'https://example.org/records/{i}' in result['source'] for i in range(3))
    assert result['retained'] is False and result['open'] is True and result['calls'] == []
    assert 'No NVIDIA inference was submitted' in result['status']


def test_auto_discovery_preserves_existing_sequence_edits_and_checked_retention_blocks_auto_fill():
    result = ui(discovery_run(), """
element('modeling-target').value='MYEDIT'; element('modeling-reference').value=''; element('modeling-candidate').value='';
element('modeling-retained').checked=false;
renderSequenceDiscovery(selectedDecision());
return {target:element('modeling-target').value, reference:element('modeling-reference').value,
 status:element('sequence-fill-status').textContent};
""")
    assert result['target'] == 'MYEDIT' and result['reference'] == 'ACDEFGHIKLMN'
    assert 'Preserved your existing target' in result['status']
    checked = ui(discovery_run(), """
element('modeling-target').value='MYEDIT'; element('modeling-reference').value='';
element('modeling-retained').checked=true;
renderSequenceDiscovery(selectedDecision());
return {reference:element('modeling-reference').value, retained:element('modeling-retained').checked};
""")
    assert checked == {'reference': '', 'retained': True}


def test_explicit_replacement_changes_only_selected_role_and_resets_retention():
    result = ui(discovery_run(), """
for (const id of ['modeling-target','modeling-reference','modeling-candidate']) element(id).value='MANUALEDIT';
element('modeling-retained').checked=true;
fillDiscoveredSequences('reference_binder');
return {target:element('modeling-target').value, reference:element('modeling-reference').value,
 candidate:element('modeling-candidate').value, retained:element('modeling-retained').checked};
""")
    assert result == {'target': 'MANUALEDIT', 'reference': 'ACDEFGHIKLMN', 'candidate': 'MANUALEDIT', 'retained': False}


def test_unverified_rejected_invalid_and_cross_role_records_cannot_fill_fields():
    for patch in [{'verified': False}, {'qualification': {'status': 'rejected'}}, {'length': 1000},
                  {'sequence_sha256': 'missing'}, {'sequence': '<img>'}, {'role': 'target_isoform'}]:
        data = discovery_run()
        data['sequence_discoveries'][0]['sequences'][1].update(patch)
        result = ui(data, "element('modeling-reference').value=''; fillDiscoveredSequences('reference_binder'); return element('modeling-reference').value;")
        assert result == ''
    result = ui(discovery_run(), """
element('discovered-reference_binder').value='seq-0'; element('modeling-reference').value='';
fillDiscoveredSequences('reference_binder'); return element('modeling-reference').value;
""")
    assert result == ''


def test_partial_discovery_displays_missing_roles_without_substituting_target_for_binder():
    data = discovery_run()
    record = data['sequence_discoveries'][0]
    record.update(status='needs_inputs', sequences=record['sequences'][:1], missing_inputs=['A qualified comparator binder'])
    result = ui(data, """
renderSequenceDiscovery(selectedDecision());
return {html:element('sequence-discovery-content').innerHTML, status:element('sequence-discovery-status').textContent};
""")
    assert 'partial inputs' in result['status']
    assert result['html'].count('No qualified sequence found for this role') == 2
    assert 'A qualified comparator binder' in result['html']


def test_discovery_content_is_escaped_and_unsafe_urls_are_not_links():
    data = discovery_run()
    data['sequence_discoveries'][0]['scientific_rationale'] = '<script>bad()</script>'
    data['sequence_discoveries'][0]['sequences'][0]['source_url'] = 'javascript:alert(1)'
    result = ui(data, "renderSequenceDiscovery(selectedDecision()); return element('sequence-discovery-content').innerHTML;")
    assert '<script>' not in result and '&lt;script&gt;' in result
    assert 'href="javascript:' not in result


def test_discovery_button_records_progress_and_only_latest_settled_live_decision_is_eligible():
    data = discovery_run()
    data.update(status='running', operation={'kind': 'sequence_discovery'})
    result = ui(data, "renderSequenceDiscovery(selectedDecision()); return {disabled:element('discover-sequences').disabled, label:element('discover-sequences').textContent};")
    assert result == {'disabled': True, 'label': 'Searching and qualifying…'}
    for mode, version in [('demo', 3), ('live', 2)]:
        trial = discovery_run()
        trial['mode'] = mode
        trial['decisions'].insert(0, {'version': 2})
        result = ui(trial, f"state.version={version}; renderSequenceDiscovery(selectedDecision()); return element('discover-sequences').disabled;")
        assert result is True


def test_discovery_submission_uses_version_and_stable_key_for_uncertain_ack():
    result = ui(discovery_run(), """
updateStartButton=()=>{};setFormsEnabled=()=>{};toast=()=>{};renderRun=()=>{};schedulePoll=()=>{};refreshHistory=()=>{};
let first=true;
api=async(path, options={})=>{
 calls.push({path, method:options.method || 'GET', body:options.body ? JSON.parse(options.body) : null});
 if(options.method==='POST' && first){first=false;throw new Error('Lost acknowledgement');}
 return {...payload.run,status:'queued',operation:{kind:'sequence_discovery'}};
};
await requestSequenceDiscovery();const retained=state.pendingKeys.size;
await requestSequenceDiscovery();return {calls,retained,pending:state.pendingKeys.size};
""")
    posts = [item for item in result['calls'] if item['method'] == 'POST']
    assert len(posts) == 2 and posts[0] == posts[1]
    assert posts[0]['path'] == '/api/runs/test-run/sequence-discoveries'
    assert posts[0]['body'] == {'decision_version': 3, 'idempotency_key': 'stable-ui-request-key'}
    assert result['retained'] == 1 and result['pending'] == 0


def test_skill_sources_require_matching_version_and_hash_and_available_is_not_applied():
    data = run()
    data['skill_receipts'] = [
        {'skill_id': 'local', 'name': 'Scientific workflow', 'version': '1', 'sha256': 'a'*64, 'role': 'coordinator', 'operation_id': 'science', 'origin': 'Team TBD: Rosalind-informed guidance'},
        {'skill_id': 'openai-uniprot', 'name': 'UniProt retrieval', 'version': '1', 'sha256': 'b'*64, 'role': 'molecular_scientist', 'operation_id': 'discovery'},
        {'skill_id': 'bionemo-boltz2', 'name': 'Boltz2', 'version': 'old', 'sha256': 'c'*64, 'role': 'reviewer', 'operation_id': 'science'}]
    result = ui(data, """
state.skillCatalog=[
{id:'openai-uniprot',version:'1',sha256:'b'.repeat(64),origin:'Installed OpenAI life-sciences skill', source_url:'https://example.org/skill'},
{id:'bionemo-boltz2',version:'new',sha256:'d'.repeat(64),origin:'Installed NVIDIA BioNeMo agent toolkit'},
{id:'unused-skill',version:'1',sha256:'e'.repeat(64),origin:'Installed other skill'}];
renderSkillReceipts(state.run);
return {receipts:allAppliedSkillReceipts(state.run),html:element('applied-skills-cards').innerHTML,context:element('applied-skills-context').textContent};
""")
    assert result['receipts'][1]['origin'] == 'Installed OpenAI life-sciences skill'
    assert result['receipts'][2]['origin'] == 'Source not recorded for this exact instruction version'
    assert 'unused-skill' not in result['html'] and 'TEAM TBD WORKFLOW' in result['html']
    assert 'does not establish GPT-Rosalind model access' in result['context']
    assert 'Installed NVIDIA BioNeMo' not in result['html']


def test_skill_receipts_deduplicate_and_include_separate_interpretation_and_discovery_versions():
    data = run()
    receipt = {'skill_id': 'science', 'name': 'Scientific workflow', 'version': '1', 'sha256': 'a'*64,
               'role': 'coordinator', 'operation_id': 'science-op', 'origin': 'Team TBD: workflow'}
    data['skill_receipts'] = [receipt, copy.deepcopy(receipt)]
    data['research_briefs'][0]['skill_receipts'] = [{**receipt, 'operation_id': 'brief-op'}]
    data['sequence_discoveries'] = [{'id': 'discovery-1', 'skill_receipts': [{**receipt, 'operation_id': 'discovery-op', 'version': '2', 'sha256': 'b'*64, 'role': 'molecular_scientist'}]}]
    result = ui(data, """
const receipts=allAppliedSkillReceipts(state.run);return {count:receipts.length,groups:appliedSkillGroups(receipts).map(item=>({version:item.version,count:item.count,roles:item.roles}))};
""")
    assert result['count'] == 3
    assert result['groups'] == [{'version': '1', 'count': 2, 'roles': ['coordinator']}, {'version': '2', 'count': 1, 'roles': ['molecular_scientist']}]


def test_discovery_activity_preserves_original_handoffs_and_labels_actual_new_role_work():
    data = discovery_run()
    data.update(status='running', active_agent='molecular_scientist',
                operation={'id':'discovery-op','kind':'sequence_discovery','input':{'created_at':'2026-09-20T02:00:00Z','reused_handoff_ids':['molecular-old','bio-old']}})
    data['handoffs'] = [{'id':'molecular-old','sender':'molecular_scientist','operation_id':'science-op','result_status':'supported'},
                        {'id':'bio-old','sender':'bioinformatician','operation_id':'science-op','result_status':'supported'}]
    data['events'] = [{'agent':'molecular_scientist','time':'2026-09-20T02:00:01Z','type':'agent','status':'running'}]
    result = ui(data, "return ['bioinformatician','molecular_scientist'].map(id=>roleActivity(state.run,architectureRoles.find(role=>role.id===id)));")
    assert result[0]['status'] == 'Reused accepted work'
    assert result[1]['status'] == 'Finding sequences' and result[1]['sequenceDiscovery'] is True


def test_external_registry_entry_reports_unknown_installation_without_claiming_it_was_applied():
    result = ui(run(), """
state.run=null;
api=async()=>({skills:[{id:'external', name:'OpenAI reference skill', version:'1', sha256:'a'.repeat(64),
 external_plugin:'life-sciences-databases', origin:'OpenAI-authored installed Life Sciences Databases plugin', roles:['molecular_scientist']} ]});
await refreshSkills();
return {registry:element('skill-registry').innerHTML, applied:element('applied-skills-cards').innerHTML};
""")
    assert 'Installation status not reported' in result['registry']
    assert 'requires the private plugin runtime' in result['registry']
    assert 'OpenAI reference skill' not in result['applied']
    assert 'Only actual load receipts appear here' in result['applied']
