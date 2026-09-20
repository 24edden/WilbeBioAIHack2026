"""Inspectable, read-only collaboration using recorded Team TBD relationships.

Recipient routes and explicitly consumed upstream work are different relations.
Only the saved handoff IDs, acceptance IDs and operation IDs connect records here.
"""
from collections import Counter
from html import escape
from types import SimpleNamespace
from urllib.parse import urlsplit

import streamlit as st

from .network_svg import network_svg
from .pets import LABELS, pet_picture


def role_label(role):
    if role == 'scientist':
        return 'Human scientist'
    return LABELS.get(role, str(role or 'Unspecified participant').replace('_', ' ').title())


def _text(value, tag='p', css=''):
    if value not in (None, ''):
        st.markdown(f'<{tag} class="{css}">{escape(str(value)).replace(chr(10), "<br>")}</{tag}>', unsafe_allow_html=True)


def _exact(value, label='Exact saved record'):
    with st.expander(label):
        st.json(value, expanded=False)


def _recipients(handoff):
    value = handoff.get('recipient') or []
    return [value] if isinstance(value, str) else value


def collaboration_index(run):
    """Index explicit routes and consumption; never infer a dependency from order."""
    handoffs = run.get('handoffs') or []
    by_id = {h['id']: h for h in handoffs if h.get('id')}
    roles = list(dict.fromkeys([h.get('sender', 'unknown') for h in handoffs]
                              + [r for h in handoffs for r in _recipients(h)]))
    return {
        'handoffs': handoffs,
        'by_id': by_id,
        'roles': roles,
        'outgoing': {role: [h for h in handoffs if h.get('sender') == role] for role in roles},
        'incoming': {role: [h for h in handoffs if role in _recipients(h)] for role in roles},
        'consumers': {hid: [h for h in handoffs if hid in (h.get('input_versions') or {}).get('upstream_handoff_ids', [])]
                      for hid in by_id},
        'routes': Counter((h.get('sender', 'unknown'), r) for h in handoffs for r in _recipients(h)),
    }


def _handoff_label(handoff, all_handoffs):
    number = next((i + 1 for i, h in enumerate(all_handoffs) if h is handoff or h.get('id') == handoff.get('id')), '?')
    return f'{number:02d} · {role_label(handoff.get("sender"))} · {handoff.get("result_status", "status unrecorded")}' if isinstance(number, int) else f'{role_label(handoff.get("sender"))} · {handoff.get("id", "Unidentified handoff")}'


def _select_handoff(prefix, handoff):
    """Callbacks run before widgets are instantiated on the following rerun."""
    st.session_state[prefix + ':role'] = handoff.get('sender', 'unknown')
    st.session_state[prefix + ':handoff'] = handoff['id']
    st.session_state[prefix + ':view'] = 'Agent work'


def _select_role(prefix, role):
    st.session_state[prefix + ':role'] = role
    st.session_state[prefix + ':view'] = 'Agent work'


def _relation_button(handoff, run, prefix, key, label=None):
    st.button(label or _handoff_label(handoff, run.get('handoffs') or []), key=key,
              on_click=_select_handoff, args=(prefix, handoff), width='stretch')


def _evidence_detail(item, pinned_hash=None):
    _text(item.get('title'), 'h4')
    st.caption(f'{item.get("id", "Evidence")} · {item.get("kind", "type unrecorded")}')
    _text(item.get('summary'))
    source = item.get('source') or {}
    _text(source.get('name'))
    _text(source.get('locator'))
    url = source.get('url')
    if isinstance(url, str) and urlsplit(url).scheme in {'https', 'http'}:
        st.link_button('Open original source', url)
    if pinned_hash:
        with st.expander('Exact input version used by this agent'):
            st.caption('The source digest pinned in this handoff. Current evidence is shown above; the saved digest identifies the consumed version.')
            st.code(pinned_hash, language=None, wrap_lines=True)
    _exact(item, 'Full evidence record and measured values')


def _request_receipts(run, handoff):
    """Use an exact operation match, then an explicit agent match inside receipts."""
    operation_id = handoff.get('operation_id')
    if not operation_id:
        return []
    result, seen = [], set()
    for decision in run.get('decisions') or []:
        if decision.get('operation_id') != operation_id:
            continue
        metadata = decision.get('metadata') or {}
        for request in metadata.get('requests') or []:
            if request.get('agent') != handoff.get('sender'):
                continue
            identity = request.get('request_id') or request.get('request_sha256') or str(request)
            if identity not in seen:
                seen.add(identity)
                result.append(request)
    return result


