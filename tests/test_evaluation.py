import asyncio
import json
from pathlib import Path

import pytest

from eval.investigation import InvestigationAdapter, summarize_usage
from eval.runner import Outcome, compare


async def test_comparison_bounds_concurrency_hides_labels_and_isolates_failures(tmp_path):
    active = peak = 0

    class Backend:
        async def run(self, inputs, config):
            nonlocal active, peak
            assert "expected" not in inputs
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.sleep(0.01)
                if config["fail"]:
                    raise RuntimeError("private diagnostic")
                return Outcome(answer="ok", abstained=False)
            finally:
                active -= 1

    cases = [{"id": str(i), "inputs": {"question": str(i)}, "expected": {"abstained": False}}
             for i in range(3)]
    configs = [{"id": "ok", "settings": {"fail": False}}, {"id": "bad", "settings": {"fail": True}}]
    output = tmp_path / "results.jsonl"
    rows = await compare(cases, configs, Backend, concurrency=2, output=output)
    assert peak == 2 and active == 0
    assert sum(row["status"] == "error" for row in rows) == 3
    assert sum(row["behavioral_pass"] for row in rows) == 3
    assert len(output.read_text().splitlines()) == 6
    assert "private diagnostic" not in output.read_text()
    assert all(row["scientific_correctness"] is None for row in rows)
    for case in cases:
        assert len({r["input_sha256"] for r in rows if r["case_id"] == case["id"]}) == 1


async def test_timeout_is_not_an_abstention(tmp_path):
    class Slow:
        async def run(self, inputs, config):
            await asyncio.sleep(10)
    rows = await compare([{"id": "x", "inputs": {}, "expected": {"abstained": True}}],
                         [{"id": "slow"}], Slow, timeout_seconds=0.01)
    assert rows[0]["status"] == "timeout" and rows[0]["behavioral_pass"] is False
    assert rows[0]["usage"]["status"] == "unavailable"


def test_usage_uses_reported_tokens_and_does_not_fill_missing_values():
    records = [{"usage": {"input_tokens": 12, "output_tokens": 5}},
               {"usage": {"prompt_tokens": 8, "completion_tokens": 3}}]
    result = summarize_usage(records)
    assert result["input_tokens"] == 20 and result["output_tokens"] == 8
    assert result["cost_usd"] is None and result["bio_usage"] == "unavailable"
    assert summarize_usage(records + [{"usage": None}])["input_tokens"] is None
    assert summarize_usage([])["input_tokens"] is None


async def test_repo_smoke_uses_real_engine_but_never_claims_model_performance():
    root = Path(__file__).resolve().parent.parent
    cases = json.loads((root / "eval/cases.json").read_text())["cases"]
    rows = await compare(cases, [{"id": "mock", "settings": {"run_mode": "mock"}}],
                         lambda: InvestigationAdapter(root))
    assert all(row["status"] == "complete" and row["behavioral_pass"] for row in rows)
    assert all(row["usage"]["status"] == "not_applicable_mock" for row in rows)
    assert all(row["artifact"]["provider_calls"] for row in rows)


async def test_live_requires_explicit_enablement():
    with pytest.raises(ValueError, match="--live"):
        await InvestigationAdapter(Path.cwd()).run({"question": "q"}, {"run_mode": "live"})


async def test_snapshot_failure_cannot_abort_comparison():
    class Broken:
        async def run(self, inputs, config):
            raise ValueError("trial failed")
        def snapshot(self):
            raise RuntimeError("snapshot failed")
    rows = await compare([{"id": "x", "inputs": {}}], [{"id": "a"}], Broken)
    assert rows[0]["status"] == "error"
    assert rows[0]["snapshot_error_type"] == "RuntimeError"


async def test_timeout_retains_completed_call_usage():
    class Slow:
        async def run(self, inputs, config):
            await asyncio.sleep(10)
        def snapshot(self):
            return {"usage": {"status": "partial_reasoning_only", "input_tokens": 42}}
    rows = await compare([{"id": "x", "inputs": {}}], [{"id": "a"}], Slow, timeout_seconds=0.01)
    assert rows[0]["status"] == "timeout"
    assert rows[0]["usage"]["input_tokens"] == 42
