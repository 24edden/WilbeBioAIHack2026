"""Read-only Team TBD presentation using the pet branch's assets and theme.

No scientific execution controls or backend mutations are exposed here.
"""
from collections import Counter
from datetime import datetime, timezone
from html import escape
import io
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

from .appearance import toggle_theme
from .pets import pet_picture, LABELS
from .network_svg import network_svg
from .team_tbd_adapter import Capsule, LiveSource

PAGES = ['Overview', 'Findings', 'Team', 'Evidence', 'NVIDIA & sequences', 'Handoffs & review', 'Next steps', 'History']
SOURCES = {'brev-main': os.environ.get('TEAM_TBD_MAIN_URL', 'http://127.0.0.1:8081'),
           'mac-ana-isolated': os.environ.get('TEAM_TBD_ANA_URL', 'http://127.0.0.1:8082')}


def prose(value, tag='p', css=''):
    """Scientific content is text, never trusted HTML or active Markdown."""
    if value is not None:
        st.markdown(f'<{tag} class="{css}">{escape(str(value)).replace(chr(10), "<br>")}</{tag}>', unsafe_allow_html=True)


def record(value, label='Exact saved record'):
    with st.expander(label):
        st.json(value, expanded=False)


def refs(ids, evidence):
    for evidence_id in ids or []:
        item = next((e for e in evidence if e.get('id') == evidence_id), None)
        with st.expander(str(evidence_id)):
            if item:
                prose(item.get('title'), 'h4')
                prose(item.get('summary'))
                st.json(item, expanded=False)
            else:
                st.caption('Reference retained; this record is not present in this snapshot.')


@st.cache_resource
def capsule_at(root):
    return Capsule(root)


@st.cache_resource
def live_source_at(base):
    return LiveSource(base)


@st.cache_data(ttl=15, show_spinner=False)
def load_bundle(root, mode, source_id, run_id):
    source = capsule_at(root) if mode == 'Frozen replay' else live_source_at(SOURCES[source_id])
    return source.load(run_id), datetime.now(timezone.utc).isoformat(timespec='seconds')


def render_workspace():
    root = os.environ['TEAM_TBD_CAPSULE']
    st.markdown('<style>' + (Path(__file__).resolve().parents[1] / 'static' / 'team_tbd.css').read_text() + '</style>', unsafe_allow_html=True)
    st.markdown('<div class="tbd-marker"></div>', unsafe_allow_html=True)
    try:
        capsule = capsule_at(root)
    except Exception as exc:
        st.error(f'Could not open the configured frozen results: {exc}')
        return
    with st.container(key='workspace_header'):
        brand, theme, settings = st.columns([6, 1, .5], vertical_alignment='center')
        with brand:
            with st.container(key='trace_home'):
                if st.button('TRACE', help='Return to completed studies'):
                    st.session_state.tbd_page = 'Overview'
                    st.rerun()
        with theme:
            st.button('☾ Dark mode' if st.session_state.ui_theme == 'light' else '☀ Light mode', on_click=toggle_theme)
        with settings:
            with st.popover('Settings', icon=':material/settings:'):
                st.markdown('<div class="trace-setup-marker"></div>', unsafe_allow_html=True)
                st.subheader('Study connection')
                st.caption('A read-only view of the existing Team TBD workbench.')
                st.write('Frozen replay verifies files against the sealed capsule. Live reads fetch the selected existing run from its original service.')
                st.write('Model, agent, skill and governance settings are preserved with each run.')
                st.caption('Private preview · loopback only')
                st.link_button('Open original workbench', SOURCES['brev-main'])
    st.markdown('<div class="tbd-eyebrow">TEAM TBD / COMPLETED STUDIES</div>', unsafe_allow_html=True)
    featured = capsule.manifest.get('featured_run_ids', [])
    entries = sorted(capsule.runs, key=lambda r: (r['run_id'] not in featured, featured.index(r['run_id']) if r['run_id'] in featured else 99))
    ids = [r['run_id'] for r in entries]
    by_id = {r['run_id']: r for r in entries}
    initial = st.query_params.get('run', ids[0])
    if initial not in ids:
        initial = ids[0]
    a, b = st.columns([2.6, 1])
    with a:
        run_id = st.selectbox('Study', ids, index=ids.index(initial), format_func=lambda x: by_id[x]['label'], key='tbd_study')
    with b:
        mode = st.selectbox('Connection', ['Frozen replay', 'Live reads'], index=1 if st.query_params.get('mode') == 'live' else 0, key='tbd_mode')
    st.query_params['run'] = run_id
    st.query_params['mode'] = 'live' if mode == 'Live reads' else 'replay'
    meta = by_id[run_id]
    if mode == 'Live reads':
        x, y = st.columns([3, 1])
        with x:
            auto = st.toggle('Refresh existing run every 15 seconds', value=False)
        with y:
            if st.button('Refresh now'):
                load_bundle.clear()
    else:
        auto = False
    st.session_state.setdefault('tbd_page', 'Overview')
    page = st.radio('Explore this study', PAGES, horizontal=True, key='tbd_page', label_visibility='collapsed')

    @st.fragment(run_every=15 if auto else None)
    def body():
        try:
            bundle, checked = load_bundle(root, mode, meta['source_id'], run_id)
        except Exception as exc:
            st.error(f'{mode} unavailable: {exc}')
            st.caption('No substitute data was loaded. Choose Frozen replay explicitly to inspect the sealed snapshot.')
            return
        run, view = bundle['run'], bundle['view']
        if mode == 'Frozen replay':
            st.caption(f'FROZEN REPLAY · Read-only snapshot · {capsule.manifest.get("created_at", "")} · No new analysis')
        else:
            location = 'Brev via private tunnel' if meta['source_id'] == 'brev-main' else 'Mac · independent Ana service'
            st.caption(f'LIVE BACKEND READ · {location} · Fetched {checked} · Run {run.get("status", "unknown")} · No new analysis')
        source = capsule if mode == 'Frozen replay' else live_source_at(SOURCES[meta['source_id']])
        render_page(page, bundle, source)
        st.markdown('<div class="tbd-footer">Team TBD · Saved scientific work products and execution records · Research use</div>', unsafe_allow_html=True)
    body()


