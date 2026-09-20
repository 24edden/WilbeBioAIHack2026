"""Page composition. Reorder panels here without changing transport or state."""
import streamlit as st
from . import help as H
from . import components as C
from .state import RunState
from .config import PROFILE
from .help_text import HELP
from .details import render_details
from .activity import render_activity_history

def render_agent_setup(mode: str, backend: str, capabilities: dict, error: str = "", saved_config: dict | None = None) -> tuple[dict, bool]:
    """Return backend-supported configuration, never cosmetic agent controls."""
    saved_config = saved_config or {}
    with st.container():
        C.section("Agent setup", help=HELP["agent_setup"])
        if mode == "Mock":
            st.caption("Recorded cases use their saved agents and model outputs. Switch to Investigate my data to configure a new run.")
            return {}, True
        roles = capabilities.get("specialist_roles")
        if not isinstance(roles, list) or not roles:
            st.info("Agent configuration is unavailable for this backend. Runs will use its default settings.")
            if error:
                st.caption(error)
            return {}, True
        options = {str(role["id"]): str(role.get("label", role["id"]))
                   for role in roles if isinstance(role, dict) and role.get("id")}
        defaults = capabilities.get("defaults", {})
        required = capabilities.get("required_roles", [])
        config = {}
        task_modes = capabilities.get("task_modes", [])
        mode_options = {str(item["id"]): str(item.get("label", item["id"])) for item in task_modes if isinstance(item, dict) and item.get("id")}
        task_mode = "investigation"
        if mode_options:
            if "draft_task_mode" not in st.session_state or st.session_state.draft_task_mode not in mode_options:
                preferred = saved_config.get("task_mode", "auto" if "auto" in mode_options else defaults.get("task_mode", "investigation"))
                st.session_state.draft_task_mode = preferred if preferred in mode_options else next(iter(mode_options))
            task_mode = H.widget(st.selectbox, "Task mode", list(mode_options), format_func=lambda value: mode_options[value],
                                     key="draft_task_mode", help=HELP["task_mode"])
            config["task_mode"] = task_mode
        skill_catalog = capabilities.get("skills", [])
        review_roles = capabilities.get("review_roles", [])
        if task_mode in ("auto", "idea_review"):
            if task_mode == "auto":
                st.caption("The backend chooses the workflow from your question and evidence. The chosen plan appears when the run starts. Select Evidence investigation to customize its specialist team.")
                with st.expander("Available teams and skills"):
                    st.write("Evidence investigation")
                    C.render_role_catalog(roles, skill_catalog)
                    st.write("Idea review")
                    C.render_role_catalog(review_roles, skill_catalog)
            else:
                st.caption(f"Fixed review team: {len(review_roles) + len(required)} agents including {', '.join(required)}. The research agent inventories supplied evidence, then support and challenge agents exchange and revise arguments.")
                C.render_role_catalog(review_roles, skill_catalog)
                st.caption("These are design-review perspectives, not measures of truth or scientific confidence.")
            valid = True
        else:
            if "draft_specialists" not in st.session_state:
                st.session_state.draft_specialists = [role for role in saved_config.get("specialists", defaults.get("specialists", list(options))) if role in options]
            selected = H.widget(st.multiselect, "Specialist agents", list(options),
                                      format_func=lambda role: options[role], key="draft_specialists", help=HELP["specialists"])
            st.caption(f"{len(selected) + len(required)} agents total. Required: {', '.join(str(role) for role in required) or 'none'}.")
            if len(selected) == 1 and PROFILE.single_specialist_note:
                st.caption(PROFILE.single_specialist_note)
            if not selected:
                st.warning("Select at least one specialist before starting.")
            config["specialists"] = selected
            with st.expander("Selected agent skills"):
                C.render_role_catalog([role for role in roles if role.get("id") in selected], skill_catalog)
            valid = bool(selected)
        with st.expander("Model settings"):
            if capabilities.get("model_overrides_supported"):
                st.caption("Model IDs run on the server's configured providers. Credentials stay on the server.")
                labels = {"reasoning_model": "Reasoning model (shared by planner, specialists and critic)",
                          "variant_model": "Variant analysis model", "embedding_model": "Literature embedding model"}
                for field, label in labels.items():
                    key = f"draft_{field}"
                    if key not in st.session_state:
                        st.session_state[key] = str(saved_config.get(field, defaults.get(field)) or "")
                    value = H.widget(st.text_input, label, key=key, help=HELP[field])
                    # Preserve an intentional blank when returning to this step.
                    config[field] = value.strip()
            else:
                st.caption("This backend uses mock model outputs. Agent selection changes the actual workflow; model overrides are unavailable."
                           if capabilities.get("run_mode") == "mock" else "Model selection is fixed by the backend. Agent selection remains configurable.")
        return config, valid

