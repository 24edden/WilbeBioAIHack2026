"""Optional browser voice controls. No audio is sent to the TRACE backend.

Mount before the editable question widget, then apply the returned action through
the same draft/navigation guards as typed input. No action submits or cancels work.
"""
from __future__ import annotations

from pathlib import Path


NAVIGATION_TARGETS = frozenset({"evidence", "question", "investigation", "results"})
MAX_TRANSCRIPT = 8000


def validate_action(value: object) -> dict | None:
    """Treat browser events as untrusted input and keep the command set small."""
    if not isinstance(value, dict):
        return None
    event_id = value.get("id")
    if not isinstance(event_id, str) or not 1 <= len(event_id) <= 160:
        return None
    if value.get("type") == "dictation":
        text = value.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TRANSCRIPT:
            return None
        return {"id": event_id, "type": "dictation", "text": text.strip()}
    if value.get("type") == "navigate" and isinstance(value.get("target"), str) and value["target"] in NAVIGATION_TARGETS:
        return {"id": event_id, "type": "navigate", "target": value["target"]}
    return None


def stage_announcement(stage: str, phase: str = "", agent_stage: str = "") -> str:
    """Speak fixed workflow facts only, never generate or narrate scientific claims."""
    terminal = {
        "complete": "The investigation is ready. You can review the findings and see where they came from.",
        "cancelled": "The investigation has stopped. You can still look through the findings collected so far.",
        "error": "Something interrupted the investigation. The details are on screen when you're ready.",
    }
    if phase in terminal:
        return terminal[phase]
    agents = {
        "orchestrator": "Let's get started. The planner is organizing the investigation.",
        "genomics": "The genomics agent is examining the variant evidence.",
        "clinical": "The clinical agent is reviewing laboratory results and notes.",
        "literature": "The literature agent is comparing the reference evidence.",
        "stats": "The statistics agent is checking the available measurements.",
        "critic": "Time for a closer look. The critic is reviewing the team's reasoning and open questions.",
    }
    if phase == "running" and agent_stage in agents:
        return agents[agent_stage]
    return {
        "evidence": "Start with your evidence, or try the sample case.",
        "question": "What would you like to investigate? Set your question and choose the team.",
        "investigation": "The agents' work appears here. You can follow their messages and inspect the evidence.",
        "results": "Your results are here. Take a look at the conclusion, its evidence, and the open questions.",
    }.get(stage, "Voice controls are ready.")


def _voice_component():
    from streamlit.components.v2 import component

    assets = Path(__file__).resolve().parents[1] / "static"
    return component(
        "trace_voice_controls",
        html=(assets / "voice.html").read_text(encoding="utf-8"),
        css=(assets / "voice.css").read_text(encoding="utf-8"),
        js=(assets / "voice.js").read_text(encoding="utf-8"),
    )


def render_voice_controls(
    stage: str, active_question: str = "", *, phase: str = "", run_id: str = "",
    agent_stage: str = "", dictation_enabled: bool = True, key: str = "trace_voice",
) -> dict | None:
    """Return one validated, deduplicated dictation/navigation action or None.

    ``active_question`` is accepted for caller convenience but deliberately never
    sent to the speech component. Dictation replaces the draft only after review.
    Requires Streamlit 1.64; older installations retain typed input.
    """
    import streamlit as st

    try:
        voice = _voice_component()
    except ImportError:
        st.caption("Voice controls need Streamlit 1.64 or newer. You can continue by typing.")
        return None
    result = voice(
        key=key,
        data={
            "theme": "astral" if st.session_state.get("astral_theme", False) else "dark",
            "dictationEnabled": bool(dictation_enabled),
            "setupMode": stage == "evidence",
            "announcement": stage_announcement(stage, phase, agent_stage),
            "announcementId": f"{run_id}:{stage}:{phase}:{agent_stage}",
        },
        on_action_change=lambda: None,
    )
    action = validate_action(result.action)
    if not action or (action["type"] == "dictation" and not dictation_enabled):
        return None
    seen_key = f"_{key}_last_action"
    if st.session_state.get(seen_key) == action["id"]:
        return None
    st.session_state[seen_key] = action["id"]
    return action
