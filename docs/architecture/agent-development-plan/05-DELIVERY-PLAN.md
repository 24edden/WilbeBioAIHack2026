# Delivery plan and engineering backlog

Planning assumption: three engineers and two working days for the initial release, with a domain reviewer available for a short review if possible. Actual team size, deadline, access and budget were asked about and remain unconfirmed. Effort estimates are person-hours, not promises about elapsed time.

## Workstreams

| Role | Ownership | First integration artifact |
| --- | --- | --- |
| Engineer A: runtime | OpenAI SDK, state machine, persistence, budgets, recovery | One typed coordinator turn with a durable deterministic tool result |
| Engineer B: science/data | ALK packet, source locators, biological gates, CPU tools | Frozen assay evidence table with source-cell validation |
| Engineer C: tools/product | NIM transport, ligand branch, UI, deployment | Real validated NIM artifact plus visible run/evidence page |
| Scientific reviewer | Interpretation boundaries and next-experiment quality | Review of the exact selected decision version |

Engineers B/C jointly own molecular mapping. Assign real people before starting; workspace directory names are not assignments or an assumption about who is available.

Use one branch per workstream, small PRs and a shared contract version. Merge only demoable pieces. Add every setup step to the repository's DeveloperREADME as requested by its AGENTS.md.

## P0 backlog

| ID | Owner | Hours | Depends on | Concrete change | Done when |
| --- | --- | --- | --- | --- | --- |
| W00 | A | 1–2 | — | Add local prototype source/tests/vendor licenses to team repo; reconcile docs branch | Clean checkout contains code; 20 existing tests pass; source provenance recorded |
| W01 | A/C | 2–3 | W00 | New isolated Python 3.11 runtime, locked packages, settings and doctor | Local and Brev imports succeed; source/output mounts checked; no global environment modified |
| W02 | A | 1–2 | W01 | GPT-Rosalind capability probe; explicit model/provider config | Text, function-result round trip and output-validation path recorded; no silent fallback |
| W03 | A | 4–5 | W00 | SQLite schema/migrations, action identities, artifact writer and worker leases | Restart and duplicate submission tests pass; unknown remote outcome is represented |
| W04 | A/B | 3–4 | W00 | Hypothesis intake contract/template and source pinning; ALK manifest, source-key lookup, units/construct checks, qualified evidence table | User hypothesis and source/version retained; ambiguity surfaced; exact source rows/cells resolve; concentration discrepancy retained; no fabricated patient ID |
| W05 | A | 3–4 | W02/W03/W04 | SDK coordinator bound to the supplied hypothesis/version, typed CPU wrappers and compact evidence retrieval | One complete hypothesis → source → tool → decision draft trace; derived alternatives labeled; limits enforced across calls |
| W06 | B/C | 4–6 | W01/W04 | Exact ALK WT/mutant construct + alectinib ligand package, mapping and validators | Canonical-to-construct residue map and chemical identity checked; appropriate scientific question |
| W07 | C | 4–6 | W03/W06 | New Boltz ligand pair adapter; per-tool backends; real job/pending/error semantics | Matched real pair accepted or exact blocker retained; partial pair never treated as completed |
| W08 | A/B | 3–4 | W05 | Independent reviewer, one revision, claim-to-evidence/numerical finalizer | Unsupported claim blocked; dissent/unknowns retained; v1 export resolves all evidence |
| W09 | C | 3–4 | W03/W05/W08 | Case/run/evidence/decision pages, SSE, correction form, export | Scientist corrects a claim; v2 preserves v1 and feedback; reload survives restart |
| W10 | A/C | 2–3 | W01/W09 | CPU deployment, private forwarding, restart and backup runbook | Another developer runs the same pinned application and restores a case |
| W20 | B/C | 3–5 | W08/W09 | R&D brief record/schema, handoff page/export, candidate/test and outcome-return requirements | Each investigation links evidence to a design objective or precise block and a reviewable experiment plan; R16 |
| W11 | B/all | 3–4 | W07/W08/W09/W10/W20 | Regression/evaluation fixtures, recorded real trace, five-minute walkthrough | Tests below pass; live/replay/synthetic modes are visibly distinct; R&D handoff is visible |

P0 estimate: **36–52 engineer-hours**, consisting of the original 33–47-hour investigation slice plus W20's 3–5-hour R&D handoff. This excludes uncertain entitlement delays, large dependency downloads and unresolved molecular-input work. With three people this is approximately 12–18 focused hours each plus coordination. W06/W07 have the largest initial uncertainty. Actual CAR-T structural comparison and measurement return are the separately estimated W21/W18 milestone below.

## Milestones and critical path

