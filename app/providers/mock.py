"""Mock providers — fixtures plus simulated latency.

`RUN_MODE=mock` runs the *real* orchestrator, the real agent graph and the real
event stream; only the model outputs are faked. That makes it the daily dev
loop, the token-free rehearsal path and the fallback if the GPU or Rosalind is
unavailable on the day.

Two rules the fakes follow:

* **Grounded in the upload.** Messages and claims are built from the parsed
  `PatientBundle`, not from canned prose. Upload a different VCF and the run
  changes. A fixture that ignores its input makes a demo that dies the moment a
  judge hands us their own file.
* **Deterministic.** Same input, same run, same wording — rehearsals stay valid.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.hypothesis import extract_hypothesis, mentioned_genes
from app.models import AgentRole, PatientBundle, Variant
from app.providers.base import (
    ClaimDraft,
    Plan,
    ReasoningStep,
    SubTask,
    SynthesisResult,
    VariantScore,
)
from app.providers.fixtures import hash_embed, stable_unit, variants_fixture

# Seconds of "thinking" per call, before MOCK_LATENCY_SCALE. Tuned so a full
# investigation lands around 20-25 seconds: long enough that the graph animates
# and the audience can read it, short enough for a five-minute slot.
# Total claim weight at which the evidence counts as "enough to be sure";
# below it, confidence is scaled down in proportion.
EVIDENCE_SATURATION = 3.0

LATENCY = {
    "plan": 2.2,
    "step": 1.6,
    "synthesize": 2.6,
    "score_variant": 0.9,
    "embed": 0.6,
}


def _call_pathogenicity(score: float) -> str:
    if score >= 0.9:
        return "pathogenic"
    if score >= 0.66:
        return "likely_pathogenic"
    if score >= 0.34:
        return "uncertain"
    return "benign"


class MockBioProvider:
    """Stands in for BioNeMo NIM calls."""

    name = "bionemo-nim(mock)"

    def __init__(self, latency_scale: float = 1.0) -> None:
        self.latency_scale = latency_scale
        self.calls: list[tuple[str, str]] = []

    async def _sleep(self, key: str, seed: str) -> None:
        if self.latency_scale <= 0:
            return
        jitter = 0.7 + 0.6 * stable_unit(key, seed)
        await asyncio.sleep(LATENCY[key] * jitter * self.latency_scale)

    async def score_variant(self, variant: Variant) -> VariantScore:
        self.calls.append(("score_variant", variant.label))
        await self._sleep("score_variant", variant.label)

        fixture = variants_fixture()
        record: dict[str, Any] | None = None
        if variant.rsid:
            record = fixture["by_rsid"].get(variant.rsid)
        if record is None and variant.gene:
            record = fixture["by_gene"].get(variant.gene)

        if record is None:
            # Unknown variant: a stable score so an arbitrary uploaded VCF still
            # produces a coherent run, and an explicit note that it is a guess.
            score = round(0.15 + 0.55 * stable_unit("variant", variant.label), 2)
            record = {
                "pathogenicity": score,
                "call": _call_pathogenicity(score),
                "notes": "No curated annotation for this variant in the mock fixture set; "
                         "the score is a placeholder and must not be read as a prediction.",
                "therapy_implication": "unknown",
            }

        pathogenicity = float(record["pathogenicity"])
        return VariantScore(
            variant_label=variant.label,
            pathogenicity=pathogenicity,
            call=str(record.get("call") or _call_pathogenicity(pathogenicity)),
            model=f"{self.name}:variant-effect",
            output_id=f"nim-var-{variant.chrom}-{variant.pos}-{variant.ref}{variant.alt}",
            notes=str(record.get("notes", "")),
            therapy_implication=str(record.get("therapy_implication", "")),
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(("embed", f"{len(texts)} text(s)"))
        await self._sleep("embed", str(len(texts)))
        return [hash_embed(text) for text in texts]


class MockReasoningProvider:
    """Stands in for GPT-Rosalind / OpenAI."""

    name = "rosalind(mock)"

    def __init__(self, latency_scale: float = 1.0) -> None:
        self.latency_scale = latency_scale
        self.calls: list[tuple[str, str]] = []

    async def _sleep(self, key: str, seed: str) -> None:
        if self.latency_scale <= 0:
            return
        jitter = 0.7 + 0.6 * stable_unit(key, seed)
        await asyncio.sleep(LATENCY[key] * jitter * self.latency_scale)

    # --- plan ------------------------------------------------------------

    async def plan(self, question: str, bundle: PatientBundle) -> Plan:
        self.calls.append(("plan", question))
        await self._sleep("plan", question)

        hypothesis = extract_hypothesis(question)
        tasks: list[SubTask] = []

        if bundle.variants:
            focus = mentioned_genes(question)
            focus_note = f" Prioritise {', '.join(focus)}." if focus else ""
            tasks.append(
                SubTask(
                    role="genomics",
                    task=f"Score the {len(bundle.variants)} uploaded variant(s) for "
                         f"functional effect and therapy relevance.{focus_note}",
                    rationale="A treatment failure with a molecular profile available is "
                              "first a question about the variants.",
                )
            )
        if bundle.labs or bundle.notes:
            tasks.append(
                SubTask(
                    role="clinical",
                    task="Reconstruct the treatment timeline and flag out-of-range "
                         "laboratory trends around each exposure.",
                    rationale="Timing separates a drug that did not work from a drug the "
                              "patient could not tolerate.",
                )
            )
        tasks.append(
            SubTask(
                role="literature",
                task="Retrieve supporting and contradicting evidence for the candidate "
                     "mechanisms the other specialists surface.",
                rationale="Contradicting evidence is the point; a search that can only "
                          "confirm is a search that cannot fail.",
            )
        )

        restated = question.strip().rstrip("?") + "?"
        notes = (
            f"Hypothesis under test: {hypothesis}. Evidence is scored for and against it."
            if hypothesis
            else "Open question: enumerate candidate causes, then test each against the "
                 "uploaded evidence."
        )
        return Plan(
            restated_question=restated,
            hypothesis=hypothesis,
            tasks=tasks,
            notes=notes,
        )

    # --- per-agent step --------------------------------------------------

    async def step(
        self, role: AgentRole, task: str, context: dict[str, Any]
    ) -> ReasoningStep:
        self.calls.append(("step", role))
        await self._sleep("step", f"{role}:{task}")
        if context.get("task_mode") == "idea_review":
            def excerpt(value: str, limit: int) -> str:
                value = " ".join(value.split())
                return value if len(value) <= limit else value[:limit].rsplit(" ", 1)[0] + "..."

            question = excerpt(context.get("question", "the proposal"), 180)
            prior = context.get("discussion", [])
            # Retain a visible connection to the previous turn without recursively
            # quoting the whole transcript in every mock response.
            reply = excerpt(prior[-1]["text"], 220) if prior else "No prior discussion."
            phase = context.get("phase")
            if phase == "opening":
                text = f"Proposal for '{question}': define a measurable target, a baseline and a small falsifiable comparison. Potential value is conditional on outperforming that baseline; feasibility is an assumption."
            elif phase == "challenge":
                text = f"Challenge to the preceding proposal ({reply}): the target, baseline quality and independent evaluation data have not been established. What result would refute the idea, and could leakage explain an apparent improvement?"
            elif phase == "revision":
                text = f"Revision responding to the challenge ({reply}): for '{question}', predefine the target and failure criterion, hold out evaluation inputs, and compare against a simple baseline before making a usefulness claim. These are proposed checks, not completed experiments."
            else:
                incomplete = [name for name, status in context.get("review_agent_statuses", {}).items() if status != "done"]
                status_note = ("Incomplete contributions: " + ", ".join(incomplete) + ". "
                               if incomplete else "The research, support and challenge turns are complete. ")
                text = (f"Review of '{question}': {len(prior)} contributions were considered. "
                        + status_note + "Next, define a measurable target and failure criterion, "
                        "hold out evaluation inputs, and compare against a simple baseline. "
                        "Proceed as a testable proposal; independent evidence is still needed before claiming scientific validity.")
            return ReasoningStep(message=text)
        handler = {
            "genomics": self._step_genomics,
            "clinical": self._step_clinical,
            "literature": self._step_literature,
            "stats": self._step_stats,
        }.get(role, self._step_generic)
        return handler(task, context)

    def _hypothesis_terms(self, context: dict[str, Any]) -> list[str]:
        return [term.upper() for term in mentioned_genes(context.get("hypothesis") or "")]

    def _stance(self, subject: str, positive: bool, context: dict[str, Any]) -> str:
        """Evidence only takes a side when it is about the thing the user named."""
        terms = self._hypothesis_terms(context)
        if not terms:
            return "neutral"
        if not any(term in subject.upper() for term in terms):
            return "neutral"
        return "supports" if positive else "contradicts"

    def _step_genomics(self, task: str, context: dict[str, Any]) -> ReasoningStep:
        scored: list[dict[str, Any]] = context.get("scored", [])
        if not scored:
            return ReasoningStep(message="No variants in the bundle to score.")

        ranked = sorted(scored, key=lambda s: s["pathogenicity"], reverse=True)
        headline = ranked[0]
        rest = "; ".join(f"{s['label']} {s['call']}" for s in ranked[1:4])
        message = (
            f"Scored {len(scored)} variant(s). Highest functional impact: "
            f"{headline['label']} ({headline['call']}, {headline['pathogenicity']:.2f})."
            + (f" Also: {rest}." if rest else "")
        )

        claims: list[ClaimDraft] = []
        for entry in ranked:
            positive = entry["pathogenicity"] >= 0.6
            stance = self._stance(entry["label"], positive, context)
            if not positive and stance == "neutral":
                continue  # low impact and nobody asked about it
            implication = entry.get("therapy_implication") or "no established action"
            claims.append(
                ClaimDraft(
                    claim=f"{entry['label']} scores {entry['call']} "
                          f"({entry['pathogenicity']:.2f}); therapy implication: "
                          f"{implication}.",
                    stance=stance,
                    confidence=round(
                        entry["pathogenicity"] if positive else 1.0 - entry["pathogenicity"], 2
                    ),
                    detail=entry,
                )
            )
        return ReasoningStep(message=message, claims=claims)

    def _step_clinical(self, task: str, context: dict[str, Any]) -> ReasoningStep:
        abnormal: list[dict[str, Any]] = context.get("abnormal_labs", [])
        trends: list[dict[str, Any]] = context.get("trends", [])
        timeline: list[dict[str, Any]] = context.get("timeline", [])

        parts: list[str] = []
        if abnormal:
            parts.append(
                f"{len(abnormal)} out-of-range value(s) including "
                + ", ".join(f"{a['name']} {a['value']} ({a['flag']})" for a in abnormal[:3])
            )
        if trends:
            parts.append(
                "; ".join(
                    f"{t['name']} {t['direction']} {t['first']} to {t['last']}"
                    for t in trends[:3]
                )
            )
        if timeline:
            parts.append(f"{len(timeline)} dated event(s) in the notes")
        message = "Clinical review: " + ("; ".join(parts) if parts else "nothing out of range.")

        claims: list[ClaimDraft] = []
        for trend in trends:
            if trend["direction"] != "rising":
                continue
            claims.append(
                ClaimDraft(
                    claim=f"{trend['name']} rose from {trend['first']} to {trend['last']} "
                          f"over the treatment window, a trajectory consistent with "
                          f"progression rather than response.",
                    stance="neutral",
                    confidence=0.72,
                    detail=trend,
                )
            )
        cytopenias = ("neutrophils", "platelets", "hemoglobin", "haemoglobin", "wbc")
        for lab in abnormal:
            if lab["flag"] != "low" or lab["name"].lower() not in cytopenias:
                continue
            claims.append(
                ClaimDraft(
                    claim=f"{lab['name']} {lab['value']} {lab.get('unit') or ''} is below "
                          f"the reference range ({lab.get('ref_low')}-{lab.get('ref_high')}), "
                          f"indicating haematological toxicity during treatment.".replace(
                              "  ", " "
                          ),
                    stance="neutral",
                    confidence=0.68,
                    detail=lab,
                )
            )
        if context.get("toxicity_terms"):
            terms = ", ".join(context["toxicity_terms"][:4])
            claims.append(
                ClaimDraft(
                    claim=f"The notes record toxicity ({terms}) early in treatment, which "
                          f"points at tolerability limiting dose intensity rather than at "
                          f"the regimen simply being ineffective.",
                    stance="neutral",
                    confidence=0.62,
                    detail={"terms": context["toxicity_terms"]},
                )
            )
        return ReasoningStep(message=message, claims=claims)

    def _step_literature(self, task: str, context: dict[str, Any]) -> ReasoningStep:
        hits: list[dict[str, Any]] = context.get("hits", [])
        query = context.get("query", "")
        if not hits:
            return ReasoningStep(
                message=f"No corpus document passed the relevance threshold for '{query}'."
            )
        message = (
            f"Retrieved {len(hits)} document(s) for '{query}'. Top: "
            + "; ".join(f"PMID {h['pmid']} ({h['score']:.2f})" for h in hits[:3])
        )

        negative_tags = ("negative", "no association", "replication failure", "not predictive")
        claims: list[ClaimDraft] = []
        for hit in hits:
            tags = [t.lower() for t in hit.get("tags", [])]
            is_negative = any(t in tags for t in negative_tags)
            subject = hit.get("title", "") + " " + " ".join(hit.get("tags", []))
            excerpt = hit["text"][:220].rstrip()
            claims.append(
                ClaimDraft(
                    claim=f"{hit['title']} (PMID {hit['pmid']}, {hit['journal']} "
                          f"{hit['year']}): {excerpt}...",
                    stance=self._stance(subject, not is_negative, context),
                    confidence=round(min(0.9, 0.45 + hit["score"]), 2),
                    detail=hit,
                )
            )
        return ReasoningStep(message=message, claims=claims)

    def _step_stats(self, task: str, context: dict[str, Any]) -> ReasoningStep:
        return ReasoningStep(
            message="Cohort comparison skipped: a single patient bundle was uploaded."
        )

    def _step_generic(self, task: str, context: dict[str, Any]) -> ReasoningStep:
        return ReasoningStep(message=f"Completed: {task}")

    # --- synthesis -------------------------------------------------------

    async def synthesize(
        self, question: str, claims: list[dict[str, Any]], context: dict[str, Any]
    ) -> SynthesisResult:
        self.calls.append(("synthesize", question))
        await self._sleep("synthesize", question)

        hypothesis = context.get("hypothesis")
        supporting = [c for c in claims if c["stance"] == "supports"]
        contradicting = [c for c in claims if c["stance"] == "contradicts"]
        neutral = [c for c in claims if c["stance"] == "neutral"]

        def weight(items: list[dict[str, Any]]) -> float:
            return round(sum(c["confidence"] for c in items), 3)

        support_w, contra_w = weight(supporting), weight(contradicting)
        strongest = max(claims, key=lambda c: c["confidence"]) if claims else None

        caveats = [
            "Single patient, no cohort comparison: associations here are not causal.",
            "Evidence is limited to the uploaded files and the bundled corpus subset.",
        ]

        if hypothesis:
            if contra_w > support_w:
                answer = (
                    f"The evidence does not support the proposed cause ({hypothesis}); "
                    f"the stronger signal points elsewhere."
                )
            elif support_w > contra_w:
                answer = f"The evidence is consistent with the proposed cause ({hypothesis})."
            else:
                answer = (
                    f"The evidence is balanced on the proposed cause ({hypothesis}) and "
                    f"does not settle it."
                )
            rationale = (
                f"{len(supporting)} supporting claim(s) (weight {support_w}) against "
                f"{len(contradicting)} contradicting claim(s) (weight {contra_w}), plus "
                f"{len(neutral)} contextual finding(s)."
            )
            total = support_w + contra_w
            # Separation says which way the evidence leans; saturation stops a
            # single one-sided claim from reading as certainty.
            separation = abs(support_w - contra_w) / total if total else 0.0
            saturation = min(1.0, total / EVIDENCE_SATURATION)
            confidence = round(min(0.95, separation * saturation), 2)
        else:
            lead = strongest["claim"] if strongest else "no claim was produced"
            answer = f"Most likely account of the failure: {lead}"
            rationale = (
                f"Ranked {len(claims)} claim(s) from the specialists by per-claim "
                f"confidence, with cross-agent agreement as the tie-breaker."
            )
            roles = {c.get("agent_role") for c in claims}
            ceiling = 0.7 if len(roles) < 2 else 0.9   # one voice is not a consensus
            confidence = round(min(ceiling, strongest["confidence"]), 2) if strongest else 0.0

        return SynthesisResult(
            answer=answer,
            rationale=rationale,
            confidence=confidence,
            # Abstention is not the model's call: the critic's evidence gate decides,
            # so the rule survives swapping this provider for a live one.
            abstained=False,
            caveats=caveats,
        )
