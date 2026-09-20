# Team TBD engineering handoff

Start with [stage contracts and executable evaluations](STAGE-CONTRACTS.md) for the implemented stage order, required upstream products, acceptance criteria, repair and review loops, terminal states and tests.

Read [hypothesis governance](HYPOTHESIS-GOVERNANCE.md) for scoped hypothesis states and the new live contract's reviewed automatic continuation. A specialist proposal does not execute work; one accepted reviewer-selected action can pass into the existing durable executor, then return through the full team. Historical runs retain their original policy, and modeled structures alone cannot promote or exclude biological mechanisms.

Read [specialist discovery planning](DISCOVERY-PLANNING.md) for the latest role skill versions, early BioNeMo awareness, proposal contracts and bioinformatics-to-molecular route. Read the [scientific answer review](SCIENTIFIC-REDTEAM.md) for the earlier synthesis changes: preserve the parent decision on narrow follow-ups, compare every user alternative at the appropriate evidence scope, retain numerical controls, and distinguish total functional impact from effects at matched display. These are review obligations, not automated proof of scientific correctness. The Markdown export includes every recorded competing explanation.

Read [research interpretation](RESEARCH-INTERPRETATION.md) for the model-written Working answer, concise decision story, existing-artifact molecular audit and verified form preparation. This is a durable coordinator/reviewer operation that publishes separate numbered addenda; it must not silently rewrite the scientific ledger or rerun specialist/NVIDIA work. Exact source and instruction hashes, acceptance checks and usage receipts travel with each addendum. The completed live version-2 receipt is in [validation](VALIDATION.md).

Read [AI sequence discovery](SEQUENCE-DISCOVERY.md) for public-source lookup, exact-sequence selection, private installed-plugin setup and durable reviewed form preparation. [Ana’s GSE28460 paired study](GSE28460-PAIRED-DATA.md) is newly registered as conventional-treatment relapse context. Scientist-selected `required_analysis_ids` execute and pass source checks before model investigation; their downloadable artifacts and inclusion receipts stay with the run.

## Entry points

| Area | Files | Responsibility |
| --- | --- | --- |
| Browser | `static/index.html`, `styles.css`, `app.js` | Hypothesis, catalog, capabilities, work products, skills, decisions and feedback |
| HTTP boundary | `app/main.py` | Strict inputs, same-origin writes, readiness gates and artifact scope |
| Durable state | `app/store.py` | SQLite transactions, request deduplication, immutable versions and worker lease |
| Workflow | `app/worker.py` | One active operation, evidence/handoff acceptance, checkpoints and publication |
| Model orchestration | `app/providers.py`, `provider_schemas.py` | OpenAI Agents SDK roles, selected-model enforcement and BioNeMo adapters |
| Scientific process | `app/process_contract.py` | Versioned role routes, handoff contract and four feedback loops |
| Skills | `app/scientific_skills.py`, `skills/manifest.json`, `skills/` | Role-scoped instruction files with pinned hashes and receipts |
| Data discovery | `app/data_catalog.py` | Registered Brev dataset/file IDs, bounded readers and approved summaries |
| Fixed source analyses | `app/analysis_tools.py`, `app/cd19_discovery.py`, `app/cases.py`, `casepacks/` | Approved numerical recipes and integrity-checked evidence |
| Discovery follow-ups | `app/followups.py`, `app/structural_followups.py`, `app/structure_preview.py` | Decision-linked execution, public-sequence predictions and verified coordinate views |
| Hypothesis governance | `app/hypothesis_governance.py`, `app/followups.py`, `app/worker.py` | Stable scoped ledger, reviewed continuation, atomic queue transition and actual stop history |
| Research interpretation | `app/brief_operations.py`, `app/research_brief.py`, `app/molecular_interpretation.py` | Durable model-reviewed addenda, exact sequence selection and read-only structural audit |
| Learning | `app/learning.py` | Provisional lessons, scientist review, disjoint evaluation, release and suspension |
| Operations | `app/__main__.py`, `scripts/`, `deploy/` | Startup, doctor, backup, export verification and deployment |

The product is **Team TBD**. GPT-6 Astra with high reasoning is the explicitly authorized temporary Rosalind placeholder; GPT-Rosalind remains a selectable, entitlement-gated provider identity. Preserve actual requested and returned identities in validation reports. Historical directory names and `capabilities.rosalind` are compatibility identifiers.

## Execution graph