| Elapsed working time | Parallel work | Integration gate |
| --- | --- | --- |
| H0–H2 | A: repo/runtime/model probe. B: ALK source qualification. C: NIM credentials/contract readiness | Can access requested model and at least one scientifically relevant NIM route? |
| H2–H6 | A: DB/gateway. B: assay extraction/mapping. C: NIM transport and UI shell | CPU evidence is attributable; real molecular input contract is qualified |
| H6–H10 | A: coordinator. B: finalizer/rubric. C: ligand pair + evidence page | Complete one real-data investigation; capture the trace before adding roles |
| H10–H16 | Correction loop, R&D handoff, bounded critique, replay, fault tests | Restart and scientist correction work; design brief points back to evidence and forward to an experiment |
| H16–H20 | Fresh-machine replay, documentation, recorded demo, final review | Freeze release commit and input/output manifests |

Critical path: **W00 → W01/W02 → W03/W04 → W05 → W08 → W09 → W10/W20 → W11**. The scientific NIM path **W04 → W06 → W07 → W11** must also pass for the live sponsor-integrated release.

These times are a coordination template. If the Sunday deadline leaves fewer than 12 working hours, use the reduced release below instead of implying all P0 work fits.

## Reduced remaining-weekend release

Keep one ALK case, a coordinator plus one critic call, six or fewer initially exposed tools, one validated NIM route, CLI-generated evidence/decision/R&D-brief files, and a simple review page. Defer the rich timeline, multiple simultaneous cases, general graph retrieval, all specialist roles and memory learning. Preserve stable action IDs, citations, honest mode labels and a basic restart checkpoint. A design brief without a completed candidate comparison must show that modeling remains pending.

Cut rules:

- **H2:** if GPT-Rosalind entitlement/tool calling is not established, continue replay infrastructure and mark the requested live model blocked. An alternate model requires an explicit project choice and a visible model label.
- **H4:** if ALK ligand inputs remain unqualified, do not send guessed sequences or chemistry. A qualified hosted Evo 2 route can become the NIM slice if it answers the selected molecular question; otherwise report the blocker and keep scientific inference out of the demo claim.
- **H8:** if live inference remains unreliable, capture any completed validated result and demonstrate exact recorded replay. Label it recorded; synthetic output cannot become the recorded real result.
- **Before final demo:** freeze features. A small honest demonstration with a failure/correction example is more valuable than claiming the entire reference architecture is implemented.

The reduced release is not presented as satisfying every full P0 requirement. Publish the implemented requirements and omissions beside the demo.

## P1 and P2 backlog

| ID | Scope | Hours | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| W12 | Hosted Evo 2 7B forward adapter and score version | 3–5 | W03 and reference-mapping tools | Exact documented endpoint, tensor/schema validation, correct model labeling, no generation/scoring confusion |
| W13 | Prepared BCMA case adapter | 4–6 | W05/W08 | Correct S5/S6 identity, CD138 baseline caveat, post-WES timing, copy-number-input boundary |
| W14 | Maynard RDS inspection and two-biopsy slice | 6–10 | W05/W08 | Scale verified; mapped malignant-cell summaries; RD kept distinct from progression; no patient-level inference from cell counts |
| W15 | Four bounded specialists and one challenge round | 4–6 | W11 | Clear brief contracts; common budget; distinct tool permissions; no evidence multiplication |
| W16 | Paired single-agent/team pilot and NIM ablation | 4–8 + review | W11/W15 | All trials reported at matched budgets; reviewer scores and errors retained; no broad efficacy claim |
| W17 | Feedback lesson records and scoped retrieval | 6–10 | W09/W16 | Candidate/review/evaluation/release separation; disjoint case check; scope exclusions and rollback |
| W18 | P1 R&D outcome intake and next iteration | 4–8 | W20; integrate with W21 | Versioned candidate/experiment identity, units, controls and raw-data hashes qualify; accepted measurements create a new decision/design round; negative/failed outcomes preserved |
| W19 | Separate Brev GPU NIM profile | 3–6 + provisioning | Need established | Image/hardware contract, private reachability, readiness, resource/cost cap and shutdown ownership |
| W21 | P1 CAR-T reference/candidate structural comparison | 5–8 | W03/W20; qualified target, candidates and NIM transport | New action contract/schema, matched BioNeMo structures, controls/limitations and R&D comparison export; no reuse of single-target-mutation assumptions; R17 |

Target the next one to two weeks for these extensions after the first release. Re-estimate from the first measured run and data-preparation results.

