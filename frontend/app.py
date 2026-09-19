"""Patient failure-investigation UI.

Run:  streamlit run frontend/app.py

Two modes, chosen in the sidebar:

  Mock  replays a fixture. No backend, no tokens, no GPU. This is the daily dev
        loop and the rehearsal path.
  Live  POST /investigate on the backend, then stream GET /events/{run_id}.

Both paths produce the same `Event` objects and fold into the same `RunState`,
so what you rehearse in mock mode is what you get live.
"""

from __future__ import annotations

import streamlit as st

from ui import components as C
from ui.state import RunState
from ui.stream import DEFAULT_BACKEND, list_fixtures, live_stream, start_run, upload_files
from ui.theme import CSS

st.set_page_config(page_title="Failure Investigation", page_icon="\U0001f9ec", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

st.session_state.setdefault("run", RunState())
st.session_state.setdefault("pending", None)

PLACEHOLDER = "Why did this patient fail pembrolizumab therapy?"


# -- sidebar: settings only, never the question ----------------------------

with st.sidebar:
    st.markdown("<div class='eyebrow'>Run settings</div>", unsafe_allow_html=True)
    mode = st.radio(
        "Mode", ["Mock", "Live"], horizontal=True,
        help="Mock replays a recorded run. No backend required.",
    )

    fixture, backend, speed, uploads = None, DEFAULT_BACKEND, 1.5, []

    if mode == "Mock":
        fixtures = list_fixtures()
        if not fixtures:
            st.error("No fixtures found in frontend/fixtures/.")
        else:
            fixture = st.selectbox(
                "Recorded run", fixtures, format_func=lambda p: p.stem.replace("_", " ")
            )
        speed = st.slider(
            "Playback speed", 0.25, 6.0, 1.5, 0.25,
            help="Lower to watch agents arrive one by one. Higher to skim.",
        )
    else:
        backend = st.text_input("Backend", DEFAULT_BACKEND)
        uploads = st.file_uploader(
            "Patient files", accept_multiple_files=True,
            type=["vcf", "csv", "txt", "tsv", "json"],
        ) or []

    st.divider()
    if st.button("Clear run", width="stretch"):
        st.session_state.run = RunState()
        st.session_state.pending = None
        st.rerun()

    st.markdown(
        "<div class='eyebrow' style='margin-top:1rem'>Agent colour</div>"
        "<div style='font-size:.78rem;color:var(--ink-2);line-height:1.7'>"
        "<span style='display:inline-block;width:9px;height:9px;border-radius:2px;"
        "background:var(--planner);margin-right:.45rem'></span>planner<br>"
        "<span style='display:inline-block;width:9px;height:9px;border-radius:2px;"
        "background:var(--specialist);margin-right:.45rem'></span>specialist<br>"
        "<span style='display:inline-block;width:9px;height:9px;border-radius:2px;"
        "background:var(--critic);margin-right:.45rem'></span>critic</div>"
        "<div style='font-size:.72rem;color:var(--ink-3);margin-top:.5rem;"
        "line-height:1.45'>Colour marks what an agent does. The role name on "
        "each node carries which one it is.</div>",
        unsafe_allow_html=True,
    )


# -- hero: the question is the entry point of the whole program ------------

st.markdown(
    "<div class='eyebrow'>Multi-agent failure analysis</div>"
    "<h1 class='hd'>Patient failure investigation</h1>"
    "<p class='sub'>Specialist agents investigate in parallel, cross-examine each "
    "other, and a critic returns a verdict with provenance, or abstains when the "
    "evidence is too thin to answer.</p>",
    unsafe_allow_html=True,
)

st.markdown("<div class='ask-label'>Ask the system</div>", unsafe_allow_html=True)
ask, launch = st.columns([5, 1], vertical_alignment="bottom")
with ask:
    question = st.text_area(
        "Question", value=PLACEHOLDER, height=92,
        label_visibility="collapsed", placeholder=PLACEHOLDER,
    )
with launch:
    go = st.button("Investigate", type="primary", width="stretch")

st.markdown(
    "<div style='font-size:.76rem;color:var(--ink-3);margin-top:-.4rem'>"
    "Ask a question or state a hypothesis to test.</div>",
    unsafe_allow_html=True,
)

run: RunState = st.session_state.run

live_slot = st.empty()
verdict_slot = st.empty()
detail_slot = st.empty()


def paint_live(state: RunState) -> None:
    with live_slot.container():
        C.render_stats(state)
        C.section("Agent graph")
        left, right = st.columns([3, 2], gap="medium")
        with left:
            st.markdown(
                "<div style='font-size:.74rem;color:var(--ink-3);margin-bottom:.3rem'>"
                "Solid arrows spawn. Dashed arrows are messages between agents.</div>",
                unsafe_allow_html=True,
            )
            C.render_graph(state)
        with right:
            st.markdown(
                "<div style='font-size:.74rem;color:var(--ink-3);margin-bottom:.3rem'>"
                "What the agents are saying to each other.</div>",
                unsafe_allow_html=True,
            )
            C.render_conversation(state)
        C.section(f"Agents ({len(state.agents)})")
        C.render_agent_cards(state)


def paint_detail(state: RunState) -> None:
    with verdict_slot.container():
        if state.complete:
            C.section("Result")
            C.render_verdict(state)
    with detail_slot.container():
        findings, timeline, agents, raw = st.tabs(
            ["Findings", "Timeline", "Agents", "Raw events"]
        )
        with findings:
            C.render_findings(state)
        with timeline:
            C.render_timeline(state)
        with agents:
            C.render_agent_table(state)
        with raw:
            st.json([vars(e) for e in state.raw], expanded=False)


# -- kick off --------------------------------------------------------------

if go:
    if mode == "Mock" and fixture is None:
        st.error("No recorded run selected.")
    elif not question.strip():
        st.error("Ask a question first.")
    else:
        st.session_state.run = RunState()
        st.session_state.pending = {
            "mode": mode,
            "fixture": str(fixture) if fixture else None,
            "speed": speed,
            "backend": backend,
            "question": question.strip(),
            "uploads": [(f.name, f.getvalue()) for f in uploads],
        }
        st.rerun()

pending = st.session_state.pending

if pending is None:
    paint_live(run)
    paint_detail(run)
else:
    st.session_state.pending = None
    state = st.session_state.run

    if pending["mode"] == "Mock":
        from ui.stream import mock_stream

        stream = mock_stream(pending["fixture"], speed=pending["speed"])
    else:
        try:
            with st.spinner("Uploading and starting the run"):
                file_ids = (
                    upload_files(pending["backend"], pending["uploads"])
                    if pending["uploads"] else []
                )
                run_id = start_run(pending["backend"], pending["question"], file_ids)
            stream = live_stream(pending["backend"], run_id)
        except Exception as exc:  # noqa: BLE001 - surface any backend problem in the UI
            st.error(f"Could not start the run. {type(exc).__name__}: {exc}")
            stream = iter(())

    # Fold events in as they arrive, repainting the live panels each time. The
    # detail panels are painted once at the end so the tab selection is stable.
    for event in stream:
        state.apply(event)
        paint_live(state)

    paint_detail(state)
