# Hypothesis testing and reviewed continuation

New live runs pin process contract `team-tbd-resistance-4`, including `hypothesis_governance.enabled: true` and `auto_continue: true`. The team maintains a scoped hypothesis ledger, and its independent reviewer can select one informative registered follow-up. The application accepts the decision, rechecks execution eligibility, performs that action and sends the accepted result through a new specialist and review cycle. Completed live run `b5898d6c3b3940ee9eac90f01b8b8e19` demonstrated two successive agent-selected follow-ups, including real NVIDIA predictions, followed by a specific `needs_method` stop. That observed loop does not establish patient-level causation, optimal research planning or full-paper reproduction. See the receipts and boundaries in [VALIDATION.md](VALIDATION.md).

## Scientific states

| State | Meaning | Required interpretation |
| --- | --- | --- |
| `possible` | Unresolved or compatible with current evidence | Neither affirmative support nor a 50% probability. Missing data, failed QC, low power, an unrun analysis and an unavailable service leave the relevant question open. |
| `probable` | Accepted evidence favors the explanation within its stated scope | A reviewer judgment, not proof, exclusivity or a calibrated probability. Material competing explanations and limitations remain visible. |
| `clearly_ruled_out` | Accepted counterevidence contradicts a claim under a meaningful falsification test | State the performed test, result, detection/design fitness and exact scope excluded. Nonsignificance alone is insufficient. Predictions alone cannot establish biological exclusion. |

Mechanisms may coexist. A construct-level finding does not determine a patient's cause, and a computational result does not automatically establish a biological effect. Each ledger item declares `scope` and `scope_type` (`biological` or `computational`). Original user wording and provenance remain preserved separately; the ledger's concise statement does not replace them.

`decision.governance.hypotheses` preserves stable IDs, including `primary`, user versus agent ownership, source quotations, scope, accepted supporting/counterevidence and test references, rationale, registered next-analysis IDs and a blocker when needed. Existing IDs cannot disappear or change their statement, ownership or scope across decisions. Reopening an excluded hypothesis requires newly accepted or corrected evidence and an explicit revised rationale. Merely citing an old record for the first time is not new evidence.

## One action, then reassessment

1. Specialists receive current evidence, previous governance and the actual recipe catalog. They assess their own remit and can attach validated `propose_followup` records to accepted handoffs.
2. Coordinator synthesis proposes the ledger and a useful next comparison. The reviewer independently challenges evidence, status changes, controls and unresolved alternatives.
3. To continue, the reviewer returns one registered `next_action_id`, named `target_hypothesis_ids`, a discriminating `continuation_reason` and `stop_reason: continue`. The same action must appear as a ready final follow-up and in the targeted possible/probable hypotheses' next analyses.
4. Publication validates the ledger and commits its immutable decision and continuation transition together. The execution boundary rechecks source/recipe versions, current readiness, policy, cancellation and previous attempts. A model's readiness assertion cannot override these checks.
5. The durable executor records intent, executes the selected registered method and accepts qualified evidence. All specialist stages, coordinator and independent reviewer reassess the new evidence and original objective. A missing-input role can still return its explicit blocked product without a model call.

Planning tools remain proposal-only. They do not submit OpenAI, NVIDIA or analysis jobs. Automatic selection is authorized only by the hash-validated live process contract; `followup_only` recipes remain inaccessible to initial-analysis and reviewer-diagnostic tools. Existing in-stage diagnostic/repair limits still apply. A reviewer-selected follow-up is an outer operation with its own role checks, not an unrestricted model-generated program. Wet-lab work remains a protocol proposal.

## Continue or stop honestly

Continue when a qualified, unperformed registered action can materially distinguish an unresolved hypothesis. The scientific plan must explain the comparison, possible outcomes, input/QC requirements and return criteria. Do not continue solely to display NVIDIA activity or stop solely because the narrative is polished.

The decision records one explicit reason: `resolved_within_scope`, `needs_data`, `needs_method`, `wet_lab_required`, `no_informative_action` or `provider_unresolved`. `resolved_within_scope` cannot retain possible hypotheses; it still does not mean probable findings are proven. A stopped investigation with possible hypotheses must preserve their concrete blockers. The validator rejects a stopped decision that simultaneously nominates a ready, unperformed next test. The reviewer's judgment about scientific usefulness remains necessary: software cannot prove that every worthwhile analysis was considered.

`governance_state` and append-only `governance_transitions` record what actually happened, separately from the immutable reviewed plan. A source/provider change can suppress a selected action. Operational cancellation or failure records its own reason without rewriting the scientific ledger or treating interruption as falsification. The website and exports show the ledger, selected action, evidence and actual continuation state.

## Persistence, manual work and recovery

- A registered recipe/source version already durably attempted is not automatically resubmitted. Completed evidence is reused; unknown or failed external work requires reconciliation. Successful matched-binder results are also reused across operations for identical qualified inputs; an unresolved or unsuccessful same-input attempt blocks automatic repetition.
- Cancellation stops new submissions and queues. It does not establish that a remote provider stopped work already submitted. Partial results and request receipts remain available where recorded.
- Explicit manual follow-up selection remains available on a completed live decision, with the existing version/idempotency checks. Operation origin distinguishes `scientist_selection` from `agent_governance`; neither changes original hypothesis ownership.
- A manual modeling-only operation does not run the scientific team or update hypothesis states. It records earlier governance as `prior_governance`, marks the new modeling evidence as not yet reassessed and does not trigger automatic continuation. Later scientific reassessment retains that history and its stable identities.
- Historical runs retain their pinned process contracts, source snapshots, receipts and decision versions. Runs without the enabled automatic policy are not silently opted in. New source requirements need a fresh qualified snapshot.

Aggregate budgets remain advisory by default, with per-operation usage and warnings recorded. Stage/response limits and actual failures still apply; continuation does not provide a fixed whole-investigation cost ceiling or promise convergence.

## Engineering boundary

`app/hypothesis_governance.py` validates ledger shape, citations, versions, history and continuation consistency. `app/providers.py` supplies the typed coordinator/reviewer schema and role context. `app/followups.py` owns policy and atomic queue decisions; `app/worker.py` owns durable execution, evidence acceptance and publication. The role skills describe scientific responsibilities; they do not grant execution authority.

Contract checks establish provenance and eligibility, not that an interpretation is true, a falsification was scientifically adequate, or all causes were discovered. Offline helper and mocked-SDK tests exercise these boundaries without proving live model behavior or NVIDIA success. See [stage contracts](STAGE-CONTRACTS.md), [follow-up contracts](FOLLOWUPS.md) and the actual [validation record](VALIDATION.md).
