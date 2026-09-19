"""Session-local playback of normalized events, independent of model execution."""
from copy import deepcopy
from time import monotonic

from .state import RunState


class Playback:
    def __init__(self, events, *, clock=monotonic):
        self.events = deepcopy(list(events))
        self.clock = clock
        self.speed = 1.0
        self.restart()

    def restart(self):
        self.state = RunState()
        self.index = 0
        self.elapsed = 0.0
        self.last_tick = self.clock()
        self.playing = bool(self.events)
        self.due = [0.0]
        for before, after in zip(self.events, self.events[1:]):
            # Compress long waits and give near-simultaneous events time to read.
            self.due.append(self.due[-1] + min(.9, max(.18, (after.ts - before.ts) / 1000)))
        self.advance()

    @property
    def finished(self):
        return self.index == len(self.events)

    def advance(self):
        now = self.clock()
        if self.playing:
            self.elapsed += max(0, now - self.last_tick) * self.speed
            while self.index < len(self.events) and self.due[self.index] <= self.elapsed:
                self.state.apply(self.events[self.index])
                self.index += 1
            if self.finished:
                self.playing = False
        self.last_tick = now

    def pause(self):
        self.advance()
        self.playing = False

    def resume(self):
        self.last_tick = self.clock()
        self.playing = not self.finished

    def set_speed(self, speed):
        self.advance()
        self.speed = max(.25, min(4.0, float(speed)))

    def step(self):
        self.pause()
        if not self.finished:
            self.elapsed = self.due[self.index]
            self.state.apply(self.events[self.index])
            self.index += 1
