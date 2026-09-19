"""The only evaluation module coupled to the current patient investigation backend."""

from dataclasses import replace
import hashlib
import math
import time
from pathlib import Path

from app.config import get_settings
from app.engine import run_investigation
from app.events import EventBus
from app.ingest import build_bundle
from app.models import Report, RunConfig
from app.providers import build_providers
from eval.runner import Outcome


def summarize_usage(records: list[dict]) -> dict:
    def total(primary, alternative):
        values = [(record.get("usage") or {}).get(primary, (record.get("usage") or {}).get(alternative))
                  for record in records]
        return sum(values) if values and all(type(value) is int and value >= 0 for value in values) else None
    available = sum(isinstance(record.get("usage"), dict) for record in records)
    status = "reported_reasoning_only" if records and available == len(records) else "partial_reasoning_only" if available else "unavailable"
    return {"status": status,
            "input_tokens": total("input_tokens", "prompt_tokens"),
            "output_tokens": total("output_tokens", "completion_tokens"),
            "response_count": len(records), "records": records,
            "bio_usage": "unavailable", "cost_usd": None}


class TimedProvider:
    def __init__(self, provider, category, calls):
        self.provider, self.category, self.calls = provider, category, calls

    def __getattr__(self, name):
        member = getattr(self.provider, name)
        if name not in {"plan", "step", "synthesize", "embed", "score_variant"}:
            return member

        async def measured(*args, **kwargs):
            start = time.perf_counter()
            status = "error"
            try:
                result = await member(*args, **kwargs)
                status = "complete"
                return result
            finally:
                self.calls.append({"provider": self.category, "method": name,
                                   "wall_seconds": time.perf_counter() - start, "status": status})
        return measured


class InvestigationAdapter:
    def __init__(self, root: Path, allow_live: bool = False):
        self.root = root.resolve()
        self.allow_live = allow_live
        self.reasoning = None
        self.calls = []
        self.artifact = {}

    def snapshot(self):
        return {"usage": summarize_usage(getattr(self.reasoning, "usage", [])),
                "artifact": {**self.artifact, "provider_calls": list(self.calls)},
                "usage_note": "Recorded responses only; an in-flight request may still consume unreported tokens."}

    async def run(self, inputs: dict, config: dict) -> Outcome:
        mode = config.get("run_mode", "mock")
        if mode not in ("mock", "live") or (mode == "live" and not self.allow_live):
            raise ValueError("Live evaluation requires explicit --live authorization")
        settings = get_settings()
        allowed = {"run_mode", "specialists", "reasoning_model", "reasoning_api", "bionemo_variant_model",
                   "bionemo_embed_model", "reasoning_max_output_tokens", "reasoning_timeout_seconds"}
        if set(config) - allowed:
            raise ValueError("Unknown configuration fields")
        model_fields = {"reasoning_model", "bionemo_variant_model", "bionemo_embed_model"}
        if mode == "mock" and model_fields & config.keys():
            raise ValueError("Mock model selection does not measure model performance")
        validated = RunConfig(specialists=config.get("specialists"), reasoning_model=config.get("reasoning_model"),
                  variant_model=config.get("bionemo_variant_model"), embedding_model=config.get("bionemo_embed_model"))
        config = dict(config)
        for input_key, validated_key in (("reasoning_model", "reasoning_model"),
                                         ("bionemo_variant_model", "variant_model"),
                                         ("bionemo_embed_model", "embedding_model")):
            if input_key in config:
                value = getattr(validated, validated_key)
                if value is None:
                    config.pop(input_key)
                else:
                    config[input_key] = value
        if config.get("reasoning_api", "auto") not in {"auto", "responses", "chat_completions"}:
            raise ValueError("Unknown reasoning API")
        budget = config.get("reasoning_max_output_tokens", settings.reasoning_max_output_tokens)
        timeout = config.get("reasoning_timeout_seconds", settings.reasoning_timeout_seconds)
        if type(budget) is not int or budget <= 0:
            raise ValueError("Output budget must be a positive integer")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Provider timeout must be finite and positive")
        settings = replace(settings, run_mode=mode, mock_latency_scale=0,
                           **{key: value for key, value in config.items() if key not in {"run_mode", "specialists"}})
        files = []
        input_hashes = {}
        for index, relative in enumerate(inputs.get("files", [])):
            path = (self.root / relative).resolve()
            if not path.is_relative_to(self.root):
                raise ValueError("Evaluation files must stay inside the dataset root")
            content = path.read_bytes()
            input_hashes[relative] = hashlib.sha256(content).hexdigest()
            files.append((f"eval-file-{index}", path.name, content.decode("utf-8")))
        bundle = build_bundle(files)
        providers = build_providers(settings)
        calls = []
        reasoning = providers.reasoning
        self.reasoning, self.calls = reasoning, calls
        self.artifact = {"input_file_sha256": input_hashes, "effective_settings": {
            "run_mode": mode, "reasoning_model": settings.reasoning_model if mode == "live" else "mock",
            "reasoning_api": settings.effective_reasoning_api if mode == "live" else None,
            "reasoning_max_output_tokens": budget, "reasoning_timeout_seconds": timeout,
            "variant_model": settings.bionemo_variant_model if mode == "live" else "mock",
            "embedding_model": settings.bionemo_embed_model if mode == "live" else "mock",
            "specialists": config.get("specialists")}}
        providers.reasoning = TimedProvider(reasoning, "reasoning", calls)
        providers.bio = TimedProvider(providers.bio, "bio", calls)
        bus = EventBus("evaluation")
        report = Report(run_id="evaluation", question=inputs["question"], run_mode=mode)
        await run_investigation(run_id="evaluation", question=inputs["question"], bundle=bundle,
            bus=bus, providers=providers, report=report, specialists=config.get("specialists"))
        specialist_findings = [finding for finding in report.findings if finding.agent_role != "critic"]
        total = len(specialist_findings)
        cited = sum(bool(finding.provenance) for finding in specialist_findings)
        usage = summarize_usage(getattr(reasoning, "usage", []))
        if mode == "mock":
            usage = {"status": "not_applicable_mock", "input_tokens": 0, "output_tokens": 0}
        return Outcome(answer=report.verdict.answer if report.verdict else "",
                       abstained=report.verdict.abstained if report.verdict else None,
                       status=report.status, usage=usage,
                       metrics={"findings": total, "citation_presence_fraction": cited / total if total else None,
                                "citation_entailment": None, "causal_validity": None,
                                "tool_calls": sum(event.type == "tool_call" for event in bus.history),
                                "provider_error_events": sum(event.type == "error" for event in bus.history)},
                       artifact={**self.artifact, "report": report.model_dump(),
                                 "input_file_sha256": input_hashes, "provider_calls": calls,
                                 "events": [event.model_dump() for event in bus.history],
                                 "effective_reasoning_model": settings.reasoning_model if mode == "live" else "mock",
                                 "effective_reasoning_api": settings.effective_reasoning_api if mode == "live" else None})
