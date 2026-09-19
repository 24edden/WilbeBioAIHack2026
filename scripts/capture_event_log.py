"""Record a mock investigation to JSON.

    python scripts/capture_event_log.py

Writes `fixtures/sample_event_log.json` (the full event stream) and
`fixtures/sample_report.json`. The frontend can build the graph and the report
view against these files with no backend running, and the same pair is the
safety net for the demo: if the service dies on stage, the UI still has a real
run to replay.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.engine import run_investigation  # noqa: E402
from app.events import EventBus  # noqa: E402
from app.ingest import build_bundle  # noqa: E402
from app.models import Report  # noqa: E402
from app.providers import build_providers  # noqa: E402

DEFAULT_QUESTION = "Why did this patient fail?"


async def capture(question: str, out_dir: Path, tag: str) -> tuple[Path, Path]:
    os.environ["RUN_MODE"] = "mock"
    os.environ["MOCK_LATENCY_SCALE"] = "0"

    files = [
        (f"file-{i}", path.name, path.read_text(encoding="utf-8"))
        for i, path in enumerate(sorted((ROOT / "samples").glob("patient-0*")))
    ]
    bundle = build_bundle(files)
    bus = EventBus(f"sample-{tag}")
    report = Report(
        run_id=bus.run_id, question=question, bundle_summary=bundle.summary(), run_mode="mock"
    )
    await run_investigation(
        run_id=bus.run_id,
        question=question,
        bundle=bundle,
        bus=bus,
        providers=build_providers(),
        report=report,
    )

    events_path = out_dir / f"sample_event_log{tag}.json"
    report_path = out_dir / f"sample_report{tag}.json"
    events_path.write_text(
        json.dumps([e.model_dump() for e in bus.history], indent=2), encoding="utf-8"
    )
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return events_path, report_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--tag", default="", help="suffix for the output filenames")
    parser.add_argument("--out", default=str(ROOT / "fixtures"))
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path, report_path = asyncio.run(capture(args.question, out_dir, args.tag))
    print(f"wrote {events_path.relative_to(ROOT)} and {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
