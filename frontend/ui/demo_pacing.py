"""Pace mock-demo event delivery without delaying real backend runs.

The local engine still computes the supplied question/data once with mock providers.
Only its presentation timing is simulated. Payloads, event ordering and reports are
unchanged, and cancellation interrupts a wait immediately.
"""
from threading import Event as Signal
from time import monotonic

DEMO_DURATION_SECONDS=25.0


class PacedDemoSource:
    def __init__(self, source, *, duration=DEMO_DURATION_SECONDS, clock=monotonic, wait=None):
        self.source=source
        self.duration=duration
        self.clock=clock
        self.stopped=Signal()
        self.wait=wait or self.stopped.wait

    def interrupt_wait(self):
        self.stopped.set()

    def _until(self,deadline):
        delay=max(0.0,deadline-self.clock())
        return self.stopped.is_set() or (delay>0 and bool(self.wait(delay)))

    def events(self,request):
        start=self.clock()
        stream=iter(self.source.events(request))
        try:
            events=[]
            for event in stream:
                if self.stopped.is_set():return
                events.append(event)
        finally:
            if hasattr(stream,'close'):stream.close()
        if not events:return
        terminal=events[-1]
        if (terminal.type!='run_complete' or terminal.payload.get('error')
                or terminal.payload.get('status') in {'error','cancelled'}
                or any(e.type=='error' and e.payload.get('fatal') for e in events)):
            yield from events  # Configuration/input/execution failures are never hidden by pacing.
            return
        groups=[];actor=None
        for event in events[:-1]:
            if not groups or (event.agent_id and actor and event.agent_id!=actor):groups.append([])
            groups[-1].append(event)
            if event.agent_id:actor=event.agent_id
        interval=self.duration/max(1,len(groups))
        for i,group in enumerate(groups):
            if self._until(start+i*interval):return
            yield group[0]
            if len(group)>1:
                if self._until(start+(i+.55)*interval):return
                yield from group[1:]
        if self._until(start+self.duration):return
        yield terminal