def render_handoff_detail(run, handoff, evidence, *, key_prefix='tbd_handoff', navigation_prefix=None):
    """Render one exact work product, optionally enabling handoff-to-handoff navigation."""
    index = collaboration_index(run)
    handoff_id = handoff.get('id', 'unidentified')
    prefix = f'{key_prefix}:{run.get("id", "unknown-run")}:{handoff_id}'
    inputs = handoff.get('input_versions') or {}
    source_ids = inputs.get('evidence_ids') or []
    upstream = inputs.get('upstream_handoff_ids') or []
    downstream = index['consumers'].get(handoff_id, [])
    recipients = ', '.join(role_label(r) for r in _recipients(handoff)) or 'No recipient recorded'
    _text(f'{role_label(handoff.get("sender"))} → {recipients}', 'div', 'tbd-handoff-route')
    st.caption(f'Created {handoff.get("created_at", "time unrecorded")} · Scientific result: {handoff.get("result_status", "unrecorded")} · Contract: {handoff.get("acceptance_status", "unrecorded")}')

    left, right = st.columns(2)
    with left:
        st.markdown('**Inputs from other agents**')
        if not upstream:
            st.caption('No upstream handoff is declared. This work starts from its pinned evidence packet.')
        for number, hid in enumerate(upstream):
            linked = index['by_id'].get(hid)
            if linked and navigation_prefix:
                _relation_button(linked, run, navigation_prefix, prefix + f':upstream:{number}', '← ' + _handoff_label(linked, index['handoffs']))
            elif linked:
                _text(_handoff_label(linked, index['handoffs']))
                _exact(linked, 'Upstream work product')
            else:
                st.caption(f'Referenced upstream record is absent from this snapshot: {hid}')
    with right:
        st.markdown('**Work that explicitly used this handoff**')
        if not downstream:
            st.caption('No later handoff declares this record as an input. The recipient route is still recorded above.')
        for number, linked in enumerate(downstream):
            if navigation_prefix:
                _relation_button(linked, run, navigation_prefix, prefix + f':downstream:{number}', _handoff_label(linked, index['handoffs']) + ' →')
            else:
                _text(_handoff_label(linked, index['handoffs']))
                _exact(linked, 'Downstream work product')

    work_tab, evidence_tab, skills_tab, checks_tab = st.tabs(['Work & conclusions', 'Inputs & evidence', 'Skills & model', 'Checks & decisions'])
    with work_tab:
        st.subheader('What this agent handed over')
        _text(handoff.get('result') or 'No result text was saved.', css='tbd-finding')
        with st.expander('Question, method and affected decision'):
            st.markdown('**Question assigned**')
            _text(handoff.get('question'))
            st.markdown('**How the work was done**')
            _text(handoff.get('method'))
            st.markdown('**Decision this could change**')
            _text(handoff.get('decision_it_could_change'))
        limitations = handoff.get('limitations') or []
        with st.expander(f'Limitations retained by this agent ({len(limitations)})'):
            for limitation in limitations:
                _text(limitation)
            if not limitations:
                st.caption('No limitations were recorded.')
        proposals = handoff.get('followup_proposals') or []
        if proposals:
            with st.expander(f'Follow-up proposals from this agent ({len(proposals)})'):
                st.caption('These are proposals in this handoff; their presence does not mean they were executed.')
                for proposal in proposals:
                    _text(proposal.get('title'), 'h4')
                    _text(proposal.get('scientific_question'))
                    _text(proposal.get('rationale'))
                    st.caption(f'Owner: {role_label(proposal.get("owner"))} · Saved status: {proposal.get("status", "unrecorded")}')
                    _exact(proposal, 'Full proposal and prerequisites')

    with evidence_tab:
        st.subheader('Evidence this agent actually received')
        st.caption(f'{len(source_ids)} evidence IDs pinned in this handoff. Select a record to inspect its source and exact input version.')
        lookup = {item.get('id'): item for item in evidence}
        if source_ids:
            evidence_id = st.selectbox('Inspect an input evidence record', source_ids, key=prefix + ':evidence',
                                       format_func=lambda eid: f'{eid} · {lookup.get(eid, {}).get("title", "Record not in snapshot")}')
            item = lookup.get(evidence_id)
            if item:
                _evidence_detail(item, (inputs.get('evidence_versions') or {}).get(evidence_id))
            else:
                st.info('The handoff retains this input reference, but its full record is absent from this snapshot.')
        for number, claim in enumerate(handoff.get('claims') or [], 1):
            with st.expander(f'Claim {number} · {claim.get("kind", "saved claim")}'):
                _text(claim.get('text'))
                for evidence_id in claim.get('evidence_ids') or []:
                    item = lookup.get(evidence_id)
                    if item:
                        with st.expander(f'Supporting record · {evidence_id}'):
                            _evidence_detail(item, (inputs.get('evidence_versions') or {}).get(evidence_id))
                    else:
                        st.caption(f'Referenced evidence is not present in this snapshot: {evidence_id}')
        _exact(inputs, 'Full accepted input packet, versions and hashes')

    with skills_tab:
        st.subheader('Applied instructions and actual model')
        _text(f'Model: {handoff.get("model") or "Not recorded"}', 'h4')
        st.caption(f'Model called: {handoff.get("model_called", "unrecorded")}. Skills are applied instructions with separate provenance; they are not alternative model identities.')
        skill_ids = set(handoff.get('skill_receipt_ids') or [])
        skills = [s for s in run.get('skill_receipts') or [] if s.get('id') in skill_ids]
        for skill in skills:
            with st.expander(f'{skill.get("name", skill.get("skill_id", "Skill"))} · {skill.get("version", "unversioned")}'):
                _text(skill.get('origin'))
                st.caption(f'Loaded {skill.get("loaded_at", "time unrecorded")} · {skill.get("skill_id", "")}')
                st.json(skill, expanded=False)
        missing_skills = skill_ids - {s.get('id') for s in skills}
        if missing_skills:
            st.caption(f'{len(missing_skills)} skill references are retained without a matching receipt in this snapshot.')
        if not skill_ids:
            st.caption('No applied-skill receipts were attached to this work product.')
        requests = _request_receipts(run, handoff)
        with st.expander(f'Actual model request receipts for this agent and operation ({len(requests)})'):
            st.caption('Matched by the exact operation ID and agent role. These calls are already included in run usage; they are not additional work.')
            if requests:
                st.dataframe([{'Request': r.get('number'), 'Model returned': r.get('returned_model'),
                               'Reasoning': r.get('reasoning_effort'), 'Status': r.get('status'),
                               'Input tokens': (r.get('usage') or {}).get('input_tokens'),
                               'Output tokens': (r.get('usage') or {}).get('output_tokens')}
                              for r in requests], hide_index=True)
                st.json(requests, expanded=False)
            else:
                st.caption('No operation- and role-matched detailed request receipt is available here. The saved handoff model remains shown above.')
        _exact(handoff.get('skill_versions') or {}, 'Pinned skill versions and instruction hashes')

    with checks_tab:
        st.subheader('Was this handoff accepted?')
        evaluation_id = handoff.get('acceptance_evaluation_id')
        evaluation = next((e for e in run.get('stage_evaluations') or [] if evaluation_id and e.get('id') == evaluation_id), None)
        if evaluation:
            _text(f'{str(evaluation.get("verdict", "unrecorded")).title()} · {evaluation.get("stage", "")}', 'h4')
            _text(evaluation.get('reason'))
            st.caption('These checks establish the software and evidence contract. They do not establish scientific validity or human approval.')
            checks = evaluation.get('checks') or []
            st.dataframe([{'Check': c.get('id', '').replace('_', ' '),
                           'Result': 'Passed' if c.get('passed') is True else 'Failed' if c.get('passed') is False else 'Not recorded',
                           'Requirement': c.get('detail')} for c in checks], hide_index=True)
            _exact(evaluation, 'Exact acceptance evaluation')
        else:
            st.caption('No linked acceptance evaluation is present in this snapshot.')
        decisions = [d for d in run.get('decisions') or [] if handoff.get('operation_id') and d.get('operation_id') == handoff['operation_id']]
        st.subheader('Decision from the same recorded operation')
        st.caption('The operation ID links these records. Individual causal influence is not inferred from their order.')
        for decision in decisions:
            with st.expander(f'Decision v{decision.get("version", "?")} · {decision.get("assessment", "unrecorded")}'):
                _text(decision.get('summary'))
                st.caption(f'Human review when issued: {decision.get("review_status_at_issue", "unrecorded")}')
                if decision.get('changes'):
                    _text('Recorded changes', 'h4')
                    value = decision['changes']
                    if isinstance(value, (dict, list)):
                        st.json(value, expanded=False)
                    else:
                        _text(value)
                _exact(decision, 'Full immutable decision version')
        if not decisions:
            st.caption('No decision version with this exact operation ID is present.')
    _exact(handoff, 'Full handoff record')


