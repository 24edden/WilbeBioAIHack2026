"""The live agent graph, emitted as Graphviz DOT.

`st.graphviz_chart` renders DOT directly, so the whole live visualisation is a
string rebuilt on each event. No extra dependency, no layout code, and it
replays identically from a saved event log.

Nodes are opaque light tints with near-black text, so they read on both the
light and dark Streamlit themes; the canvas itself is transparent. Colour marks
the agent's function (planner, specialist, critic) and the role name is written
on every node, so identity never rests on hue alone. See `theme.py`.
"""

from __future__ import annotations

from .state import DONE, FAILED, RUNNING, STOPPED, RunState
from .theme import GRAPH_INK, hue, tint
from .icons import alignment_style

STATUS_BADGE = {RUNNING: "●", DONE: "✓", FAILED: "✗", STOPPED: "■"}


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def build_dot(state: RunState, theme: str = "dark") -> str:
    light = theme == "astral"
    edge_color = "#8d9fbe" if light else "#9CA3AF"
    edge_label = "#425372" if light else "#B5BFB9"
    talk_color = "#667b9e" if light else "#8D9C94"
    perspective_colors = {"supporting": "#3159bb", "challenging": "#7650ad", "neutral": "#526782"}
    lines = [
        "digraph investigation {",
        "  rankdir=TB;",
        "  bgcolor=transparent;",
        '  graph [ranksep=.55, nodesep=.35];',
        '  node [shape=box, style="filled,rounded", fontname="Helvetica bold", '
        f'fontsize=11, fontcolor="{GRAPH_INK}", margin="0.20,0.13", penwidth=1.6];',
        f'  edge [fontname="Helvetica", fontsize=9, color="{edge_color}", fontcolor="{edge_label}", '
        "arrowsize=0.7, penwidth=1.2];",
    ]

    if not state.agents:
        lines.append(
            '  waiting [label="waiting for agents", fillcolor="#F3F4F6", '
            'color="#9CA3AF", style="filled,rounded,dashed", fontcolor="#6B7280"];'
        )
        lines.append("}")
        return "\n".join(lines)

    for agent in state.agents.values():
        badge = STATUS_BADGE.get(agent.status, "")
        label = f"{_esc(agent.role)} {badge}\\n{_esc(agent.id)}"
        perspective, alignment_color, alignment_fill = alignment_style(agent.alignment)
        if light:
            alignment_color = perspective_colors.get(agent.alignment, "#526782")
        if agent.alignment:
            label += f"\\n{_esc(perspective)}"
        if agent.skills:
            label += "\\n" + _esc(" · ".join(agent.skills[:2]).replace("_", " ")[:60])
        if agent.activity:
            label += f"\\n{agent.activity} step{'' if agent.activity == 1 else 's'}"

        border = alignment_color if agent.alignment else hue(agent.role)
        pen = 1.6 if agent.status == DONE else 2.6
        style = "filled,rounded,dashed" if agent.status == FAILED else "filled,rounded"
        # Whichever agent just acted gets a heavy dark outline, so the eye
        # follows the investigation rather than hunting for it.
        if agent.id == state.active_id:
            border, pen = GRAPH_INK, 3.6

        lines.append(
            f'  "{_esc(agent.id)}" [label="{label}", fillcolor="{alignment_fill if agent.alignment else tint(agent.role)}", '
            f'color="{border}", style="{style}", penwidth={pen}];'
        )

    spawn_edges = {
        (p, c) for p, c in state.edges
        if state.agents.get(c) and state.agents[c].parent_id == p
    }
    for parent, child in sorted(state.edges):
        if parent not in state.agents or child not in state.agents:
            continue
        if (parent, child) in spawn_edges:
            lines.append(f'  "{_esc(parent)}" -> "{_esc(child)}" [label=" spawns"];')
        if state.talk.get((parent, child), 0):
            # Agent-to-agent talk: dashed, labelled with the message count, and
            # off the rank constraint so it never distorts the spawn tree.
            count = state.talk.get((parent, child), 0)
            sender = state.agents[parent]
            perspective, color, _ = alignment_style(sender.alignment)
            if light:
                color = perspective_colors.get(sender.alignment, "#526782")
            label = f" {perspective} ({count})" if sender.alignment else f" {count}x" if count > 1 else " talks"
            lines.append(
                f'  "{_esc(parent)}" -> "{_esc(child)}" '
                f'[style=dashed, color="{color if sender.alignment else talk_color}", fontcolor="{edge_label}", '
                f'constraint=false, label="{label}"];'
            )

    lines.append("}")
    return "\n".join(lines)
