"""Headless check of the fold + graph logic. No Streamlit, no backend.

    python frontend/smoke_test.py

Run this before pushing UI changes; it catches the schema and rendering breaks
that would otherwise only show up live in front of judges.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui.events import Event  # noqa: E402
from ui.graph import build_dot  # noqa: E402
from ui.state import RunState  # noqa: E402
from ui.stream import list_fixtures, load_fixture  # noqa: E402


def check_fixture(path: Path) -> RunState:
    state = RunState()
    for event in load_fixture(path):
        state.apply(event)
    dot = build_dot(state)
    assert dot.startswith("digraph"), "graph did not build"
    assert state.agents, "no agents were spawned"
    assert state.complete, "run never completed"
    assert state.verdict, "no verdict text"
    assert state.conversation, "no agent-to-agent messages"
    for agent in state.agents.values():
        assert agent.status != "running", f"{agent.id} left running"
        assert f'"{agent.id}"' in dot, f"{agent.id} missing from graph"
    return state


def check_tolerance() -> None:
    """Malformed input must degrade, never raise."""
    state = RunState()
    for raw in ["not-an-object", {}, {"type": "made_up_type", "payload": 5},
                {"type": "finding", "ts": "x", "payload": {"confidence": "high"}},
                {"type": "agent_message", "agent_id": "ghost-9", "parent_id": "nobody"}]:
        state.apply(Event.from_dict(raw))
    build_dot(state)


def main() -> int:
    fixtures = list_fixtures()
    if not fixtures:
        print("FAIL: no fixtures found")
        return 1
    for path in fixtures:
        state = check_fixture(path)
        verdict = "ABSTAIN" if state.abstained else "verdict"
        print(
            f"ok  {path.stem:<16} {len(state.agents)} agents, "
            f"{len(state.raw)} events, {len(state.findings)} findings, "
            f"{len(state.conversation)} messages, {verdict} @ {state.confidence}"
        )
    check_tolerance()
    print("ok  malformed events tolerated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
