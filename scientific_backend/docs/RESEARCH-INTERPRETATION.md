# Clear research interpretations

The **Working answer** section supplements a completed live investigation with a new model-written, independently AI-reviewed brief. It states the leading explanation at the supported scope, the strongest findings, why each decision changed, what molecular predictions added, and the next discriminating test. It does not rewrite the original hypothesis, historical decisions or possible/probable/clearly-ruled-out ledger. Human scientific review remains pending.

## Use

Select the latest decision and choose **Explain these results**. The application queues a durable `research_brief` operation, visibly runs a coordinator and separate reviewer, and saves the accepted addendum. This makes real OpenAI model calls using the configured model; GPT-6 Astra/high remains the authorized placeholder, not GPT-Rosalind entitlement. Aggregate budgets remain advisory. This operation does not submit new NVIDIA predictions or wet-lab work.

The generation route is `POST /api/runs/{id}/research-briefs` with only `decision_version` and `idempotency_key`. Reuse the same key after an uncertain acknowledgement. The source decision, original hypothesis, accepted evidence, latest accepted role products, process/governance context, model and instruction hashes are pinned. Unknown provider outcomes are preserved without automatic resubmission. A saved complete model result can be published after interruption without rerunning the model or artifact audit.

`research_briefs` contains immutable numbered addenda, accepted AI-review checks, exact context/instruction hashes, model request and usage receipts, and the deterministic audit of existing molecular artifacts. `research_brief_operations` records queued/running/completed and interruption states. The original decisions remain separate, and the export verifier checks addendum hashes and their exact source decisions. Source handoffs shown during this operation are reused historical work, not nine newly executed specialists.

Scientist-required study results must appear in the substantive findings. The interpretation context identifies completed `required_analysis_operations` whose analysis is in the pinned case's `required_analysis_ids` and whose evidence was accepted. Each such evidence ID must be cited by a finding explaining the observed result, cohort or experimental scope, and why it changes or leaves unchanged the working answer. Mentioning a study only as a limitation, source receipt or proposed next step does not satisfy coverage. Null findings and results from contextual cohorts are still explained without forcing support for the original hypothesis.

The deterministic check enforces coverage in the findings; the independent reviewer separately checks that the prose explains the actual result, scope and implication. Up to eight concise findings are allowed, and related results may be grouped only when each is explained. Existing word caps remain. The exact coverage references are included in the context hash and a separate input-version hash. This adds no raw-data analysis or scientific status promotion and leaves historical addenda unchanged.

## Molecular context and form preparation

The [molecular audit](MOLECULAR-INTERPRETATION.md) verifies exact sequence bytes, role, provenance, returned-artifact identity, request settings where receipts permit, declared confidence semantics and alignment sensitivity. New audit results are labeled separately from what the prior reviewer knew. No clinical or binding claim follows automatically from a picture, confidence metric or structural displacement.

The model chooses verified sequence **IDs**, not amino-acid strings. A saved brief automatically prepares appropriate known fields and the model's rationale only when the form is untouched. **Prepare from this investigation** explicitly reapplies them; user edits block automatic replacement. The completed target-isoform comparison is shown directly with its exact sequences. A target isoform cannot populate a binder slot; absent binder inputs stay empty and target retention is never automatically asserted. The manual binder-design form is optional and collapsed, so it is not confused with the completed monomer comparison. Merely preparing the form submits no provider job.

## Runtime and instruction handoff

- `app/brief_operations.py`: transactional selection, input/instruction pins, durable action intent, immutable publication and recovery.
- `app/research_brief.py`: typed coordinator/reviewer SDK calls, evidence and sequence-reference validation, concise output.
- `app/molecular_interpretation.py`: deterministic read-only artifact audit; no provider or dataset changes.
- `skills/scientific/research-interpretation.md`: useful scoped working answer, simple findings and evidence-based decision rationale.
- `skills/scientific/molecular-interpretation.md`: exact identities, metric semantics, settings and cautious but informative molecular interpretation.

Both skills are registered with content hashes. The first is applied to every model-driven scientific role; the second is applied to relevant computational and synthesis/reviewer roles. Existing historical skill receipts are preserved. Validation checks catch citations, provenance and input-role violations; the separate model review improves scientific interpretation but is not experimental verification or human approval.

Software and live validation receipts are recorded separately in [VALIDATION.md](VALIDATION.md).
