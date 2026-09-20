"""Stats specialist — deterministic cohort comparison.

Only spawned when more than one patient bundle is uploaded, which the current
UI does not do. Kept small and honest: it computes a rate, it does not model.
With one patient it says so and produces no finding, which is the correct
behaviour for a system whose selling point is knowing when it cannot answer.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.models import PatientBundle, Provenance


def carrier_rate(cohort: list[PatientBundle], gene: str) -> tuple[int, int]:
    """(carriers, total) for a gene across the cohort."""
    carriers = sum(
        1 for bundle in cohort if any(v.gene == gene for v in bundle.variants)
    )
    return carriers, len(cohort)


class StatsAgent(Agent):
    role = "stats"

    async def investigate(self) -> None:
        cohort: list[PatientBundle] = self.ctx.extras.get("cohort", [])
        if len(cohort) < 2:
            self.say("Single patient bundle: no cohort to compare against, skipping.")
            return

        genes = sorted({v.gene for b in cohort for v in b.variants if v.gene})
        self.tool_call("stats.carrier_rate", genes=genes, n_patients=len(cohort))
        rates = {gene: carrier_rate(cohort, gene) for gene in genes}
        self.tool_result(
            "stats.carrier_rate",
            {gene: f"{c}/{n}" for gene, (c, n) in rates.items()},
        )

        for gene, (carriers, total) in rates.items():
            if carriers < 2:
                continue
            self.record(
                f"{gene} is carried by {carriers} of {total} patients in the uploaded "
                f"cohort ({carriers / total:.0%}).",
                confidence=0.5,
                provenance=[
                    Provenance(
                        kind="derived",
                        ref="stats.carrier_rate",
                        locator=f"{total} bundles",
                    )
                ],
                detail={"gene": gene, "carriers": carriers, "total": total},
            )
