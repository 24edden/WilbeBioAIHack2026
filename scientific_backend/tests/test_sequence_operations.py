"""Durable sequence-discovery boundaries; all model and public-source transport is mocked."""
import asyncio
import copy
import hashlib

import pytest

from app import providers, sequence_discovery, sequence_operations, sequence_sources
from app.sequence_operations import enqueue_sequence_discovery, input_identity
from app.store import Conflict, digest
from test_harness import harness, complete


@pytest.fixture
def completed_live(harness, monkeypatch):
    client, store, worker = harness
    original = complete(harness)
    def preserve_scientific_context(run):
        run.update(mode='live', governance_state={
            'status': 'stopped', 'decision_version': 1, 'operation_id': run['operation']['id'],
            'reason': 'Awaiting a discriminating assay', 'hypotheses': [{'id': 'H1', 'status': 'possible'}]},
            research_briefs=[{'id': 'prior-interpretation', 'decision_version': 1, 'content': {'headline': 'Preserved scientific interpretation'}}])
    original = store.mutate(original['id'], preserve_scientific_context)
    # This suite tests instruction pinning, not installation of the private plugin.
    # Actual skill bytes and public-source adapters are tested separately.
    monkeypatch.setattr(sequence_operations, 'load_skill', lambda skill_id, role: {
        'sha256': hashlib.sha256(f'{role}:{skill_id}:test-instruction-v1'.encode()).hexdigest()})
    monkeypatch.setattr(providers, 'selected_model', lambda: 'gpt-6-astra')
    monkeypatch.setattr(providers, 'investigate', lambda *_a, **_kw: pytest.fail('Sequence discovery cannot rerun scientific specialists'))
    monkeypatch.setattr(providers, 'predict_complex', lambda *_a, **_kw: pytest.fail('Sequence discovery cannot submit NVIDIA inference'))
    return client, store, worker, original


def request(**updates):
    return {'decision_version': 1, 'idempotency_key': 'explicit-sequence-discovery', **updates}


def fake_result(run, partial=False):
    sequences = []
    for index, role in enumerate(['target', 'reference_binder', 'candidate_binder'][:1 if partial else 3]):
        sequence = 'ACDEFGHIKLMNPQRSTVWY' + ('A' * (index + 1))
        source = f'Isolated test source {index}, not scientific evidence'.encode()
        sequences.append({'id': f'test-source-{index}', 'role': role, 'label': f'Test {role}',
                          'sequence': sequence, 'length': len(sequence), 'verified': True,
                          'sequence_sha256': hashlib.sha256(sequence.encode()).hexdigest(),
                          'source_sha256': hashlib.sha256(source).hexdigest(),
                          'source_url': f'https://example.org/sequence-fixture/{index}', 'source_locator': f'fixture chain {index}'})
    return {'schema': 'team-tbd-sequence-discovery-1', 'status': 'needs_inputs' if partial else 'completed',
            'decision_version': 1, 'summary': 'Software fixture only.', 'sequences': sequences,
            'missing_inputs': ['Two qualified binders'] if partial else [],
            'provider_metadata': {'dispatched_requests': 2, 'requests': [{'status': 'completed'}, {'status': 'completed'}],
                                  'usage': {'input_tokens': 100, 'output_tokens': 50}},
            'skill_receipts': [{'skill_id': 'uniprot-skill', 'role': 'molecular_scientist', 'version': 'test-v1',
                                'sha256': 'a' * 64, 'origin': 'Test-only instruction receipt'}],
            'source_receipts': [{'tool': 'source_fixture', 'status': 'completed', 'sha256': hashlib.sha256(b'fixture response').hexdigest()}],
            'model_review': {'verdict': 'accepted'}, 'nvidia_submitted': False,
            'target_retention_established': False, 'sha256': 'incoming-provider-envelope-hash'}


def saved_success(store, run_id, queued, result, **changes):
    entry = queued['operation']['input']
    action_id = entry['id'] + '-sequence-discovery'
    frozen = {key: copy.deepcopy(entry[key]) for key in ('input_versions', 'instruction_hashes', 'model', 'source_decision_sha256')}
    frozen.update(changes)
    store.begin_action(run_id, action_id, 'sequence-discovery', frozen)
    store.end_action(run_id, action_id, 'succeeded', result)
    return action_id


