"""Next-run setup, separate from immutable submitted requests."""
from copy import deepcopy
from pathlib import Path
from html import escape
import streamlit as st
from .adapters import source_for
from .capabilities import CapabilityLookup
from .config import PROFILE
from .layout import render_agent_setup
from .stream import list_fixtures, load_fixture
from .voice_settings import render_voice_settings
from .agent_profiles import profiles
from .skill_badges import skill_badges
from .client_controls import render_drawer_heading


def render_setup(draft):
    with st.popover('Settings', icon=':material/settings:', width='content'):
        st.markdown('<div class="trace-setup-marker"></div>', unsafe_allow_html=True)
        render_drawer_heading()
        st.caption('Applies to your next investigation. A running request stays unchanged. Close with Escape or click outside.')
        mode=st.selectbox('Evidence source', ['Demo','Live','Mock'],
            index=['Demo','Live','Mock'].index(draft['mode']), format_func=PROFILE.mode_labels.get, key='setup_source')
        draft['mode']=mode
        if mode=='Live':
            draft['backend']=st.text_input('Research service URL',value=draft['backend'],key='setup_backend').strip()
            st.caption('Files go to this service only when you start. Credentials stay on the server.')
        if mode=='Mock':
            fixtures=list_fixtures()
            if fixtures:
                selected=st.selectbox('Recorded investigation',[str(p) for p in fixtures],
                    format_func=lambda p:PROFILE.fixture_labels.get(Path(p).stem,Path(p).stem),key='setup_fixture')
                draft['fixture']=selected
                events=load_fixture(selected)
                draft['recorded_question']=next((str(e.payload.get('question','')) for e in events if e.type=='run_started'), 'Recorded investigation')
                draft['speed']=st.select_slider('Playback speed',options=[.5,1.,1.5,2.,4.],value=1.5,key='setup_speed')
            st.caption('Recorded events only. No new model calls or uploaded evidence.')
        else:
            with st.expander('Evidence',expanded=True):
                if mode=='Demo':st.caption('Local workflow with simulated model outputs. Uses the bundled synthetic case when no files are attached.')
                draft['sample']=st.checkbox('Use bundled synthetic evidence',value=draft.get('sample',False),key='setup_sample')
                files=st.file_uploader('Choose evidence files',type=list(PROFILE.input_extensions),accept_multiple_files=True,key='setup_uploads',max_upload_size=20)
                st.caption('Up to 20 files and 40 MB total, including prompt attachments.')
                draft['evidence_uploads']=[(f.name,f.getvalue()) for f in files]
                if draft['sample'] and (files or draft.get('uploads')):
                    st.warning('The sample option takes precedence over attached files. Turn it off to investigate your files.')
        lookup_key=(mode,draft['backend'])
        if st.session_state.get('_setup_lookup_key')!=lookup_key:
            st.session_state._setup_lookup_key=lookup_key
            source=source_for(mode)
            st.session_state._setup_lookup=CapabilityLookup(lambda:source.capabilities(lookup_key[1]))
            for key in list(st.session_state):
                if key in {'draft_task_mode','draft_specialists','draft_reasoning_model','draft_variant_model','draft_embedding_model'}:
                    del st.session_state[key]
            draft['config']={'task_mode':'auto'}
        lookup=st.session_state._setup_lookup
        @st.fragment(run_every=.5 if lookup.snapshot()[3] else None)
        def agents():
            data,error,ready,loading,revision=lookup.snapshot()
            st.session_state.skill_catalog=deepcopy(data.get('skills',[]))
            with st.expander('Agents and models',expanded=False):
                if loading:st.caption('Reading available agent controls…')
                config,valid=render_agent_setup(mode,draft['backend'],data,error,draft.get('config'))
                draft['config']=config or {'task_mode':'auto'}
                draft['setup_valid']=valid
                if st.button('Refresh available controls',key='refresh_setup_capabilities',disabled=loading):
                    lookup.refresh();st.rerun()
            if ready and st.session_state.get('_setup_ready_revision')!=(lookup_key,revision):
                st.session_state._setup_ready_revision=(lookup_key,revision)
                st.rerun()
        agents()
        with st.expander('Voice',expanded=False):
            render_voice_settings()
        with st.expander('Brev team skill reference',expanded=False):
            st.caption('Nine configured profiles from docs/agent-profiles. This separate Brev team is not the local demo roster. Icons describe capabilities, not completed actions.')
            for profile in profiles():
                configured=profile.get('main_investigation',{}).get('automatic_skills',[])
                st.markdown('<div class="profile-agent"><strong>'+escape(profile['name'])+'</strong>'+skill_badges(configured,owner='profile-'+profile['id'],configured=True)+'</div>',unsafe_allow_html=True)
