"""Pet presentation only. The canonical results renderer is not modified."""
from html import escape
from pathlib import Path
import streamlit as st

from .pet_activity import PetActivity
from .skill_badges import skill_badges
from .agent_profiles import profiles

ASSETS = Path(__file__).resolve().parents[1] / "static" / "scientist-pets"
CAST = {"orchestrator": "generic-scientist", "genomics": "bioinformatician",
        "clinical": "clinical-scientist", "literature": "computational-biologist",
        "stats": "statistician", "critic": "pharmacologist", "researcher": "bioinformatician",
        "research": "bioinformatician", "supporter": "immunologist", "challenger": "synthetic-biologist"}
LABELS = {"orchestrator": "Lead investigator", "genomics": "Genomics", "clinical": "Clinical scientist",
          "literature": "Literature specialist", "stats": "Statistics", "critic": "Scientific critic",
          "research": "Research specialist", "researcher": "Research specialist", "supporter": "Supporting perspective", "challenger": "Challenging perspective"}
CAST.update(clinical_scientist='clinical-scientist',bioinformatician='bioinformatician',
            statistician='statistician',clinical_pharmacologist='pharmacologist',
            molecular_scientist='computational-biologist',translational_scientist='epidemiologist',
            assay_scientist='synthetic-biologist',coordinator='generic-scientist',reviewer='immunologist')
LABELS.update({p['id']:p['name'] for p in profiles()})


def pet_key(role):
    return CAST.get(role, "generic-scientist")


def pet_picture(role, animate=False, *, css_class="scientist-pet"):
    key = pet_key(role)
    # Paths contain only a fixed, local allowlisted asset key.
    static = f"app/static/scientist-pets/{key}.png"
    source = f"app/static/scientist-pets/{key}.{'webp' if animate else 'png'}"
    label = escape(LABELS.get(role, role or "Scientist"), quote=True)
    return f'<picture><source media="(prefers-reduced-motion: reduce)" srcset="{static}"><img class="{css_class}" src="{source}" width="288" height="288" alt="{label} scientist pet"></picture>'


def stylesheet():
    css = (Path(__file__).resolve().parents[1] / "static" / "pets.css").read_text(encoding='utf-8')
    return f"<style>{css}</style>"


def render_pet(state, presentation: PetActivity, *, mode="Demo"):
    current = presentation.current
    role = current.role if current else "orchestrator"
    label = LABELS.get(role, role.replace("_", " ").title())
    working = bool(current and current.kind in {"agent_spawned", "tool_call"})
    paused = not presentation.playing
    # A completed source is always labeled as recorded updates, never live thinking.
    status = "Preparing the investigation" if current is None else "Presentation paused" if paused else "Recorded working update" if state.complete and working else "Working" if working else "Shared update"
    note = "Saved activity" if state.complete or mode == "Mock" else "Simulated model outputs" if mode == "Demo" or state.config.get("run_mode") == "mock" else "Connected investigation"
    text = current.text if current else "Preparing the evidence and waiting for the first expert update."
    progress = f"Update {len(presentation.turns)}" if current else "Preparing"
    caption = "Expert updates arrive as the analysis runs."
    image = pet_picture(role, animate=working and not paused)
    agent=state.agents.get(current.agent_id) if current else None
    skills=skill_badges(agent.skills,catalog=st.session_state.get('skill_catalog',[]),owner='featured-'+agent.id) if agent else ''
    st.markdown(f'''<div class="pet-live-marker"></div><section class="trace-pet-stage" aria-label="Expert discussion"><header><span>{escape(note)}</span><span>{progress}</span></header><div class="trace-pet-scene"><div class="trace-pet-character"><div class="pet-halo"></div>{image}<strong>{escape(label)}</strong>{skills}</div><article class="trace-pet-bubble"><div class="pet-status"><span>●</span>{status}</div><p>{escape(text)}</p><div class="pet-bubble-foot">Public event excerpt · full text in Results</div></article></div><footer>{escape(caption)}</footer></section>''', unsafe_allow_html=True)
