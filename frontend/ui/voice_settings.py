"""Browser-owned voice preferences and fixed workflow announcements."""
from pathlib import Path
import streamlit as st
from .appearance import palette

ASSETS=Path(__file__).resolve().parents[1]/'static'

def render_voice_settings():
    from streamlit.components.v2 import component
    control=component('pet_voice_settings',html=(ASSETS/'voice_settings.html').read_text(encoding='utf-8'),
        css='/* Inline voice controls */\n'+(ASSETS/'voice_settings.css').read_text(encoding='utf-8'),js=(ASSETS/'voice_shared.js').read_text(encoding='utf-8')+'\n'+(ASSETS/'voice_settings.js').read_text(encoding='utf-8'))
    control(key='pet_voice_settings',data={'colors':palette(st.session_state.get('ui_theme','light'))})

def render_stage_audio(stage,run_id='',role=''):
    from streamlit.components.v2 import component
    cue='Reviewing the findings.' if role=='critic' and stage=='running' else {
        'running':'The investigation has started. You can follow the agents below.',
        'results':'Your investigation has ended. The results and any limitations are ready to review.'}.get(stage,'')
    if not cue:return
    player=component('pet_stage_audio',html='<span aria-hidden="true"></span>',
        js=(ASSETS/'voice_shared.js').read_text(encoding='utf-8')+'\n'+(ASSETS/'stage_audio.js').read_text(encoding='utf-8'))
    player(key='pet_stage_audio',data={'cue':cue,'id':f'{run_id}:{stage}:{"critic" if role=="critic" else "run"}'})
