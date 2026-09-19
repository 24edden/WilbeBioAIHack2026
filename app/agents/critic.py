"""Critic / synthesis agent — and the abstention gate.

This is the part of the system worth defending. Everything upstream produces
claims; this agent decides whether the claims add up to an answer, and says so
out loud when they do not.

The gate is deterministic and enforced when the reasoning provider's synthesis
is turned into a verdict. A model asked "are you confident?" may say yes, so the
abstention decision is taken away from it: the rules below look at how many
specialist roles contributed, whether the strongest evidence clears a floor,
and whether support and contradiction cancel out. Role diversity does not prove
independent evidence: two agents may cite the same source. Swapping the mock provider
for a live one cannot weaken it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agents.base import Agent
from app.models import Finding, Provenance, Verdict

MIN_TOP_CONFIDENCE = 0.55   # strongest single piece of evidence must clear this
MIN_CORROBORATION = 0.35    # minimum confidence from a second specialist role
BALANCE_MARGIN = 0.15       # support vs contradiction must separate by this much


@dataclass
class GateResult:
    abstain: bool
    reason: str | None = None
    checks: list[dict[str, Any]] = field(default_factory=list)
    disagreement: bool = False


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": passed, "detail": detail}


def evidence_gate(findings: list[Finding], hypothesis: str | None) -> GateResult:
    """Decide whether the evidence is thick enough to answer at all."""
    checks: list[dict[str, Any]] = []

    if not findings:
        return GateResult(
            abstain=True,
            reason="No specialist produced a finding, so there is nothing to answer from.",
            checks=[_check("any_evidence", False, "0 findings")],
        )
    checks.append(_check("any_evidence", True, f"{len(findings)} finding(s)"))

    cited = [f for f in findings if f.provenance]
    checks.append(
        _check(
            "provenance",
            bool(cited),
            f"{len(cited)}/{len(findings)} finding(s) cite a source",
        )
    )
    if not cited:
        return GateResult(
            abstain=True,
            reason="No finding cites a source; an uncited claim is not evidence.",
            checks=checks,
        )

    top = max(cited, key=lambda f: f.confidence)
    top_ok = top.confidence >= MIN_TOP_CONFIDENCE
    checks.append(
        _check(
            "confidence_floor",
            top_ok,
            f"strongest cited finding is {top.confidence:.2f} "
            f"(floor {MIN_TOP_CONFIDENCE:.2f})",
        )
    )
    if not top_ok:
        return GateResult(
            abstain=True,
            reason=(
                f"The strongest piece of evidence scores {top.confidence:.2f}, below the "
                f"{MIN_TOP_CONFIDENCE:.2f} floor. The honest answer is that the uploaded "
                f"data does not settle this."
            ),
            checks=checks,
        )

    roles = {f.agent_role for f in cited if f.confidence >= MIN_CORROBORATION}
    corroborated = len(roles) > 1
    checks.append(
        _check(
            "corroboration",
            corroborated,
            f"{len(roles)} specialist role(s) contributed: {sorted(roles)}",
        )
    )

    supporting = [f for f in cited if f.stance == "supports"]
    contradicting = [f for f in cited if f.stance == "contradicts"]
    support_w = round(sum(f.confidence for f in supporting), 3)
    contra_w = round(sum(f.confidence for f in contradicting), 3)
    disagreement = bool(supporting and contradicting)

    if hypothesis:
        total = support_w + contra_w
        separation = abs(support_w - contra_w) / total if total else 0.0
        decisive = total > 0 and separation >= BALANCE_MARGIN
        checks.append(
            _check(
                "hypothesis_separation",
                decisive,
                f"support {support_w} vs contradiction {contra_w} "
                f"(separation {separation:.2f}, needs {BALANCE_MARGIN:.2f})",
            )
        )
        if not decisive:
            return GateResult(
                abstain=True,
                reason=(
                    "Support and contradiction for the proposed cause are too evenly "
                    "matched to call one way or the other."
                    if total
                    else "No evidence bears on the proposed cause either way."
                ),
                checks=checks,
                disagreement=disagreement,
            )
        relevant = supporting + contradicting
        if max(f.confidence for f in relevant) < MIN_TOP_CONFIDENCE:
            return GateResult(
                abstain=True,
                reason="Evidence bearing on the proposed cause is below the confidence floor.",
                checks=checks + [_check("hypothesis_confidence", False, "Only weak relevant evidence")],
                disagreement=disagreement,
            )

    if not corroborated:
        return GateResult(
            abstain=True,
            reason="The findings lack corroboration from a second specialist; one voice is not a consensus.",
            checks=checks,
            disagreement=disagreement,
        )
    return GateResult(abstain=False, checks=checks, disagreement=disagreement)


class CriticAgent(Agent):
    role = "critic"

    async def investigate(self) -> None:  # pragma: no cover - `synthesize` is the entry
        await self.synthesize()

    async def synthesize(self) -> Verdict:
        findings = self.ctx.blackboard.all()
        roles = sorted({f.agent_role for f in findings})
        self.say(
            f"Cross-checking {len(findings)} finding(s) from {len(roles)} specialist(s): "
            f"{', '.join(roles) or 'none'}."
        )

        # Tell each specialist what was taken from it. These messages are what
        # draws the return edges in the graph, and they are how a viewer sees
        # which agent actually carried the verdict.
        for role in roles:
            role_findings = [f for f in findings if f.agent_role == role]
            strongest = max(role_findings, key=lambda f: f.confidence)
            self.say(
                f"Accepted {len(role_findings)} finding(s); strongest at "
                f"{strongest.confidence:.2f}.",
                to=strongest.agent_id,
            )

        self.tool_call("critic.evidence_gate", n_findings=len(findings))
        gate = evidence_gate(findings, self.ctx.hypothesis)
        self.tool_result(
            "critic.evidence_gate",
            {"abstain": gate.abstain, "checks": gate.checks},
            disagreement=gate.disagreement,
        )

        if gate.disagreement:
            self.say(
                "Specialists disagree: the findings include both supporting and "
                "contradicting evidence for the proposed cause."
            )

        synthesis = await self.ctx.providers.reasoning.synthesize(
            self.ctx.question,
            [
                {
                    "agent_role": f.agent_role,
                    "claim": f.claim,
                    "stance": f.stance,
                    "confidence": f.confidence,
                    "provenance": [p.model_dump() for p in f.provenance],
                }
                for f in findings if f.provenance
            ],
            {
                "hypothesis": self.ctx.hypothesis,
                "gate": {"abstain": gate.abstain, "checks": gate.checks},
                "bundle": self.ctx.bundle.summary(),
            },
        )

        caveats = list(synthesis.caveats)
        if gate.disagreement:
            caveats.append("Specialists disagreed; see the contradicting findings.")
        if self.ctx.providers.mode == "mock":
            caveats.insert(0, "Mock mode: model outputs are fixtures, not predictions.")

        if gate.abstain or synthesis.abstained:
            reason = gate.reason or synthesis.abstain_reason or "The reasoning provider declined to draw a conclusion."
            verdict = Verdict(
                answer=f"ABSTAIN: {reason}",
                rationale=(
                    f"The synthesis offered was: {synthesis.answer} It is withheld because "
                    f"{reason} {synthesis.rationale}"
                ),
                confidence=min(synthesis.confidence, 0.3),
                abstained=True,
                abstain_reason=reason,
                caveats=caveats,
            )
        else:
            verdict = Verdict(
                answer=synthesis.answer,
                rationale=synthesis.rationale,
                confidence=synthesis.confidence,
                abstained=False,
                caveats=caveats,
            )

        self.record(
            verdict.answer,
            confidence=verdict.confidence,
            provenance=[
                Provenance(
                    kind="derived",
                    ref="critic.evidence_gate",
                    locator=f"{len(findings)} finding(s) from {len(roles)} specialist(s)",
                )
            ],
            stance="neutral",
            detail={
                "abstained": verdict.abstained,
                "abstain_reason": verdict.abstain_reason,
                "checks": gate.checks,
            },
        )
        return verdict
