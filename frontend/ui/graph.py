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

from .state import DONE, FAILED, RUNNING, RunState
from .theme import GRAPH_INK, hue, tint

STATUS_BADGE = {RUNNING: "●", DONE: "✓", FAILED: "✗"}


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def build_dot(state: RunState) -> str:
    lines = [
        "digraph investigation {",
        "  rankdir=TB;",
        "  bgcolor=transparent;",
        '  graph [ranksep=.55, nodesep=.35];',
        '  node [shape=box, style="filled,rounded", fontname="Helvetica bold", '
        f'fontsize=11, fontcolor="{GRAPH_INK}", margin="0.20,0.13", penwidth=1.6];',
        '  edge [fontname="Helvetica", fontsize=9, color="#9CA3AF", '
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
        if agent.activity:
            label += f"\\n{agent.activity} step{'' if agent.activity == 1 else 's'}"

        border = hue(agent.role)
        pen = 1.6 if agent.status == DONE else 2.6
        style = "filled,rounded,dashed" if agent.status == FAILED else "filled,rounded"
        # Whichever agent just acted gets a heavy dark outline, so the eye
        # follows the investigation rather than hunting for it.
        if agent.id == state.active_id:
            border, pen = GRAPH_INK, 3.6

        lines.append(
            f'  "{_esc(agent.id)}" [label="{label}", fillcolor="{tint(agent.role)}", '
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
        else:
            # Agent-to-agent talk: dashed, labelled with the message count, and
            # off the rank constraint so it never distorts the spawn tree.
            count = state.talk.get((parent, child), 0)
            label = f" {count}x" if count > 1 else " talks"
            lines.append(
                f'  "{_esc(parent)}" -> "{_esc(child)}" '
                f'[style=dashed, color="#6B7280", fontcolor="#6B7280", '
                f'constraint=false, label="{label}"];'
            )

    lines.append("}")
    return "\n".join(lines)
