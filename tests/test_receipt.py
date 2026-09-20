"""Request receipts preserve the selected request subset and exclude connection data."""
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from frontend.ui import receipt as R
from frontend.ui.adapters import RunRequest
from frontend.ui.state import RunState


def record(record_id='local-one', mode='Live'):
    request = RunRequest(mode=mode, question='  Exact submitted αβγ <literal> & question\n',
        backend='https://secret-endpoint.invalid/?token=BACKEND_SECRET',
        fixture='C:/PRIVATE_LOCAL_RECORDING.json', uploads=[('SECRET_NAME.txt', b'UPLOAD_SECRET')],
        sample=False, speed=2.0,
        config={'task_mode': 'idea_review', 'specialists': ['clinical'],
                'reasoning_model': 'requested-model', 'variant_model': None, 'embedding_model': '',
                'api_key': 'CONFIG_SECRET', 'future_endpoint': 'CONFIG_ENDPOINT'},
        context={'question': 'Previous αβγ', 'findings': [{'claim': '<recorded claim>', 'refs': ['exact string']}],
                 'nested': {'empty': [], 'null': None}})
    state = RunState(run_id='shared-backend-id', question='Different recorded question',
        complete=True, status='complete', config={'reasoning_model': 'reported-model', 'run_mode': 'mock'})
    return {'id': record_id, 'run': state, 'request': request}


def test_receipt_keeps_exact_saved_values_and_excludes_nonallowlisted_connection_and_file_data():
    saved = record()
    original = deepcopy(saved)
    result = json.loads(R.receipt_json(saved))
    assert result['schema'] == 'trace.request-receipt' and result['schema_version'] == 1
    assert result['session_record_id'] == 'local-one' and result['backend_run_id'] == 'shared-backend-id'
    request = result['submitted_request']
    assert request['question'] == saved['request'].question
    assert request['prior_context'] == saved['request'].context
    assert request['requested_settings'] == {key: saved['request'].config[key] for key in R.SETTING_FIELDS}
    assert request['requested_settings_omitted_count'] == 2
    assert request['connection_mode'] == 'Live' and request['sample_requested'] is False
    assert result['recorded_outcome']['question'] == 'Different recorded question'
    assert result['recorded_outcome']['execution_mode_reported_in_configuration'] == 'mock'
    encoded = json.dumps(result)
    for secret in ('BACKEND_SECRET', 'CONFIG_SECRET', 'CONFIG_ENDPOINT', 'UPLOAD_SECRET', 'SECRET_NAME',
                   'PRIVATE_LOCAL_RECORDING', 'reported-model'):
        assert secret not in encoded
    request['prior_context']['nested']['empty'].append('changed exported copy')
    request['requested_settings']['specialists'].append('literature')
    assert saved == original


@pytest.mark.parametrize('mode,status,abstained', [('Demo', 'complete', False), ('Mock', 'complete', True),
                                                ('Live', 'cancelled', False), ('Live', 'error', False),
                                                ('Live', 'unfamiliar', False)])
def test_mode_outcome_and_recording_meaning_stay_explicit(mode, status, abstained):
    saved = record(mode=mode)
    saved['run'].status, saved['run'].abstained = status, abstained
    result = R.request_receipt(saved)
    assert result['submitted_request']['connection_mode'] == mode
    assert result['recorded_outcome']['status'] == status
    assert result['recorded_outcome']['abstained'] == abstained
    if mode == 'Mock':
        assert result['submitted_request']['recording_playback_speed'] == 2.0
        assert 'not the original model invocation' in result['scope']['notes'][0]
    else:
        assert 'recording_playback_speed' not in result['submitted_request']


def test_missing_legacy_request_and_unsupported_fields_are_not_reconstructed_or_stringified():
    saved = record()
    saved['request'] = None
    saved['run'].run_id = ''
    result = R.request_receipt(saved)
    assert result['submitted_request'] is None and result['backend_run_id'] is None
    assert result['recorded_outcome']['question'] == 'Different recorded question'

    class SensitiveObject:
        def __str__(self):
            raise AssertionError('Unsupported objects must not be stringified')

    saved['request'] = SimpleNamespace(question='', mode=None, sample=None,
        config={'reasoning_model': {'api_key': SensitiveObject()}, 'specialists': 'invalid-list',
                'future_secret': SensitiveObject()}, context={'bytes': b'PRIVATE_BYTES'})
    result = json.loads(R.receipt_json(saved))
    assert result['submitted_request']['question'] == ''
    assert result['submitted_request']['connection_mode'] is None
    assert result['submitted_request']['requested_settings'] == {}
    assert result['submitted_request']['requested_settings_omitted_count'] == 3
    assert result['submitted_request']['prior_context'] is None
    assert any('could not be exported as JSON' in note for note in result['scope']['notes'])


def test_empty_context_is_distinct_from_unknown_and_receipt_does_not_read_output_or_uploads():
    class Untouched:
        def __iter__(self):
            raise AssertionError('Unrelated data must remain untouched')

    saved = record()
    saved['request'] = replace(saved['request'], context={}, uploads=Untouched())
    saved['run'].raw = saved['run'].findings = Untouched()
    assert R.request_receipt(saved)['submitted_request']['prior_context'] == {}


def test_receipt_is_prepared_only_on_open_and_download_is_client_only_and_owner_scoped(monkeypatch):
    visited = []
    original = R.receipt_json
    monkeypatch.setattr(R, 'receipt_json', lambda value: (visited.append(value['id']), original(value))[1])
    app = AppTest.from_string('''
import streamlit as st
from frontend.ui.receipt import render_request_receipt
if 'record' in st.session_state:
    render_request_receipt(st.session_state.record, key='receipt:' + st.session_state.record['id'])
''').run()
    app.session_state['record'] = record()
    app.run()
    assert visited == [] and not app.json and not app.get('download_button')
    app.session_state['receipt:local-one:open'] = True
    app.run()
    assert visited == ['local-one']
    payload = json.loads(app.json[0].value)
    assert payload['session_record_id'] == 'local-one'
    assert app.get('download_button')[0].proto.ignore_rerun
    app.session_state['record'] = record('local-two')  # Same backend ID, different saved entry.
    app.run()
    assert visited == ['local-one'] and not app.json and not app.get('download_button')
    app.session_state['receipt:local-two:open'] = True
    app.run()
    assert visited == ['local-one', 'local-two']
    assert json.loads(app.json[0].value)['session_record_id'] == 'local-two'
    assert not app.exception
