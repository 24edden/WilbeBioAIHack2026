"""TRACE: prompt → running → results. One interface, one immutable run boundary."""
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4
import streamlit as st

from ui import components as C
from ui.state import RunState
from ui.config import PROFILE
from ui.adapters import RunRequest, source_for, DemoSource
from ui.runtime import BackgroundRun
from ui.demo_pacing import PacedDemoSource
from ui.followup import FollowUpSource, context_for
from ui.pet_activity import PetActivity
from ui.pets import render_pet, stylesheet as pet_stylesheet
from ui.pet_start import render_start
from ui.theme import stylesheet
from ui.appearance import stylesheet as appearance_stylesheet, toggle_theme
from ui.workspace import new_draft, normalized_stage, collect_updates, save_result, result_kind
from ui.setup_drawer import render_setup
from ui.network_view import render_network
from ui.replay import Playback
from ui.voice_settings import render_stage_audio
from ui.client_controls import render_client_controls

st.set_page_config(page_title=PROFILE.page_title,page_icon=":material/science:",layout="wide",initial_sidebar_state="collapsed")
st.session_state.setdefault('ui_theme','light')
st.session_state.astral_theme=st.session_state.ui_theme=='light'
st.markdown(stylesheet('astral' if st.session_state.ui_theme=='light' else 'dark'),unsafe_allow_html=True)
st.markdown(pet_stylesheet(),unsafe_allow_html=True)
st.markdown(appearance_stylesheet(st.session_state.ui_theme),unsafe_allow_html=True)

for key,value in {'stage':'prompt','draft':new_draft(),'run':RunState(),'submitted':None,'job':None,
                  'previous_runs':[],'followup_drafts':{},'result_id':uuid4().hex}.items():
    st.session_state.setdefault(key,value)
st.session_state.stage=normalized_stage(st.session_state.stage)
st.session_state.draft.setdefault('composer_id',uuid4().hex)
if st.session_state.get('flow_version') != 3:
    configured=new_draft()
    st.session_state.draft.update(mode=configured['mode'],backend=configured['backend'],config={'task_mode':'auto'})
    st.session_state.flow_version=3


def go_home():
    st.session_state.stage='prompt'


def show_running():
    st.session_state.stage='running' if st.session_state.job and st.session_state.job.active else 'results'


def start(request):
    if not request.question.strip():
        st.error('Enter a research question before starting.')
        return
    if st.session_state.job and st.session_state.job.active:
        st.warning('An investigation is already running. Return to it before starting another.')
        return
    save_result(st.session_state)
    st.session_state.result_id=uuid4().hex
    st.session_state.submitted=deepcopy(request)
    st.session_state.run=RunState()
    st.session_state.network_playback=None
    st.session_state.job=None
    try:
        source=source_for(request.mode)
        if request.mode=='Demo' and isinstance(source,DemoSource):
            source.mock_latency_scale=0
            source=PacedDemoSource(source)
        can_cancel=request.mode!='Live' or callable(getattr(source,'cancel',None))
        if request.context:source=FollowUpSource(source)
        st.session_state.job=BackgroundRun(source,request,can_cancel=can_cancel)
        st.session_state.stage='running'
    except Exception as exc:
        st.session_state.run.status='error'
        st.session_state.run.errors.append(f'Could not start the investigation: {exc}')
        st.session_state.stage='results'
    st.rerun()


_collected=collect_updates(st.session_state)
job=st.session_state.job
run_active=bool(job and job.active)
# Old bookmarks/session state never reveal an alternate interface.
if st.session_state.stage=='results' and st.session_state.submitted is None:
    st.session_state.stage='prompt'
if st.session_state.stage=='running' and not run_active:
    st.session_state.stage='results' if st.session_state.submitted else 'prompt'

with st.container(key='workspace_header'):
    brand,theme,settings=st.columns([6,1,.5],vertical_alignment='center')
    with brand:
        with st.container(key='trace_home'):
            st.button(PROFILE.name,key='home',on_click=go_home,help='Return to the question window. An active investigation keeps running.')
    with theme:
        st.button('☾ Dark mode' if st.session_state.ui_theme=='light' else '☀ Light mode',
                  key='theme_toggle',on_click=toggle_theme,help='Use this appearance on all three screens.')
    with settings:render_setup(st.session_state.draft)
render_client_controls()

if st.session_state.stage=='prompt':
    if run_active:
        with st.container(key='resume_strip'):
            st.caption('An investigation is running in the background.')
            st.button('Return to investigation',key='return_running',on_click=show_running)
    elif st.session_state.submitted is not None:
        st.button('View last results',key='view_last_results',on_click=show_running)
    request=render_start(st.session_state.draft,run_active=run_active)
    if isinstance(request,RunRequest):start(request)

