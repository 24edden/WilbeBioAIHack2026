from threading import Event as Signal
from time import monotonic

from frontend.ui.adapters import RunRequest
from frontend.ui.events import Event
from frontend.ui.runtime import BackgroundRun
from frontend.ui.state import RunState


def test_hundred_events_are_folded_in_one_available_batch_without_loss():
    class Burst:
        def events(self, request):
            for i in range(100):
                yield Event(type='tool_result', ts=i, payload={'result': str(i)})
            yield Event(type='run_complete', payload={'verdict': 'Finished'})
    job = BackgroundRun(Burst(), RunRequest(mode='Demo', question='Q'))
    job.thread.join(1)
    batch = job.drain()
    assert len(batch) == 101
    state = RunState()
    for event in batch:
        state.apply(event)
    assert len(state.raw) == 101 and state.complete
    assert not job.active and not job.drain()


def test_slow_source_does_not_block_caller_and_local_cancel_waits_for_cleanup():
    release, cleanup = Signal(), Signal()
    class Slow:
        def events(self, request):
            try:
                yield Event(type='run_started', run_id='slow')
                release.wait(2)
                yield Event(type='finding', payload={'finding': 'After wait'})
            finally:
                cleanup.set()
    started = monotonic()
    job = BackgroundRun(Slow(), RunRequest(mode='Demo', question='Q'), can_cancel=True)
    assert monotonic() - started < .5
    job.request_cancel()
    assert job.active and not cleanup.is_set()
    release.set()
    job.thread.join(1)
    batch = job.drain()
    assert cleanup.is_set()
    assert batch[-1].payload['status'] == 'cancelled'
    assert not any(event.type == 'finding' for event in batch)


def test_unsupported_remote_cancel_never_fabricates_cancellation():
    release = Signal()
    class Remote:
        def events(self, request):
            release.wait(2)
            yield Event(type='run_complete', payload={'verdict': 'Completed normally'})
    job = BackgroundRun(Remote(), RunRequest(mode='Live', question='Q'), can_cancel=False)
    job.request_cancel()
    assert not job.cancel_requested and not job.stop_requested.is_set()
    release.set()
    job.thread.join(1)
    assert not job.drain()[-1].payload.get('cancelled')


def test_queue_backpressure_bounds_backlog_without_dropping_events():
    class Burst:
        def events(self, request):
            for i in range(20):
                yield Event(type='tool_result', ts=i)
            yield Event(type='run_complete')
    job = BackgroundRun(Burst(), RunRequest(mode='Demo', question='Q'), max_events=4)
    events = []
    deadline = monotonic() + 2
    while job.active and monotonic() < deadline:
        assert job.queue.qsize() <= 4
        events.extend(job.drain())
        job.finished.wait(.001)
    assert len(events) == 21

def test_real_terminal_outcome_wins_local_cancel_race():
    release = Signal()
    class Finishing:
        def events(self, request):
            release.wait(2)
            yield Event(type='run_complete', payload={'status': 'complete', 'verdict': 'Finished'})
    job = BackgroundRun(Finishing(), RunRequest(mode='Demo', question='Q'), can_cancel=True)
    job.request_cancel()
    release.set()
    job.thread.join(1)
    terminal = job.drain()[-1]
    assert terminal.payload['status'] == 'complete'
    assert not terminal.payload.get('cancelled')

def test_cancel_with_full_queue_finishes_without_waiting_for_a_consumer():
    entered = Signal()
    class Busy:
        def events(self, request):
            yield Event(type='run_started')
            entered.set()
            for index in range(10):
                yield Event(type='finding', ts=index)
    job = BackgroundRun(Busy(), RunRequest(mode='Demo', question='Q'), can_cancel=True, max_events=1)
    assert entered.wait(1)
    job.request_cancel()
    job.thread.join(1)
    assert job.finished.is_set()
    assert job.drain()[-1].payload['status'] == 'cancelled'


def test_idle_lease_calls_real_remote_cancel_and_retains_terminal_outcome():
    cancelled = Signal()
    class Remote:
        def events(self, request):
            cancelled.wait(1)
            yield Event(type='run_complete', payload={'status': 'cancelled', 'cancelled': True})
        def cancel(self, request):
            cancelled.set()
            return {'status': 'cancelled'}
    job = BackgroundRun(Remote(), RunRequest(mode='Live', question='Q'), can_cancel=True, lease_seconds=.03)
    job.thread.join(1)
    assert cancelled.is_set() and job.finished.is_set()
    assert job.drain()[-1].payload['status'] == 'cancelled'


def test_unsupported_remote_lease_detaches_without_claiming_cancellation():
    detached = Signal()
    class Legacy:
        def events(self, request):
            detached.wait(1)
            return
            yield
        def detach(self):
            detached.set()
    job = BackgroundRun(Legacy(), RunRequest(mode='Live', question='Q'), lease_seconds=.03)
    job.thread.join(1)
    assert detached.is_set()
    batch = job.drain()
    assert batch[-1].type == 'error'
    assert not any(event.payload.get('cancelled') for event in batch)
