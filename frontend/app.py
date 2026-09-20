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
from ui.theme import stylesheet, render_theme_control
from ui.help_text import HELP
from ui.runtime import BackgroundRun
from ui.voice import render_voice_controls
from ui.replay import Playback
from ui.followup import FollowUpSource, ContextInspection, weak_point_question
from ui.followup_preview import render_context_preview
from ui.capabilities import CapabilityLookup
from ui.run_clock import clock_data, render_run_clock
from ui.outcomes import outcome_notice, render_outcome_notice
from ui.history import result_labels, selected_result_html
from ui.receipt import render_request_receipt

st.set_page_config(page_title=PROFILE.page_title, page_icon=":material/science:", layout="wide", initial_sidebar_state="collapsed")
st.markdown(stylesheet(), unsafe_allow_html=True)


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
st.session_state.setdefault("followup_drafts", {})
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


def capability_lookup(base_url, mode="Live"):
    key = (base_url.strip(), mode)
    # One current discovery per session. Keep known settings until explicit refresh.
    if st.session_state.get("capability_key") != key:
        st.session_state.capability_key = key
        st.session_state.capability_lookup = CapabilityLookup(lambda: source_for(mode).capabilities(base_url))
    return st.session_state.capability_lookup


def backend_capabilities(base_url, mode="Live"):
    # Starting a run only reads an existing snapshot, never waits on HTTP.
    return capability_lookup(base_url, mode).snapshot()[:2]


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


def followup_draft():
    """Keep unsent drafts outside widget state, scoped to retained results."""
    current_id = st.session_state.result_id
    retained = {current_id, *(item["id"] for item in st.session_state.previous_runs)}
    drafts = st.session_state.followup_drafts
    for result_id in list(drafts):
        if result_id not in retained:
            del drafts[result_id]
    return drafts.setdefault(current_id, {"prompt": "", "weak_points": {}})


def remember_followup(widget_key, weak_point=None):
    saved = followup_draft()
    if weak_point is None:
        saved["prompt"] = st.session_state.get(widget_key, "")
    elif weak_point in saved["weak_points"]:
        saved["weak_points"][weak_point]["prompt"] = st.session_state.get(widget_key, "")


def discard_followup(widget_key, weak_point=None):
    saved = followup_draft()
    if weak_point is None:
        saved["prompt"] = ""
    else:
        saved["weak_points"].pop(weak_point, None)
    st.session_state.pop(widget_key, None)


def queue_followup(prompt, inspection):
    if not prompt.strip():
        st.error("Enter a follow-up question first.")
        return
    if st.session_state.job and st.session_state.job.active:
        st.warning("Wait for the current investigation to finish before running a follow-up.")
        return
    previous = st.session_state.submitted
    recording = previous.mode == "Mock"
    config = deepcopy(previous.config)
    # Keep routing stable when the context mentions a different workflow.
    config["task_mode"] = "idea_review" if recording else st.session_state.run.task_mode
    st.session_state.queued_followup = replace(previous, mode="Demo" if recording else previous.mode,
        question=prompt.strip(), context=deepcopy(inspection.payload), config=config,
        fixture=None if recording else previous.fixture, sample=False if recording else previous.sample,
        uploads=[] if recording else deepcopy(previous.uploads))
    st.rerun()


def render_weak_point_followup(index, item, inspection):
    saved = followup_draft()
    # The completed result has a stable item order, including older records without IDs.
    point_key = str(index)
    widget_key = f"weak_point_followup:{st.session_state.result_id}:{point_key}"
    entry = saved["weak_points"].get(point_key)
    if entry is None:
        if st.button("Draft a follow-up", key=f"draft_weak_point:{index}", disabled=run_active):
            saved["weak_points"][point_key] = {
                "id": item.get("id"), "prompt": weak_point_question(st.session_state.run, item),
            }
            st.rerun()
        return
    with st.container(border=True):
        st.caption("Follow-up draft for this weak point")
        st.caption("This drafts a question using the evidence already in this run. It does not add the requested evidence.")
        if st.session_state.submitted.mode == "Mock":
            st.caption("Running this follow-up reviews the saved context with simulated agents. Original source files are not reanalyzed.")
        seed(widget_key, entry["prompt"])
        entry["prompt"] = st.text_area("Review and edit the follow-up", key=widget_key, height=220,
                                      on_change=remember_followup, args=(widget_key, point_key))
        render_context_preview(inspection, key=f"weak_followup_context:{st.session_state.result_id}:{point_key}")
        run, discard = st.columns(2)
        with run:
            if st.button("Run follow-up", key=f"run_weak_point:{index}", type="primary", disabled=run_active):
                queue_followup(entry["prompt"], inspection)
        with discard:
            st.button("Discard draft", key=f"discard_weak_point:{index}",
                      on_click=discard_followup, args=(widget_key, point_key))


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
        render_theme_control("astral" if st.session_state.get("astral_theme") else "dark")
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
pending_capabilities = None
previous_result_slot = st.empty()
if st.session_state.stage in ("evidence", "question") and st.session_state.run.complete:
    # Reserve this outer position before completion so a draft's blur rerun
    # cannot shift the polling fragment and replace its outcome button midclick.
    with previous_result_slot.container():
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
    if draft["mode"] != "Mock":
        capability_lookup(draft["backend"], draft["mode"])
    if st.button("Continue to question", key="evidence_next", type="primary"):
        if valid:
            navigate("question")
        else:
            st.error("Add files, select the bundled sample, or choose Start from an idea without files.")

