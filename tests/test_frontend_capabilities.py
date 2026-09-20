from threading import Event
from time import monotonic

from frontend.ui.capabilities import CapabilityLookup


def test_slow_capability_lookup_never_blocks_the_caller_or_discards_known_settings():
    release = Event()
    calls = []
    def fetch():
        calls.append(True)
        release.wait(2)
        return {'models': ['first']}
    began = monotonic()
    lookup = CapabilityLookup(fetch)
    assert monotonic() - began < .5
    assert lookup.snapshot() == ({}, '', False, True, 0)
    lookup.refresh()  # Coalesce refreshes while one request is pending.
    release.set()
    lookup.thread.join(1)
    assert len(calls) == 1
    data, error, ready, loading, revision = lookup.snapshot()
    assert data == {'models': ['first']} and ready and not loading and revision == 1
    data['models'].append('changed outside')
    assert lookup.snapshot()[0] == {'models': ['first']}
    def failure():
        raise TimeoutError()
    lookup.fetch = failure
    lookup.refresh()
    lookup.thread.join(1)
    assert lookup.snapshot()[0] == {'models': ['first']}
    assert 'TimeoutError' in lookup.snapshot()[1]


def test_empty_or_failed_capabilities_resolve_without_an_endless_spinner():
    def invalid():
        return []
    lookup = CapabilityLookup(invalid)
    lookup.thread.join(1)
    _, error, ready, loading, _ = lookup.snapshot()
    assert ready and not loading and error
