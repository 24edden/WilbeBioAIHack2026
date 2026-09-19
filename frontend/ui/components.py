"""Render panels from a `RunState`. Every function here is a pure view."""

from __future__ import annotations

from typing import Any

import streamlit as st

from .graph import ROLE_COLORS, build_dot
from .state import DONE, FAILED, RunState

TYPE_ICON = {
    "run_started": "▶",
    "agent_spawned": "✦",
    "agent_message": "\U0001f4ac",
    "tool_call": "⚙",
    "tool_result": "←",
    "finding": "\U0001f4cc",
    "run_complete": "✔",
    "error": "⚠",
}


def confidence_band(value: float | None) -> tuple[str, str]:
    """(label, colour) for a confidence in [0,1]. Bands are the critic's, not cosmetic."""
    if value is None:
        return "unscored", "#6B7280"
    if value >= 0.7:
        return "high", "#047857"
    if value >= 0.4:
        return "moderate", "#B45309"
    return "low", "#B91C1C"


def render_graph(state: RunState) -> None:
    st.graphviz_chart(build_dot(state), width="stretch")


def render_header(state: RunState) -> None:
    cols = st.columns(4)
    cols[0].metric("Agents", len(state.agents), f"{state.active_agents} active")
    cols[1].metric("Events", len(state.raw))
    cols[2].metric("Findings", len(state.findings))
    cols[3].metric("Elapsed", f"{state.elapsed_ms / 1000:.1f}s")


def render_agent_cards(state: RunState, per_row: int = 3) -> None:
    """One card per agent, appearing as it spawns. The roster is the point:
    a judge should see agents arrive without reading a log."""
    if not state.agents:
        st.caption("No agents spawned yet.")
        return

    agents = sorted(state.agents.values(), key=lambda a: a.spawned_ts)
    for start in range(0, len(agents), per_row):
        row = agents[start : start + per_row]
        cols = st.columns(per_row)
        for col, agent in zip(cols, row):
            fill, border = ROLE_COLORS.get(agent.role, ROLE_COLORS["unknown"])
            dot, word = {
                DONE: ("✓", "done"),
                FAILED: ("✗", "failed"),
            }.get(agent.status, ("●", "working"))
            live = agent.status not in (DONE, FAILED)
            with col:
                st.markdown(
                    f"<div style='border-left:4px solid {border};background:{fill}33;"
                    f"border-radius:6px;padding:.5rem .7rem;margin-bottom:.5rem;"
                    f"min-height:5.2rem'>"
                    f"<div style='color:{border};font-weight:700;font-size:.95rem'>"
                    f"{_escape(agent.role)}"
                    f"<span style='float:right;opacity:{'1' if live else '.55'}'>"
                    f"{dot} {word}</span></div>"
                    f"<div style='opacity:.55;font-size:.8rem'>{_escape(agent.id)}"
                    f" · {agent.activity} step{'' if agent.activity == 1 else 's'}</div>"
                    f"<div style='font-size:.8rem;opacity:.8;margin-top:.3rem'>"
                    f"{_escape(agent.last_line[:110])}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


def render_conversation(state: RunState, limit: int = 12) -> None:
    """Agent-to-agent messages as a chat. This is where the cross-examination
    shows — the critic pushing back is the most persuasive thing on screen."""
    talk = state.conversation
    if not talk:
        st.caption("No agent messages yet.")
        return
    for msg in talk[-limit:]:
        colour = ROLE_COLORS.get(msg.role, ROLE_COLORS["unknown"])[1]
        to = msg.parent_id or "all"
        st.markdown(
            f"<div style='margin-bottom:.6rem'>"
            f"<span style='color:{colour};font-weight:600'>{_escape(msg.agent_id)}</span>"
            f"<span style='opacity:.5'> → {_escape(to)}"
            f" · {msg.ts / 1000:.1f}s</span>"
            f"<div style='border-left:2px solid {colour}55;padding-left:.6rem;"
            f"margin-top:.15rem;line-height:1.4'>{_escape(msg.text)}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_timeline(state: RunState, limit: int = 40) -> None:
    if not state.timeline:
        st.caption("No activity yet.")
        return
    for msg in reversed(state.timeline[-limit:]):
        icon = TYPE_ICON.get(msg.type, "·")
        role = msg.role or "system"
        colour = ROLE_COLORS.get(role, ROLE_COLORS["unknown"])[1]
        target = f" → {msg.parent_id}" if msg.type == "agent_message" and msg.parent_id else ""
        st.markdown(
            f"<div style='margin-bottom:.45rem;line-height:1.35'>"
            f"<span style='opacity:.5;font-variant-numeric:tabular-nums'>"
            f"{msg.ts / 1000:6.1f}s</span> "
            f"<span>{icon}</span> "
            f"<strong style='color:{colour}'>{msg.agent_id}</strong>"
            f"<span style='opacity:.6'>{target}</span><br>"
            f"<span style='opacity:.85'>{_escape(msg.text)}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_findings(state: RunState) -> None:
    if not state.findings:
        st.caption("No findings yet.")
        return
    for finding in state.findings_by_confidence():
        label, colour = confidence_band(finding.confidence)
        score = "—" if finding.confidence is None else f"{finding.confidence:.2f}"
        role_colour = ROLE_COLORS.get(finding.role, ROLE_COLORS["unknown"])[1]
        with st.container(border=True):
            st.markdown(
                f"<span style='color:{role_colour};font-weight:600'>{finding.role}</span>"
                f"<span style='opacity:.5'> · {finding.agent_id}</span>"
                f"<span style='float:right;color:{colour};font-weight:600'>"
                f"{score} {label}</span>",
                unsafe_allow_html=True,
            )
            st.write(finding.text)
            if finding.provenance:
                with st.expander(f"Provenance ({len(finding.provenance)})"):
                    for item in finding.provenance:
                        st.markdown(f"- {_provenance_line(item)}")
            else:
                st.caption("⚠ No provenance attached.")


def render_verdict(state: RunState) -> None:
    if not state.complete:
        if state.agents:
            st.info("Investigation running…")
        return

    label, colour = confidence_band(state.confidence)
    score = "—" if state.confidence is None else f"{state.confidence:.2f}"

    if state.abstained:
        st.warning("**ABSTAINED** — the critic judged the evidence too thin for a verdict.")
    else:
        st.success("**VERDICT**")

    st.markdown(
        f"<div style='font-size:1.05rem;line-height:1.5;margin:.25rem 0 .75rem'>"
        f"{_escape(state.verdict) or '<em>no verdict text</em>'}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Overall confidence: <strong style='color:{colour}'>{score} ({label})</strong>",
        unsafe_allow_html=True,
    )

    if state.errors:
        with st.expander(f"Errors ({len(state.errors)})"):
            for err in state.errors:
                st.error(err)


def render_agent_table(state: RunState) -> None:
    if not state.agents:
        return
    rows = [
        {
            "agent": a.id,
            "role": a.role,
            "status": {DONE: "done", FAILED: "failed"}.get(a.status, "running"),
            "steps": a.activity,
            "last": a.last_line[:80],
        }
        for a in state.agents.values()
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


def _provenance_line(item: dict[str, Any]) -> str:
    source = item.get("source") or item.get("pmid") or item.get("file") or "source"
    detail = {k: v for k, v in item.items() if k != "source"}
    if not detail:
        return f"`{source}`"
    rendered = ", ".join(f"{k}: {v}" for k, v in detail.items())
    return f"`{source}` — {rendered}"


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