elif st.session_state.stage == "question":
    st.title("Choose your agents")
    mode = draft["mode"]
    capabilities_ready = True
    if mode == "Mock":
        st.caption("This recording uses its saved question and agents. It does not analyze a new prompt.")
        agent_config, config_valid = {}, True
    else:
        lookup = capability_lookup(draft["backend"], mode)
        capabilities, error, capabilities_ready, refreshing, _ = lookup.snapshot()
        if refreshing:
            pending_capabilities = lookup
        if capabilities.get("run_mode") == "mock":
            st.caption("This backend uses simulated model outputs.")
        if not capabilities_ready:
            st.markdown("<div class='loading-status'><span></span>Loading available agents and models</div>", unsafe_allow_html=True)
            st.caption("You can edit your question or return to evidence while the service responds.")
            agent_config, config_valid = deepcopy(draft["config"]), False
        else:
            agent_config, config_valid = render_agent_setup(mode, draft["backend"], capabilities, error, saved_config=draft["config"])
            draft["config"] = deepcopy(agent_config)
            if mode == "Live" and st.button("Refresh available models and agents", key="refresh_capabilities", disabled=refreshing):
                lookup.refresh()
                st.rerun()
            if refreshing:
                st.caption("Refreshing available controls. Your current settings remain usable.")
    back, launch = st.columns([1, 2])
    with back:
        if st.button("Back to evidence", key="question_back"):
            navigate("evidence")
    with launch:
        if st.button("Start replay" if mode == "Mock" else "Start investigation", key="start_run", type="primary", disabled=run_active or not capabilities_ready):
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
            render_context_preview(ContextInspection(payload=st.session_state.submitted.context),
                                   key=f"carried_followup_context:{st.session_state.result_id}")
    if st.button("Replay agent activity", key="results_replay", disabled=run_active or not st.session_state.run.raw):
        st.session_state.playback = Playback(st.session_state.run.raw)
        navigate("investigation")
    st.caption(st.session_state.run.question)
    C.render_verdict(st.session_state.run)
    recording = st.session_state.submitted.mode == "Mock"
    context_inspection = ContextInspection(st.session_state.run)
    with st.expander("Ask a follow-up"):
        st.caption("Follow-ups to recordings review the saved context with simulated agents. Original source files are not reanalyzed."
                   if recording else "Ask a follow-up using the same evidence and agent settings. Previous findings and weak points are included as context to check.")
        saved_followup = followup_draft()
        if st.session_state.get("followup_owner") != st.session_state.result_id:
            st.session_state.followup_owner = st.session_state.result_id
            st.session_state.followup_prompt = saved_followup["prompt"]
        seed("followup_prompt", saved_followup["prompt"])
        saved_followup["prompt"] = st.text_input("Follow-up prompt", key="followup_prompt", max_chars=4000,
            on_change=remember_followup, args=("followup_prompt",),
            placeholder="What evidence would distinguish the competing explanations?")
        render_context_preview(context_inspection, key=f"manual_followup_context:{st.session_state.result_id}")
        run_followup, discard = st.columns(2)
        with run_followup:
            if st.button("Run follow-up", key="run_followup", type="primary", disabled=run_active):
                queue_followup(saved_followup["prompt"], context_inspection)
        with discard:
            st.button("Discard draft", key="discard_followup", disabled=not saved_followup["prompt"],
                      on_click=discard_followup, args=("followup_prompt",))
    render_results(st.session_state.run, show_summary=False,
                   weak_point_actions=lambda index, item: render_weak_point_followup(index, item, context_inspection))
    render_request_receipt({'id': st.session_state.result_id, 'run': st.session_state.run,
                            'request': st.session_state.submitted},
                           key=f"current_receipt:{st.session_state.result_id}")
    previous_runs = [item for item in st.session_state.previous_runs if item["id"] != st.session_state.result_id]
    if previous_runs:
        with st.expander("Previous results in this session"):
            st.caption("The five most recent results are kept while this session is open.")
            records_by_id = {item["id"]: item for item in previous_runs}
            saved_labels = result_labels(previous_runs)
            if st.session_state.get("saved_result") not in records_by_id:
                st.session_state.saved_result = previous_runs[0]["id"]
            chosen = st.selectbox("Saved result", list(records_by_id), key="saved_result",
                                  format_func=saved_labels.__getitem__)
            selected = records_by_id[chosen]
            st.markdown(selected_result_html(selected), unsafe_allow_html=True)
            render_request_receipt(selected, key=f"selected_receipt:{selected['id']}",
                                   label='Request receipt for selected result')
            if st.button("Open selected result", key="open_saved_result", disabled=run_active):
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

