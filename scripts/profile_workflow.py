"""Profile orchestration with synthetic files and mock providers, never live APIs.

python scripts/profile_workflow.py --output .deploy/profile-before.json
Latency includes explicit simulated provider waits, not real model performance.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.engine import run_investigation
from app.events import EventBus
from app.ingest import build_bundle
from app.models import Report
from app.providers.base import Providers
from app.providers.mock import MockBioProvider, MockReasoningProvider


class InstrumentedBio(MockBioProvider):
    def __init__(self, scale):
        super().__init__(scale)
        self.active = 0
        self.peak = 0
        self.variant_calls = 0

    async def score_variant(self, variant):
        self.active += 1
        self.peak = max(self.peak, self.active)
        self.variant_calls += 1
        try:
            return await super().score_variant(variant)
        finally:
            self.active -= 1


async def trial(copies: int, scale: float) -> dict:
    files = []
    for path in sorted((ROOT / "samples").glob("patient-0*")):
        for n in range(copies if path.suffix == ".vcf" else 1):
            files.append((f"file-{len(files)}", f"{n}-{path.name}", path.read_text(encoding="utf-8")))
    bundle = build_bundle(files)
    bio = InstrumentedBio(scale)
    providers = Providers(reasoning=MockReasoningProvider(scale), bio=bio, mode="mock")
    report = Report(run_id="profile", question="Why did this patient's treatment fail?", run_mode="mock")
    bus = EventBus(report.run_id)
    started = time.perf_counter()
    first_event = first_finding = None

    async def observe():
        nonlocal first_event, first_finding
        async for event in bus.subscribe():
            elapsed = time.perf_counter() - started
            if first_event is None:
                first_event = elapsed
            if event.type == "finding" and first_finding is None:
                first_finding = elapsed

    observer = asyncio.create_task(observe())
    await run_investigation(run_id=report.run_id, question=report.question, bundle=bundle,
                            bus=bus, providers=providers, report=report,
                            specialists=["genomics", "clinical", "literature"])
    await observer
    wall = time.perf_counter() - started
    signature = {"findings": [f.model_dump() for f in report.findings],
                 "verdict": report.verdict.model_dump() if report.verdict else None}
    return {"wall_seconds": wall, "first_event_seconds": first_event,
            "first_finding_seconds": first_finding, "variants": len(bundle.variants),
            "score_calls": bio.variant_calls, "peak_variant_calls": bio.peak,
            "events": len(bus.history), "findings": len(report.findings),
            "status": report.status, "abstained": report.verdict.abstained if report.verdict else None,
            "result_sha256": hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()}


async def profile(repeats: int) -> dict:
    cases = {}
    for name, copies, scale in (("sample_no_wait", 1, 0), ("sample_paced", 1, .2),
                                 ("repeated_uploads", 12, .05)):
        trials = [await trial(copies, scale) for _ in range(repeats)]
        cases[name] = {"synthetic_vcf_copies": copies, "mock_latency_scale": scale,
                       "median_wall_seconds": statistics.median(t["wall_seconds"] for t in trials),
                       "trials": trials}
    return {"kind": "synthetic_mock_workflow_profile", "live_model_calls": 0,
            "note": "Paced cases include simulated waits. These are orchestration measurements, not inference speed or scientific accuracy.",
            "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    result = asyncio.run(profile(args.repeats))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({name: {"median_seconds": round(case["median_wall_seconds"], 4),
                            "score_calls": case["trials"][0]["score_calls"],
                            "peak_calls": case["trials"][0]["peak_variant_calls"]}
                      for name, case in result["cases"].items()}))