def _render_map(run, index, prefix):
    st.subheader('Follow the recorded routes')
    st.caption('Dashed arrows show who each handoff was addressed to. Choose a route, then open an actual work product to follow its declared inputs and consumers.')
    agents = {role: SimpleNamespace(id=role, role=role_label(role) if role == 'scientist' else role,
                                   parent_id=None, layout_row=i // 3, alignment='neutral',
                                   status='recorded' if index['outgoing'][role] else 'recipient',
                                   activity=len(index['outgoing'][role]))
              for i, role in enumerate(index['roles'])}
    state = SimpleNamespace(agents=agents, edges=set(), talk=index['routes'], active_id=None, complete=True,
                            activity_label='handoffs', network_description='Recorded recipient routes. No spawning or unrecorded dependencies are inferred.')
    st.markdown(network_svg(state), unsafe_allow_html=True)
    routes = list(index['routes'])
    if not routes:
        st.info('There are no recipient routes in this snapshot.')
        return
    route = st.selectbox('Choose a communication route', routes, key=prefix + ':route',
                         format_func=lambda r: f'{role_label(r[0])} → {role_label(r[1])} · {index["routes"][r]} handoff(s)')
    for number, handoff in enumerate(index['handoffs']):
        if handoff.get('sender') == route[0] and route[1] in _recipients(handoff):
            with st.container(border=True):
                _text(_handoff_label(handoff, index['handoffs']), 'h4')
                st.caption(handoff.get('created_at', 'Time unrecorded'))
                _text(handoff.get('question'))
                if handoff.get('id'):
                    _relation_button(handoff, run, prefix, prefix + f':route-open:{number}', 'Open this handoff →')
                else:
                    _exact(handoff)


