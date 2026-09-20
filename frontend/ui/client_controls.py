"""Small browser-only controls. No run or transport state is owned here."""
from pathlib import Path
import streamlit as st
from .appearance import PALETTES

def render_client_controls():
    from streamlit.components.v2 import component
    bridge=component('pet_client_controls',html='<span aria-hidden="true"></span>',
        js=(Path(__file__).resolve().parents[1]/'static'/'client_controls.js').read_text(encoding='utf-8'))
    bridge(key='pet_client_controls',data={'palettes':PALETTES,'fallback':st.session_state.get('ui_theme','light')})

def render_drawer_heading():
    from streamlit.components.v2 import component
    heading=component('pet_drawer_heading',html='<div class="heading"><h3>Investigation setup</h3><button type="button" aria-label="Close settings">&#215;</button></div>',
        css='/* Drawer heading */\n.heading{display:flex;align-items:center;justify-content:space-between;font-family:inherit;color:var(--ui-text)}h3{margin:0;font-size:22px}button{width:40px;height:40px;border:1px solid var(--ui-border);border-radius:8px;background:var(--ui-soft);color:inherit;font-size:24px;cursor:pointer}button:focus-visible{outline:2px solid var(--ui-focus);outline-offset:2px}',
        js="// Inline drawer control\nexport default function({parentElement}) {const button=parentElement.querySelector('button');button.onclick=()=>document.querySelector('.st-key-workspace_header [data-testid=stPopover] button')?.click();return()=>{button.onclick=null;};}")
    heading(key='pet_drawer_heading')
