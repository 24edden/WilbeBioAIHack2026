"""Test setup: mock mode, zero latency, clean stores."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("RUN_MODE", "mock")
os.environ["MOCK_LATENCY_SCALE"] = "0"   # tests must not wait for the demo pacing

SAMPLES = ROOT / "samples"


@pytest.fixture(autouse=True)
def clean_stores():
    from app.store import files, runs

    files.clear()
    runs.clear()
    yield
    files.clear()
    runs.clear()


@pytest.fixture
def sample_files() -> list[tuple[str, str, str]]:
    return [
        (f"file-{i}", path.name, path.read_text(encoding="utf-8"))
        for i, path in enumerate(sorted(SAMPLES.glob("patient-0*")))
    ]


@pytest.fixture
def sample_bundle(sample_files):
    from app.ingest import build_bundle

    return build_bundle(sample_files)
