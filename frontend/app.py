"""Patient failure-investigation UI.

Run:  streamlit run frontend/app.py

Two modes, chosen in the sidebar:

  Mock  — replays a fixture. No backend, no tokens, no GPU. This is the daily
          dev loop and the rehearsal path.
  Live  — POST /investigate on the backend, then stream GET /events/{run_id}.

Both paths produce the same `Event` objects and fold into the same `RunState`,
so what you see in mock mode is what you get live.
"""

from __future__ import annotations

import streamlit as st

from ui import components as C
from ui.state import RunState
from ui.stream import DEFAULT_BACKEND, list_fixtures, live_stream, start_run, upload_files

st.set_page_config(page_title="Failure Investigation", page_icon="\U0001f9ec", layout="wide")


def _init() -> None:
    st.session_state.setdefault("run", RunState())
    st.session_state.setdefault("pending", None)


_init()


# -- sidebar ---------------------------------------------------------------

with st.sidebar:
    st.header("Run")
    mode = st.radio("Mode", ["Mock", "Live"], horizontal=True,
                    help="Mock replays a fixture with no backend running.")

    fixture = None
    backend = DEFAULT_BACKEND
    speed = 1.0
    uploads: list = []

    if mode == "Mock":
        fixtures = list_fixtures()
        if not fixtures:
            st.error("No fixtures in frontend/fixtures/.")
        else:
            fixture = st.selectbox("Fixture", fixtures, format_func=lambda p: p.stem)
        speed = st.slider("Playback speed", 0.25, 6.0, 1.5, 0.25,
                          help="Higher is faster. The demo is paced for ~1.5×.")
    else:
        backend = st.text_input("Backend", DEFAULT_BACKEND)
        uploads = st.file_uploader(
            "Patient files", accept_multiple_files=True,
            type=["vcf", "csv", "txt", "tsv", "json"],
        ) or []

    st.divider()
    question = st.text_area(
        "Question",
        value="Why did this patient fail pembrolizumab therapy?",
        height=90,
        help="A question or a hypothesis to test.",
    )
    go = st.button("Investigate", type="primary", width="stretch")
    if st.button("Clear", width="stretch"):
        st.session_state.run = RunState()
        st.session_state.pending = None
        st.rerun()

    st.divider()
    st.caption("Legend")
    st.markdown(
        "\n".join(
            f"<span style='color:{border};font-weight:600'>■</span> {role}"
            for role, (_fill, border) in C.ROLE_COLORS.items() if role != "unknown"
        ),
        unsafe_allow_html=True,
    )


# -- header ----------------------------------------------------------------

st.title("Patient failure investigation")
st.caption(
    "Specialist agents investigate in parallel, cross-examine each other, and a critic "
    "returns a verdict with provenance — or abstains when the evidence is thin."
)

run: RunState = st.session_state.run
if run.question:
    st.markdown(f"**Question** — {run.question}")
    if run.files:
        st.caption("Bundle: " + ", ".join(run.files))

live_slot = st.empty()
verdict_slot = st.empty()
detail_slot = st.empty()


def paint_live(state: RunState) -> None:
    with live_slot.container():
        C.render_header(state)
        left, right = st.columns([3, 2], gap="medium")
        with left:
            st.caption("Agent graph — solid arrows spawn, dashed arrows are messages")
            C.render_graph(state)
        with right:
            st.caption("Agent conversation")
            C.render_conversation(state)
        st.caption("Agents")
        C.render_agent_cards(state)


def paint_detail(state: RunState) -> None:
    with verdict_slot.container():
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
        st.error("No fixture selected.")
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
            with st.spinner("Uploading and starting the run…"):
                file_ids = (
                    upload_files(pending["backend"], pending["uploads"])
                    if pending["uploads"] else []
                )
                run_id = start_run(pending["backend"], pending["question"], file_ids)
            stream = live_stream(pending["backend"], run_id)
        except Exception as exc:  # noqa: BLE001 - surface any backend problem in the UI
            st.error(f"Could not start the run: {type(exc).__name__}: {exc}")
            stream = iter(())

    # Fold events in as they arrive, repainting the live panels each time. The
    # detail panels are painted once at the end so the tab selection is stable.
    for event in stream:
        state.apply(event)
        paint_live(state)

    paint_detail(state)
