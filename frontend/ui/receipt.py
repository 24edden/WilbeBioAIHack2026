"""Export the saved request subset, never connection details or source-file bytes."""
import json
import math
import re

import streamlit as st

from .details import render_details

SETTING_FIELDS = ('task_mode', 'specialists', 'reasoning_model', 'variant_model', 'embedding_model')


def _settings(config):
    if not isinstance(config, dict):
        return None, None
    kept = {}
    for name in SETTING_FIELDS:
        if name not in config:
            continue
        value = config[name]
        valid = (value is None or (isinstance(value, list) and all(isinstance(role, str) for role in value))) \
            if name == 'specialists' else value is None or isinstance(value, str)
        if valid:
            kept[name] = value.copy() if isinstance(value, list) else value
    return kept, len(config) - len(kept)


def request_receipt(record):
    """Preserve request values; omitted/missing metadata is explicit, not inferred."""
    state, request = record['run'], record.get('request')
    notes = []
    submitted = None
    if request is None:
        notes.append('The submitted request was not retained for this record.')
    else:
        settings, omitted = _settings(getattr(request, 'config', None))
        context = getattr(request, 'context', None)
        try:
            # This also makes an independent JSON-safe copy without stringifying
            # unsupported objects (which could expose bytes or object internals).
            context = json.loads(json.dumps(context, ensure_ascii=False, allow_nan=False))
        except (TypeError, ValueError, OverflowError):
            context = None
            notes.append('Saved prior context could not be exported as JSON without changing it; it is unavailable here.')
        mode = getattr(request, 'mode', None)
        speed = getattr(request, 'speed', None)
        if not isinstance(speed, (int, float)) or isinstance(speed, bool) or not math.isfinite(speed):
            speed = None
        submitted = {
            'question': getattr(request, 'question', None),
            'connection_mode': mode,
            'sample_requested': getattr(request, 'sample', None),
            'requested_settings': settings,
            'requested_settings_omitted_count': omitted,
            'prior_context': context,
        }
        if mode == 'Mock':
            submitted['recording_playback_speed'] = speed
            notes.append('This request played a recording; it is not the original model invocation.')
    config = state.config if isinstance(state.config, dict) else {}
    execution_mode = config.get('run_mode')
    return {
        'schema': 'trace.request-receipt',
        'schema_version': 1,
        'session_record_id': record['id'],
        'backend_run_id': state.run_id or None,
        'submitted_request': submitted,
        'recorded_outcome': {
            'question': state.question,
            'status': state.status or None,
            'terminal_received': state.complete,
            'abstained': state.abstained,
            'execution_mode_reported_in_configuration': execution_mode if isinstance(execution_mode, str) else None,
        },
        'scope': {
            'description': 'A receipt of saved request fields and outcome metadata, not the full provider prompt, '
                           'a reproducibility bundle or a file that can resume a session.',
            'requested_settings_allowlist': list(SETTING_FIELDS),
            'excluded': ['uploaded file contents and names', 'backend connection URL and credentials',
                         'local recording path', 'unlisted or unsupported configuration fields',
                         'provider instructions', 'full results and raw event payloads'],
            'notes': notes,
        },
    }


def receipt_json(record):
    return json.dumps(request_receipt(record), ensure_ascii=False, allow_nan=False, indent=2)


def render_request_receipt(record, *, key, label='Request receipt for this result'):
    def prepare():
        st.caption('Saves this record’s submitted question, carried context and requested settings. '
                   'Uploaded files, connection details and the full model prompt are not included.')
        st.caption('This receipt cannot restore a session or reproduce execution. Missing saved fields stay unknown.')
        st.text(f"Session record ID: {record['id']}")
        encoded = receipt_json(record)
        st.json(encoded, expanded=False)
        # Session IDs are application-generated; sanitize legacy identifiers for
        # the download name without changing their exact value in the receipt.
        safe_id = re.sub(r'[^A-Za-z0-9_-]', '_', str(record['id']))[:64] or 'saved-result'
        st.download_button('Download request receipt (.json)', encoded.encode('utf-8'),
                           file_name=f'trace-request-{safe_id}.json', mime='application/json',
                           key=f'{key}:download', on_click='ignore')

    render_details(label, prepare, key=f'{key}:open', lazy=True)
