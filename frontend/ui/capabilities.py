"""Nonblocking, session-owned discovery of a backend's available controls."""
from copy import deepcopy
from threading import Lock, Thread


class CapabilityLookup:
    def __init__(self, fetch):
        self.fetch = fetch
        self.data = {}
        self.error = ""
        self.ready = False
        self.loading = False
        self.revision = 0
        self.lock = Lock()
        self.refresh()

    def refresh(self):
        with self.lock:
            if self.loading:
                return
            self.loading = True
        self.thread = Thread(target=self._fetch, name="capability-discovery", daemon=True)
        self.thread.start()

    def _fetch(self):
        try:
            data = self.fetch()
            if not isinstance(data, dict):
                raise ValueError("Expected a capability object")
            error = ""
        except Exception as exc:
            data, error = None, f"Could not read backend capabilities ({type(exc).__name__})."
        with self.lock:
            if data is not None:
                self.data = deepcopy(data)
            self.error = error
            self.ready = True
            self.loading = False
            self.revision += 1

    def snapshot(self):
        with self.lock:
            return deepcopy(self.data), self.error, self.ready, self.loading, self.revision
