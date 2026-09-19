# Product requirements

Version 0.3 · Proposed implementation · 19 September 2026

## Product and problem

**Rosalind Investigation** helps a translational scientist move from a treatment failure or a functional assay question to a defensible interpretation, a testable therapy-design proposal and the next experiment. The current project already has source data, case narratives, proposed specialist roles, and a deterministic tool scaffold. It lacks the application that connects those assets into a resumable scientific investigation and carries the findings back into R&D.

**The product closes an explicit R&D feedback loop:** user-supplied hypothesis + available evidence → investigation → design objective → BioNeMo prediction → candidate/test package → measured result → updated assessment and proposed next design. CAR-T is the concrete example: use BioNeMo to predict candidate antigen-binding-domain/target structures and compare them with a reference design, then return a qualified shortlist and experiment plan to the research team. Improvement remains a hypothesis until measured. See the [full process and deliverable contract](07-RD-FEEDBACK-LOOP.md).

The product must answer: what was measured, which explanations remain plausible, what contradicts each explanation, what calculation or model result actually changed the interpretation, and which next observation would distinguish the alternatives?

The first release serves research interpretation. It does not prescribe treatment, prove a mechanism from a prediction, run laboratory experiments, or make a prospective diagnostic-performance claim.

## Hypothesis supplied by the user

Every investigation starts with a hypothesis the user supplies or explicitly selects. Accepted inputs include a chat message, pasted prompt, user-selected `.md` or text file, structured case brief, or several of these together. The [input template](contracts/hypothesis-template.md) is optional; free text is sufficient to state the hypothesis.

Preserve the original wording, source message/file, source version or hash, and relevant file section. Extract a concise investigation statement, scope, comparison and success/disconfirmation criteria when provided. Display the original hypothesis alongside the interpretation used by the agent. Missing analysis inputs become readiness requirements; they do not authorize inventing a different hypothesis.

The agent may refine wording without changing meaning, generate testable subquestions, compare alternatives and challenge the hypothesis using evidence. Label these as agent-derived and link them to the supplied hypothesis. A supplied hypothesis is a proposition to test, not accepted evidence. Changes to the user's research objective must come from a new user instruction or selection; ordinary evidence-based revision of its assessment proceeds within the existing scope.

If no hypothesis is supplied, or conflicting inputs leave the intended objective unclear, ask a focused clarification before launching dependent investigation. A clearly stated current user instruction can amend an earlier file; preserve both versions and the amendment. Selecting one of the example case hypotheses is also valid intake. The ALK/BCMA/CAR-T examples do not automatically determine every user's question.

## Users and jobs

| User | Job | Required outcome |
| --- | --- | --- |
| Translational scientist | Investigate a defined phenotype | Evidence matrix, alternatives, uncertainty, next experiment |
| Bioinformatician | Establish that analysis inputs are valid | Exact input versions, sample joins, QC, exclusions, reproducible outputs |
| Reviewing scientist | Correct a misleading claim | Feedback attached to a decision version; visible corrected version |
| Therapy-design R&D scientist | Turn a failure hypothesis into a candidate and test the improvement | Baseline/candidate structures, evidence-linked design rationale, controls, assay endpoints and a route to return measurements |
| Engineer | Reproduce and debug a run | Run manifest, typed events, tool requests/results, hashes, failure states, replay |
| Hackathon judge | Understand a working contribution | Five-minute trace from real data through meaningful OpenAI/NVIDIA use to a qualified result |

## Scientific scope and case order

### Release 0: ALK L1196M

**Question:** does the functional atlas support a drug-specific phenotype for L1196M, and which observations support or limit an interaction-based mechanism?

Use the local/Brev ALK atlas workbook and supplementary assay descriptions. The current case document identifies `Table S2`, source row 1331, and nucleotide/construct key `ALK_E23_C70A`. Implement a lookup by the source key and assert the amino-acid label; use the row as provenance, not a fragile row-number-only join.

The core output is a drug-by-endpoint table with exact source cells, a distinction between measured phenotype and proposed mechanism, counterexplanations, and one orthogonal experiment. If molecular inputs are qualified, compare matched WT/mutant ALK–alectinib predictions with Boltz-2. The predicted structural result can change a mechanistic hypothesis or experiment choice; it cannot overwrite the measured drug-response result.

Preserve the reported Table S5 concentration-header versus supplementary-legend discrepancy. Quantitative exposure claims remain blocked until resolved. Do not invent a patient ID for this functional-assay case.