The seven specialists are bioinformatician, statistician, clinical scientist, clinical pharmacologist, molecular/structural scientist, translational scientist and assay/wet-lab scientist. The coordinator synthesizes; an independent reviewer challenges the synthesis and can request at most two diagnostic follow-ups. The graph is bounded application policy, with scoped SDK tools and typed outputs. Clinical science still frames the research question when no patient timeline is qualified, without making patient-specific temporal claims. Pharmacology skips inference and records a blocked product when actual exposure data is absent. Molecular science uses its model and skills to qualify inputs. Missing matched constructs block the binder-comparison branch. Separately accepted public-isoform monomer predictions can be reviewed as exploratory structural context; they do not establish binding or target retention.

The frontend shows intended roles before execution. It activates role status only from actual persisted events or work products. Handoffs include sender/recipients, case identity, question, method, result status, limitations, decision affected, claims, exact input versions and upstream product IDs. A completed run means an accepted research decision was published; scientific conclusions can remain unresolved and molecular work blocked.

`POST /api/runs` saves a case snapshot, original hypothesis hash, process contract and applicable procedural releases before queueing. One worker holds a renewable SQLite lease and processes runs sequentially. Browser closure does not stop it. The UI polls durable state; `/api/runs/{id}/events` also exposes events.

New live runs pin `team-tbd-resistance-4` with hypothesis governance and automatic continuation enabled. Coordinator/reviewer produce `decision.governance`; the application validates cited evidence, stable identities, source/recipe versions and consistency between continuation targets and ready recommendations. Each outer cycle performs one qualified unperformed action, accepts its evidence and reruns all specialist stages plus review. Missing-input stages remain honestly blocked. Stop reasons distinguish resolution within scope from unavailable inputs/methods, wet-lab requirements, no useful executable action or unresolved providers. A possible hypothesis cannot be declared resolved simply because execution ended.

## Tools, sources and skills

For fixed cases, the model selects approved recipes through `analysis_catalog` / `run_case_analysis`. CAR-T discovery uses registered dataset/file IDs, bounded schema inspection and approved analysis kinds through the data catalog adapter. Metadata availability does not mean all source files were analyzed. Tools return scoped deterministic measurements; the model chooses what to investigate, interprets results and requests review diagnostics. There is no arbitrary model shell, code execution, filesystem path or endpoint.

Case/file hashes are qualified before intake; source bytes remain read-only. Accepted analysis records carry source and derivation hashes. Claims must cite accepted evidence. Repeated computations of the same source are explicitly not independent evidence. The curated offline answer is excluded from live model context, and source passages remain untrusted data.

Scientific role skills are read from the pinned registry, scoped by role and checked against their SHA-256. The installed BioNeMo Boltz2 skill is included with attribution. Durable receipts identify skill/version/hash, role, operation and load time; work products link their skill provenance. These records establish loaded instructions, not scientific validity or vendor invocation. Receipt availability must never be used as a proxy for model access.

## Durable actions and molecular work

Each live operation records model requests, tokens, tool calls and elapsed time against pinned thresholds. Aggregate thresholds are advisory by default; per-response and per-stage scope limits remain enforced. Real request/model/usage metadata is retained and charged once per durable action. Operational persistence lives in SQLite, not the SDK conversation. Interrupted inference is not automatically replayed: unresolved intent becomes unknown, while a completed receipt can be reused. Exactly-once vendor execution and resumable in-flight reasoning are not promised.

Cancellation stops new submissions. Submitted external work may still complete; partial artifacts and request identifiers stay visible. Only the molecular executor may attach accepted prediction artifacts. Boltz-2 requires qualified target/reference/candidate inputs and the target-retained scope. Invalid structures, mismatched chains, a missing pair member, pending jobs and timeouts cannot become completed paired predictions. Structure confidence does not establish efficacy. No actual NIM result should be claimed without its real receipt and validated artifacts.

Automatic continuation checks prior recipe/source attempts, and the molecular specialist reuses a successful same-input binder result across operations instead of paying for an identical pair again. Unknown or failed attempts are not automatically replayed. `governance_state`/`governance_transitions` record operational suppression separately from immutable scientific decisions. Manual follow-up selection remains available on eligible completed runs. A manual modeling-only decision sets current governance to null and preserves `prior_governance`; later scientific cycles recover that ledger and must keep its identities and reopening constraints.

Candidate/experimental-arm IDs are server-assigned per decision version. Curated arms are proposed experiments, not generated binders. Returned measurements must match the exact experiment, candidate and version. Stale submissions fail; corrections create a new version, preserving earlier records. Artifact downloads are confined to published paths belonging to the run.

## Four feedback loops

