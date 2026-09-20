"""Render panels from a `RunState`. Every function here is a pure view.

Markup is written by hand rather than assembled from default Streamlit widgets,
so the page reads as one designed surface. Colour is always a mark (a bar, a
dot, a chip, a node fill) and never the text itself, which keeps label contrast
compliant on both themes. See `theme.py` for the colour policy.
"""

from __future__ import annotations

from typing import Any
import json
import re

import streamlit as st
from . import help as H

from .graph import build_dot
from .state import DONE, FAILED, STOPPED, RunState
from .theme import STATUS, hue
from .config import PROFILE
from .icons import svg_icon, alignment_style
from .help_text import HELP
from .details import render_details
from .discussion import inspect_replies
from .finding_refs import FindingReferenceIndex, compact_provenance
from .run_clock import measured_execution_ms

TYPE_ICON = {
    "run_started": "▶",
    "agent_spawned": "✦",
    "agent_message": "◈",
    "tool_call": "⚙",
    "tool_result": "←",
    "finding": "◆",
    "run_complete": "✔",
    "error": "⚠",
}


def confidence_band(value: float | None) -> tuple[str, str]:
    """(label, colour) for a confidence in [0,1].

    These are the reserved status colours, not the agent palette, and they
    always ship beside the numeric score so the band never rests on hue.
    """
    if value is None:
        return "unscored", "var(--ink-3)"
    if value >= 0.7:
        return "high", STATUS["good"]
    if value >= 0.4:
        return "moderate", STATUS["warning"]
    return "low", STATUS["critical"]


def _html(markup: str, help: str | None = None, help_label: str | None = None, help_key: str | None = None) -> None:
    H.widget(st.markdown, markup, unsafe_allow_html=True, help=help, help_label=help_label, help_key=help_key)


def _empty(text: str) -> None:
    _html(f"<div class='empty'>{text}</div>")


def section(label: str, help: str | None = None, help_key: str | None = None) -> None:
    _html(f"<div class='rule'>{_escape(label)}</div>", help=help, help_label=label, help_key=help_key)


def _relative_time(state: RunState, timestamp: int) -> str:
    """Display elapsed run time for both relative fixtures and epoch streams."""
    origin = state.raw[0].ts if state.raw else 0
    return f"{(timestamp - origin) / 1000:+.1f}s"


# -- panels ---------------------------------------------------------------


def render_graph(state: RunState) -> None:
    if not state.agents:
        _html("<div class='network-idle'><div class='orbit orbit-one'></div>"
              "<div class='orbit orbit-two'></div><div class='network-core'>"
              "<strong>Agent network</strong>"
              "<small>Start a run to view agent activity.</small></div>"
              f"<span class='satellite s-one'>{_escape(PROFILE.preview_roles[0]).upper()}</span>"
              f"<span class='satellite s-two'>{_escape(PROFILE.preview_roles[1]).upper()}</span>"
              f"<span class='satellite s-three'>{_escape(PROFILE.preview_roles[2]).upper()}</span></div>")
        return
    st.graphviz_chart(build_dot(state), width="stretch")


def render_progress(state: RunState) -> None:
    """Stages reflect observed events, never a fabricated percentage."""
    stage = 3 if state.complete else 2 if any(a.role in PROFILE.review_roles for a in state.agents.values()) else 1 if state.agents else 0
    labels = PROFILE.stages
    cells = "".join(
        f"<div class='stage {'reached' if i <= stage else ''}'><b>{i + 1:02}</b> {label}</div>"
        for i, label in enumerate(labels)
    )
    if state.errors:
        status = "Run needs attention"
    elif state.complete:
        status = "Evidence insufficient · abstained" if state.abstained else "Investigation complete"
    elif state.raw:
        status = "Investigation in progress"
    else:
        status = "Awaiting your question"
    _html(f"<div class='run-heading'><span>INVESTIGATION WORKSPACE</span><span>{status}</span></div>"
          f"<div class='stages'>{cells}</div>")
    if state.question:
        _html(f"<div class='run-question'>{_escape(state.question)}</div>")
    for error in state.errors:
        st.error(error)