### Release 1: prepared BCMA case

Reuse `/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19/input/`. The package already records eight longitudinal RNA samples, a post-retreatment mutation table and full allele counts. The investigator receives only the approved input files; the reviewer receives the reference interpretation separately.

Expected behavior includes recognizing the depleted baseline, using the corrected S5/S6 mapping, preserving post-treatment DNA timing, and asking for appropriate copy-number/protein evidence. The current missense protein-pair Boltz adapter is not appropriate for a truncating BCMA variant. An explicit decision to skip an irrelevant model is a successful routing outcome.

The R&D output must follow the mechanism. If antigen loss is supported, a better binder to the absent antigen is not a rescue claim; return an antigen-selection or multi-target research hypothesis and the measurements needed to qualify it. Demonstrate a binder structural comparison only in a separate, qualified target-retained scenario with an identified reference and candidate. Do not relabel that scenario as an observed finding in this BCMA patient.

### Release 2: Maynard TH266

Use the two biopsies LT_S75 and LT_S81 after verifying the expression object and cell mapping. This is **one patient's pretreatment-to-residual-disease comparison**, not progression and not an independently replicated patient cohort. Baseline day is missing; on-treatment RD is day 14.

Compare tumor-state and composition explanations using descriptive, prespecified analyses. Keep genetic selection, exposure and technical effects open where measurements are missing. This case has no established hidden mechanistic answer in the current project. It tests useful uncertainty and experiment choice.

### Other project ideas

The early `Plan/` candidates remain a portfolio, not simultaneous release requirements. Variant triage contributes the molecular analysis branch; failure benchmarking contributes evaluation cases; negative-result mining becomes explicit counterevidence; the tool registry becomes infrastructure. A bounded binder comparison belongs to the core R&D feedback process. Large de novo binder campaigns, protocol compilation, broad assay QC, survival analysis and raw-read processing remain later extensions.

## User journey

1. Supply or select the hypothesis via message, prompt, Markdown/text file or structured brief; attach the relevant case data and select live, recorded replay, or synthetic demonstration mode. Show the model and available compute capabilities.
2. Inspect the supplied hypothesis, its source and the agent's interpreted scope, followed by a readiness card: files found, versions, missing fields, sample identity, analysis scale, and scientific limitations. Clarify material ambiguity before dependent work.
3. Start the investigation. Show progress as understandable actions: qualifying sources, extracting measurements, testing an explanation, reviewing contradictions.
4. Open a claim to see its exact measurement/result, source locator, tool version, and artifact. Large arrays remain downloadable artifacts.
5. Read the decision: supported scope, unresolved alternatives, contrary evidence, and the next experiment with expected positive, negative and inconclusive outcomes.
6. Submit a correction to a specific claim or decision. Preserve v1, create v2, and show what changed and why.
7. Open the R&D handoff: select an evidence-linked design objective, inspect reference/candidate structures when eligible, and review a comparison table and experiment plan. Missing inputs produce a specific modeling block, not invented designs or scores.
8. Export the decision, evidence, R&D package and run manifest. A replay reconstructs the displayed result from pinned artifacts.
9. R&D returns measured outcomes against the exact candidate and experiment IDs. Qualify the new data, retain negative and inconclusive findings, and issue a new case/design version showing what changed and why.

## Functional requirements

