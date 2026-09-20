"""In-memory stores for uploads and runs.

A hackathon backend with a five-minute demo does not need a database, and a
process-local dict is one less thing to reproduce on a judge's laptop. Both
stores are module-level singletons; swap them for something persistent only if
we ever need runs to survive a restart.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

from app.events import EventBus
from app.models import PatientBundle, Report


@dataclass
class StoredFile:
    file_id: str
    filename: str
    kind: str
    text: str
    n_records: int = 0


class FileStore:
    def __init__(self) -> None:
        self._files: dict[str, StoredFile] = {}

    def add(self, filename: str, text: str, kind: str, n_records: int = 0) -> StoredFile:
        file_id = f"file-{uuid.uuid4().hex[:8]}"
        stored = StoredFile(
            file_id=file_id, filename=filename, kind=kind, text=text, n_records=n_records
        )
        self._files[file_id] = stored
        return stored

    def get(self, file_id: str) -> StoredFile | None:
        return self._files.get(file_id)

    def many(self, file_ids: list[str]) -> list[StoredFile]:
        """Missing ids are skipped — the caller reports what it could not find."""
        return [self._files[f] for f in file_ids if f in self._files]

    def all(self) -> list[StoredFile]:
        return list(self._files.values())

    def clear(self) -> None:
        self._files.clear()


@dataclass
class Run:
    run_id: str
    question: str
    bus: EventBus
    report: Report
    bundle: PatientBundle
    task: asyncio.Task | None = field(default=None, repr=False)


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}

    def create(self, question: str, bundle: PatientBundle, run_mode: str) -> Run:
        run_id = str(uuid.uuid4())
        run = Run(
            run_id=run_id,
            question=question,
            bus=EventBus(run_id),
            report=Report(
                run_id=run_id,
                question=question,
                bundle_summary=bundle.summary(),
                run_mode=run_mode,
            ),
            bundle=bundle,
        )
        self._runs[run_id] = run
        return run

    def get(self, run_id: str) -> Run | None:
        return self._runs.get(run_id)

    def all(self) -> list[Run]:
        return list(self._runs.values())

    def clear(self) -> None:
        self._runs.clear()


files = FileStore()
runs = RunStore()