def render_stats(state: RunState, *, recording: bool = False) -> None:
    if state.complete:
        phase = "complete"
    elif state.agents:
        phase = f"{state.active_agents} working"
    else:
        phase = "idle"

    event_span = max(0, max(event.ts for event in state.raw) - min(event.ts for event in state.raw)) if state.raw else 0
    measured = measured_execution_ms(state)
    timing = ("Recording time", event_span, "saved event span") if recording else (
        ("Backend time", measured, "measured execution") if measured is not None else
        ("Event span", event_span, "between received events"))
    tiles = [
        ("Agents", str(len(state.agents)), phase),
        ("Events", str(len(state.raw)), "on the stream"),
        ("Findings", str(len(state.findings)), "with provenance"),
        (timing[0], f"{timing[1] / 1000:.1f}s", timing[2]),
    ]
    cells = "".join(
        f"<div class='stat'><div class='k'>{k}</div>"
        f"<div class='v'>{v}</div><div class='n'>{n}</div></div>"
        for k, v, n in tiles
    )
    _html(f"<div class='stats'>{cells}</div>")


def render_agent_cards(state: RunState) -> None:
    """The roster, growing as agents spawn. A judge should see agents arrive
    without reading a log."""
    if not state.agents:
        _empty("No agents spawned yet.")
        return

    cards = []
    for agent in sorted(state.agents.values(), key=lambda a: a.spawned_ts):
        cls, word = {
            DONE: ("ok", "done"),
            FAILED: ("bad", "failed"),
            STOPPED: ("ok", "stopped"),
        }.get(agent.status, ("on", "working"))
        steps = f"{agent.activity} step{'' if agent.activity == 1 else 's'}"
        stance, color, _ = alignment_style(agent.alignment)
        perspective = f"<span class='perspective' style='--perspective:{color}'>{_escape(stance)}</span>" if agent.alignment else ""
        skills = "".join(f"<span class='skill-chip'>{svg_icon(skill, 14)}{_escape(skill.replace('_', ' '))}</span>" for skill in agent.skills)
        cards.append(
            f"<div class='agent' style='--g:{hue(agent.role)}'>"
            f"<div class='top'><span class='role'>{svg_icon(agent.icon)} {_escape(agent.role)}</span>"
            f"<span class='state {cls}'><span class='dot'></span>{word}</span></div>"
            f"<div class='id'>{_escape(agent.id)} · {steps}</div>"
            f"{perspective}<div class='skill-chips'>{skills}</div>"
            f"<div class='say'>{_escape(agent.last_line[:130])}</div>"
            f"</div>"
        )
    _html(f"<div class='agents'>{''.join(cards)}</div>")


def render_conversation(state: RunState, limit: int = 12) -> None:
    """Agent-to-agent messages as a chat. The critic pushing back is the most
    persuasive thing on screen, so it gets its own panel."""
    talk = state.conversation
    if not talk:
        _html("<div class='conversation-empty'><span class='eyebrow'>Agent messages</span>"
              "<h3>Review agent exchanges</h3>"
              "<p>Messages show how agents share evidence, question assumptions, "
              "and assess the available data.</p>"
              "<div class='waiting-line'><span></span>Waiting for the first exchange</div></div>")
        return

    st.caption(f"Latest {min(limit, len(talk))} of {len(talk)} agent messages, shown in arrival order.")
    rows = []
    for msg in talk[-limit:]:
        to = msg.parent_id or "all"
        agent = state.agents.get(msg.agent_id)
        stance, color, _ = alignment_style(agent.alignment if agent else "")
        perspective = f" · {_escape(stance)}" if agent and agent.alignment else ""
        rows.append(
            f"<div class='msg' style='--g:{color if agent and agent.alignment else hue(msg.role)}'>"
            f"<div class='bar'></div><div>"
            f"<div><span class='who'>{_escape(msg.agent_id)}</span> "
            f"<span class='to'>to {_escape(to)}{perspective} · {_relative_time(state, msg.ts)}</span></div>"
            f"<div class='body'>{_message_text(msg.text)}</div>"
            f"</div></div>"
        )
    _html("<div class='conversation-feed'>" + "".join(rows) + "</div>")


