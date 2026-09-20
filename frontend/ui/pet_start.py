"""One composer. Source configuration belongs to deployment, not a second UI."""
from copy import deepcopy
import streamlit as st
from .adapters import RunRequest
from .config import PROFILE
from .pets import pet_picture
from .composer import render_composer
from .composer import MAX_FILE, MAX_TOTAL


def configured_request(draft, action):
    if draft['mode']=='Mock':
        return RunRequest(mode='Mock',question=draft.get('recorded_question','Recorded investigation'),
            fixture=draft.get('fixture'),speed=draft.get('speed',1.5))
    files=deepcopy(action['uploads'])+deepcopy(draft.get('evidence_uploads',[]))
    # File sources share one budget; the sidebar must not bypass composer limits.
    if len(files)>20 or any(len(data)>MAX_FILE for _,data in files) or sum(len(data) for _,data in files)>MAX_TOTAL:
        raise ValueError('Use up to 20 files, 20 MB per file and 40 MB in total across both upload controls.')
    return RunRequest(mode=draft['mode'],question=action['question'],backend=draft['backend'],
        sample=bool(draft.get('sample')) or (draft['mode']=='Demo' and not files),uploads=files,
        config=deepcopy(draft.get('config')) or {'task_mode':'auto'})


def render_start(draft, *, run_active=False):
    st.markdown('<div class="pet-composer-marker"></div><div class="pet-start-heading">'+pet_picture('orchestrator',css_class='pet-welcome')+'<h1>What are we investigating?</h1><p>Bring your question and data. Follow the experts to the next experiment.</p></div>',unsafe_allow_html=True)
    mode=draft['mode']
    note=('Demo mode · about 25 seconds with simulated model outputs. Without attachments, the bundled sample is used.' if mode=='Demo'
          else 'Your files are sent to the configured research service only when you start.')
    if run_active:note='Your investigation continues in the background. You can prepare the next question here.'
    if mode=='Mock':note='Recorded event playback. No new analysis or model calls.'
    if draft.get('evidence_uploads'):note+=f" {len(draft['evidence_uploads'])} evidence file(s) selected in Settings."
    action=render_composer(draft,question=draft.get('recorded_question','') if mode=='Mock' else draft['question'],read_only=mode=='Mock',disabled=run_active or not draft.get('setup_valid',True),note=note)
    if not action or run_active:return None
    if action['type']=='demo':
        return RunRequest(mode='Demo',question=PROFILE.default_question,backend=draft['backend'],sample=True,config={'task_mode':'investigation'})
    try:return configured_request(draft,action)
    except ValueError as exc:st.error(str(exc));return None
