# L4: provisional lessons and scoped memory releases

Team TBD separates a correction to one case from a procedure that may help another case. A lesson is never activated merely because an agent or user proposed it.

## Implemented release path

1. `POST /api/lessons` records a proposed conditional procedure, its exact origin decision/version/hash, in-scope cases, excluded cases and author. The initial status is `provisional`.
2. `POST /api/lessons/{id}/review` records an explicitly attributed scientist review (`approved`, `reviewer`, `notes`). This does not activate the lesson.
3. After review, a new investigation may explicitly set `evaluation_lesson_id` in `POST /api/runs`. Only a disjoint, in-scope case in the same execution mode may receive that provisional lesson. It is marked evaluation-only in model context and run state.
4. Run a matched baseline with no provisional lesson, the candidate condition, and a separate excluded-case control. `POST /api/lessons/{id}/evaluation` references all three run IDs, a scientist's `quality_passed` judgment, evaluator and notes. Software checks completion, disjointness from the origin, matched hypotheses/source evidence, exact candidate exposure and excluded-case isolation.
5. `POST /api/lessons/{id}/release` requires approved review and passing evaluation. It rechecks that evaluated decisions have not changed, saves an immutable release and makes it retrievable only for future matching case/mode combinations.
6. `POST /api/memory-releases/{id}/suspend` prevents future retrieval without overwriting old run snapshots. Released lessons cannot be edited; propose a new version.

`GET /api/lessons` shows the state. Each investigation pins applicable releases at creation. Source evidence and the user's objective retain their authority; procedural memory cannot create new facts or grant new tool permissions.

## What this gate means

Scientist review and quality judgments are **user-attributed inputs**. Software verifies identity, scope, disjointness, versioning and release conditions; it does not claim to independently prove that a procedure improves science. Offline tests exercise the mechanics with explicitly synthetic judgments. Demo-mode releases are never retrieved into live runs. No lesson is pre-approved or shipped as a learned biological fact.

The API is intended for the private single-team service. Before wider use, add authenticated reviewer/evaluator roles. A name entered into this private prototype is attribution, not identity verification or a regulated approval signature.

## Example proposal

```json
{
  "origin_run_id": "EXACT_COMPLETED_RUN_ID",
  "decision_version": 2,
  "procedure": "When the assay does not measure surface target protein, retain antigen loss as unresolved and request the discriminating protein measurement.",
  "conditions": "Only in target-retention interpretation with missing direct protein evidence; not as a universal target-selection rule.",
  "scope_case_ids": ["bcma-gse164551"],
  "excluded_case_ids": ["alk-l1196m"],
  "author": "Scientist name"
}
```

This is a procedural example, not an accepted scientific lesson. The UI supports proposal/status inspection; review and evaluation are explicit API actions documented by the service at `/docs`.