def render_findings(state: RunState) -> None:
    section("Findings", help=HELP["findings"])
    if not state.findings:
        _empty("No findings yet.")
        return

    H.widget(st.caption, "Confidence is a model or heuristic score, not a calibrated probability.", help=HELP["confidence"])
    for index, finding in enumerate(state.findings_by_confidence()):
        label, colour = confidence_band(finding.confidence)
        score = "n/a" if finding.confidence is None else f"{finding.confidence:.2f}"
        width = int((finding.confidence or 0) * 100)
        _html(
            f"<div class='find' style='--g:{hue(finding.role)};--c:{colour}'>"
            f"<div class='top'>"
            f"<span class='who'><span class='chip'></span>{_escape(finding.role)}"
            f" <span style='color:var(--ink-3);font-weight:500'>"
            f"{_escape(finding.agent_id)}</span></span>"
            f"<span class='score' style='color:{colour}'>{score} {label}</span></div>"
            f"<div class='body'>{_escape(finding.text)}</div>"
            f"<div class='meter'><i style='width:{width}%'></i></div>"
            f"</div>"
        )
        if finding.provenance:
            def provenance(records=finding.provenance):
                H.widget(st.caption, "Sources for this finding", help=HELP["provenance"])
                for item in records:
                    st.markdown(f"- {_provenance_line(item)}")
            render_details(f"Provenance ({len(finding.provenance)})", provenance,
                           key=f"finding_sources:{state.run_id}:{index}", lazy=len(finding.provenance) > 12)
        else:
            _empty("No provenance attached to this finding.")


def render_verdict(state: RunState) -> None:
    if not state.complete:
        return
    if state.task_mode == "idea_review" and state.status == "complete" and not state.abstained:
        _html("<div class='verdict' style='--c:var(--accent)'><div class='tag'>Idea review complete</div>"
              f"<div class='body'>{_escape(state.verdict)}</div>"
              "<div style='color:var(--ink-2);font-size:.85rem'>This is a design review of the proposal. Scientific validation has not been established.</div></div>")
        return

    label, colour = confidence_band(state.confidence)
    score = "n/a" if state.confidence is None else f"{state.confidence:.2f}"

    if state.status == "cancelled":
        colour = "var(--ink-3)"
        tag = "Cancelled"
        note = "Any findings shown are partial. This is not a completed assessment."
    elif state.status == "error":
        colour = STATUS["critical"]
        tag = "Run ended with an error"
        note = "Inspect the recorded errors and available output before drawing a conclusion."
    elif state.status != "complete":
        colour = "var(--ink-3)"
        tag = "Run ended"
        note = f"Reported status: {_escape(state.status or 'unspecified')}. This outcome has not been marked complete."
    elif state.abstained:
        colour = STATUS["warning"]
        tag = "⚠ Abstained"
        note = "The run withheld a supported conclusion. Review its limitations and suggested next evidence."
    else:
        colour = STATUS["good"]
        tag = "✔ Verdict"
        note = "Synthesised from the agents' findings."

    _html(
        f"<div class='verdict' style='--c:{colour}'>"
        f"<div class='tag'>{tag}</div>"
        f"<div class='body'>{_escape(state.verdict) or 'No verdict text.'}</div>"
        f"<div style='display:flex;align-items:center;gap:.6rem;flex-wrap:wrap'>"
        f"<span class='score' style='color:{colour}'>"
        f"confidence score {score} ({label})</span>"
        f"<span style='color:var(--ink-3);font-size:.78rem'>{note}</span>"
        f"</div><div style='color:var(--ink-3);font-size:.72rem;margin-top:.6rem'>"
        f"Model or heuristic score · not a calibrated probability.</div></div>",
        help=HELP["verdict"], help_label="Verdict",
    )

    if state.errors:
        with st.expander(f"Errors ({len(state.errors)})"):
            for err in state.errors:
                st.error(err)


