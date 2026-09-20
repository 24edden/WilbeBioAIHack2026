"""Scientific controls over durable Team TBD records; no inference in the UI."""
from copy import deepcopy
from html import escape
import os
from uuid import uuid4

import streamlit as st

from .appearance import stylesheet as appearance_stylesheet
from .composer import capture_composer_draft, render_composer
from .pets import LABELS, pet_picture, stylesheet as pet_stylesheet
from .team_tbd import (PAGES, SOURCES, open_study, prose, record, render_brand,
                       render_home_studies, render_page, render_workspace, return_to_chat)
from .team_tbd_client import TeamTBDClient, APIError, UncertainWriteError, available_controls
from .theme import stylesheet

ACTIVE = {'queued', 'running'}
ROLE_IDS = ('coordinator', 'clinical_scientist', 'bioinformatician', 'statistician',
            'clinical_pharmacologist', 'molecular_scientist', 'translational_scientist',
            'assay_scientist', 'reviewer')


def configured_base():
    # No implicit legacy transport, demo mode, or alternate live service.
    return os.environ.get('TEAM_TBD_BACKEND_URL', '').strip().rstrip('/')


@st.cache_resource
def client_at(base):
    return TeamTBDClient(base)


def home():
    return_to_chat()
    for key in ('active_run', 'service'):
        st.query_params.pop(key, None)


def open_live(run_id, service='scientific'):
    for key in ('run', 'mode', 'view'):
        st.query_params.pop(key, None)
    st.query_params['active_run'] = run_id
    st.query_params['service'] = service
    st.session_state['_tbd_next_page'] = 'Overview'


def base_for(service):
    if service == 'scientific':
        return configured_base()
    if service in SOURCES:
        return SOURCES[service]
    raise ValueError('Unknown scientific connection.')


def connection(client):
    health = client.health()
    if health.get('service') != 'Team TBD':
        raise ValueError('The configured service is not the Team TBD scientific engine.')
    cases = client.cases()
    st.session_state['scientific_connection'] = {'base': client.base, 'health': health, 'cases': cases}
    return health, cases


def perform(client, action, payload=None, run_id=None, service='scientific'):
    """Persist intent in this session before sending; never blindly repeat work."""
    if st.session_state.get('scientific_pending'):
        st.error('Resolve the pending request before submitting another action.')
        return
    data = deepcopy(payload) if payload is not None else None
    if data is not None:
        data['idempotency_key'] = uuid4().hex
    st.session_state.scientific_pending = {'base': client.base, 'action': action,
        'payload': data, 'run_id': run_id, 'service': service}
    dispatch_pending()


def dispatch_pending():
    pending = st.session_state.scientific_pending
    client = client_at(pending['base'])
    try:
        method = getattr(client, pending['action'])
        if pending['action'] == 'create_run':
            result = method(pending['payload'])
        elif pending['payload'] is None:
            result = method(pending['run_id'])
        else:
            result = method(pending['run_id'], pending['payload'])
    except UncertainWriteError:
        st.warning('The response was interrupted. The server may have accepted this request. '
                   'Its original request key and inputs are retained; no repeat was sent.')
        return
    except (APIError, ValueError) as exc:
        st.session_state.scientific_pending = None
        st.error(str(exc))
        return
    st.session_state.scientific_pending = None
    st.session_state.scientific_notice = 'Request accepted. The recorded status below determines what has completed.'
    st.session_state.scientific_last = (result['id'], pending['service'])
    open_live(result['id'], pending['service'])
    st.rerun()


