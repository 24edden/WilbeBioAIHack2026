"""Genomics specialist — variant effect via a BioNeMo NIM."""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base import Agent
from app.models import PatientBundle, Provenance, Variant
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
        scores = await asyncio.gather(*(self._score(v) for v in variants))

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
                    "source_file": vcf_name,
                }
            )

        step = await self.ctx.providers.reasoning.step(
            "genomics",
            self.task,
            {"scored": scored, "hypothesis": self.ctx.hypothesis, "question": self.ctx.question},
        )
        if step.message:
            self.say(step.message)

        by_label = {entry["label"]: entry for entry in scored}
        for claim in step.claims:
            entry = by_label.get(str(claim.detail.get("label", "")), {})
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
