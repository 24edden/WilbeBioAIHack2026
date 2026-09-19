"""Bounded audit of a run's recorded evidence, not a new model/scientific judgment."""

from app.events import Event
from app.models import Finding, PatientBundle, Report, WeakPoint, WeakPointAssessment


def assess_weak_points(report: Report, bundle: PatientBundle, events: list[Event],
                       hypothesis: str | None = None) -> WeakPointAssessment:
    findings = [finding for finding in report.findings if finding.agent_role != "critic"]
    items = []

    def add(identifier, category, title, rationale, next_evidence, linked=()):
        sources = {}
        for finding in linked:
            for source in finding.provenance:
                sources[(source.kind, source.ref, source.locator, source.quote)] = source
        items.append(WeakPoint(id=identifier, category=category, title=title,
            rationale=rationale, next_evidence=next_evidence,
            finding_ids=list(dict.fromkeys(finding.finding_id for finding in linked)),
            sources=list(sources.values())))

    idea_review = report.config.get("task_mode") == "idea_review"
    if idea_review:
        add("proposal-not-validated", "scope_limit", "Ideas are not scientific evidence",
            "The discussion develops and challenges a proposal. Its arguments, assumptions and input inventory have not been independently validated; disagreement between review roles is not conflicting research.",
            "Define a falsifiable test, obtain relevant independent sources and evaluate against a baseline before drawing a scientific conclusion.")
    if bundle.is_empty and not idea_review:
        add("empty-input", "evidence_gap", "No parsed input evidence",
            "The uploaded bundle contains no parsed variants, laboratory records or note sections.",
            "Provide relevant source files and verify that their records parse before rerunning.")
    if report.status == "cancelled":
        add("cancelled-investigation", "scope_limit", "The investigation was stopped early",
            "Execution was cancelled. The findings retained here are partial; missing outputs are not negative evidence.",
            "Resume the research with a new investigation if the remaining evidence is still needed.", findings)
    if not findings and not idea_review:
        add("no-findings", "evidence_gap", "No specialist findings",
            "No specialist produced a finding available to this assessment.",
            "Inspect input coverage and agent errors, then supply evidence relevant to the question.")
    elif findings and len({finding.agent_role for finding in findings if finding.provenance}) < 2:
        add("limited-corroboration", "evidence_gap", "Limited specialist corroboration",
            "Fewer than two specialist roles contributed cited findings. Role diversity alone would not establish independent evidence.",
            "Seek an independent source addressing the claim and review it with an appropriate additional specialist.", findings)

    supports = [finding for finding in findings if finding.stance == "supports"]
    contradicts = [finding for finding in findings if finding.stance == "contradicts"]
    if hypothesis and supports and contradicts:
        add("hypothesis-conflict", "conflicting_findings", "Findings point in different directions",
            f"For the proposed cause ({hypothesis}), {len(supports)} finding(s) support it and {len(contradicts)} contradict it. This is a conflict between recorded findings, not a verified conflict between independent studies.",
            "Compare the linked evidence, context and source reuse; identify an observation that distinguishes the competing explanations.",
            [*supports, *contradicts])
    elif hypothesis and not supports and not contradicts and not idea_review:
        add("hypothesis-unaddressed", "evidence_gap", "The proposed cause lacks direct evidence",
            f"No recorded specialist finding supports or contradicts the proposed cause ({hypothesis}).",
            "Supply a source that directly addresses the proposed mechanism or narrow the question.", findings)

    known_files = {file.filename for file in bundle.files}
    known_pmids = set()
    known_outputs = set()
    for event in events:
        if event.type != "tool_result":
            continue
        if event.payload.get("output_id"):
            known_outputs.add(str(event.payload["output_id"]))
        if event.payload.get("tool") == "bionemo.embed" and isinstance(event.payload.get("result"), list):
            known_pmids.update(str(item["pmid"]) for item in event.payload["result"]
                               if isinstance(item, dict) and item.get("pmid"))

    def unresolved(finding: Finding) -> bool:
        if not finding.provenance:
            return True
        for source in finding.provenance:
            if not source.ref.strip() or source.ref.lower() == "unknown":
                return True
            known = {"file": known_files, "pmid": known_pmids, "nim": known_outputs}.get(source.kind)
            if known is not None and source.ref not in known:
                return True
        return False

    unsupported_sources = [finding for finding in findings if unresolved(finding)]
    if unsupported_sources:
        add("unresolved-sources", "source_gap", "Some source references cannot be resolved",
            "The linked findings have no citation or cite a file, retrieved PMID or tool-output identifier absent from this run. This identifier check does not establish whether a source supports its claim.",
            "Locate the original source or tool result, correct the reference, and check the supporting passage before relying on the claim.",
            unsupported_sources)

    errors = [event for event in events if event.type == "error"]
    if errors:
        affected = sorted({event.agent_id for event in errors})
        add("agent-errors", "provider_failure", "Agent or tool failures limited the investigation",
            f"The run recorded {len(errors)} error event(s), affecting {', '.join(affected)}. A completed report does not erase these failures; inspect the event log for details.",
            "Resolve the recorded input, provider or tool error and rerun the affected investigation before treating missing outputs as negative evidence.",
            [finding for finding in findings if finding.agent_id in affected])

    if report.verdict and report.verdict.abstained:
        add("withheld-conclusion", "evidence_gap", "The conclusion was withheld",
            report.verdict.abstain_reason or "The critic declined to draw a conclusion from this run.",
            "Review the stated evidence gap and gather a source that addresses it before seeking a stronger conclusion.", findings)
    if report.run_mode == "mock":
        add("simulated-models", "scope_limit", "Model outputs are simulated",
            "This run used mock providers. The workflow executed, but its model outputs are fixtures rather than measured predictions.",
            "Validate the same inputs with configured live providers and independently check the resulting claims.")
    causal_caveats = [caveat for caveat in report.verdict.caveats if "not causal" in caveat.lower()] if report.verdict else []
    if causal_caveats:
        add("causal-limitation", "scope_limit", "Associations do not establish the cause",
            "Report caveat: " + " ".join(causal_caveats),
            "State the assumptions and seek evidence that distinguishes the proposed mechanism from alternatives.", findings)

    return WeakPointAssessment(status="assessed", items=items)