def render_weak_points(state: RunState, *, followup_actions=None) -> None:
    """Present the backend's assessment without deriving new scientific claims."""
    section("Weak points", help=HELP["weak_points"])
    assessment = state.weak_points
    if assessment.get("status") != "assessed":
        st.info("Not assessed. This run does not include a compatible weak-points assessment. No analysis has been inferred from its findings.")
        return
    items = assessment["items"]
    st.caption(f"{len(items)} weak point{'s' if len(items) != 1 else ''} reported by the backend assessment.")
    if not items:
        st.info("No weak points were returned by the backend assessment.")
        return
    categories = {
        "evidence_gap": "Evidence gap", "conflicting_findings": "Conflicting findings",
        "source_gap": "Source gap", "provider_failure": "Provider failure", "scope_limit": "Scope limit",
    }
    finding_index = FindingReferenceIndex(state.findings)
    for index, item in enumerate(items, 1):
        category_id = str(item.get("category") or "Other")
        category = categories.get(category_id, category_id.replace("_", " "))
        title = str(item.get("title") or f"Weak point {index}")
        rationale = str(item.get("rationale") or "No rationale supplied.")
        next_evidence = str(item.get("next_evidence") or "No next evidence specified.")
        _html(f"<div class='find'><div class='eyebrow'>{index:02} / {_escape(category)}</div>"
              f"<div class='body'><strong>{_escape(title)}</strong></div>"
              f"<p style='color:var(--ink-2);font-size:.9rem;margin:.65rem 0'>{_escape(rationale)}</p>"
              f"<div class='ask-label'>Evidence to resolve this</div>"
              f"<div style='color:var(--ink-2);font-size:.85rem'>{_escape(next_evidence)}</div></div>")
        if followup_actions is not None:
            followup_actions(index, item)
        refs = item.get("finding_ids") if isinstance(item.get("finding_ids"), list) else []
        sources = item.get("sources") if isinstance(item.get("sources"), list) else []
        resolved = [finding_index.resolve(ref) for ref in refs]
        def references(refs=refs, sources=sources, resolved=resolved):
            if isinstance(refs, list) and refs:
                st.caption("Finding references")
                st.code("\n".join(str(ref) for ref in refs), language=None)
                for reference in resolved:
                    if reference.finding is not None:
                        _render_referenced_finding(reference.finding)
                    else:
                        _html(f"<p class='argument-trace-note'>Reference {_escape(str(reference.identifier))}: {_escape(reference.message)}</p>")
            if isinstance(sources, list) and sources:
                st.caption("Source records supplied by the backend")
                st.json(sources, expanded=False)
            if not refs and not sources:
                st.caption("No finding or source references supplied for this item.")
        render_details(f"References for {index:02}: {title}", references,
                       key=f"weak_point_sources:{state.run_id}:{index}",
                       lazy=len(refs) + len(sources) > 12 or not compact_provenance(sources)
                       or any(not compact_provenance(ref.finding.provenance) for ref in resolved if ref.finding))


def _render_referenced_finding(finding) -> None:
    reported = getattr(finding, "stance", None)
    stance = {"supports": "Supports", "contradicts": "Contradicts", "neutral": "Neutral"}.get(reported, "Unknown / not supplied") if isinstance(reported, str) else "Unknown / not supplied"
    _html("<details class='argument-trace'>"
          f"<summary>Inspect finding {_escape(str(finding.finding_id))} · {_escape(finding.role)}</summary>"
          "<article class='argument-trace-turn'>"
          f"<div class='argument-trace-text'>{_escape(finding.text)}</div>"
          f"<div class='argument-trace-agent'>Produced by {_escape(finding.agent_id)} · {_escape(finding.role)}</div>"
          f"<div class='argument-trace-id'>Finding ID: {_escape(str(finding.finding_id))}</div>"
          f"<p class='argument-trace-note'>Backend-reported relation to the hypothesis: {stance}. "
          "This describes the finding's assigned stance, not whether it is correct.</p>"
          "<p class='argument-trace-note'>Finding located in this run. Attached source records have not been independently verified here.</p>"
          f"{_finding_provenance_html(finding.provenance)}"
          "</article></details>")