elif st.session_state.stage=='results':
    state=st.session_state.run
    submitted=st.session_state.submitted
    st.title('Results')
    st.caption(state.question or submitted.question)
    render_stage_audio('results',st.session_state.result_id)
    if submitted.mode=='Demo' or state.config.get('run_mode')=='mock':
        st.caption('Demo · simulated model outputs, not a validated scientific assessment.')
    elif submitted.mode=='Mock':st.caption('Recorded results · no new analysis was performed.')
    kind=result_kind(state)
    if kind=='interrupted':
        st.error('The investigation was interrupted. No completed scientific conclusion is available.')
        for error in state.errors:st.caption(error)
        if st.button('Retry investigation',key='retry_run',type='primary'):start(submitted)
    elif kind=='cancelled':
        st.info('Investigation canceled. Any partial findings remain below; this is not a completed assessment.')
        if st.button('Try again',key='retry_run'):start(submitted)
    else:
        C.render_verdict(state)
    # All supporting science remains on this one result page, progressively disclosed.
    with st.expander('Evidence and source references',key='result_evidence',on_change='rerun'):
        if kind!='complete':st.caption('Partial observations; scientific review may be incomplete.')
        if state.task_mode=='idea_review':
            C.render_discussion(state)
        else:
            C.render_findings(state)
    with st.expander('Limitations and open questions',key='result_limits',on_change='rerun'):
        C.render_weak_points(state)
    with st.expander('Investigation details',key='result_details',on_change='rerun'):
        C.render_timeline(state)
        if state.files:st.write('Input files',state.files)
        if state.config:st.json(state.config,expanded=False)
    if kind=='complete':
        with st.expander('Ask a follow-up',key='result_followup',on_change='rerun'):
            result_id=st.session_state.result_id
            if st.session_state.get('followup_owner')!=result_id or 'followup_prompt' not in st.session_state:
                st.session_state.followup_prompt=st.session_state.followup_drafts.get(result_id,'')
                st.session_state.followup_owner=result_id
            def capture_followup():
                st.session_state.followup_drafts[st.session_state.result_id]=st.session_state.followup_prompt
            followup=st.text_input('Follow-up question',key='followup_prompt',max_chars=4000,
                placeholder='Which experiment would test this explanation?',on_change=capture_followup)
            if st.button('Run follow-up',key='run_followup',type='primary'):
                if not followup.strip():st.error('Enter a follow-up question first.')
                else:
                    st.session_state.followup_drafts[result_id]=''
                    config=deepcopy(submitted.config)
                    recording=submitted.mode=='Mock'
                    config['task_mode']='idea_review' if recording else state.task_mode
                    start(replace(submitted,question=followup.strip(),config=config,context=context_for(state),
                        mode='Demo' if recording else submitted.mode,fixture=None if recording else submitted.fixture,
                        sample=False if recording else submitted.sample))
    previous=[item for item in st.session_state.previous_runs if item['id']!=st.session_state.result_id]
    if previous:
        with st.expander('Previous results',key='result_history',on_change='rerun'):
            selected=st.selectbox('Saved result',range(len(previous)),key='saved_result',
                format_func=lambda i:(previous[i]['run'].question or previous[i]['request'].question)[:100])
            if st.button('Open saved result',key='open_saved_result'):
                item=previous[selected];save_result(st.session_state)
                st.session_state.run=deepcopy(item['run']);st.session_state.submitted=deepcopy(item['request'])
                st.session_state.result_id=item['id'];st.session_state.job=None
                st.rerun()
    if st.button('Ask another question',key='new_question'):
        st.session_state.draft=new_draft()
        go_home();st.rerun()
    with st.container(key='network_replay_controls'):
        if st.button('Replay agent network',key='network_replay_start',disabled=not state.raw):
            st.session_state.network_playback=Playback(state.raw)
            st.session_state.network_playback_owner=st.session_state.result_id
            st.rerun()
        replay=st.session_state.get('network_playback')
        if replay and st.session_state.get('network_playback_owner')==st.session_state.result_id:
            if st.button('Pause replay' if replay.playing else 'Resume replay',key='network_replay_pause',disabled=replay.finished):
                replay.pause() if replay.playing else replay.resume();st.rerun()
            if st.button('Show complete network',key='network_replay_end'):
                st.session_state.network_playback=None;st.rerun()


replay=st.session_state.get('network_playback')
replay_active=bool(replay and replay.playing and st.session_state.stage=='results' and st.session_state.get('network_playback_owner')==st.session_state.result_id)
@st.fragment(run_every=.5 if run_active or replay_active else None)
def monitor():
    ended=collect_updates(st.session_state)
    if ended:
        st.rerun()
    if st.session_state.stage=='results':
        playback=st.session_state.get('network_playback') if st.session_state.get('network_playback_owner')==st.session_state.result_id else None
        if playback:
            was_playing=playback.playing;playback.advance()
            if was_playing and playback.finished:st.rerun()
            render_network(playback.state,recorded=True)
        else:render_network(st.session_state.run)
        return
    if st.session_state.stage!='running':return
    current_job=st.session_state.job
    if not current_job or not current_job.active:
        st.session_state.stage='results' if st.session_state.submitted else 'prompt'
        st.rerun()
    state=st.session_state.run
    question=state.question or st.session_state.submitted.question
    st.markdown(f"<div class='pet-question'><small>YOUR QUESTION</small>{C._escape(question)}</div>",unsafe_allow_html=True)
    # Select the latest public update. There is no post-completion replay queue.
    presentation=PetActivity()
    presentation.ingest(state.raw,complete=False)
    presentation.index=max(0,len(presentation.turns)-1)
    render_pet(state,presentation,mode=st.session_state.submitted.mode)
    active=state.agents.get(state.active_id)
    render_stage_audio('running',st.session_state.result_id,active.role if active else '')
    with st.expander('Network and live stats',expanded=True):render_network(state)
    if current_job.cancel_requested or (current_job.can_cancel and (st.session_state.submitted.mode!='Live' or state.run_id)):
        with st.container(key='run_actions'):
            if current_job.cancel_requested:
                st.caption('Cancellation requested. Waiting for the investigation to stop safely.')
            elif st.button('Cancel investigation',key='cancel_run'):
                current_job.request_cancel();st.rerun()
    if state.errors:
        st.caption('An issue was reported; the investigation is still running.')


monitor()
