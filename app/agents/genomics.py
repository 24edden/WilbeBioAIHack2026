"""Genomics specialist — variant effect via a BioNeMo NIM."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import Agent
from app.models import PatientBundle, Provenance, Variant
from app.execution import bounded_map, DEFAULT_VARIANT_CONCURRENCY
from app.providers.base import VariantScore


def source_filename(bundle: PatientBundle, kind: str) -> str:
    for file in bundle.files:
        if file.kind == kind:
            return file.filename
    return f"uploaded {kind}"


class GenomicsAgent(Agent):
    role = "genomics"

    async def investigate(self) -> None:
        variants = self.ctx.bundle.variants
        if not variants:
            self.say("No variant file in the bundle; nothing to score.")
            return

        self.say(
            f"Scoring {len(variants)} variant(s) with "
            f"{self.ctx.providers.bio.name} for functional effect."
        )
        # Reuse exact biological inputs only within this run/provider context.
        # Source metadata stays on each row and is reattached to every finding.
        keys = [json.dumps(variant.model_dump(exclude={"source_line", "source_file", "source_file_id"}),
                           sort_keys=True) for variant in variants]
        unique = dict(zip(keys, variants))
        metrics = self.ctx.extras.setdefault("metrics", {})
        metrics["variant_requests"] = metrics.get("variant_requests", 0) + len(variants)
        active = 0

        async def score_unique(variant):
            nonlocal active
            metrics["variant_unique_requests"] = metrics.get("variant_unique_requests", 0) + 1
            active += 1
            metrics["variant_peak_concurrency"] = max(metrics.get("variant_peak_concurrency", 0), active)
            try:
                return await self._score(variant)
            finally:
                active -= 1

        unique_scores = await bounded_map(list(unique.values()), score_unique,
            self.ctx.extras.get("variant_concurrency", DEFAULT_VARIANT_CONCURRENCY))
        by_key = dict(zip(unique, unique_scores))
        scores = [by_key[key] for key in keys]
        seen = set()
        for variant, key, score in zip(variants, keys, scores):
            if key in seen and score is not None:
                metrics["variant_cache_hits"] = metrics.get("variant_cache_hits", 0) + 1
                self.tool_result("bionemo.score_variant", {"call": score.call, "pathogenicity": score.pathogenicity},
                                 variant=variant.label, output_id=score.output_id, reused=True,
                                 source_file=variant.source_file, source_file_id=variant.source_file_id)
            seen.add(key)

        vcf_name = source_filename(self.ctx.bundle, "vcf")
        scored: list[dict[str, Any]] = []
        for variant, score in zip(variants, scores):
            if score is None:
                continue
            scored.append(
                {
                    "label": score.variant_label,
                    "gene": variant.gene,
                    "rsid": variant.rsid,
                    "consequence": variant.consequence,
                    "zygosity": variant.zygosity,
                    "pathogenicity": score.pathogenicity,
                    "call": score.call,
                    "notes": score.notes,
                    "therapy_implication": self._implication(score),
                    "model": score.model,
                    "output_id": score.output_id,
                    "source_line": variant.source_line,
                    "source_file": variant.source_file or vcf_name,
                    "source_file_id": variant.source_file_id,
                }
            )

        step = await self.ctx.providers.reasoning.step(
            "genomics",
            self.task,
            {"scored": scored, "hypothesis": self.ctx.hypothesis, "question": self.ctx.question},
        )
        if step.message:
            self.say(step.message)

        for claim in step.claims:
            matches = [entry for entry in scored
                       if entry["label"] == str(claim.detail.get("label", ""))
                       and (not claim.detail.get("source_file_id")
                            or entry["source_file_id"] == claim.detail["source_file_id"])]
            if len(matches) != 1:
                self.say("Withheld a claim: its variant source was missing or ambiguous in the scored evidence.")
                continue
            entry = matches[0]
            provenance = [
                Provenance(
                    kind="file",
                    ref=entry.get("source_file", vcf_name),
                    locator=f"line {entry['source_line']}" if entry.get("source_line") else None,
                    quote=entry.get("label"),
                ),
                Provenance(
                    kind="nim",
                    ref=str(entry.get("output_id", "unknown")),
                    locator=str(entry.get("model", self.ctx.providers.bio.name)),
                    quote=entry.get("notes") or None,
                ),
            ]
            self.record(
                claim.claim,
                confidence=claim.confidence,
                provenance=provenance,
                stance=claim.stance,
                detail=entry or claim.detail,
            )

    async def _score(self, variant: Variant) -> VariantScore | None:
        self.tool_call(
            "bionemo.score_variant",
            variant=variant.label,
            rsid=variant.rsid,
            consequence=variant.consequence,
        )
        try:
            score = await self.ctx.providers.bio.score_variant(variant)
        except Exception as exc:  # noqa: BLE001 - one bad variant is not a dead run
            self.ctx.bus.emit(
                "error",
                agent_id=self.agent_id,
                agent_role=self.role,
                parent_id=self.parent_id,
                payload={"error": f"score_variant failed for {variant.label}: {exc}"},
            )
            return None
        self.tool_result(
            "bionemo.score_variant",
            {"call": score.call, "pathogenicity": score.pathogenicity},
            variant=variant.label,
            output_id=score.output_id,
        )
        return score

    def _implication(self, score: VariantScore) -> str:
        """What the result changes clinically, as reported by the provider."""
        if score.therapy_implication:
            return score.therapy_implication
        return "no established action" if score.pathogenicity < 0.6 else "review indicated"