def _finding_provenance_html(records: list[dict]) -> str:
    if not records:
        return "<p class='argument-trace-note'>No source records were attached to this finding.</p>"
    labels = {"kind": "Source kind", "ref": "Source reference", "locator": "Location", "source": "Source",
              "file": "File", "pmid": "PMID", "quote": "Source excerpt supplied with this finding"}
    chunks = []
    for index, record in enumerate(records, 1):
        fields = []
        for key, value in record.items():
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str, indent=2)
            label = labels.get(key, str(key).replace("_", " "))
            fields.append(f"<div class='argument-trace-agent'>{_escape(label)}</div>"
                          f"<div class='argument-trace-text'>{_escape(text)}</div>")
        chunks.append(f"<section class='argument-trace-turn'><div class='argument-trace-kicker'>Source record {index}</div>"
                      + ("".join(fields) or "<p class='argument-trace-note'>No source metadata supplied.</p>") + "</section>")
    return "".join(chunks)


def render_role_catalog(roles: list[dict], skills: list[dict]) -> None:
    """Cards are descriptions from the catalog, not invented active agents."""
    names = {str(skill.get("id")): str(skill.get("label", skill.get("id"))) for skill in skills if isinstance(skill, dict)}
    cards = []
    for role in roles:
        stance, color, _ = alignment_style(str(role.get("alignment") or ""))
        perspective = f"<span class='perspective' style='--perspective:{color}'>{_escape(stance)}</span>" if role.get("alignment") else ""
        role_skills = role.get("skills") if isinstance(role.get("skills"), list) else []
        chips = "".join(f"<span class='skill-chip'>{svg_icon(str(skill), 14)}{_escape(names.get(str(skill), str(skill).replace('_', ' ')))}</span>"
                        for skill in role_skills)
        cards.append(f"<div class='skill-card'><div class='skill-heading'>{svg_icon(str(role.get('icon') or role.get('id')))}"
                     f"<strong>{_escape(str(role.get('label') or role.get('id') or 'Agent'))}</strong></div>"
                     f"{perspective}<div class='skill-chips'>{chips}</div></div>")
    if cards:
        _html("<div class='skill-grid'>" + "".join(cards) + "</div>")


def render_plan(state: RunState) -> None:
    if "task_mode" not in state.config:
        return
    label = {"investigation": "Evidence investigation", "idea_review": "Idea review"}.get(state.task_mode, state.task_mode)
    st.caption(f"Selected plan: {label}")
    if state.config.get("routing_reason"):
        st.caption(str(state.config["routing_reason"]))


def render_discussion(state: RunState) -> None:
    section("Proposal discussion", help=HELP["discussion"])
    st.caption("Arguments, assumptions and proposed checks. A revision does not establish scientific correctness.")
    if not state.discussion:
        _empty("No structured discussion was supplied by this run.")
    inspections = inspect_replies(state.discussion)
    for index, (entry, inspection) in enumerate(zip(state.discussion, inspections), 1):
        stance, color, _ = alignment_style(str(entry.get("alignment") or entry.get("stance") or ""))
        phase = str(entry.get("phase") or "Review").replace("_", " ")
        _html(f"<div class='find' style='border-left:3px solid {color}'><div class='eyebrow'>{index:02} / {_escape(phase)}</div>"
              f"<span class='perspective' style='--perspective:{color}'>{_escape(stance)}</span>"
              f"<div class='body'>{_escape(str(entry.get('text') or ''))}</div>"
              f"<div class='id'>{_escape(str(entry.get('agent_id') or ''))}</div></div>")
        if inspection.status == "linked":
            earlier_index = inspection.target_index
            earlier = state.discussion[earlier_index]
            earlier_phase = str(earlier.get("phase") or "Review").replace("_", " ")
            earlier_agent = str(earlier.get("agent_id") or earlier.get("role") or "Unspecified agent")
            earlier_stance, _, _ = alignment_style(str(earlier.get("alignment") or earlier.get("stance") or ""))
            chain = " → ".join(
                f"Turn {turn + 1:02} · {str(state.discussion[turn].get('phase') or 'Review').replace('_', ' ')}"
                for turn in inspection.chain
            )
            _html("<details class='argument-trace'>"
                  f"<summary>View earlier argument: turn {earlier_index + 1:02} · {_escape(earlier_agent)} · {_escape(earlier_phase)}</summary>"
                  f"<div class='argument-trace-path'>Recorded links: {_escape(chain)}</div>"
                  "<p class='argument-trace-note'>Recorded discussion, not independently verified evidence.</p>"
                  "<article class='argument-trace-turn'>"
                  f"<div class='argument-trace-kicker'>Turn {earlier_index + 1:02} · {_escape(earlier_phase)}</div>"
                  f"<div class='argument-trace-agent'>{_escape(earlier_agent)} · {_escape(earlier_stance)}</div>"
                  f"<div class='argument-trace-id'>Source turn ID: {_escape(earlier['id'])}</div>"
                  f"<div class='argument-trace-text'>{_escape(str(earlier.get('text') or ''))}</div>"
                  "</article>"
                  f"<p class='argument-trace-note'>Assumptions and references remain with turn {earlier_index + 1:02} in the full discussion.</p>"
                  "</details>")
        else:
            st.caption(inspection.message)
        with st.expander(f"Assumptions and references for turn {index}"):
            for key, label in (("assumptions", "Assumptions"), ("evidence_refs", "Evidence references"), ("open_questions", "Open questions")):
                values = entry.get(key)
                if isinstance(values, list) and values:
                    st.write(label)
                    for value in values:
                        st.text(str(value))
            if entry.get("basis"):
                st.caption("Basis: " + str(entry["basis"]).replace("_", " "))
            if entry.get("provenance"):
                st.json(entry["provenance"], expanded=False)
            if entry.get("reply_to"):
                st.caption(f"Responds to: {entry['reply_to']}")


