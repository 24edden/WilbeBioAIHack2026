"""Single prompt/drop surface. Validate browser payloads before creating RunRequest."""
from pathlib import Path
import base64
import binascii
import streamlit as st
from .config import PROFILE
from .appearance import palette

MAX_FILE=20*1024*1024
MAX_TOTAL=40*1024*1024
MAX_QUESTION=12000


def decode_files(items):
    if not isinstance(items,list) or len(items)>20:
        raise ValueError('Attach up to 20 files.')
    result=[];total=0
    for item in items:
        if not isinstance(item,dict):raise ValueError('Invalid attachment.')
        name=item.get('name');encoded=item.get('data');size=item.get('size')
        if not isinstance(name,str) or not 1<=len(name)<=200 or '/' in name or '\\' in name:
            raise ValueError('Invalid attachment filename.')
        if name.rsplit('.',1)[-1].lower() not in PROFILE.input_extensions:
            raise ValueError('Unsupported attachment format.')
        if isinstance(size,bool) or not isinstance(size,int) or not 0<=size<=MAX_FILE or not isinstance(encoded,str) or len(encoded)>(MAX_FILE*4//3+8):
            raise ValueError('Each file must be 20 MB or smaller.')
        try:data=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error):raise ValueError('Could not decode the attachment.') from None
        if len(data)!=size:raise ValueError('Attachment size does not match its contents.')
        total+=size
        if total>MAX_TOTAL:raise ValueError('Keep total attachments under 40 MB.')
        result.append((name,data))
    return result


def validate_action(value, *, preserve_question=False):
    if not isinstance(value,dict):return None
    if value.get('type') not in ('start','demo'):return None
    if not isinstance(value.get('id'),str) or not 1<=len(value['id'])<=160:return None
    question=value.get('question','')
    if not isinstance(question,str) or len(question)>MAX_QUESTION:raise ValueError('Question must be 12,000 characters or fewer.')
    if value['type']=='start' and not question.strip():raise ValueError('Enter a scientific question before starting.')
    return {**value,'question':question if preserve_question else question.strip(),'uploads':decode_files(value.get('files',[]))}


def apply_composer_draft(draft, pending):
    """Persist a browser draft independently of whether its composer stays mounted."""
    if draft.get('mode') == 'Mock' or not isinstance(pending, dict) or pending.get('generation') != draft['composer_id']:
        return
    text = pending.get('question')
    if not isinstance(text, str) or len(text) > MAX_QUESTION:
        return
    try:
        uploads = decode_files(pending.get('files', []))
    except ValueError as exc:
        st.error(str(exc))
        return
    draft.update(question=text, uploads=uploads)


def capture_composer_draft(draft):
    # Blur can deliver a component update in the same rerun as a navigation
    # click. Capture it before routing removes the component from the page.
    component_state = st.session_state.get('trace_prompt_composer', {})
    if isinstance(component_state, dict):
        apply_composer_draft(draft, component_state.get('draft'))


def render_composer(draft,*,question,read_only=False,disabled=False,note='',allow_uploads=True,allow_demo=True,preserve_question=False):
    from streamlit.components.v2 import component
    assets=Path(__file__).resolve().parents[1]/'static'
    composer=component('trace_prompt_composer',html=(assets/'composer.html').read_text(encoding='utf-8'),
        css=(assets/'composer.css').read_text(encoding='utf-8'),js=(assets/'voice_shared.js').read_text(encoding='utf-8')+'\n'+(assets/'microphone.js').read_text(encoding='utf-8')+'\n'+(assets/'composer.js').read_text(encoding='utf-8'))
    result=composer(key='trace_prompt_composer',data={'question':question,'generation':draft['composer_id'],
        'colors':palette('team-tbd' if draft.get('appearance')=='team-tbd' else st.session_state.get('ui_theme','light')),'theme':st.session_state.get('ui_theme','light'),
        'readOnly':read_only,'disabled':disabled,'allowUploads':allow_uploads,'allowDemo':allow_demo,'note':note,'extensions':list(PROFILE.input_extensions),
        'files':[{'name':name,'size':len(data),'data':base64.b64encode(data).decode()} for name,data in draft['uploads']]},
        on_action_change=lambda:None,on_draft_change=lambda:capture_composer_draft(draft))
    pending=getattr(result,'draft',None)
    if not read_only:
        apply_composer_draft(draft, pending)
    raw_action=getattr(result,'action',None)
    if not isinstance(raw_action,dict) or raw_action.get('generation')!=draft['composer_id']:return None
    try:action=validate_action(raw_action, preserve_question=preserve_question)
    except ValueError as exc:st.error(str(exc));return None
    if not action or st.session_state.get('_pet_composer_action')==action['id']:return None
    st.session_state._pet_composer_action=action['id']
    if not read_only:
        draft['question']=action['question'];draft['uploads']=action['uploads']
        st.session_state.draft_question=action['question']
    return action