def render_collaboration(run, brief, evidence):
    """Compact entry to every recorded participant, work product and dependency."""
    st.title('How the agents worked together')
    st.caption('Choose an agent, inspect what they produced, then follow the clickable inputs and handoffs to see how the team connected its work.')
    index = collaboration_index(run)
    if not index['roles']:
        st.info('No agent handoffs were recorded for this run.')
        return
    prefix = 'tbd_collaboration:' + str(run.get('id', 'unknown-run'))
    view = st.radio('Explore collaboration', ['Agent work', 'Communication map'], horizontal=True, key=prefix + ':view')
    if view == 'Communication map':
        _render_map(run, index, prefix)
        return

    roles = index['roles']
    default = roles.index('coordinator') if 'coordinator' in roles else 0
    st.session_state.setdefault(prefix + ':role', roles[default])
    left, right = st.columns([1, 1.8])
    with left:
        role = st.selectbox('Choose an agent', roles, format_func=role_label, key=prefix + ':role')
    products = index['outgoing'][role] or index['incoming'][role]
    product_ids = [h['id'] for h in products if h.get('id')]
    selected = None
    with right:
        if product_ids:
            if st.session_state.get(prefix + ':handoff') not in product_ids:
                st.session_state[prefix + ':handoff'] = product_ids[-1]
            hid = st.selectbox('Choose their handoff' if index['outgoing'][role] else 'Choose a handoff received', product_ids,
                               format_func=lambda value: _handoff_label(index['by_id'][value], index['handoffs']), key=prefix + ':handoff')
            selected = index['by_id'][hid]
        else:
            st.caption('No identified handoff is available to open.')
    with st.popover(f'Browse all {len(roles)} team members', width='stretch'):
        st.caption('Open a participant to inspect their saved work or received review.')
        columns = st.columns(2)
        for number, teammate in enumerate(roles):
            with columns[number % 2]:
                st.markdown(f'<div class="tbd-collaboration-intro">{pet_picture(teammate, css_class="tbd-collaboration-pet")}<div>{escape(role_label(teammate))}</div></div>', unsafe_allow_html=True)
                st.button(f'View {role_label(teammate)}', key=prefix + ':teammate:' + teammate,
                          on_click=_select_role, args=(prefix, teammate), width='stretch')
    summaries = {s.get('role'): s for s in brief.get('role_summaries') or []}
    summary = summaries.get(role, {})
    found = summary.get('what_found') or ('Receives the reviewed research proposal. This route does not imply scientific approval.' if role == 'scientist' else 'Inspect the saved work product, evidence and instructions below.')
    st.markdown(f'<section class="tbd-collaboration-intro">{pet_picture(role, css_class="tbd-collaboration-pet")}<div><h2>{escape(role_label(role))}</h2><small>Saved study summary</small><p>{escape(found)}</p><small>{len(index["outgoing"][role])} produced handoff(s) · {len(index["incoming"][role])} addressed to this participant</small></div></section>', unsafe_allow_html=True)
    if summary.get('why_it_matters'):
        _text(summary['why_it_matters'], css='tbd-collaboration-note')
    if not index['outgoing'][role]:
        st.info('This participant appears as a recipient only. No agent work product or human approval is invented for them.')
    if selected:
        render_handoff_detail(run, selected, evidence, key_prefix=prefix + ':detail', navigation_prefix=prefix)