| ID | Priority | Requirement | Acceptance |
| --- | --- | --- | --- |
| R01 | P0 | User-supplied hypothesis and versioned case intake | Message/prompt/file hypothesis and provenance are pinned; interpretation preserves scope; missing/ambiguous objective is clarified; changed data bytes or wrong sample identity block dependent analysis |
| R02 | P0 | Source-backed data access | Every extracted quantity has file hash plus table/cell/row/column locator |
| R03 | P0 | GPT-Rosalind reasoning through OpenAI SDK | Actual returned model identity recorded; real tool round trip succeeds before capability is enabled |
| R04 | P0 | Competing hypotheses | Supplied hypothesis remains identifiable; agent-derived alternatives/subquestions are labeled; relevant counterevidence/unknowns retained; no silent objective replacement or majority-vote truth claim |
| R05 | P0 | Deterministic numerical tools | Reported values reproduce from accepted inputs; LLM does not calculate assay statistics in prose |
| R06 | P0 | Meaningful BioNeMo integration | A qualified molecular question produces a validated real NIM result and an evidence-linked interpretation, or an accurately reported block |
| R07 | P0 | Durable execution | Restart resumes known work; uncertain external submission is reconciled rather than blindly repeated |
| R08 | P0 | Evidence-linked decision | Every consequential empirical claim resolves to accepted evidence; inference is identified as inference |
| R09 | P0 | Scientist correction | Feedback is idempotent, survives restart and creates a new immutable decision version |
| R10 | P0 | Reproducible display/export | Decision, evidence and manifest exports match the UI; replay makes no hidden inference call |
| R11 | P0 | Bounded operation | Global token/tool/time limits include reviewer and specialist work; cancellation stops new submissions |
| R12 | P1 | Modular specialists | Separate bioinformatics, quantitative, clinical and molecular briefs with bounded ownership and one challenge round |
| R13 | P1 | BCMA and TH266 case packs | Case-specific gates and interpretation limits survive the shared runtime |
| R14 | P2 | Scoped procedural memory | Reviewed lessons are evaluated before activation; release versions, exclusions and rollback are supported |
| R15 | P1 | R&D experiment outcomes | Measurements resolve to an exact candidate/design brief and experiment; QC precedes interpretation; a new version revises the case without overwriting predictions |
| R16 | P0 | Explicit R&D design handoff | Export a design objective tied to evidence, reference design or missing-input block, candidate/test plan, expected discriminating outcomes and return-data requirements |
| R17 | P1 | BioNeMo CAR-T structural comparison | Qualified reference and candidate binding domains are modeled against the same target; structures, controls, returned metrics and limitations reach the R&D package; no whole-cell efficacy claim |

P0 application mechanics can be demonstrated in replay if access is unavailable. **R03 and R06 are not satisfied by synthetic fixtures or an unlabeled substitute model.** Track infrastructure readiness, scientific readiness and demonstration mode separately.

## Scope controls

The initial UI is a small FastAPI-served application with a case list, run timeline, evidence table, decision page, R&D handoff and correction form. P1 adds candidate comparison and experimental-outcome intake to that handoff. Use server-rendered pages plus server-sent events. A 3D structure viewer can be linked later; a structure screenshot alone does not count as quantitative evidence.

No Kubernetes, message broker, vector database, GPU model training, broad autonomous shell access, or automatic laboratory execution is required. A read-only subset of the existing biotech graph supplies process contracts. Operational evidence lives in the application database. The model cannot activate its own cross-case memory.

The published archive is not an isolated blinded benchmark. Do not expose the project planning documents, answer-bearing source titles, evaluation notes or expected labels to a supposedly blinded investigator. Open-book source adjudication is an explicit alternative mode.

## Nonfunctional targets

These are engineering targets to measure, not observed performance:

- Local replay should finish within 60 seconds for the selected compact case.
- A normal live case has a 15-minute application deadline; external jobs are surfaced as pending if they outlast it.
- First visible progress event within two seconds of accepted start; events include monotonic sequence IDs for reconnect.
- One active investigation and one heavy CPU analysis on the current Brev host. Reserve headroom for the team's other work.
- No raw matrix, credential, or unrestricted filesystem path in model context. Default tool summaries are bounded to approximately 2,000 tokens.
- An accepted claim must resolve to a valid evidence ID and artifact/source locator. Exact numerical comparisons use stored numerical results.
- All failures and manual intervention appear in the run export. An unresolved scientific result is distinct from failed execution.

## Demonstration and release criteria

Show ALK source qualification, one extracted drug-specific result, a justified NIM action, a challenged interpretation, a scientist correction and replay. Explain what the model result contributed and what it could not establish.

The R&D milestone must additionally show a CAR-T design brief, an eligible baseline/candidate structural comparison, a downloadable R&D package, and a returned outcome that changes or preserves the next decision with an explanation. Historical or synthetic outcome fixtures may demonstrate the software return path when no new experiment exists; label them, and do not count them as validation of a better therapy. This milestone requires R15–R17 and the work in the [delivery plan](05-DELIVERY-PLAN.md).

Release only when the P0 invariant tests pass, a scientist or domain reviewer has checked the selected example within their availability, and another developer can reproduce the exact run from the repository and manifest. If no domain reviewer is available, label scientific review pending and do not call the result scientifically validated.

The existing rubric weights scientific relevance, meaningful OpenAI/NVIDIA use, execution, originality, and reproducibility equally. The evidence-to-design-to-experiment feedback loop, traceable correction and failure demonstration define the project's contribution; merely renting Brev or using Codex to write code is insufficient evidence of in-product scientific use.
