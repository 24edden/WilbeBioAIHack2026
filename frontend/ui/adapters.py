"""The replaceable data-source seam between page controls and normalized events."""

from dataclasses import dataclass, field
import asyncio
import math
import sys
import uuid
from threading import Event as Signal
from pathlib import Path
from typing import Iterator, Protocol

from .events import Event
from .stream import (
    DEFAULT_BACKEND, DEFAULT_CONTRACT, BackendContract, list_fixtures, load_fixture,
    live_stream, load_sample_patient, mock_stream, start_run, upload_files,
    fetch_capabilities,
    cancel_run,
)


@dataclass(frozen=True)
class RunRequest:
    mode: str
    question: str
    backend: str = DEFAULT_BACKEND
    fixture: str | None = None
    speed: float = 1.5
    sample: bool = False
    uploads: list[tuple[str, bytes]] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)


class InvestigationSource(Protocol):
    def capabilities(self, backend: str) -> dict:
        """Return the normalized optional agent/model catalog; {} means unavailable."""
        ...

    def events(self, request: RunRequest) -> Iterator[Event]:
        """Yield normalized Events; views never consume backend-specific records."""
        ...


class ReplaySource:
    def capabilities(self, backend: str) -> dict:
        return {}

    def events(self, request: RunRequest) -> Iterator[Event]:
        if not request.fixture:
            raise ValueError("No recorded run selected.")
        yield from mock_stream(request.fixture, speed=request.speed)


@dataclass
class DemoSource:
    """Run the actual local engine on mock providers; never consult live credentials."""

    mock_latency_scale: float = 0.25

    def capabilities(self, backend: str) -> dict:
        root = Path(__file__).resolve().parents[2]
        if str(root) != sys.path[0]:
            sys.path.insert(0, str(root))
        from app.skills import workflow_capabilities, role_metadata
        return {
            **workflow_capabilities(),
            "run_mode": "mock",
            "specialist_roles": [{"id": role, "label": role.title(), **role_metadata(role)}
                                 for role in ("genomics", "clinical", "literature")],
            "required_roles": ["orchestrator", "critic"],
            "defaults": {"task_mode": "investigation", "specialists": ["genomics", "clinical", "literature"],
                         "reasoning_model": "rosalind(mock)",
                         "variant_model": "bionemo-nim(mock):variant-effect",
                         "embedding_model": "hash-embedding(mock)"},
            "model_overrides_supported": False,
        }

    def events(self, request: RunRequest) -> Iterator[Event]:
        run_id = str(uuid.uuid4())
        try:
            # Streamlit prepends frontend/, whose app.py otherwise shadows the
            # backend app package. Prefer this repository's package explicitly.
            root = Path(__file__).resolve().parents[2]
            if not (root / "app" / "__init__.py").is_file():
                raise ImportError("Local demo engine is not included in this frontend installation.")
            if str(root) != sys.path[0]:
                sys.path.insert(0, str(root))
            # Lazy imports keep recorded playback usable in standalone frontend installs.
            from app.engine import run_investigation
            from app.events import EventBus
            from app.ingest import build_bundle
            from app.models import Report, RunConfig, PatientBundle
            from app.skills import resolve_task_mode
            from app.providers.base import Providers
            from app.providers.mock import MockBioProvider, MockReasoningProvider

            question = request.question.strip()
            if not question:
                raise ValueError("Enter a question for the demo investigation.")
            config = RunConfig(**request.config)
            if any((config.reasoning_model, config.variant_model, config.embedding_model)):
                raise ValueError("Demo uses fixed mock providers; model overrides require Live mode.")
            if not math.isfinite(self.mock_latency_scale) or self.mock_latency_scale < 0:
                raise ValueError("Demo latency must be a finite non-negative number.")
            if request.uploads and not request.sample:
                files = [(f"demo-file-{i}", name, data.decode("utf-8"))
                         for i, (name, data) in enumerate(request.uploads)]
            elif resolve_task_mode(config.task_mode, question, PatientBundle())[0] == "idea_review":
                files = []
            else:
                samples = Path(__file__).resolve().parents[2] / "samples"
                files = [(f"demo-file-{i}", path.name, path.read_text(encoding="utf-8"))
                         for i, path in enumerate(sorted(samples.glob("patient-0*")))]
                if not files:
                    raise ValueError("Bundled demo files are unavailable. Run the frontend from the complete repository.")
            bundle = build_bundle(files)
            bus = EventBus(run_id)
            report = Report(run_id=run_id, question=question, run_mode="mock", config={
                "specialists": config.specialists,
                "roster_source": "user" if config.specialists else "planner",
                "run_mode": "mock", "execution_source": "local_demo",
                **{key: value for key, value in self.capabilities("")["defaults"].items()
                   if key != "specialists"},
            })
            providers = Providers(reasoning=MockReasoningProvider(self.mock_latency_scale),
                                  bio=MockBioProvider(self.mock_latency_scale), mode="mock")

            async def begin():
                return asyncio.create_task(run_investigation(run_id=run_id, question=question,
                    bundle=bundle, bus=bus, providers=providers, report=report,
                    specialists=config.specialists, task_mode=config.task_mode))

            # Drive the async engine on its source worker. Closing this generator
            # cancels and joins its task before the worker reports cancellation.
            with asyncio.Runner() as runner:
                task = runner.run(begin())
                stream = bus.subscribe()
                try:
                    while True:
                        try:
                            event = runner.run(anext(stream))
                        except StopAsyncIteration:
                            break
                        yield Event.from_dict(event.model_dump())
                finally:
                    task.cancel()
                    async def cleanup():
                        await asyncio.gather(task, return_exceptions=True)
                        await stream.aclose()
                    runner.run(cleanup())
        except Exception as exc:
            message = ("Interactive demo dependencies are unavailable. Install the root requirements and run "
                       "the full repository, or use a recorded case." if isinstance(exc, ImportError)
                       else f"Demo could not run: {exc}")
            yield Event(type="error", run_id=run_id, payload={"message": message, "fatal": True})
            yield Event(type="run_complete", run_id=run_id,
                        payload={"verdict": "Demo failed before a result was available.",
                                 "abstained": True, "confidence": 0.0, "error": message})