| Loop | Trigger | Durable result |
| --- | --- | --- |
| L1 | Specialist validation failure, concrete reviewer gap or reviewed informative next test | Bounded repair/diagnostic, or one qualified governed follow-up and a new team cycle; accepted evidence and work-product trail |
| L2 | Scientist correction to latest decision | New operation, original hypothesis preserved, immutable decision revision |
| L3 | Returned measurement with exact experiment/candidate identity | Attributed user report, reassessment and new version |
| L4 | Proposed reusable procedure | Provisional lesson followed by explicit review/evaluation/release gates |

The Learning UI only proposes and lists lessons. Manual API sequence:

1. `POST /api/lessons` pins origin run/decision, procedure, conditions, scope, exclusions and author.
2. `POST /api/lessons/{id}/review` records `{approved, reviewer, notes}`.
3. Create baseline and matching candidate runs on an in-scope case disjoint from the origin. Only candidate creation includes `evaluation_lesson_id`. Complete an explicitly excluded-case run too.
4. `POST /api/lessons/{id}/evaluation` records `{baseline_run_id, candidate_run_id, out_of_scope_run_id, quality_passed, evaluator, notes}`. Software checks identity, mode, disjointness, matching source/hypothesis context and pinned decision hashes; the quality judgment remains attributed to the scientist.
5. `POST /api/lessons/{id}/release` releases only a reviewed, passing evaluation. `POST /api/memory-releases/{release_id}/suspend` excludes the release from future intake. Existing snapshots retain history.

Released guidance is procedural only. It cannot supply evidence, cross execution modes or override scope. Review/evaluation names are supplied attribution, not authenticated signatures. An approved evaluation is not clinical validation.

## Operating practice

Keep `.env` private and mode 0600; hosted SDK trace export is disabled. Pin dependencies with `requirements.lock.txt`. Use one API process with embedded worker, or a separate worker sharing one local runtime directory. Do not share a live SQLite file over a network filesystem. Use `python -m app backup <new-path>` for consistent snapshots, and retain immutable artifacts and source manifests with the backup.

Run focused regression checks after changes to provider behavior, acceptance gates, release scope or source extraction. Source changes require regenerated manifests and integrity checks. See [VALIDATION.md](VALIDATION.md) for actual checks, [PROVIDERS.md](PROVIDERS.md) for transport details and [BREV.md](BREV.md) for private deployment.

Public service hardening, authenticated scientist signatures, automatic pending NIM reconciliation and additional scientific analysis methods remain separate work. Extend approved tool and test contracts before expanding model authority.


## Live operations and budget policy

The UI starts with an empty hypothesis composer; a scientist may explicitly load the CD19 example or enter a different question. Selected investigations place live role activity, evidence-backed scientific rationale, handoffs and acceptance checks before intake. `active_agent`, `last_activity` and role-specific `stage` are persisted; older runs derive their display from actual events. Model reasoning is shown as authored scientific work products, not hidden chain-of-thought.

`TEAM_TBD_BUDGET_MODE=advisory` is the default. Cumulative provider request/input/output/tool thresholds and worker time/tool-operation thresholds emit one warning per category and continue. `worker_budget_policy` freezes the operation's worker settings; `budget_alerts` and provider metadata retain warnings. Optional `enforced` mode restores aggregate stops. Actual per-response API limits, stage turn/analysis/repair scope, malformed outputs, unavailable inputs, cancellation and provider failures remain separate controls.

A real NVIDIA monomer service check is presented independently of a case-specific matched comparison. `/api/engineering/bionemo/{check_id}/prediction.cif` serves only hash-verified registered output; `/receipt.json` exposes sanitized provenance. Engineering-check success is never copied into the scientific evidence of a CAR-T investigation.

Findings and executable recommendations are documented in [FOLLOWUPS.md](FOLLOWUPS.md). `app/followups.py` owns recipe/readiness validation and serialized selection; `worker.execute_followup` owns durable execution and accepted evidence before reassessment. New decision insights are actual model outputs with citations. Public CD19 isoform monomer follow-ups have a separate scientific scope and output view from qualified binder comparisons. The exact original hypothesis and earlier decision versions remain intact. Old source snapshots require a fresh investigation when a new recipe needs later source pins.

## Known incomplete synthesis recovery

See [SYNTHESIS-RECOVERY.md](SYNTHESIS-RECOVERY.md). Explicit recovery can reuse exactly seven verified specialist handoffs after a known terminal coordinator output-limit response. It creates a new operation with checkpoint lineage and fresh coordinator/reviewer calls, preserves original failed requests and handoffs, and rejects unknown outcomes. Checkpoint synthesis cannot create new evidence; registered next tests run through governance and full specialist review after publication. Coordinator/reviewer output capacity is separate from specialist capacity.