def paint_live(state: RunState, live_slot, *, recording: bool = False, help_scope: str = "live-activity") -> None:
    with live_slot.container():
        if state.question:
            st.caption(state.question)
        for error in state.errors:
            st.error(error)
        if state.config:
            with st.expander("Run configuration"):
                H.widget(st.caption, "Effective settings reported by this run.", help=HELP["run_config"],
                         help_key=f"{help_scope}:configuration")
                st.json(state.config)
        C.render_plan(state)
        C.render_stats(state, recording=recording)
        left, right = st.columns([3, 2], gap="medium")
        with left:
            C.section("Agent network", help=HELP["network"], help_key=f"{help_scope}:network")
            st.markdown(
                "<div style='font-size:.74rem;color:var(--ink-3);margin-bottom:.3rem'>"
                "Solid arrows spawn. Dashed arrows are messages between agents.</div>",
                unsafe_allow_html=True,
            )
            C.render_graph(state)
        with right:
            C.section("Agent messages", help=HELP["messages"], help_key=f"{help_scope}:messages")
            st.markdown(
                "<div style='font-size:.74rem;color:var(--ink-3);margin-bottom:.3rem'>"
                "What the agents are saying to each other.</div>",
                unsafe_allow_html=True,
            )
            C.render_conversation(state)
        if state.agents:
            with st.expander(f"Agent details ({len(state.agents)})"):
                C.render_agent_cards(state)


def paint_detail(state: RunState, verdict_slot, detail_slot) -> None:
    with verdict_slot.container():
        if state.complete:
            C.section("Results")
            C.render_verdict(state)
    with detail_slot.container():
        if not state.raw:
            return
        findings, timeline, agents, raw = st.tabs(
            ["Findings", "Timeline", "Agents", "Raw events"]
        )
        with findings:
            C.render_findings(state)
        with timeline:
            render_activity_history(state, key=f"detail_activity:{st.session_state.get('result_id', id(state))}")
        with agents:
            C.render_agent_table(state)
        with raw:
            render_raw_events(state, key="detail_raw_events")




def render_results(state: RunState, *, show_summary: bool = True, weak_point_actions=None) -> None:
    """Lead with the conclusion. Keep supporting details one level below it."""
    if show_summary:
        st.caption(state.question)
        C.render_verdict(state)
    assessment = state.weak_points
    weak_label = f"Weak points ({len(assessment['items'])})" if assessment.get("status") == "assessed" else "Weak points"
    evidence, weaknesses, activity, context = st.tabs(["Review discussion" if state.task_mode == "idea_review" else "Evidence", weak_label, "Agent activity", "Run details"])
    with evidence:
        if state.task_mode == "idea_review":
            C.render_discussion(state)
        else:
            C.render_findings(state)
    with weaknesses:
        C.render_weak_points(state, followup_actions=weak_point_actions)
    with activity:
        network, messages = st.columns([3, 2])
        with network:
            C.section("Agent network", help=HELP["network"])
            C.render_graph(state)
        with messages:
            C.section("Agent messages", help=HELP["messages"])
            C.render_conversation(state)
        render_activity_history(state, key=f"result_activity:{st.session_state.get('result_id', id(state))}")
        with st.expander("Agent details"):
            C.render_agent_table(state)
    with context:
        C.render_plan(state)
        if state.metrics:
            with st.expander("Execution metrics"):
                st.caption("Measured by the backend. Durations are in milliseconds.")
                st.json(state.metrics)
        if state.config:
            H.widget(st.caption, "Effective settings reported by this run. Editing the setup does not change this result.", help=HELP["run_config"])
            st.json(state.config)
        if state.files:
            st.write("Evidence files", state.files)
        render_raw_events(state)


def render_raw_events(state: RunState, *, key: str = "result_raw_events") -> None:
    def records():
        H.widget(st.caption, "Run event records", help=HELP["raw_events"])
        st.json([vars(event) for event in state.raw], expanded=False)

    render_details("Raw events", records, key=f"{key}:{state.run_id}", lazy=True)