def render_page(page, bundle, source):
    run, view, evidence = bundle['run'], bundle['view'], bundle['evidence']
    brief = view.get('findings') or {}
    if page == 'Overview':
        question = view.get('question') or run.get('hypothesis') or {}
        prose(question.get('text', '').split('\n')[0], css='tbd-question')
        with st.expander('Original question & provenance'):
            prose(question.get('text'))
            record(question, 'Exact original question record')
        headline = brief.get('headline') or 'No completed research brief is available'
        summary = brief.get('plain_summary') or run.get('error') or 'Inspect the preserved status, partial work and evidence in this historical run.'
        st.markdown(f'<section class="trace-pet-stage tbd-summary"><div class="trace-pet-scene"><div class="trace-pet-character">{pet_picture("coordinator")}<strong>Team TBD</strong></div><article><div class="tbd-eyebrow">{escape(run.get("status", "unknown"))} · SAVED FINDING</div><h1>{escape(headline)}</h1><p>{escape(summary)}</p></article></div></section>', unsafe_allow_html=True)
        answer = brief.get('proposed_answer') or {}
        prose(answer.get('scope'), css='tbd-scope')
        a, b, c = st.columns(3)
        a.metric('Decision versions', len(run.get('decisions', [])))
        b.metric('Recorded handoffs', len(run.get('handoffs', [])))
        c.metric('Human review', run.get('review_status', 'unknown').replace('_', ' ').title())
        with st.expander('What this finding does—and does not—support'):
            prose(answer.get('statement'))
            prose(answer.get('caveat'))
            prose(answer.get('strongest_alternative'))
        st.caption('Both featured studies reuse GSE28460. They are different questions about the same cohort, not independent replication.')
    elif page == 'Findings':
        st.title('What the evidence says')
        prose(brief.get('plain_summary'))
        for i, finding in enumerate(brief.get('findings', []), 1):
            with st.container(border=True):
                st.caption(f'FINDING {i:02d}')
                prose(finding.get('what'), css='tbd-finding')
                with st.expander('Why it matters & supporting evidence'):
                    prose(finding.get('why_it_matters'))
                    refs(finding.get('evidence_ids'), evidence)
        if not brief:
            st.info('This historical run has no research brief. Its partial records remain available in the other views.')
    elif page == 'Team':
        render_team(run, brief, evidence)
    elif page == 'Evidence':
        st.title('Evidence, with its limits')
        st.caption(f'{len(evidence)} saved records. Measured data, literature, predictions and proposals keep their original qualifications.')
        search = st.text_input('Find evidence', placeholder='Search a title, ID or summary')
        items = [e for e in evidence if search.lower() in json.dumps(e).lower()]
        if not items:
            st.info('No matching evidence.')
        for e in items:
            with st.expander(f'{e.get("id", "")} · {e.get("title", "Evidence")}'):
                prose(e.get('kind'), css='tbd-eyebrow')
                prose(e.get('summary'))
                src = e.get('source') or {}
                prose(src.get('name'), 'h4')
                prose(src.get('locator'))
                st.json({'source': src, 'values': e.get('values')}, expanded=False)
    elif page == 'NVIDIA & sequences':
        render_nvidia(run, brief, bundle['artifacts'], source)
    elif page == 'Handoffs & review':
        render_review(run, brief, evidence)
    elif page == 'Next steps':
        st.title('The next experiment')
        st.caption('Saved proposals and prerequisites. Nothing on this page launches new work.')
        proposal = brief.get('recommended_next_step') or {}
        prose(proposal.get('action'), css='tbd-finding')
        prose(proposal.get('why'))
        for key, label in [('positive_result', 'What would support it'), ('negative_result', 'What would challenge it'), ('prerequisites', 'Required before execution')]:
            with st.expander(label):
                value = proposal.get(key)
                if isinstance(value, list):
                    for item in value: prose(item)
                else: prose(value)
        record(brief.get('modeling_draft') or {}, 'Proposed modeling work & missing inputs')
        state = run.get('governance_state') or {}
        st.subheader('Where the investigation stopped')
        prose(state.get('stop_reason'))
        prose(state.get('reason'))
        record(run.get('followup_operations', []), 'Executed follow-up records and their exact statuses')
    elif page == 'History':
        render_history(run, view)


