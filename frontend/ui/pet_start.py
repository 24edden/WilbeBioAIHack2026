"""Prompt-and-upload entry screen using the existing immutable RunRequest."""
from copy import deepcopy
from pathlib import Path
import streamlit as st
from .adapters import RunRequest, recorded_context, list_fixtures
from .config import PROFILE
from .pets import pet_picture
from .composer import render_composer


def render_start(draft, *, capture_uploads, run_active=False):
    st.markdown('<div class="pet-composer-marker"></div><div class="pet-start-heading">'+pet_picture('orchestrator', css_class='pet-welcome')+'<h1>What are we investigating?</h1><p>Bring your question and data. Follow the experts to the next experiment.</p></div>', unsafe_allow_html=True)
    mode = draft['mode']
    read_only=mode=='Mock'
    if read_only:
        path=Path(draft['fixture']) if draft['fixture'] else next(iter(list_fixtures()),None)
        question,_=recorded_context(path,PROFILE.default_question)
    else:
        question=draft['question']
    note=("No backend or API key needed. Model outputs are simulated. Without files, the demo uses its bundled sample."
          if mode=='Demo' else "Recorded playback keeps its original question and findings. Attachments are not analyzed."
          if read_only else "Your files are sent to the configured backend only when you start the investigation.")
    action=render_composer(draft,question=question,read_only=read_only,disabled=run_active,note=note)
    with st.expander('Source and advanced options'):
        if 'draft_mode' not in st.session_state:
            st.session_state.draft_mode = draft['mode']
        new_mode = st.radio('Source', list(PROFILE.mode_labels), format_func=lambda x: PROFILE.mode_labels[x],
                           key='draft_mode', horizontal=True)
        if new_mode != draft['mode']:
            draft['mode'] = new_mode
            st.rerun()
        if mode=='Live':
            if 'draft_backend' not in st.session_state:
                st.session_state.draft_backend=draft['backend']
            draft['backend']=st.text_input('Backend',key='draft_backend')
            draft['sample']=st.checkbox('Use bundled server sample',value=draft['sample'])
        if mode=='Mock':
            paths=list(list_fixtures())
            if paths:
                selected=st.selectbox('Recorded case',paths,format_func=lambda p: PROFILE.fixture_labels.get(p.stem,p.stem))
                if str(selected)!=draft['fixture']:
                    draft['fixture']=str(selected)
                    st.rerun()
            else:
                st.error('No recorded cases are available.')
        st.caption('The planner chooses relevant specialists by default. Advanced setup retains the original agent and model controls.')
        if st.button('Open advanced setup',key='pet_advanced'):
            return 'advanced'
    if action and action['type']=='demo':
        return RunRequest(mode='Demo',question=PROFILE.default_question,backend=draft['backend'],sample=True,
                          config={'task_mode':'investigation'})
    if action and action['type']=='start':
        question=question if read_only else action['question']
        if not question.strip():
            st.error('Enter a research question before starting.')
        elif mode=='Live' and (not draft['backend'].strip() or (not draft['sample'] and not draft['uploads'])):
            st.error('Attach evidence or choose the server sample, and provide a backend address.')
        elif mode=='Mock' and not draft['fixture']:
            st.error('Choose a recorded case first.')
        else:
            # DemoSource supports uploaded bytes; never silently discard them in favor of the sample.
            return RunRequest(mode=mode,question=question.strip(),backend=draft['backend'],
                fixture=draft['fixture'],speed=draft['speed'],sample=not draft['uploads'] if mode=='Demo' else draft['sample'],
                uploads=deepcopy(action['uploads']) if mode!='Mock' else [],config=deepcopy(draft['config']) or {'task_mode':'auto'})
    return None
