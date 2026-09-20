"""Headless run: the same engine the API drives, printed to a terminal.

    python -m app.cli "Why did this patient fail?" samples/*

Useful for three things: developing without a browser, capturing an event log
for the frontend to replay, and proving on stage that the investigation is not
a scripted animation.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.config import get_settings
from app.engine import run_investigation
from app.events import EventBus
from app.ingest import build_bundle
from app.models import Report
from app.providers import build_providers


def read_files(paths: list[str]) -> list[tuple[str, str, str]]:
    files = []
    for index, raw in enumerate(paths):
        path = Path(raw)
        if not path.is_file():
            raise SystemExit(f"not a file: {path}")
        files.append((f"file-{index}", path.name, path.read_text(encoding="utf-8")))
    return files


async def _print_events(bus: EventBus, as_json: bool) -> None:
    async for event in bus.subscribe():
        if as_json:
            print(json.dumps(event.model_dump()), flush=True)
            continue
        payload = event.payload
        summary = (
            payload.get("text")
            or payload.get("finding")
            or payload.get("verdict")
            or payload.get("error")
            or payload.get("tool")
            or payload.get("task")
            or ""
        )
        print(f"  {event.type:<14} {event.agent_id:<14} {str(summary)[:110]}", flush=True)


async def run(question: str, paths: list[str], as_json: bool) -> Report:
    settings = get_settings()
    bundle = build_bundle(read_files(paths))
    bus = EventBus("cli-run")
    report = Report(
        run_id="cli-run",
        question=question,
        bundle_summary=bundle.summary(),
        run_mode=settings.run_mode,
    )
    printer = asyncio.create_task(_print_events(bus, as_json))
    await run_investigation(
        run_id="cli-run",
        question=question,
        bundle=bundle,
        bus=bus,
        providers=build_providers(settings),
        report=report,
    )
    await printer
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one investigation headlessly.")
    parser.add_argument("question")
    parser.add_argument("files", nargs="+", help="VCF / labs CSV / notes")
    parser.add_argument("--json", action="store_true", help="emit the raw event stream")
    args = parser.parse_args(argv)

    report = asyncio.run(run(args.question, args.files, args.json))
    if not args.json:
        verdict = report.verdict
        print("\n" + "=" * 78)
        print(f"STATUS     {report.status}   mode={report.run_mode}")
        if verdict:
            print(f"ABSTAINED  {verdict.abstained}")
            print(f"CONFIDENCE {verdict.confidence:.2f}")
            print(f"VERDICT    {verdict.answer}")
            print(f"RATIONALE  {verdict.rationale}")
            for caveat in verdict.caveats:
                print(f"  caveat   {caveat}")
        print(f"FINDINGS   {len(report.findings)}")
    return 0 if report.status == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