def render_team(run, brief, evidence):
    st.title('Meet the scientific team')
    st.caption('Recorded contributions. Choose a scientist to inspect their work and applied skills.')
    roles = list(dict.fromkeys(h['sender'] for h in run.get('handoffs', [])))
    if not roles:
        st.info('No accepted specialist handoffs in this run.')
        return
    summaries = {s['role']: s for s in brief.get('role_summaries', [])}
    columns = st.columns(3)
    for i, role in enumerate(roles):
        with columns[i % 3]:
            with st.container(border=True):
                st.markdown(f'<div class="tbd-role">{pet_picture(role, css_class="pet-roster-image")}<strong>{escape(LABELS.get(role, role))}</strong></div>', unsafe_allow_html=True)
                prose(summaries.get(role, {}).get('what_found', 'Saved specialist work product available.'))
                if st.button('View work', key='role_' + role, width='stretch'):
                    st.session_state.tbd_role = role
    if st.session_state.get('tbd_role') not in roles:
        st.session_state.tbd_role = roles[0]
    role = st.selectbox('Scientist work product', roles, format_func=lambda r: LABELS.get(r, r), key='tbd_role')
    summary = summaries.get(role, {})
    prose(summary.get('why_it_matters'))
    handoffs = [h for h in run.get('handoffs', []) if h['sender'] == role]
    index = st.selectbox('Saved handoff', range(len(handoffs)), index=len(handoffs) - 1,
        format_func=lambda i: f'{i+1} · {handoffs[i].get("created_at", "")} · {handoffs[i].get("result_status", "unknown")}')
    h = handoffs[index]
    prose(h.get('result'), css='tbd-finding')
    with st.expander('Method, limitations & evidence'):
        prose(h.get('method'))
        for limitation in h.get('limitations', []): prose(limitation)
        for claim in h.get('claims', []):
            prose(claim.get('text'))
            refs(claim.get('evidence_ids'), evidence)
    with st.expander('Applied skills & actual model'):
        prose('Model: ' + str(h.get('model', 'not recorded')))
        st.caption('Applied instructions have separate provenance from model inference. Rosalind-informed guidance is not GPT-Rosalind inference.')
        skills = [s for s in run.get('skill_receipts', []) if s.get('id') in h.get('skill_receipt_ids', [])]
        for skill in skills:
            prose(f'{skill.get("name")} · {skill.get("version")}')
            st.caption(str(skill.get('origin', '')))
        st.json(skills, expanded=False)
    record(h, 'Exact handoff, hashes and accepted input versions')


