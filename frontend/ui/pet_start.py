"""One composer. Source configuration belongs to deployment, not a second UI."""
from copy import deepcopy
import streamlit as st
from .adapters import RunRequest
from .config import PROFILE
from .pets import pet_picture
from .composer import render_composer


def render_start(draft, *, run_active=False):
    st.markdown('<div class="pet-composer-marker"></div><div class="pet-start-heading">'+pet_picture('orchestrator',css_class='pet-welcome')+'<h1>What are we investigating?</h1><p>Bring your question and data. Follow the experts to the next experiment.</p></div>',unsafe_allow_html=True)
    mode=draft['mode']
    note=('Demo mode · about 25 seconds with simulated model outputs. Without attachments, the bundled sample is used.' if mode=='Demo'
          else 'Your files are sent to the configured research service only when you start.')
    if run_active:note='Your investigation continues in the background. You can prepare the next question here.'
    action=render_composer(draft,question=draft['question'],disabled=run_active,note=note)
    if not action or run_active:return None
    if action['type']=='demo':
        return RunRequest(mode='Demo',question=PROFILE.default_question,backend=draft['backend'],sample=True,config={'task_mode':'investigation'})
    return RunRequest(mode=mode,question=action['question'],backend=draft['backend'],
        sample=mode=='Demo' and not action['uploads'],uploads=deepcopy(action['uploads']),
        config=deepcopy(draft.get('config')) or {'task_mode':'auto'})