def pending_panel():
    pending = st.session_state.get('scientific_pending')
    if not pending:
        return
    with st.container(border=True):
        st.warning('A request has an unconfirmed response. Other submissions are paused.')
        st.caption('Keep this page open to retain the original request key. Inspect recorded runs before starting any new request after a lost browser session.')
        if pending['payload'] is not None:
            st.code(pending['payload']['idempotency_key'], language=None)
            if st.button('Reconcile using the same request key', key='scientific_reconcile'):
                dispatch_pending()
        elif pending['run_id']:
            if st.button('Read status of the requested action', key='scientific_reconcile_unkeyed'):
                try:
                    run = client_at(pending['base']).get_run(pending['run_id'])
                    st.session_state.scientific_pending = None
                    open_live(run['id'], pending['service'])
                    st.rerun()
                except (APIError, ValueError) as exc:
                    st.error(str(exc))


def render_header():
    with st.container(key='workspace_header'):
        brand, studies, settings = st.columns([6, 1, .5], vertical_alignment='center')
        with brand, st.container(key='trace_home'):
            st.button('TRACE', key='home', on_click=home, help='Return to the question window')
        with studies:
            st.button('Completed studies', key='tbd_open_studies', on_click=open_study)
        with settings, st.popover('Settings', icon=':material/settings:'):
            st.subheader('Scientific service')
            st.caption('The original nine-role engine owns models, budgets, instructions and scientific review.')
            base = configured_base()
            if base:
                st.code(base, language=None)
                if st.button('Check connection', key='scientific_check'):
                    try:
                        connection(client_at(base))
                        st.success('Connection checked without submitting scientific work.')
                    except (APIError, ValueError) as exc:
                        st.error(str(exc))
            else:
                st.info('A scientific service has not been configured for this deployment.')
            for role in ROLE_IDS:
                st.write(LABELS.get(role, role))
            saved = st.session_state.get('scientific_connection', {})
            if saved.get('base') == base:
                health = saved['health']
                caps = health.get('capabilities', {})
                for provider, cap in caps.items():
                    st.caption(f"{provider}: {cap.get('model', 'unspecified')} · {cap.get('status', 'unknown')}")
                st.caption('Instruction provenance and model entitlement are separate. No connection probe is submitted here.')
                if st.button('Read installed skills and process contract', key='scientific_catalog'):
                    try:
                        st.json(client_at(base).skills(), expanded=False)
                        st.json(client_at(base).process_contract(), expanded=False)
                    except (APIError, ValueError) as exc:
                        st.error(str(exc))


