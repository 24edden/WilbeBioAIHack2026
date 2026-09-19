"""The live agent graph, emitted as Graphviz DOT.

`st.graphviz_chart` renders DOT directly, so the whole live visualisation is a
string rebuilt on each event — no extra dependency, no layout code, and it
replays identically from a saved event log.

Colours are mid-tone fills with near-black text, which stay legible on both the
light and dark Streamlit themes; the graph background is transparent so it sits
on whichever one is active.
"""

from __future__ import annotations

from .state import DONE, FAILED, RUNNING, RunState

ROLE_COLORS = {
    "orchestrator": ("#C7D2FE", "#4338CA"),
    "genomics": ("#A7F3D0", "#047857"),
    "literature": ("#FDE68A", "#B45309"),
    "clinical": ("#E9D5FF", "#7E22CE"),
    "stats": ("#A5F3FC", "#0E7490"),
    "critic": ("#FECACA", "#B91C1C"),
    "unknown": ("#E5E7EB", "#4B5563"),
}

STATUS_STYLE = {
    RUNNING: ("filled", 2.4),
    DONE: ("filled", 1.2),
    FAILED: ("filled,dashed", 2.4),
}


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _wrap(text: str, width: int = 30, max_lines: int = 2) -> str:
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
        else:
            current = f"{current} {word}".strip()
    if current and len(lines) < max_lines:
        lines.append(current)
    out = "\\n".join(_esc(line) for line in lines if line)
    if len(lines) == max_lines and len(" ".join(words)) > width * max_lines:
        out += "…"
    return out


def build_dot(state: RunState) -> str:
    lines = [
        "digraph investigation {",
        "  rankdir=TB;",
        "  bgcolor=transparent;",
        '  node [shape=box, style=filled, fontname="Helvetica", fontsize=11, '
        'fontcolor="#111827", margin="0.16,0.10"];',
        '  edge [fontname="Helvetica", fontsize=9, color="#9CA3AF", arrowsize=0.7];',
    ]

    if not state.agents:
        lines.append('  waiting [label="waiting for agents…", fillcolor="#F3F4F6", '
                     'color="#9CA3AF", style="filled,dashed"];')
        lines.append("}")
        return "\n".join(lines)

    for agent in state.agents.values():
        fill, border = ROLE_COLORS.get(agent.role, ROLE_COLORS["unknown"])
        style, pen = STATUS_STYLE.get(agent.status, STATUS_STYLE[RUNNING])
        badge = {RUNNING: " ●", DONE: " ✓", FAILED: " ✗"}.get(agent.status, "")
        label = f"{_esc(agent.role)}{badge}\\n{_esc(agent.id)}"
        if agent.activity:
            label += f"\\n{agent.activity} step{'' if agent.activity == 1 else 's'}"
        # The agent that just acted gets a heavy dark border, so the eye lands
        # on wherever the investigation currently is.
        if agent.id == state.active_id:
            border, pen = "#111827", 3.4
        lines.append(
            f'  "{_esc(agent.id)}" [label="{label}", fillcolor="{fill}", '
            f'color="{border}", style="{style}", penwidth={pen}];'
        )

    spawn_edges = {(p, c) for p, c in state.edges if state.agents.get(c) and
                   state.agents[c].parent_id == p}
    for parent, child in sorted(state.edges):
        if parent not in state.agents or child not in state.agents:
            continue
        if (parent, child) in spawn_edges:
            lines.append(f'  "{_esc(parent)}" -> "{_esc(child)}" [label=" spawns"];')
        else:
            # Agent-to-agent talk: dashed, labelled with the message count, and
            # off the rank constraint so it never distorts the spawn tree.
            count = state.talk.get((parent, child), 0)
            label = f' label=" {count}×"' if count > 1 else ' label=" talks"'
            lines.append(
                f'  "{_esc(parent)}" -> "{_esc(child)}" '
                f'[style=dashed, color="#6B7280", fontcolor="#6B7280", '
                f'constraint=false,{label}];'
            )

    lines.append("}")
    return "\n".join(lines)
