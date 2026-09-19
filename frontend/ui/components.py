"""Render panels from a `RunState`. Every function here is a pure view.

Markup is written by hand rather than assembled from default Streamlit widgets,
so the page reads as one designed surface. Colour is always a mark (a bar, a
dot, a chip, a node fill) and never the text itself, which keeps label contrast
compliant on both themes. See `theme.py` for the colour policy.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from .graph import build_dot
from .state import DONE, FAILED, RunState
from .theme import STATUS, hue

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


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def _empty(text: str) -> None:
    _html(f"<div class='empty'>{text}</div>")


def section(label: str) -> None:
    _html(f"<div class='rule'>{_escape(label)}</div>")


# -- panels ---------------------------------------------------------------


def render_graph(state: RunState) -> None:
    st.graphviz_chart(build_dot(state), width="stretch")


def render_stats(state: RunState) -> None:
    if state.complete:
        phase = "complete"
    elif state.agents:
        phase = f"{state.active_agents} working"
    else:
        phase = "idle"

    tiles = [
        ("Agents", str(len(state.agents)), phase),
        ("Events", str(len(state.raw)), "on the stream"),
        ("Findings", str(len(state.findings)), "with provenance"),
        ("Elapsed", f"{state.elapsed_ms / 1000:.1f}s", "run time"),
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
        }.get(agent.status, ("on", "working"))
        steps = f"{agent.activity} step{'' if agent.activity == 1 else 's'}"
        cards.append(
            f"<div class='agent' style='--g:{hue(agent.role)}'>"
            f"<div class='top'><span class='role'>{_escape(agent.role)}</span>"
            f"<span class='state {cls}'><span class='dot'></span>{word}</span></div>"
            f"<div class='id'>{_escape(agent.id)} · {steps}</div>"
            f"<div class='say'>{_escape(agent.last_line[:130])}</div>"
            f"</div>"
        )
    _html(f"<div class='agents'>{''.join(cards)}</div>")


def render_conversation(state: RunState, limit: int = 12) -> None:
    """Agent-to-agent messages as a chat. The critic pushing back is the most
    persuasive thing on screen, so it gets its own panel."""
    talk = state.conversation
    if not talk:
        _empty("No agent messages yet.")
        return

    rows = []
    for msg in talk[-limit:]:
        to = msg.parent_id or "all"
        rows.append(
            f"<div class='msg' style='--g:{hue(msg.role)}'>"
            f"<div class='bar'></div><div>"
            f"<div><span class='who'>{_escape(msg.agent_id)}</span> "
            f"<span class='to'>to {_escape(to)} · {msg.ts / 1000:.1f}s</span></div>"
            f"<div class='body'>{_escape(msg.text)}</div>"
            f"</div></div>"
        )
    _html("".join(rows))


def render_findings(state: RunState) -> None:
    if not state.findings:
        _empty("No findings yet.")
        return

    for finding in state.findings_by_confidence():
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
            with st.expander(f"Provenance ({len(finding.provenance)})"):
                for item in finding.provenance:
                    st.markdown(f"- {_provenance_line(item)}")
        else:
            _empty("No provenance attached to this finding.")


def render_verdict(state: RunState) -> None:
    if not state.complete:
        return

    label, colour = confidence_band(state.confidence)
    score = "n/a" if state.confidence is None else f"{state.confidence:.2f}"

    if state.abstained:
        colour = STATUS["warning"]
        tag = "⚠ Abstained"
        note = "The critic judged the evidence too thin to answer."
    else:
        colour = STATUS["good"]
        tag = "✔ Verdict"
        note = "Synthesised from the findings above."

    _html(
        f"<div class='verdict' style='--c:{colour}'>"
        f"<div class='tag'>{tag}</div>"
        f"<div class='body'>{_escape(state.verdict) or 'No verdict text.'}</div>"
        f"<div style='display:flex;align-items:center;gap:.6rem;flex-wrap:wrap'>"
        f"<span class='score' style='color:{colour}'>"
        f"confidence {score} ({label})</span>"
        f"<span style='color:var(--ink-3);font-size:.78rem'>{note}</span>"
        f"</div></div>"
    )

    if state.errors:
        with st.expander(f"Errors ({len(state.errors)})"):
            for err in state.errors:
                st.error(err)


def render_timeline(state: RunState, limit: int = 40) -> None:
    if not state.timeline:
        _empty("No activity yet.")
        return

    rows = []
    for msg in reversed(state.timeline[-limit:]):
        icon = TYPE_ICON.get(msg.type, "·")
        to = (
            f" <span style='color:var(--ink-3)'>to {_escape(msg.parent_id)}</span>"
            if msg.type == "agent_message" and msg.parent_id else ""
        )
        rows.append(
            f"<div class='ev'>"
            f"<span class='t'>{msg.ts / 1000:.1f}s</span>"
            f"<span style='color:{hue(msg.role)}'>{icon}</span>"
            f"<span><span class='w'>{_escape(msg.agent_id)}</span>{to}"
            f"<div class='b'>{_escape(msg.text)}</div></span>"
            f"</div>"
        )
    _html("".join(rows))


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
            "status": {DONE: "done", FAILED: "failed"}.get(a.status, "running"),
            "steps": a.activity,
            "latest": a.last_line[:90],
        }
        for a in sorted(state.agents.values(), key=lambda a: a.spawned_ts)
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


# -- helpers --------------------------------------------------------------


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
