"""Session-owned background work. Workers never access Streamlit/session state."""
from copy import deepcopy
from queue import Empty, Full, Queue
from threading import Event as Signal, Lock, Thread
from time import monotonic

from .events import Event


class BackgroundRun:
    def __init__(self, source, request, *, can_cancel=False, max_events=1024, lease_seconds=120):
        self.source = source
        self.request = deepcopy(request)
        self.can_cancel = can_cancel
        self.queue = Queue(maxsize=max_events)
        self.finished = Signal()
        self.stop_requested = Signal()
        self.cancel_requested = False
        self.completion_announced = False
        self.last_poll = monotonic()
        self.lease_seconds = lease_seconds
        self._lock = Lock()
        self._final_event = None
        self.thread = Thread(target=self._consume, name='investigation-source', daemon=True)
        self.thread.start()
        Thread(target=self._watch_lease, name='investigation-lease', daemon=True).start()

    @property
    def active(self):
        return not self.finished.is_set() or not self.queue.empty() or self._final_event is not None

    def _watch_lease(self):
        while not self.finished.wait(min(5.0, max(.01, self.lease_seconds / 4))):
            if monotonic() - self.last_poll <= self.lease_seconds:
                continue
            if self.can_cancel:
                self.request_cancel()
            elif self.request.mode == 'Live' and hasattr(self.source, 'detach'):
                self.source.detach()  # Ends observation only, never claims remote cancellation.
            return

    def _publish(self, event):
        while True:
            if self.stop_requested.is_set():
                return False
            if monotonic() - self.last_poll > self.lease_seconds:
                # An abandoned consumer cannot exert endless backpressure on
                # remote cancellation. Preserve the final outcome separately.
                return self.request.mode == 'Live'
            try:
                self.queue.put(event, timeout=.1)
                return True
            except Full:
                continue

    def _consume(self):
        stream = None
        terminal = False
        try:
            stream = iter(self.source.events(self.request))
            for event in stream:
                if event.type == 'run_complete':
                    # A real terminal outcome wins a simultaneous cancel request.
                    terminal = True
                    self._final_event = event
                    break
                if self.stop_requested.is_set() or (self.request.mode != 'Live' and monotonic() - self.last_poll > self.lease_seconds):
                    break
                if not self._publish(event):
                    break
        except Exception as exc:
            self._publish(Event(type='error', payload={'message': f'Investigation failed ({type(exc).__name__}): {exc}'}))
        finally:
            cleanup_ok = True
            if stream is not None and hasattr(stream, 'close'):
                try:
                    stream.close()  # Local DemoSource closes/cancels its engine here.
                except Exception as exc:
                    cleanup_ok = False
                    self._final_event = Event(type='error', payload={'message': f'Source cleanup failed: {exc}'})
            if not terminal:
                if self.stop_requested.is_set() and cleanup_ok and self.request.mode != 'Live':
                    self._final_event = Event(type='run_complete', payload={'status': 'cancelled', 'cancelled': True,
                        'abstained': True, 'verdict': 'Investigation cancelled.'})
                elif self._final_event is None:
                    self._final_event = Event(type='error', payload={'message': 'The event stream ended before a result was available.'})
            self.finished.set()

    def drain(self, limit=256):
        self.last_poll = monotonic()
        events = []
        for _ in range(limit):
            try:
                events.append(self.queue.get_nowait())
            except Empty:
                break
        if self.finished.is_set() and self.queue.empty() and self._final_event is not None:
            events.append(self._final_event)
            self._final_event = None
        return events

    def request_cancel(self):
        if not self.can_cancel or not self.active:
            return
        with self._lock:
            if self.cancel_requested:
                return
            self.cancel_requested = True
        if self.request.mode != 'Live':
            self.stop_requested.set()
            interrupt=getattr(self.source,'interrupt_wait',None)
            if callable(interrupt):interrupt()
        else:
            # Closing SSE is not cancellation. Wait for the server's terminal event.
            def cancel_remote():
                try:
                    self.source.cancel(self.request)
                except Exception as exc:
                    self._publish(Event(type='error', payload={'message': f'Cancellation failed: {exc}'}))
                    self.cancel_requested = False
                    if monotonic() - self.last_poll > self.lease_seconds and hasattr(self.source, 'detach'):
                        self.source.detach()
            Thread(target=cancel_remote, name='investigation-cancel', daemon=True).start()