def render_home():
    draft = st.session_state.draft
    st.markdown('<div class="pet-composer-marker"></div><div class="pet-start-heading">'+pet_picture('coordinator', css_class='pet-welcome')+'<h1>What are we investigating?</h1><p>Bring your question. Follow the experts to the next experiment.</p></div>', unsafe_allow_html=True)
    base = configured_base()
    connected = st.session_state.get('scientific_connection', {})
    if connected.get('base') != base:
        connected = {}
    if base and not connected:
        if st.button('Connect scientific service', key='scientific_connect'):
            try:
                connection(client_at(base))
                st.rerun()
            except (APIError, ValueError) as exc:
                st.error(str(exc))
    health, cases = connected.get('health', {}), connected.get('cases', [])
    ready = (bool(cases) and health.get('worker_alive') is True and
             health.get('capabilities', {}).get('rosalind', {}).get('status') == 'verified')
    case_id = None
    source_name = st.session_state.get('scientific_source', 'User message')
    if cases:
        with st.expander('Study context & original source'):
            by_id = {c['id']: c for c in cases}
            case_id = st.selectbox('Registered study context', list(by_id), key='scientific_case',
                                   format_func=lambda value: by_id[value].get('title', value))
            source_name = st.text_input('Original question source', value='User message', max_chars=300, key='scientific_source')
            prose(by_id[case_id].get('description'))
            st.caption('Uses registered evidence and validated analysis recipes. Arbitrary file upload is not supported by this engine.')
            record(by_id[case_id].get('readiness', []), 'Study readiness')
            if st.button('Use this study’s original hypothesis', key='scientific_original'):
                draft.update(question=by_id[case_id]['hypothesis'], composer_id=uuid4().hex)
                st.session_state['_scientific_source_next'] = by_id[case_id].get('hypothesis_source', {}).get('name', 'Registered study hypothesis')
                st.rerun()
        if not ready:
            st.info('New live investigations require an available worker and a verified research model. Check the service configuration, then refresh the connection.')
    note = ('Connected scientific engine · Original question wording is preserved. Starting submits a live investigation.'
            if ready else 'Connect your scientific service to start. Saved studies remain available below.')
    if draft.get('uploads'):
        st.warning('This draft contains legacy attachments. The scientific engine accepts registered evidence; clear the attachments before starting.')
        if st.button('Clear unsupported attachments'):
            draft['uploads'] = []
            st.rerun()
    action = render_composer(draft, question=draft['question'], note=note,
        allow_uploads=False, allow_demo=False, preserve_question=True,
        disabled=not ready or bool(st.session_state.get('scientific_pending')) or bool(draft.get('uploads')))
    if action:
        if action['type'] != 'start' or action.get('uploads'):
            st.error('This scientific workspace supports questions with registered evidence. Demo and arbitrary upload actions are unavailable.')
        elif not ready or case_id is None:
            st.error('Connect a ready scientific service first.')
        elif len(action['question'].strip()) < 10:
            st.error('Supply a scientific question of at least 10 characters.')
        else:
            # Re-read capability and worker state immediately before create.
            try:
                fresh = client_at(base).health()
                if not fresh.get('worker_alive') or fresh.get('capabilities', {}).get('rosalind', {}).get('status') != 'verified':
                    st.error('The scientific service is not ready to accept a live investigation.')
                else:
                    perform(client_at(base), 'create_run', {'case_id': case_id,
                        'hypothesis': action['question'], 'source_name': source_name,
                        'mode': 'live', 'required_analysis_ids': []})
            except (APIError, ValueError) as exc:
                st.error(str(exc))
    if st.session_state.get('scientific_last'):
        if st.button('Return to last investigation', key='scientific_last'):
            open_live(*st.session_state.scientific_last)
            st.rerun()
    render_home_studies()
    if base:
        with st.expander('Your scientific investigations'):
            if st.button('Read investigations', key='scientific_list'):
                try:
                    st.session_state.scientific_runs = {'base': base, 'runs': client_at(base).list_runs()}
                except (APIError, ValueError) as exc:
                    st.error(str(exc))
            catalog = st.session_state.get('scientific_runs', {})
            if catalog.get('base') == base:
                for run in catalog['runs']:
                    question = run.get('hypothesis', {})
                    text = question.get('text', '') if isinstance(question, dict) else str(question)
                    if st.button(f"{text[:85] or run['id']} · {run.get('status', 'unknown')}", key='open:'+run['id']):
                        open_live(run['id'])
                        st.rerun()


