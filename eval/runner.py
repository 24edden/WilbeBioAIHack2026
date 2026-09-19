"""Run the same cases across configurations, keeping labels outside adapter inputs."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import math
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


@dataclass
class Outcome:
    answer: str = ""
    abstained: bool | None = None
    status: str = "complete"
    usage: dict[str, Any] = field(default_factory=lambda: {"status": "unavailable"})
    metrics: dict[str, Any] = field(default_factory=dict)
    artifact: dict[str, Any] = field(default_factory=dict)


class Adapter(Protocol):
    async def run(self, inputs: dict, config: dict) -> Outcome: ...


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def grade(outcome: Outcome, expected: dict) -> dict:
    """Behavioral checks only. Scientific correctness needs a separately reviewed rubric."""
    checks = {}
    if "abstained" in expected:
        checks["abstention_match"] = outcome.abstained == expected["abstained"]
    if expected.get("answer_contains"):
        checks["required_text"] = all(term.casefold() in outcome.answer.casefold()
                                      for term in expected["answer_contains"])
    if expected.get("answer_excludes"):
        checks["excluded_text"] = all(term.casefold() not in outcome.answer.casefold()
                                      for term in expected["answer_excludes"])
    return {"behavioral_checks": checks,
            "behavioral_pass": all(checks.values()) if checks and outcome.status == "complete" else False,
            "scientific_correctness": None,
            "grading_scope": "behavioral regression, not biological or causal validation"}


async def compare(cases: list[dict], configurations: list[dict], adapter_factory: Callable[[], Adapter],
                  *, concurrency: int = 2, timeout_seconds: float = 120, repeats: int = 1,
                  output: Path | None = None) -> list[dict]:
    if not 1 <= concurrency <= 16 or not 1 <= repeats <= 20:
        raise ValueError("concurrency must be 1..16; repeats must be 1..20")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    for items in (cases, configurations):
        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("case/configuration IDs must be unique")
    semaphore = asyncio.Semaphore(concurrency)
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation protects a previous comparison from accidental overwrite.
        with output.open("x", encoding="utf-8"):
            pass

    async def one(case, configuration, repeat):
        queued = time.perf_counter()
        async with semaphore:
            started = time.perf_counter()
            record = {"schema_version": 1, "case_id": case["id"], "configuration_id": configuration["id"],
                      "code_revision": revision, "working_tree_dirty": dirty,
                      "trial_timeout_seconds": timeout_seconds, "concurrency": concurrency,
                      "repeat": repeat, "input_sha256": digest(case["inputs"]),
                      "configuration": copy.deepcopy(configuration.get("settings", {})),
                      "configuration_sha256": digest(configuration.get("settings", {})),
                      "expected": copy.deepcopy(case.get("expected", {})),
                      "expected_sha256": digest(case.get("expected", {})),
                      "queue_seconds": started - queued}
            adapter = None
            try:
                adapter = adapter_factory()
                outcome = await asyncio.wait_for(adapter.run(copy.deepcopy(case["inputs"]),
                    copy.deepcopy(configuration.get("settings", {}))), timeout=timeout_seconds)
                json.dumps(asdict(outcome), allow_nan=False)  # reject malformed output within this trial
                record.update(asdict(outcome))
                record.update(grade(outcome, case.get("expected", {})))
            except Exception as exc:
                if adapter is not None and hasattr(adapter, "snapshot"):
                    try:
                        snapshot = adapter.snapshot()
                        json.dumps(snapshot, allow_nan=False)
                        record.update(snapshot)
                    except Exception as snapshot_error:
                        record["snapshot_error_type"] = type(snapshot_error).__name__
                # Exceptions are independent of grading and never counted as abstentions.
                record.update(status="timeout" if isinstance(exc, TimeoutError) else "error",
                              error_type=type(exc).__name__, behavioral_pass=False,
                              scientific_correctness=None)
                record.setdefault("usage", {"status": "unavailable"})
            record["wall_seconds"] = time.perf_counter() - started
            if output:
                with output.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            return record

    return await asyncio.gather(*(one(case, config, repeat)
        for repeat in range(repeats) for case in cases for config in configurations))