def render_timeline(state: RunState, limit: int = 40, *, end: int | None = None) -> None:
    if not state.timeline:
        _empty("No activity yet.")
        return

    total = len(state.timeline)
    end = total if end is None else max(0, min(total, end))
    start = max(0, end - limit)
    st.caption(f"Showing entries {start + 1} to {end} of {total}. Latest arrival first.")
    rows = []
    for ordinal, msg in reversed(list(enumerate(state.timeline[start:end], start=start + 1))):
        icon = TYPE_ICON.get(msg.type, "·")
        to = (
            f" <span style='color:var(--ink-3)'>to {_escape(msg.parent_id)}</span>"
            if msg.type == "agent_message" and msg.parent_id else ""
        )
        rows.append(
            f"<div class='ev'>"
            f"<span class='t'>{_relative_time(state, msg.ts)}</span>"
            f"<span style='color:{hue(msg.role)}'>{icon}</span>"
            f"<span><span class='w'>{_escape(msg.agent_id)}</span>{to}"
            f"<div class='argument-trace-id'>Entry {ordinal} · {_escape(msg.type)}</div>"
            f"<div class='b argument-trace-text'>{_message_text(msg.text)}</div></span>"
            f"</div>"
        )
    _html("<div class='timeline-window'>" + "".join(rows) + "</div>")


def render_agent_table(state: RunState) -> None:
    """The plain table. Present so identity and status are readable without
    any colour at all."""
    if not state.agents:
        _empty("No agents yet.")
        return
    rows = [
        {
            "agent": a.id,
            "role": a.role,
            "status": {DONE: "done", FAILED: "failed", STOPPED: "stopped"}.get(a.status, a.status),
            "steps": a.activity,
            "latest": a.last_line[:90],
        }
        for a in sorted(state.agents.values(), key=lambda a: a.spawned_ts)
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


# -- helpers --------------------------------------------------------------


def _message_text(text: str) -> str:
    """Fold echoed context for readability; retain its complete text and raw event."""
    blocks = re.split(r"(<prior_run_context>.*?</prior_run_context>)", str(text), flags=re.DOTALL)
    return "".join(
        "<details class='message-context'><summary>Prior run context</summary>"
        f"<div style='max-height:240px;overflow:auto;white-space:pre-wrap'>{_escape(block)}</div></details>"
        if block.startswith("<prior_run_context>") and block.endswith("</prior_run_context>") else _escape(block)
        for block in blocks
    )


def _provenance_line(item: dict[str, Any]) -> str:
    source = item.get("source") or item.get("pmid") or item.get("file") or "source"
    detail = {k: v for k, v in item.items() if k != "source"}
    if not detail:
        return f"`{source}`"
    return f"`{source}` " + ", ".join(f"{k}: {v}" for k, v in detail.items())


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