def render_controls(client, run, health, service):
    run_id = run['id']
    checkpoint = None
    if run.get('status') not in ACTIVE:
        try:
            checkpoint = client.synthesis_checkpoint(run_id)
        except APIError:
            pass
    gates = available_controls(run, health, checkpoint=checkpoint)
    blocked = bool(st.session_state.get('scientific_pending'))
    version = (run.get('decisions') or [{}])[-1].get('version')
    with st.expander('Continue this investigation', expanded=False):
        st.caption('Actions use the displayed decision version. The server checks current state again before accepting a request. Model work begins only after an explicit submission.')
        st.caption(f"Decision version: {version or 'none'} · Run: {run.get('status')} · Review: {run.get('review_status', 'unknown')}")
        for action, label in [('cancel', 'Request cancellation'), ('resume', 'Resume safely')]:
            if st.button(label, key='action:'+action, disabled=blocked or gates.get(action) is not None,
                         help=gates.get(action)):
                perform(client, action, run_id=run_id, service=service)
        if checkpoint and checkpoint.get('eligible'):
            st.caption('Continue from accepted synthesis inputs: '+str(checkpoint.get('reason', 'checkpoint available')))
            if st.button('Continue synthesis from checkpoint', disabled=blocked or gates.get('continue_synthesis') is not None):
                perform(client, 'continue_synthesis', {'source_operation_id': checkpoint['source_operation_id']}, run_id, service)
        elif checkpoint:
            st.caption('Synthesis continuation: '+str(checkpoint.get('reason', 'unavailable')))
        with st.form('scientific_feedback', clear_on_submit=False):
            text = st.text_area('Scientific feedback or follow-up question', max_chars=6000)
            submitted = st.form_submit_button('Submit feedback for a new decision', disabled=blocked or gates.get('feedback') is not None)
            if submitted:
                perform(client, 'feedback', {'decision_version': version, 'text': text}, run_id, service)
        if gates.get('feedback'):
            st.caption(gates['feedback'])
        try:
            packet = client.followups(run_id)
        except APIError as exc:
            st.error(str(exc))
            packet = {}
        for followup in packet.get('followups', []):
            st.write(followup.get('title', followup['id']))
            prose(followup.get('rationale'))
            st.caption(str(followup.get('reason', '')))
            record(followup, 'Recommendation & prerequisites · '+followup['id'])
            if st.button('Run supported follow-up', key='followup:'+followup['id'],
                         disabled=blocked or gates.get('followup') is not None or not followup.get('executable') or packet.get('decision_version') != version):
                perform(client, 'followup', {'decision_version': packet['decision_version'],
                    'recommendation_id': followup['id']}, run_id, service)
        for action, label in [('research_brief', 'Generate research brief'), ('sequence_discovery', 'Discover qualified sequences')]:
            if st.button(label, disabled=blocked or gates.get(action) is not None, help=gates.get(action)):
                perform(client, action, {'decision_version': version}, run_id, service)
        with st.expander('Record an experimental measurement'):
            st.caption('Supply an actual measured outcome with its experiment and candidate identifiers. Predictions do not count as measurements.')
            with st.form('scientific_outcome'):
                experiment = st.text_input('Experiment ID', max_chars=100)
                candidate = st.text_input('Candidate ID', max_chars=100)
                endpoint = st.text_input('Measured endpoint', max_chars=200)
                value = st.number_input('Measured value', value=0.0)
                unit = st.text_input('Unit', max_chars=100)
                notes = st.text_area('Measurement source and notes', max_chars=6000)
                if st.form_submit_button('Submit measured outcome', disabled=blocked or gates.get('outcome') is not None):
                    perform(client, 'outcome', {'decision_version': version, 'experiment_id': experiment,
                        'candidate_id': candidate, 'endpoint': endpoint, 'value': float(value), 'unit': unit, 'notes': notes}, run_id, service)
        with st.expander('Qualified NVIDIA comparison'):
            st.caption('Requires retained accessible target and exact, distinct reference and candidate constructs. A submitted job is not a completed prediction.')
            with st.form('scientific_modeling'):
                target = st.text_area('Exact target amino-acid sequence', max_chars=1800)
                reference = st.text_area('Exact reference binder sequence', max_chars=900)
                candidate = st.text_area('Exact candidate binder sequence', max_chars=900)
                note = st.text_area('Sequence source and construct qualification', max_chars=6000)
                retained = st.checkbox('I attest that the accessible target is retained in the relevant context')
                if st.form_submit_button('Submit qualified comparison', disabled=blocked or gates.get('modeling') is not None):
                    if not retained:
                        st.error('Target-retention attestation is required.')
                    else:
                        perform(client, 'modeling', {'decision_version': version, 'target_sequence': target,
                            'reference_binder': reference, 'candidate_binder': candidate, 'source_note': note,
                            'target_retained': True}, run_id, service)


