"""Single-expert presentation of real normalized events, separate from execution.

Never fabricates a biological result or changes RunState. Presentation may lag the
worker; completed work is labeled as replay, and results remain immediately available.
"""
from dataclasses import dataclass
from time import monotonic
import re

from .events import Event


@dataclass
class PetTurn:
    agent_id: str
    role: str
    kind: str
    text: str
    source_index: int


def excerpt(text: str) -> str:
    """At most two original sentences; explicitly displayed as an excerpt."""
    text = re.sub(r"<prior_run_context>.*?</prior_run_context>", "[prior context]", str(text), flags=re.S)
    text = " ".join(text.split())
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    short = " ".join(parts[:2])
    if len(short) > 300:
        short = short[:297].rsplit(" ", 1)[0] + "…"
    return short


def event_summary(event: Event) -> str:
    if event.type == "tool_call":
        tool = str(event.payload.get("tool") or "the assigned analysis").replace("_", " ")
        return f"Running {tool}. Findings will appear when the analysis returns."
    if event.type == "agent_spawned":
        message = event.payload.get("message")
        return excerpt(message) if isinstance(message, str) and message else "Reviewing the assigned question and available evidence."
    return excerpt(event.text) or "An update is available in the full activity record."


class PetActivity:
    def __init__(self, *, clock=monotonic, dwell=4.0):
        self.clock = clock
        self.dwell = dwell
        self.turns: list[PetTurn] = []
        self.cursor = 0
        self.index = 0
        self.playing = True
        self.elapsed = 0.0
        self.last_tick = clock()
        self.source_complete = False
        self.roles: dict[str, str] = {}

    def ingest(self, events, *, complete=False):
        # The owner creates a new presentation for a new run; never silently rewind.
        if len(events) < self.cursor:
            raise ValueError("Cannot replace the event history of an active pet presentation")
        for i in range(self.cursor, len(events)):
            event = events[i]
            if event.agent_id and event.agent_role:
                self.roles[event.agent_id] = event.agent_role
            if event.type not in {"agent_spawned", "agent_message", "finding", "tool_call", "error"}:
                continue
            if not event.agent_id:
                continue
            turn = PetTurn(event.agent_id, event.agent_role or self.roles.get(event.agent_id, "unknown"),
                           event.type, event_summary(event), i)
            if self.turns and self.turns[-1].agent_id == turn.agent_id:
                # Keep a concrete finding over a later low-level tool status.
                if self.turns[-1].kind != "finding" or turn.kind in {"finding", "agent_message", "error"}:
                    self.turns[-1] = turn
            else:
                self.turns.append(turn)
        self.cursor = len(events)
        self.source_complete = complete

    @property
    def current(self):
        return self.turns[self.index] if self.turns else None

    @property
    def finished(self):
        return self.source_complete and (not self.turns or (self.index == len(self.turns)-1 and self.elapsed >= self.dwell))

    def advance(self):
        now = self.clock()
        if self.playing:
            self.elapsed += max(0, now-self.last_tick)
            if self.elapsed >= self.dwell and self.index < len(self.turns)-1:
                self.index += 1
                self.elapsed = 0.0
        self.last_tick = now

    def pause(self):
        self.advance()
        self.playing = False

    def resume(self):
        self.last_tick = self.clock()
        self.playing = True

    def step(self):
        self.pause()
        if self.index < len(self.turns)-1:
            self.index += 1
            self.elapsed = 0.0
        elif self.source_complete:
            self.elapsed = self.dwell

    def restart(self):
        self.index = 0
        self.elapsed = 0.0
        self.last_tick = self.clock()
        self.playing = True