def render_nvidia(run, brief, artifacts, source):
    st.title('NVIDIA predictions & exact inputs')
    st.caption('Saved target-monomer predictions are exploratory structural evidence. They do not measure binding, patient causation or clinical efficacy.')
    prose((brief.get('nvidia') or {}).get('summary'))
    for operation in run.get('followup_operations', []):
        receipts = operation.get('provider_receipts', [])
        if not receipts:
            continue
        prose(f'Follow-up workflow: {operation.get("status", "unknown")} · result: {operation.get("result_status", "unknown")}', css='tbd-scope')
        for receipt in receipts:
            with st.expander(f'{receipt.get("label", "Prediction")} · {receipt.get("model", "NVIDIA")} · {receipt.get("status", "unknown")}'):
                st.json(receipt, expanded=True)
    for section in ['learned', 'not_established']:
        for item in (brief.get('nvidia') or {}).get(section, []):
            prose(item)
    st.subheader('Artifacts')
    for i, artifact in enumerate(artifacts):
        with st.expander(artifact.get('name', f'Artifact {i+1}')):
            prose(artifact.get('scope'))
            st.caption('Artifact bytes are retrieved only when requested and checked against recorded hashes where available.')
            identity = [str(getattr(source, 'base', getattr(source, 'root', ''))), run['id'], artifact.get('url', artifact.get('path')), artifact.get('sha256')]
            cache_key = 'artifact:' + hashlib.sha256(json.dumps(identity).encode()).hexdigest()
            if st.button('Load artifact', key=cache_key + ':load'):
                try:
                    st.session_state[cache_key] = source.artifact_bytes(artifact)
                except Exception as exc:
                    st.error(f'Artifact unavailable: {exc}')
            if cache_key in st.session_state:
                data = st.session_state[cache_key]
                st.download_button('Download verified artifact', data=data, file_name=artifact.get('name', 'artifact'), key=cache_key + ':download')
                if artifact.get('name', '').endswith('.tsv'):
                    import pandas as pd
                    st.dataframe(pd.read_csv(io.BytesIO(data), sep='\t', nrows=30), hide_index=True)
            st.json(artifact, expanded=False)
    st.subheader('Sequence discovery')
    for discovery in run.get('sequence_discoveries', []):
        prose(discovery.get('summary'))
        st.caption(f'Status: {discovery.get("status")} · Human review: {discovery.get("human_review_status")} · Target retention established: {discovery.get("target_retention_established")} · NVIDIA submitted: {discovery.get("nvidia_submitted")}')
        for seq in discovery.get('sequences', []):
            with st.expander(f'{seq.get("label", "Sequence")} · {seq.get("role", "")}'):
                st.code(seq.get('sequence', ''), language=None, wrap_lines=True)
                st.json(seq, expanded=False)
        with st.expander('Missing inputs and qualifications'):
            prose(discovery.get('qualification_note'))
            for item in discovery.get('missing_inputs', []): prose(item)
    for saved in run.get('research_briefs', []):
        audit = saved.get('molecular_audit') or {}
        for seq in audit.get('sequence_inventory', []):
            with st.expander(f'Prediction input · {seq.get("label")} · {seq.get("length")} residues'):
                st.caption('Exact input used for the saved prediction; distinct from subsequently discovered deposited constructs.')
                st.code(seq.get('sequence', ''), language=None, wrap_lines=True)
                st.json(seq, expanded=False)
    if not artifacts and not run.get('sequence_discoveries'):
        st.info('No NVIDIA artifacts or discovered sequences are recorded for this run.')