@dataclass
class BackendSource:
    contract: BackendContract = field(default_factory=lambda: DEFAULT_CONTRACT)
    active_run_id: str | None = field(default=None, init=False)
    detached: Signal = field(default_factory=Signal, init=False)

    def capabilities(self, backend: str) -> dict:
        return fetch_capabilities(backend, contract=self.contract)

    def cancel(self, request: RunRequest) -> dict:
        if not self.active_run_id:
            raise ValueError("The backend has not returned a run ID yet.")
        return cancel_run(request.backend, self.active_run_id, contract=self.contract)

    def detach(self):
        self.detached.set()

    def events(self, request: RunRequest) -> Iterator[Event]:
        if request.sample:
            ids = load_sample_patient(request.backend, contract=self.contract)
        elif request.uploads:
            ids = upload_files(request.backend, request.uploads, contract=self.contract)
        else:
            ids = []
        run_id = start_run(request.backend, request.question, ids, contract=self.contract, config={key: value for key, value in request.config.items() if value != ""})
        self.active_run_id = run_id
        yield from live_stream(request.backend, run_id, contract=self.contract, should_stop=self.detached.is_set)


def source_for(mode: str) -> InvestigationSource:
    """Replace this factory to use polling, WebSockets, local jobs or another API."""
    if mode == "Demo":
        return DemoSource()
    return ReplaySource() if mode == "Mock" else BackendSource()


def recorded_context(path: Path | None, default_question: str) -> tuple[str, list[str]]:
    """Read previews through the same normalized parser used for replay."""
    if path:
        event = next((event for event in load_fixture(path) if event.type == "run_started"), None)
        if event:
            files = event.payload.get("files", [])
            return str(event.payload.get("question") or default_question), [str(f) for f in files] if isinstance(files, list) else []
    return default_question, []
