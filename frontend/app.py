"""Progressive investigation flow. Transport and views remain replaceable."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from uuid import uuid4
import streamlit as st

from ui import components as C
from ui import help as H
from ui.state import RunState
from ui.config import PROFILE
from ui.adapters import RunRequest, source_for, recorded_context, list_fixtures, DEFAULT_BACKEND
from ui.layout import paint_live, render_results, render_agent_setup
from ui.events import Event
from ui.theme import stylesheet
from ui.help_text import HELP
from ui.runtime import BackgroundRun
from ui.voice import render_voice_controls
from ui.replay import Playback
from ui.followup import FollowUpSource, context_for

st.set_page_config(page_title=PROFILE.page_title, page_icon=":material/science:", layout="wide", initial_sidebar_state="collapsed")
st.session_state.setdefault("astral_theme", False)
theme = "astral" if st.session_state.astral_theme else "dark"
st.markdown(stylesheet(theme), unsafe_allow_html=True)


def new_draft():
    return dict(mode="Demo", backend=DEFAULT_BACKEND, fixture=None, speed=1.5,
                uploads=[], question=PROFILE.default_question, config={}, sample=False, question_only=False)


st.session_state.setdefault("stage", "evidence")
st.session_state.setdefault("draft", new_draft())
st.session_state.setdefault("run", RunState())
st.session_state.setdefault("submitted", None)
st.session_state.setdefault("pending", None)
st.session_state.setdefault("job", None)
st.session_state.setdefault("playback", None)
st.session_state.setdefault("previous_runs", [])
st.session_state.setdefault("result_id", uuid4().hex)
draft = st.session_state.draft


def seed(key, value):
    if key not in st.session_state:
        st.session_state[key] = value


def navigate(stage):
    if stage != "investigation" and st.session_state.playback:
        st.session_state.playback.pause()
    st.session_state.stage = stage
    st.rerun()


def evidence_ready():
    # Widget changes arrive before this script renders the evidence controls.
    editing = st.session_state.stage == "evidence"
    mode = st.session_state.get("draft_mode", draft["mode"]) if editing else draft["mode"]
    sample = st.session_state.get("draft_sample", draft["sample"]) if editing else draft["sample"]
    question_only = st.session_state.get("draft_question_only", draft.get("question_only", False)) if editing else draft.get("question_only", False)
    backend = st.session_state.get("draft_backend", draft["backend"]) if editing else draft["backend"]
    if mode == "Demo":
        return True
    if mode == "Mock":
        return bool(draft["fixture"])
    return bool(backend.strip()) and (
        not PROFILE.require_files or sample or bool(draft["uploads"]) or question_only)


def capture_uploads(widget_key):
    st.session_state.draft["uploads"] = [(file.name, file.getvalue()) for file in st.session_state.get(widget_key, [])]


@st.cache_data(ttl=15, show_spinner=False)
def backend_capabilities(base_url, mode="Live"):
    try:
        return source_for(mode).capabilities(base_url), ""
    except Exception as exc:
        return {}, f"Could not read backend capabilities ({type(exc).__name__})."


def save_result():
    if not st.session_state.run.complete:
        return
    result_id = st.session_state.result_id
    history = st.session_state.previous_runs
    if not any(item["id"] == result_id for item in history):
        history.append({"id": result_id, "run": deepcopy(st.session_state.run),
                        "request": deepcopy(st.session_state.submitted)})
        st.session_state.previous_runs = history[-5:]


def start(request):
    if st.session_state.job and st.session_state.job.active:
        st.warning("An investigation is already running. Wait for it to finish or cancel it before starting another.")
        return
    # Separate copies prevent subsequent form edits changing a submitted run.
    save_result()
    st.session_state.result_id = uuid4().hex
    st.session_state.playback = None
    st.session_state.submitted = deepcopy(request)
    st.session_state.pending = None
    st.session_state.run = RunState()
    st.session_state.voice_agent_stage = ""
    capabilities, _ = backend_capabilities(request.backend, request.mode)
    source = source_for(request.mode)
    if request.context:
        source = FollowUpSource(source)
    st.session_state.job = BackgroundRun(source, request,
        can_cancel=request.mode != "Live" or bool(capabilities.get("cancellation_supported")))
    navigate("investigation")


if st.session_state.get("queued_followup"):
    request = st.session_state.pop("queued_followup")
    draft.update(question=request.question, mode=request.mode, backend=request.backend,
                 sample=request.sample, uploads=deepcopy(request.uploads), config=deepcopy(request.config))
    for key in list(st.session_state):
        if key.startswith("draft_"):
            del st.session_state[key]
    st.session_state.draft_question = request.question
    start(request)


job = st.session_state.job
if job:
    for event in job.drain():
        st.session_state.run.apply(event)
run_active = bool(job and job.active)

with st.container(key="workspace_header"):
    brand_column, theme_column = st.columns([4, 1], vertical_alignment="center")
    with brand_column:
        st.markdown(f"<div class='flow-brand'>{C._escape(PROFILE.name)}<span>{C._escape(PROFILE.eyebrow)}</span></div>", unsafe_allow_html=True)
    with theme_column:
        H.widget(st.toggle, "Astral light", key="astral_theme",
                  help="Switch between the dark workspace and a white, blue and violet constellation theme. Your choice stays with this session.")
stages = ["evidence", "question", "investigation", "results"]
labels = ["Evidence", "Question & agents", "Investigation", "Results"]
current = stages.index(st.session_state.stage)
header_target = None
available = {"evidence": True, "question": evidence_ready(),
             "investigation": st.session_state.submitted is not None,
             "results": st.session_state.run.complete}
with st.container(key="stage_navigation"):
    for index, column in enumerate(st.columns(4)):
        stage = stages[index]
        active = index == current
        with column:
            if st.button(f"{index + 1:02} {labels[index]}" + (" (current)" if active else ""),
                         key=f"nav_{stage}", type="primary" if active else "secondary",
                         disabled=not available[stage],
                         width="stretch"):
                header_target = stage

editor_mode = st.session_state.get("draft_mode", draft["mode"]) if st.session_state.stage == "evidence" else draft["mode"]
voice_action = render_voice_controls(st.session_state.stage, draft["question"],
    phase=st.session_state.run.status if st.session_state.run.complete else ("running" if run_active else "error" if st.session_state.run.errors else ""),
    run_id=st.session_state.run.run_id, agent_stage=st.session_state.get("voice_agent_stage", ""),
    dictation_enabled=editor_mode != "Mock")
if voice_action:
    if voice_action["type"] == "dictation" and editor_mode != "Mock":
        draft["question"] = voice_action["text"]
        st.session_state.draft_question = voice_action["text"]
    elif voice_action["type"] == "navigate":
        header_target = voice_action["target"]
with st.expander("Research question", expanded=st.session_state.stage == "question"):
    submitted = st.session_state.submitted
    if submitted:
        st.caption("Question submitted for the current run")
        st.write(submitted.question)
    if editor_mode == "Mock":
        fixture_path = st.session_state.get("draft_fixture", draft["fixture"]) if st.session_state.stage == "evidence" else draft["fixture"]
        if not fixture_path:
            available_fixtures = list_fixtures()
            fixture_path = next((path for path in available_fixtures if path.stem == PROFILE.default_fixture),
                                available_fixtures[0] if available_fixtures else None)
        question, _ = recorded_context(Path(fixture_path) if fixture_path else None, PROFILE.default_question)
        st.session_state.recorded_question = question
        H.widget(st.text_area, "Recorded question", disabled=True, key="recorded_question", height=110, help=HELP["recorded_question"])
        st.caption("A recording uses its saved question. Use the interactive demo to ask a different question.")
        if st.button("Use an editable demo", key="edit_recording_question"):
            draft["mode"] = "Demo"
            draft["question"] = question
            st.session_state.draft_mode = "Demo"
            st.session_state.draft_question = question
            navigate("question")
    else:
        seed("draft_question", draft["question"])
        draft["question"] = H.widget(st.text_area, "Research question", key="draft_question", height=110, help=HELP["question"])
        question = draft["question"]
        if submitted:
            st.caption("Edits apply only when you explicitly start another investigation. The current run and its results remain unchanged.")
        else:
            st.caption("Edit this draft from any section. Nothing runs until you select Start investigation.")

if st.session_state.stage in ("investigation", "results"):
    submitted = st.session_state.submitted
    if submitted and submitted.mode == "Mock":
        st.caption("Recorded replay. These are saved outputs from the selected case.")
    elif submitted and submitted.mode == "Demo":
        st.caption("Interactive demo. Your question and agent selection drive the workflow with simulated model outputs.")
    elif st.session_state.run.config.get("run_mode") == "mock":
        st.caption("Mock execution. The workflow runs on your inputs with simulated model outputs.")

view_previous = False
if st.session_state.stage in ("evidence", "question") and st.session_state.run.complete:
    view_previous = st.button("View previous result", key="view_previous_result")

if st.session_state.stage == "evidence":
    st.title("Choose your evidence")
    st.caption("Try the sample dataset, select a recording or add your own files.")
    seed("draft_mode", draft["mode"])
    draft["mode"] = H.widget(st.radio, "Source", list(PROFILE.mode_labels), horizontal=True,
                             format_func=lambda value: PROFILE.mode_labels[value], key="draft_mode", help=HELP["source"])
    valid = True
    if draft["mode"] == "Demo":
        st.subheader("Interactive demo")
        st.write("Ask an evidence question using the bundled sample, or review an idea without adding unrelated sample data. Choose the workflow in the next step.")
        st.caption("This demo runs the investigation workflow with simulated model outputs. It does not call live model APIs.")
    elif draft["mode"] == "Mock":
        fixtures = list_fixtures()
        paths = [str(path) for path in fixtures]
        if paths:
            if draft["fixture"] not in paths:
                draft["fixture"] = next((str(p) for p in fixtures if p.stem == PROFILE.default_fixture), paths[0])
            seed("draft_fixture", draft["fixture"])
            draft["fixture"] = H.widget(st.selectbox, "Recorded case", paths, key="draft_fixture", help=HELP["recorded_case"],
                format_func=lambda path: PROFILE.fixture_labels.get(Path(path).stem, Path(path).stem.replace("_", " ")))
            recorded_question, files = recorded_context(Path(draft["fixture"]), PROFILE.default_question)
            st.caption("Recorded evidence")
            st.markdown("<div class='file-chips'>" + "".join(f"<span>{C._escape(name)}</span>" for name in files) + "</div>", unsafe_allow_html=True)
            with st.expander("Playback options"):
                seed("draft_speed", draft["speed"])
                draft["speed"] = H.widget(st.slider, "Playback speed", 0.25, 6.0, step=0.25, key="draft_speed", help=HELP["playback_speed"])
        else:
            st.error("No recorded cases are available.")
            valid = False
    else:
        seed("draft_question_only", draft.get("question_only", False))
        draft["question_only"] = H.widget(st.toggle, "Start from an idea without files", key="draft_question_only",
            help="Continue with a proposal or design question. The next step lets you choose Idea review; this does not invent scientific evidence.")
        if draft["question_only"]:
            st.caption("This run will use your question without uploading the saved files or loading the sample.")
        with st.expander("Connection settings"):
            seed("draft_backend", draft["backend"])
            draft["backend"] = H.widget(st.text_input, "Backend", key="draft_backend", help=HELP["backend"])
            st.caption("The server controls available datasets and models. Connected runs may use mock providers.")
        if PROFILE.sample_available:
            seed("draft_sample", draft["sample"])
            draft["sample"] = H.widget(st.toggle, PROFILE.sample_label, key="draft_sample", help=HELP["sample"], disabled=draft.get("question_only", False))
        if draft["sample"]:
            st.caption(PROFILE.sample_description)
        else:
            upload_key = f"draft_uploads_{st.session_state.get('upload_generation', 0)}"
            H.widget(st.file_uploader, PROFILE.upload_label, accept_multiple_files=True,
                             type=list(PROFILE.input_extensions) or None,
                             key=upload_key, on_change=capture_uploads, args=(upload_key,), help=HELP["uploads"], disabled=draft.get("question_only", False))
            if draft["uploads"]:
                st.caption("Saved evidence for this draft. Add a new selection to replace these files.")
                for name, data in draft["uploads"]:
                    st.text(f"{name} ({len(data):,} bytes)")
                if st.button("Remove saved files", key="remove_files"):
                    draft["uploads"] = []
                    # A new widget identity clears the browser-side file selection.
                    st.session_state.upload_generation = st.session_state.get("upload_generation", 0) + 1
                    st.rerun()
            st.caption("Files are sent to the backend only when you start. Remove saved files to clear this draft.")
        valid = bool(draft["backend"].strip()) and (not PROFILE.require_files or draft["sample"] or bool(draft["uploads"]) or draft.get("question_only"))
    if st.button("Continue to question", key="evidence_next", type="primary"):
        if valid:
            navigate("question")
        else:
            st.error("Add files, select the bundled sample, or choose Start from an idea without files.")

elif st.session_state.stage == "question":
    st.title("Choose your agents")
    mode = draft["mode"]
    if mode == "Mock":
        st.caption("This recording uses its saved question and agents. It does not analyze a new prompt.")
        agent_config, config_valid = {}, True
    else:
        capabilities, error = backend_capabilities(draft["backend"], mode)
        if capabilities.get("run_mode") == "mock":
            st.caption("This backend uses simulated model outputs.")
        agent_config, config_valid = render_agent_setup(mode, draft["backend"], capabilities, error, saved_config=draft["config"])
        draft["config"] = deepcopy(agent_config)
    back, launch = st.columns([1, 2])
    with back:
        if st.button("Back to evidence", key="question_back"):
            navigate("evidence")
    with launch:
        if st.button("Start replay" if mode == "Mock" else "Start investigation", key="start_run", type="primary", disabled=run_active):
            if not question.strip():
                st.error("Enter a research question before starting.")
            elif not config_valid:
                st.error("Select at least one specialist before starting.")
            else:
                start(RunRequest(mode=mode, question=question.strip(), backend=draft["backend"],
                    fixture=draft["fixture"], speed=draft["speed"], sample=mode == "Demo" or (draft["sample"] and not draft.get("question_only")),
                    uploads=[] if mode == "Demo" or draft.get("question_only") else deepcopy(draft["uploads"]), config=deepcopy(agent_config)))

elif st.session_state.stage == "investigation":
    st.title("Investigation")
    if st.session_state.run.complete and not run_active and not st.session_state.playback:
        if st.button("Replay agent activity", key="investigation_replay"):
            st.session_state.playback = Playback(st.session_state.run.raw)
            st.rerun()
    # The polling fragment below renders activity; the main script stays interactive.

elif st.session_state.stage == "results":
    st.title("Results")
    if st.session_state.submitted.context:
        with st.expander("Context carried into this follow-up"):
            st.caption("Previous generated claims are context to check, not new evidence.")
            st.json(st.session_state.submitted.context, expanded=False)
    if st.button("Replay agent activity", key="results_replay", disabled=run_active or not st.session_state.run.raw):
        st.session_state.playback = Playback(st.session_state.run.raw)
        navigate("investigation")
    st.caption(st.session_state.run.question)
    C.render_verdict(st.session_state.run)
    recording = st.session_state.submitted.mode == "Mock"
    with st.expander("Ask a follow-up"):
        st.caption("Follow-ups to recordings review the saved context with simulated agents. Original source files are not reanalyzed."
                   if recording else "Ask a follow-up using the same evidence and agent settings. Previous findings and weak points are included as context to check.")
        with st.form("followup_form", clear_on_submit=True):
            followup = st.text_input("Follow-up prompt", key="followup_prompt", max_chars=4000,
                                     placeholder="What evidence would distinguish the competing explanations?")
            followup_requested = st.form_submit_button("Run follow-up", type="primary", disabled=run_active)
    if followup_requested:
        if not followup.strip():
            st.error("Enter a follow-up question first.")
        else:
            previous = st.session_state.submitted
            config = deepcopy(previous.config)
            # Keep routing stable when the context mentions a different workflow.
            config["task_mode"] = "idea_review" if recording else st.session_state.run.task_mode
            st.session_state.queued_followup = replace(previous, mode="Demo" if recording else previous.mode,
                question=followup.strip(), context=context_for(st.session_state.run), config=config,
                fixture=None if recording else previous.fixture, sample=False if recording else previous.sample)
            st.rerun()
    render_results(st.session_state.run, show_summary=False)
    previous_runs = [item for item in st.session_state.previous_runs if item["id"] != st.session_state.result_id]
    if previous_runs:
        with st.expander("Previous results in this session"):
            st.caption("The five most recent results are kept while this session is open.")
            chosen = st.selectbox("Saved result", range(len(previous_runs)), key="saved_result",
                                  format_func=lambda index: previous_runs[index]["run"].question[:100])
            if st.button("Open saved result", key="open_saved_result", disabled=run_active):
                selected = previous_runs[chosen]
                save_result()
                st.session_state.run = deepcopy(selected["run"])
                st.session_state.submitted = deepcopy(selected["request"])
                st.session_state.result_id = selected["id"]
                st.session_state.job = None
                st.session_state.playback = None
                st.rerun()
    edit, new = st.columns(2)
    with edit:
        if st.button("Edit setup for another run", key="results_edit"):
            navigate("question")
    with new:
        if st.button("Start a new investigation", key="results_new"):
            st.session_state.draft = new_draft()
            for key in list(st.session_state):
                if key.startswith("draft_"):
                    del st.session_state[key]
            navigate("evidence")

activity_slot = st.empty()

replay_active = bool(st.session_state.playback and st.session_state.playback.playing and st.session_state.stage == "investigation")

@st.fragment(run_every=0.3 if run_active or replay_active else None)
def poll_investigation():
    playback = st.session_state.playback
    if playback and st.session_state.stage == "investigation":
        playback.advance()
        st.caption("Replay of saved activity. Timing is compressed for playback. No models are called; your result is unchanged.")
        pause, step, restart, finish = st.columns(4)
        with pause:
            if st.button("Pause" if playback.playing else "Resume", key="replay_pause", disabled=playback.finished):
                playback.pause() if playback.playing else playback.resume()
                st.rerun()
        with step:
            if st.button("Next event", key="replay_step", disabled=playback.finished):
                playback.step()
                st.rerun()
        with restart:
            if st.button("Restart replay", key="replay_restart"):
                playback.restart()
                st.rerun()
        with finish:
            if st.button("Back to results", key="replay_results"):
                navigate("results")
        speed = st.select_slider("Replay speed", options=[.5, 1., 2., 4.], value=playback.speed, format_func=lambda value: f"{value:g}x", key="replay_speed")
        if speed != playback.speed:
            playback.set_speed(speed)
        st.progress(playback.index / max(1, len(playback.events)), text=f"{playback.index} of {len(playback.events)} saved events")
        paint_live(playback.state, st.empty())
        if playback.finished:
            st.caption("Replay complete. The original result is available in Results.")
            if replay_active:
                st.rerun()
        return
    current_job = st.session_state.job
    if not current_job:
        return
    events = current_job.drain()
    for event in events:
        st.session_state.run.apply(event)
    state = st.session_state.run
    active = current_job.active
    if active:
        phase = "Cancellation requested. Waiting for cleanup." if current_job.cancel_requested else (
            "Agents are investigating" if state.agents else "Preparing evidence and starting the investigation")
        st.markdown(f"<div class='loading-status'><span></span>{phase}</div>", unsafe_allow_html=True)
        st.caption("You can switch sections and edit the next question while this run continues.")
        if current_job.can_cancel and (current_job.request.mode != "Live" or state.run_id):
            if st.button("Cancel investigation", key="cancel_run", disabled=current_job.cancel_requested):
                current_job.request_cancel()
                st.rerun()
    if st.session_state.stage == "investigation":
        # Fragment reruns clear their output. Repaint at the bounded polling rate
        # even when idle, keeping the graph visible between incoming batches.
        paint_live(state, activity_slot)
        current_job.render_batches = getattr(current_job, "render_batches", 0) + 1
        if not active and not state.complete:
            st.warning("This run has not produced a completed result. Edit the setup or explicitly start a new attempt.")
            retry, edit = st.columns(2)
            with retry:
                if st.button("Retry investigation", key="investigation_retry"):
                    start(st.session_state.submitted)
            with edit:
                if st.button("Edit setup", key="investigation_edit"):
                    navigate("question")
        elif state.complete:
            st.caption("This run has ended. Open Results to review its outcome and evidence.")
    if not active and not current_job.completion_announced:
        current_job.completion_announced = True
        if header_target or view_previous:
            return  # Explicit navigation wins; draft controls have already saved.
        if state.complete and st.session_state.stage == "investigation":
            st.session_state.stage = "results"
        st.rerun()
    if active and not header_target and not view_previous:
        roles = {agent.role for agent in state.agents.values()}
        milestone = "critic" if "critic" in roles else "orchestrator" if "orchestrator" in roles else ""
        if milestone and milestone != st.session_state.get("voice_agent_stage", ""):
            st.session_state.voice_agent_stage = milestone
            st.rerun()  # Refresh optional stage announcement once per meaningful milestone.

poll_investigation()

# Save the currently displayed controls before leaving for the previous report.
if view_previous:
    navigate("results")
if header_target and header_target != st.session_state.stage:
    # Validate after saving controls: navigation can share a rerun with an edit.
    can_open = {"evidence": True, "question": evidence_ready(),
                "investigation": st.session_state.submitted is not None, "results": st.session_state.run.complete}
    if can_open.get(header_target, False):
        navigate(header_target)
    else:
        st.info("That section is not available yet. Add evidence before Question & agents, start a run before Investigation, and wait for its outcome before Results.")