if (st.session_state.stage in ("investigation", "results") and st.session_state.job
        and st.session_state.submitted.mode != "Mock" and not st.session_state.playback):
    # Outside the 300ms activity fragment: browser ticks never request a rerun.
    render_run_clock(clock_data(st.session_state.job, st.session_state.run))

activity_slot = st.empty()


@st.fragment(run_every=.25 if pending_capabilities else None)
def poll_capabilities():
    if pending_capabilities and not pending_capabilities.snapshot()[3]:
        st.rerun()


poll_capabilities()

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
        paint_live(playback.state, st.empty(), recording=True, help_scope=f"replay:{st.session_state.result_id}")
        if playback.finished:
            st.caption("Replay complete. The original result is available in Results.")
            if replay_active:
                st.rerun()
        return
    current_job = st.session_state.job
    if not current_job:
        return
    if current_job.request.mode == "Live" and st.session_state.get("capability_key") == (current_job.request.backend.strip(), "Live"):
        current_job.can_cancel = bool(st.session_state.capability_lookup.snapshot()[0].get("cancellation_supported"))
    events = current_job.drain()
    for event in events:
        st.session_state.run.apply(event)
    state = st.session_state.run
    active = current_job.active
    if active:
        working = [agent.role.replace("_", " ") for agent in state.agents.values() if agent.status == "running"]
        phase = "Cancellation requested. Waiting for cleanup." if current_job.cancel_requested else (
            "Checking the findings and evidence" if "critic" in working else
            "Specialists are examining the evidence" if any(role != "orchestrator" for role in working) else
            "Planning the investigation" if "orchestrator" in working else "Preparing evidence and starting the investigation")
        st.markdown(f"<div class='loading-status'><span></span>{phase}</div>", unsafe_allow_html=True)
        st.caption("You can switch sections and edit the next question while this run continues.")
        if current_job.can_cancel and (current_job.request.mode != "Live" or state.run_id):
            if st.button("Cancel investigation", key="cancel_run", disabled=current_job.cancel_requested):
                current_job.request_cancel()
                st.rerun()
    if st.session_state.stage == "investigation":
        # Streamlit clears fragment-owned children on each poll, even when their
        # placeholder was declared outside it. Paint every poll until activity has
        # a separate client-owned rendering boundary; otherwise quiet runs vanish.
        paint_live(state, activity_slot, recording=current_job.request.mode == "Mock",
                   help_scope=f"live:{st.session_state.result_id}")
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
    if not active:
        if st.session_state.stage in ("investigation", "results"):
            current_job.outcome_reviewed = True
        elif not getattr(current_job, "outcome_reviewed", False):
            notice = outcome_notice(state, active=False, recording=current_job.request.mode == "Mock",
                                    replaying=bool(playback))
            if notice and render_outcome_notice(notice, key=f"view_run_outcome:{st.session_state.result_id}"):
                # A fragment button does not otherwise rerender the outer editor
                # before navigation. Retain its latest submitted widget value.
                if "draft_question" in st.session_state:
                    draft["question"] = st.session_state.draft_question
                current_job.outcome_reviewed = True
                navigate(notice.target)
    if not active and not current_job.completion_announced:
        current_job.completion_announced = True
        if header_target or view_previous:
            return  # Explicit navigation wins; draft controls have already saved.
        if state.complete and st.session_state.stage == "investigation":
            st.session_state.stage = "results"
        if st.session_state.stage in ("investigation", "results"):
            st.rerun()
        # Leave an editor's DOM and uncommitted text untouched. The fragment-owned
        # notice provides immediate navigation; headers refresh on normal input.
    if active and not header_target and not view_previous:
        roles = {agent.role for agent in state.agents.values()}
        milestone = "critic" if "critic" in roles else "orchestrator" if "orchestrator" in roles else ""
        if milestone and milestone != st.session_state.get("voice_agent_stage", ""):
            st.session_state.voice_agent_stage = milestone
            if st.session_state.stage == "investigation":
                st.rerun()  # Do not remount an editor merely for a voice milestone.

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
