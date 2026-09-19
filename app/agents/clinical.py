"""Clinical specialist — labs, notes and the treatment timeline.

The tools here are deterministic: flagging out-of-range values, computing a
per-analyte trend, and pulling dated events out of free text. The model is only
asked to interpret what those tools returned, which keeps every clinical claim
traceable back to a line of an uploaded file.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.base import Agent
from app.agents.genomics import source_filename
from app.models import LabResult, Provenance

TOXICITY_TERMS = (
    "neutropenia", "thrombocytopenia", "anaemia", "anemia", "mucositis",
    "diarrhoea", "diarrhea", "toxicity", "dose reduction", "dose-reduction",
    "grade 3", "grade 4", "hospitalisation", "hospitalization", "g-csf",
)
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
TREND_TOLERANCE = 0.2  # relative change below this is called stable


def flag_abnormal(labs: list[LabResult]) -> list[dict[str, Any]]:
    return [
        {
            "name": lab.name,
            "value": lab.value,
            "unit": lab.unit,
            "flag": lab.flag,
            "date": lab.date,
            "ref_low": lab.ref_low,
            "ref_high": lab.ref_high,
            "source_line": lab.source_line,
        }
        for lab in labs
        if lab.flag in ("high", "low")
    ]


def compute_trends(labs: list[LabResult]) -> list[dict[str, Any]]:
    """First-to-last direction per analyte, for analytes measured more than once."""
    series: dict[str, list[LabResult]] = {}
    for lab in labs:
        if lab.value is None:
            continue
        series.setdefault(lab.name, []).append(lab)

    trends: list[dict[str, Any]] = []
    for name, values in series.items():
        if len(values) < 2:
            continue
        ordered = sorted(values, key=lambda lab: (lab.date or "", lab.source_line or 0))
        first, last = ordered[0], ordered[-1]
        if first.value in (None, 0):
            change = 1.0 if last.value else 0.0
        else:
            change = (last.value - first.value) / abs(first.value)
        direction = "stable"
        if change > TREND_TOLERANCE:
            direction = "rising"
        elif change < -TREND_TOLERANCE:
            direction = "falling"
        trends.append(
            {
                "name": name,
                "direction": direction,
                "first": first.value,
                "last": last.value,
                "first_date": first.date,
                "last_date": last.date,
                "relative_change": round(change, 3),
                "n_points": len(ordered),
                "source_lines": [lab.source_line for lab in ordered],
            }
        )
    return sorted(trends, key=lambda t: abs(t["relative_change"]), reverse=True)


def extract_timeline(notes_text: str) -> list[dict[str, Any]]:
    """Dated lines from the notes, in document order."""
    events: list[dict[str, Any]] = []
    for lineno, line in enumerate(notes_text.splitlines(), start=1):
        for match in DATE_RE.finditer(line):
            events.append({"date": match.group(1), "text": line.strip(), "line": lineno})
            break
    return sorted(events, key=lambda e: e["date"])


def find_toxicity_terms(notes_text: str) -> list[dict[str, Any]]:
    lowered = notes_text.lower()
    hits: list[dict[str, Any]] = []
    for term in TOXICITY_TERMS:
        index = lowered.find(term)
        if index == -1:
            continue
        line = lowered.count("\n", 0, index) + 1
        hits.append({"term": term, "line": line})
    return hits


class ClinicalAgent(Agent):
    role = "clinical"

    async def investigate(self) -> None:
        bundle = self.ctx.bundle
        if not bundle.labs and not bundle.notes:
            self.say("No labs or notes in the bundle; nothing to review.")
            return

        labs_file = source_filename(bundle, "labs")
        notes_file = source_filename(bundle, "notes")

        self.tool_call("labs.flag_out_of_range", n_labs=len(bundle.labs))
        abnormal = flag_abnormal(bundle.labs)
        self.tool_result("labs.flag_out_of_range", {"n_abnormal": len(abnormal)})

        self.tool_call("labs.trend", analytes=sorted({lab.name for lab in bundle.labs}))
        trends = compute_trends(bundle.labs)
        self.tool_result(
            "labs.trend",
            {t["name"]: t["direction"] for t in trends},
        )

        notes_text = bundle.notes_text()
        self.tool_call("notes.timeline", n_sections=len(bundle.notes))
        timeline = extract_timeline(notes_text)
        toxicity = find_toxicity_terms(notes_text)
        self.tool_result(
            "notes.timeline",
            {"n_events": len(timeline), "toxicity_terms": [t["term"] for t in toxicity]},
        )

        step = await self.ctx.providers.reasoning.step(
            "clinical",
            self.task,
            {
                "abnormal_labs": abnormal,
                "trends": trends,
                "timeline": timeline,
                "toxicity_terms": [t["term"] for t in toxicity],
                "hypothesis": self.ctx.hypothesis,
                "question": self.ctx.question,
            },
        )
        if step.message:
            self.say(step.message)

        toxicity_lines = {t["term"]: t["line"] for t in toxicity}
        for claim in step.claims:
            detail = claim.detail or {}
            provenance: list[Provenance] = []
            lines = detail.get("source_lines") or (
                [detail["source_line"]] if detail.get("source_line") else []
            )
            for line in lines:
                provenance.append(
                    Provenance(
                        kind="file",
                        ref=labs_file,
                        locator=f"line {line}",
                        quote=detail.get("name"),
                    )
                )
            for term in detail.get("terms", []):
                provenance.append(
                    Provenance(
                        kind="file",
                        ref=notes_file,
                        locator=f"line {toxicity_lines.get(term, '?')}",
                        quote=term,
                    )
                )
            if not provenance:
                provenance.append(
                    Provenance(kind="derived", ref=notes_file, locator="clinical review")
                )
            self.record(
                claim.claim,
                confidence=claim.confidence,
                provenance=provenance,
                stance=claim.stance,
                detail=detail,
            )