def render_live():
    service = st.query_params.get('service', 'scientific')
    run_id = st.query_params['active_run']
    try:
        client = client_at(base_for(service))
        bundle = client.load(run_id)
        health = client.health()
    except (APIError, ValueError) as exc:
        st.error(f'Scientific connection unavailable: {exc}')
        st.caption('No substitute data or demo was loaded.')
        if st.button('Try reading again'):
            st.rerun()
        return
    run = bundle['run']
    st.session_state.scientific_last = (run_id, service)
    st.caption(f"LIVE SCIENTIFIC RECORD · {run.get('status', 'unknown')} · {client.base} · {run_id}")
    if run.get('cancel_requested') and run.get('status') in ACTIVE:
        st.info('Cancellation requested. Already submitted provider work may still complete; waiting for the durable status.')
    if st.session_state.get('scientific_notice'):
        st.info(st.session_state.pop('scientific_notice'))
    if run.get('error'):
        prose(run['error'])
    if st.button('Refresh recorded status', key='scientific_refresh'):
        st.rerun()
    auto = st.toggle('Refresh status every 5 seconds', value=run.get('status') in ACTIVE, key='scientific_poll:'+run_id)
    if '_tbd_next_page' in st.session_state:
        st.session_state.tbd_page = st.session_state.pop('_tbd_next_page')
    if st.session_state.get('tbd_page') not in PAGES:
        st.session_state.tbd_page = 'Overview'
    page = st.radio('Explore this investigation', PAGES, horizontal=True, key='tbd_page')
    render_controls(client, run, health, service)

    @st.fragment(run_every=5 if auto else None)
    def body():
        try:
            current = client.load(run_id) if auto else bundle
        except (APIError, ValueError) as exc:
            st.error(f'Status refresh failed: {exc}')
            return
        if current['run'].get('status') != run.get('status'):
            st.rerun(scope='app')
        events = current['run'].get('events', [])
        if current['run'].get('status') in ACTIVE:
            latest = events[-1] if events else {}
            agent = str(latest.get('agent', 'coordinator'))
            role = next((r for r in ROLE_IDS if agent in (r, LABELS.get(r))), 'coordinator')
            label = LABELS.get(agent, agent)
            st.markdown('<section class="trace-pet-stage"><div class="trace-pet-scene"><div class="trace-pet-character">'+pet_picture(role, animate=True)+'<strong>'+escape(label)+'</strong></div><article><h2>'+escape(str(latest.get('title', 'Waiting for recorded activity')))+'</h2><p>'+escape(str(latest.get('detail', 'The durable worker owns the investigation.')))+'</p></article></div></section>', unsafe_allow_html=True)
            st.caption('Recorded event · '+str(latest.get('id', 'pending'))+' · '+str(latest.get('status', current['run']['status'])))
        render_page(page, current, client)
    body()


def render():
    st.session_state.ui_theme = 'dark'
    st.session_state.astral_theme = False
    st.session_state.setdefault('stage', 'prompt')
    st.session_state.setdefault('job', None)
    st.session_state.setdefault('draft', {'composer_id': uuid4().hex, 'question': '', 'uploads': [], 'mode': 'Live', 'appearance': 'team-tbd'})
    st.session_state.draft['appearance'] = 'team-tbd'
    if '_scientific_source_next' in st.session_state:
        st.session_state.scientific_source = st.session_state.pop('_scientific_source_next')
    capture_composer_draft(st.session_state.draft)
    st.markdown(stylesheet('dark'), unsafe_allow_html=True)
    st.markdown(pet_stylesheet(), unsafe_allow_html=True)
    st.markdown(appearance_stylesheet('dark'), unsafe_allow_html=True)
    render_brand()
    if 'active_run' not in st.query_params and ('run' in st.query_params or 'view' in st.query_params):
        if not os.environ.get('TEAM_TBD_CAPSULE'):
            render_header()
            st.info('The private saved-study capsule is not installed. Connect to a service and open its recorded investigations from the question window.')
        else:
            render_workspace()
        return
    render_header()
    pending_panel()
    if 'active_run' in st.query_params:
        render_live()
    else:
        render_home()
