"""Observed network, skill roster and counters shared by live and recorded views."""
from html import escape
import streamlit as st
from . import components as C
from .pets import pet_picture, LABELS
from .skill_badges import skill_badges
from .network_svg import network_svg

def render_network(state, *, recorded=False):
    with st.container(key='network_workspace'):
        st.subheader('Agent network')
        st.caption('Saved event playback. No new reasoning.' if recorded else 'Observed activity. Solid arrows spawn agents; dashed arrows show their messages.')
        C.render_stats(state)
        st.markdown(network_svg(state),unsafe_allow_html=True)
        catalog=st.session_state.get('skill_catalog',[])
        roster=[]
        for agent in state.agents.values():
            label=LABELS.get(agent.role,agent.role.replace('_',' ').title())
            roster.append(f'<div class="pet-roster-agent">{pet_picture(agent.role,animate=False,css_class="pet-roster-image")}<strong>{escape(label)}</strong>{skill_badges(agent.skills,catalog=catalog,owner="roster-"+agent.id)}<small>{escape(agent.status)}</small></div>')
        if roster:st.markdown('<div class="pet-roster">'+''.join(roster)+'</div>',unsafe_allow_html=True)
        with st.expander('Agent messages',expanded=False):C.render_conversation(state)