Prioritize **W20 → W21/W18** as the first R&D feedback milestone. W21 and W18 add **9–16 engineer-hours** beyond P0, assuming scientifically qualified candidate inputs and working NIM transport; W13 adds 4–6 hours if the BCMA intake is included. Candidate selection/preparation, domain review, laboratory work and de novo generation are excluded and need separate estimates. The milestone must show a modeled reference/candidate comparison, export to R&D and a returned outcome changing or preserving the next decision with a reason. A labeled historical/synthetic outcome can test the software path, but cannot establish a better therapy. See [the CAR-T process](07-RD-FEEDBACK-LOOP.md).

## Required acceptance tests

| Test ID | Scenario | Expected invariant | Requirements |
| --- | --- | --- | --- |
| T01 | Source workbook changes one byte or key is missing | Qualification blocks affected analysis; source version changes | R01/R02 |
| T02 | ALK functional case has no patient ID | Valid functional-assay scope accepted; no dummy patient invented | R01/R05 |
| T03 | Wrong canonical/construct residue or ref base | NIM request rejected before submission | R06 |
| T04 | NIM returns 202, malformed CIF, nonfinite logits or partial pair | Pending/invalid/incomplete state; no accepted comparison claim | R06/R07 |
| T05 | Crash after submit or after artifact commit | Reconcile stable action; no silent duplicate paid POST | R07 |
| T06 | Tool result contains an instruction to read another directory | Scope unchanged; unauthorized source remains inaccessible | R02/R11 |
| T07 | Draft invents an evidence ID or number | Finalizer rejects claim; bounded repair or failed output | R08 |
| T08 | Duplicate feedback and stale decision version | One feedback event; stale target rejected or explicitly applied to its original version | R09 |
| T09 | Budget reached during nested reviewer/tool use | No new dispatch; accurate usage and stop reason | R11 |
| T10 | Restart while awaiting scientist | Same decision/feedback state restored | R07/R09 |
| T11 | Replay mode has no credentials/network | Exact saved outputs displayed; no vendor call attempted | R10 |
| T12 | Live endpoint fails | Visible failure; no automatic switch to synthetic or another model | R03/R06 |
| T13 | BCMA baseline depletion/S5-S6/post-WES case | Correct identities and temporal caveats; no fabricated copy-number result | R13 |
| T14 | TH266 case | One patient, missing baseline day, RD category preserved; no cohort p-value | R13 |
| T15 | Out-of-scope or suspended lesson | Lesson excluded; affected prior uses identifiable | R14 |
| T16 | Export investigation to R&D with incomplete design inputs | Evidence-linked objective/test plan present; modeling block explicit; no fabricated candidate or score | R16 |
| T17 | Same-target CAR redesign proposed despite supported antigen loss | Reject unsupported rescue claim and return an appropriate alternative objective or missing-evidence experiment | R13/R17 |
| T18 | High-confidence candidate prediction without measured improvement | Structural result remains a prediction; unavailable metrics stay missing; no affinity or whole-cell efficacy claim | R17 |
| T19 | Returned negative result, duplicate upload or wrong candidate version | Exact lineage and idempotency enforced; valid negative evidence changes or preserves the next decision with reasons; old predictions remain immutable | R15 |
| T20 | Hypothesis supplied by message, prompt or Markdown; conflicting or missing objective; mid-run amendment | Original wording/provenance preserved across formats; ambiguity blocks dependent investigation; agent alternatives stay labeled; user amendment creates a new version without changing the active run's pinned objective | R01/R04 |

These are meaningful behavior tests, not tests that simply mirror implementation functions.

## Scientific evaluation and ablations

P0: check exact source extraction, prohibited inference errors, routing, provenance, correction and recovery on the ALK case plus fabricated null/confounded/contradictory routing fixtures. Existing prototype tests are the starting baseline; they do not validate scientific accuracy.

P1: compare one tool-enabled coordinator versus the specialist workflow on identical ALK/BCMA packets and budgets, initially three runs per case/condition. Randomize review order and conceal system identity where feasible. Score source fidelity, alternatives, uncertainty, experiment discrimination and usefulness on the existing 0–3 rubric. Report unsupported consequential claims separately. Repeated runs measure workflow variation, not extra patients.

For the NVIDIA contribution, compare the same frozen case/evidence snapshot before and after a qualified NIM result. Record whether it changes a mechanistic claim, increases uncertainty or selects a different experiment; a justified finding of no added value is possible. Do not require a favorable scientific conclusion merely to show model use.

Two or three public cases cannot establish generalization. Keep the open Maynard case in a separate challenge slice, graded on fidelity and discrimination rather than agreement with invented mechanistic truth. Formal memory-transfer claims require new disjoint cases and a prespecified evaluation.

## Review and completion

Technical completion requires reproducible artifacts and passing invariants, not a fluent report. Scientific acceptance requires the review status and scope to be visible. Delivery includes code commit, dependency lock, case/input manifest, model/tool capability record, exact commands, known limitations, one real recorded trace if available, and its labeled replay.