def test_api_queue_idempotence_freezes_inputs_without_dispatching(completed_live, monkeypatch):
    client, store, _, original = completed_live
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', lambda *_a, **_kw: pytest.fail('Queue cannot call any provider'))
    endpoint = f"/api/runs/{original['id']}/sequence-discoveries"
    response = client.post(endpoint, json=request())
    assert response.status_code == 202, response.text
    queued = response.json()
    assert queued['operation']['kind'] == 'sequence_discovery'
    entry = queued['operation']['input']
    assert entry['input_versions'] == input_identity(original)
    assert entry['model'] == 'gpt-6-astra' and len(entry['instruction_hashes']) == 14
    assert entry['source_decision_sha256'] == original['decisions'][-1]['sha256']
    assert input_identity(store.get(original['id'])) == input_identity(original)
    assert len(queued['sequence_discovery_operations']) == 1
    assert client.post(endpoint, json=request()).json() == queued
    assert client.post(endpoint, json=request(idempotency_key='second-key')).status_code == 409
    assert client.post(endpoint, json=request(decision_version=2)).status_code == 409
    assert client.post(endpoint, json={**request(), 'sequences': [{'verified': True}]}).status_code == 422


@pytest.mark.parametrize('patch', [{'decision_version': True}, {'decision_version': 0}, {'idempotency_key': ''}, {'idempotency_key': ' '*5}, {'idempotency_key': 'x'*101}, {'extra': 'forged'}])
def test_direct_queue_rejects_untrusted_payload_shape_without_mutation(completed_live, patch):
    _, store, _, original = completed_live
    before = store.get(original['id'])
    with pytest.raises(Conflict):
        enqueue_sequence_discovery(store, original['id'], {**request(), **patch})
    assert store.get(original['id']) == before


@pytest.mark.parametrize('mode,version', [('demo', 1), ('live', 2)])
def test_queue_requires_live_latest_accepted_decision(completed_live, mode, version):
    client, store, _, original = completed_live
    store.mutate(original['id'], lambda run: run.update(mode=mode))
    before = store.get(original['id'])
    response = client.post(f"/api/runs/{original['id']}/sequence-discoveries", json=request(decision_version=version))
    assert response.status_code == 409
    assert store.get(original['id']) == before