def render_review(run, brief, evidence):
    st.title('How the team reached this point')
    handoffs = run.get('handoffs', [])
    roles = list(dict.fromkeys([h['sender'] for h in handoffs] + [r for h in handoffs for r in h.get('recipient', [])]))
    counts = Counter((h['sender'], r) for h in handoffs for r in h.get('recipient', []))
    agents = {r: SimpleNamespace(id=r, role='Human scientist' if r=='scientist' else r, parent_id=None, layout_row=i//3, alignment='neutral', status='recorded' if any(h['sender']==r for h in handoffs) else 'recipient', activity=sum(h['sender'] == r for h in handoffs)) for i, r in enumerate(roles)}
    state = SimpleNamespace(agents=agents, edges=set(), talk=counts, active_id=None, complete=True,
        activity_label='handoffs', network_description=f'{len(roles)} recorded participants, including recipient-only roles. Dashed arrows show handoff recipients; no spawning is inferred.')
    st.caption('Dashed arrows show recorded handoff recipients. This is a saved communication map, not live agent activity.')
    st.markdown(network_svg(state), unsafe_allow_html=True)
    st.subheader('Immutable decision versions')
    for d in run.get('decisions', []):
        with st.expander(f'Version {d.get("version")} · {d.get("assessment", "unknown")} · {d.get("review_status_at_issue", "unknown")}'):
            prose(d.get('summary'))
            for item in d.get('limitations', []): prose(item)
            st.json(d, expanded=False)
    st.subheader('Accepted handoffs')
    if handoffs:
        n = st.selectbox('Handoff', range(len(handoffs)), format_func=lambda i: f'{i+1}. {LABELS.get(handoffs[i]["sender"], handoffs[i]["sender"])} → {", ".join(handoffs[i].get("recipient", []))}')
        h = handoffs[n]
        prose(h.get('result'))
        record(h, 'Handoff inputs, claims, method and routing')
    with st.expander(f'Contract checks ({len(run.get("stage_evaluations", []))})'):
        st.caption('Acceptance verifies the software and evidence contract; it does not establish scientific validity.')
        checks = run.get('stage_evaluations', [])
        st.dataframe([{'stage': c.get('stage'), 'verdict': c.get('verdict'), 'result': c.get('result_status'), 'reason': c.get('reason')} for c in checks], hide_index=True)
        st.json(checks, expanded=False)
    record(run.get('governance_state', {}), 'Recorded governance state')


def render_history(run, view):
    st.title('Saved activity & model receipts')
    usage = run.get('usage') or {}
    columns = st.columns(4)
    for col, field, label in zip(columns, ['model_calls', 'tool_calls', 'input_tokens', 'output_tokens'], ['Model calls', 'Tool calls', 'Input tokens', 'Output tokens']):
        col.metric(label, f'{usage.get(field, 0):,}')
    st.caption('Aggregate counts are from run.usage. Overlapping model receipts are not added again.')
    events = run.get('events', [])
    with st.expander('Replay a recorded update', expanded=True):
        st.caption('READ-ONLY REPLAY · Move through saved public updates. No new model calls or scientific work occur.')
        if events:
            idx = st.slider('Recorded update', 1, len(events), 1)
            e = events[idx-1]
            role = e.get('agent', 'coordinator')
            st.markdown(f'<div class="tbd-replay">{pet_picture(role, css_class="pet-roster-image")}<div><small>{escape(str(e.get("time", "")))} · {escape(str(e.get("status", "")))}</small><h3>{escape(str(e.get("title", "")))}</h3><p>{escape(str(e.get("detail", "")))}</p></div></div>', unsafe_allow_html=True)
            record(e)
    with st.expander('Actual model and request receipts'):
        st.caption('Astra inference, Team TBD instructions, installed OpenAI database skills and NVIDIA skills retain separate provenance.')
        from .team_tbd_adapter import run_view
        for receipt in run_view(run).get('model_receipts', []):
            prose(receipt['source_pointer'])
            st.json(receipt['metadata'], expanded=False)
    with st.expander('All saved events'):
        st.dataframe([{k:e.get(k) for k in ['id', 'time', 'agent', 'title', 'status']} for e in events], hide_index=True)
    st.download_button('Download displayed run JSON', json.dumps(run, indent=2), file_name=f'{run["id"]}-view.json', mime='application/json')
