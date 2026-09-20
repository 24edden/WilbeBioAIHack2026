"""TRACE's authoritative Team TBD scientific workspace.

The historical investigation API is available only through legacy_app.py.
"""
import streamlit as st
from ui.scientific_workspace import render

st.set_page_config(page_title='TRACE · Team TBD', page_icon=':material/science:',
                   layout='wide', initial_sidebar_state='collapsed')
render()