def test_known_result_only_appends_discovery_preserving_science_and_exact_source_receipts(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    expected = fake_result(original)
    calls = []
    async def discover(run, case, emit=None, cancelled=None):
        calls.append(copy.deepcopy(run))
        assert run['case_snapshot'] == case
        assert store.get(run['id'])['actions'][-1]['state'] == 'submitting'
        assert store.get(run['id'])['sequence_discovery_operations'][-1]['status'] == 'running'
        return copy.deepcopy(expected)
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', discover)
    enqueue_sequence_discovery(store, original['id'], request())
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == 'completed', final.get('error')
    assert len(calls) == 1 and len(final['sequence_discoveries']) == 1
    assert input_identity(final) == input_identity(original)
    assert final.get('governance_state') == original.get('governance_state')
    result = final['sequence_discoveries'][0]
    assert result['sequences'] == expected['sequences']
    assert result['source_receipts'] == expected['source_receipts']
    assert result['source_decision_version'] == 1 and result['source_decision_sha256'] == original['decisions'][-1]['sha256']
    assert result['human_review_status'] == 'unreviewed' and result['nvidia_submitted'] is False
    assert result['target_retention_established'] is False
    assert result['sha256'] == digest({k: v for k, v in result.items() if k != 'sha256'})
    for sequence in result['sequences']:
        assert sequence['sequence_sha256'] == hashlib.sha256(sequence['sequence'].encode()).hexdigest()
        assert sequence['length'] == len(sequence['sequence'])
    assert final['usage']['model_calls'] == original['usage']['model_calls'] + 2
    assert final['actions'][-1]['state'] == 'succeeded'
    operation = final['sequence_discovery_operations'][-1]
    assert operation['status'] == operation['result_status'] == 'completed'
    assert operation['discovery_id'] == result['id'] and operation['finished_at']
    receipt = next(item for item in final['skill_receipts'] if item.get('operation_id') == operation['id'])
    assert receipt['sha256'] == expected['skill_receipts'][0]['sha256']
    assert enqueue_sequence_discovery(store, original['id'], request())['status'] == 'completed'
    assert len(store.get(original['id'])['sequence_discoveries']) == 1 and len(calls) == 1


@pytest.mark.parametrize('changed_field', ['evidence', 'research_briefs', 'case_snapshot', 'governance_state'])
def test_changed_source_context_is_rejected_before_dispatch(completed_live, monkeypatch, changed_field):
    _, store, worker, original = completed_live
    enqueue_sequence_discovery(store, original['id'], request())
    def mutate(run):
        if changed_field == 'evidence':
            run['evidence'][0]['summary'] = 'Changed after selection'
        elif changed_field == 'research_briefs':
            run['research_briefs'] = [{'id': 'new-interpretation', 'content': 'Changed'}]
        elif changed_field == 'case_snapshot':
            run['case_snapshot']['new_source_marker'] = 'Changed'
        else:
            run['governance_state'] = {'status': 'changed-after-selection'}
    store.mutate(original['id'], mutate)
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', lambda *_a, **_kw: pytest.fail('Frozen source mismatch must stop before inference'))
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == 'failed'
    assert 'source results changed' in final['error']
    assert final['sequence_discovery_operations'][-1]['status'] == 'failed'
    assert not final.get('sequence_discoveries') and final['actions'] == original['actions']


@pytest.mark.parametrize('change', ['model', 'skill'])
def test_changed_model_or_instruction_bytes_are_rejected_before_dispatch(completed_live, monkeypatch, change):
    _, store, worker, original = completed_live
    enqueue_sequence_discovery(store, original['id'], request())
    if change == 'model':
        monkeypatch.setattr(providers, 'selected_model', lambda: 'changed-model')
    else:
        monkeypatch.setattr(sequence_operations, 'load_skill', lambda *_a, **_kw: {'sha256': 'f'*64})
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', lambda *_a, **_kw: pytest.fail('Model/skill mismatch must stop before dispatch'))
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == 'failed' and 'instructions or configured model changed' in final['error']
    assert not final.get('sequence_discoveries') and final['actions'] == original['actions']


def test_timeout_records_unknown_and_blocks_all_new_sequence_requests(completed_live, monkeypatch):
    client, store, worker, original = completed_live
    calls = []
    async def timeout(*_a, **_kw):
        calls.append(1)
        raise providers.ProviderError('Timed out', status='unknown', reason_code='model_request_timeout',
                                      metadata={'dispatched_requests': 1, 'requests': [{'status': 'dispatched'}], 'usage': {}})
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', timeout)
    enqueue_sequence_discovery(store, original['id'], request())
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == 'blocked' and final['actions'][-1]['state'] == 'unknown'
    assert final['sequence_discovery_operations'][-1]['status'] == 'blocked'
    assert input_identity(final) == input_identity(original) and not final.get('sequence_discoveries')
    assert client.post(f"/api/runs/{original['id']}/resume").status_code == 409
    with pytest.raises(Conflict, match='unresolved'):
        enqueue_sequence_discovery(store, original['id'], request(idempotency_key='unsafe-new-key'))
    asyncio.run(worker.execute(original['id']))
    assert len(calls) == 1
    assert store.get(original['id'])['actions'][-1]['state'] == 'unknown'


@pytest.mark.parametrize('state', ['submitting', 'unknown', 'failed'])
def test_existing_attempt_for_this_operation_cannot_be_resubmitted(completed_live, monkeypatch, state):
    _, store, worker, original = completed_live
    queued = enqueue_sequence_discovery(store, original['id'], request())
    action_id = queued['operation']['id'] + '-sequence-discovery'
    store.begin_action(original['id'], action_id, 'sequence-discovery', {})
    if state != 'submitting':
        store.end_action(original['id'], action_id, state, {'reason': 'Test prior attempt'})
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', lambda *_a, **_kw: pytest.fail('Prior attempt cannot repeat'))
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == ('failed' if state == 'failed' else 'blocked')
    assert final['actions'][-1]['state'] == state
    assert not final.get('sequence_discoveries') and input_identity(final) == input_identity(original)


def test_saved_success_publishes_once_without_model_or_source_calls(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    queued = enqueue_sequence_discovery(store, original['id'], request())
    result = fake_result(original)
    saved_success(store, original['id'], queued, result)
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', lambda *_a, **_kw: pytest.fail('Cached success cannot rerun models or tools'))
    monkeypatch.setattr(sequence_sources, 'SequenceSources', lambda *_a, **_kw: pytest.fail('Cached success cannot initialize public-source retrieval'))
    asyncio.run(worker.execute(original['id']))
    first = store.get(original['id'])
    assert first['status'] == 'completed'
    assert first['sequence_discoveries'][0]['sequences'] == result['sequences']
    assert input_identity(first) == input_identity(original)
    # Even a duplicate worker invocation must not publish a second addendum or charge usage twice.
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['sequence_discoveries'] == first['sequence_discoveries']
    assert final['usage'] == first['usage']
    assert final['skill_receipts'] == first['skill_receipts']


@pytest.mark.parametrize('change', ['kind', 'request'])
def test_cached_success_requires_matching_frozen_request_and_kind(completed_live, monkeypatch, change):
    _, store, worker, original = completed_live
    queued = enqueue_sequence_discovery(store, original['id'], request())
    action_id = saved_success(store, original['id'], queued, fake_result(original), **({'model': 'wrong-model'} if change == 'request' else {}))
    if change == 'kind':
        with store.connect() as db:
            db.execute('UPDATE actions SET kind=? WHERE id=?', ('wrong-action-kind', action_id))
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', lambda *_a, **_kw: pytest.fail('Mismatched saved action must not dispatch'))
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == 'failed' and 'does not match its frozen inputs' in final['error']
    assert not final.get('sequence_discoveries')


def test_queued_cancel_does_not_dispatch_and_marks_operation_cancelled(completed_live, monkeypatch):
    client, store, worker, original = completed_live
    enqueue_sequence_discovery(store, original['id'], request())
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', lambda *_a, **_kw: pytest.fail('Cancelled work cannot call providers'))
    assert client.post(f"/api/runs/{original['id']}/cancel").status_code == 200
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == final['sequence_discovery_operations'][-1]['status'] == 'cancelled'
    assert not final.get('sequence_discoveries') and input_identity(final) == input_identity(original)


def test_cancel_after_provider_return_preserves_success_receipt_without_publishing(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    async def discover(run, *_a, **_kw):
        store.mutate(run['id'], lambda current: current.update(cancel_requested=True))
        return fake_result(run)
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', discover)
    enqueue_sequence_discovery(store, original['id'], request())
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == final['sequence_discovery_operations'][-1]['status'] == 'cancelled'
    assert final['actions'][-1]['state'] == 'succeeded' and not final.get('sequence_discoveries')
    assert input_identity(final) == input_identity(original)


@pytest.mark.parametrize('submitted', [False, True])
def test_restart_reconciles_running_operation_and_unknown_submission(completed_live, submitted):
    _, store, worker, original = completed_live
    queued = enqueue_sequence_discovery(store, original['id'], request())
    if submitted:
        store.begin_action(original['id'], queued['operation']['id'] + '-sequence-discovery', 'sequence-discovery', {})
    def running(run):
        run['status'] = 'running'
        run['sequence_discovery_operations'][-1]['status'] = 'running'
    store.mutate(original['id'], running)
    worker.recover()
    final = store.get(original['id'])
    expected = 'blocked' if submitted else 'paused'
    assert final['status'] == final['sequence_discovery_operations'][-1]['status'] == expected
    assert final['sequence_discovery_operations'][-1]['finished_at']
    if submitted:
        assert final['actions'][-1]['state'] == 'unknown'
    assert input_identity(final) == input_identity(original) and not final.get('sequence_discoveries')


def test_partial_qualified_inputs_complete_operation_but_remain_needs_inputs(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    async def discover(run, *_a, **_kw):
        return fake_result(run, partial=True)
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', discover)
    enqueue_sequence_discovery(store, original['id'], request())
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == 'completed'
    record = final['sequence_discoveries'][0]
    assert record['status'] == 'needs_inputs' and record['missing_inputs'] == ['Two qualified binders']
    assert {item['role'] for item in record['sequences']} == {'target'}
    assert final['sequence_discovery_operations'][-1]['status'] == 'completed'
    assert final['sequence_discovery_operations'][-1]['result_status'] == 'needs_inputs'
    assert input_identity(final) == input_identity(original)


def test_source_change_during_external_work_keeps_receipt_but_refuses_publication(completed_live, monkeypatch):
    _, store, worker, original = completed_live
    async def discover(run, *_a, **_kw):
        store.mutate(run['id'], lambda current: current['evidence'][0].update(summary='Concurrent source change'))
        return fake_result(run)
    monkeypatch.setattr(sequence_discovery, 'discover_sequences', discover)
    enqueue_sequence_discovery(store, original['id'], request())
    asyncio.run(worker.execute(original['id']))
    final = store.get(original['id'])
    assert final['status'] == 'failed' and 'source results changed' in final['error']
    assert final['actions'][-1]['state'] == 'succeeded'
    assert not final.get('sequence_discoveries')
