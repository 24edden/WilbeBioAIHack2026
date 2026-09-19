# Starting engineering contracts

These are **proposed application contracts**, not vendor API definitions or a finished service. They make the planned interfaces reviewable and provide a starting point for implementation.

| File | Purpose |
| --- | --- |
| [case-manifest.schema.json](case-manifest.schema.json) | Input identity, scope, allowed evidence and mode |
| [case-alk.example.json](case-alk.example.json) | An ALK assay packet referencing the known workbook/hash; no fabricated patient |
| [hypothesis-template.md](hypothesis-template.md) | Optional user-authored investigation input; direct messages and free-text prompts are equally valid |
| [action.schema.json](action.schema.json) | Initial analysis-action envelope, with tool-specific parameters and routing |
| [decision.schema.json](decision.schema.json) | Claims, alternatives, evidence links, uncertainty and next experiment |
| [state-schema.sql](state-schema.sql) | SQLite migration starting point for durable run/action/evidence/feedback state |
| [runtime-config.example.yaml](runtime-config.example.yaml) | Proposed CPU deployment defaults and disabled-until-probed model capabilities |

Validate schemas using JSON Schema Draft 2020-12. Model-visible SDK functions should use small strict Pydantic types per tool. Do not pass these complete application schemas directly to a model API: conditional validation and some schema constructs are application concerns, and vendor structured-output subsets differ.

The schema can validate the shape of a path, hash or evidence identifier. The gateway must additionally resolve paths beneath approved roots, reject traversal and symlink escape, confirm file hashes, check cross-record relationships, enforce case scope, validate source meanings and apply budgets. A syntactically valid evidence ID is not proof that evidence exists.

`action.schema.json` covers the first four analysis-action families. Readiness, retrieval and result-inspection calls use the same gateway policy and emit events; expand/version the action schema when adding other executable analyses. All model-selected identifiers are checked against the trusted case manifest.

The current case schema has a `question` field. W04/W05 must add/version the `HypothesisSpec` intake and run linkage described in [the architecture](../02-ARCHITECTURE.md): original user hypothesis, interpreted statement, source artifacts/hashes/locators and version. That provenance extension is **not yet implemented in these JSON/SQL files**. The supplied ALK question is a selectable example, not proof that a user has submitted it. Agent-derived alternatives are separate records; they cannot replace the pinned user objective.

The ALK example is **open-book development**, not blinded phenotype prediction. Its source row is a locator hint. Extraction must find `ALK_E23_C70A` in the correct table and verify the label rather than assume row 1331 will always be correct. The molecular sequence/ligand bundle is deliberately absent until W06 qualifies it.

The example leaves the count of independent experimental units null until the assay is qualified. That does not prevent source extraction; it blocks inferential statistics that require a verified replicate structure. Review status at decision issuance is fixed by the application. Later disposition is derived from exact-version feedback.

The SQL file is syntactically executable as a proposed empty database schema. It does not implement migrations, leases, state-transition rules, file writing or worker recovery by itself. JSON evidence references inside a decision require semantic validation in one publication transaction.

The [R&D feedback-loop specification](../07-RD-FEEDBACK-LOOP.md) adds planned `DesignBrief`, `DesignCandidate`, `ExperimentOutcome` and `DesignIteration` records plus a `compare_binder_candidates` action. These are **not yet represented in these JSON/SQL starting files**. W20 adds the brief schema/migration and versioned export linkage; W21 adds candidate/comparison contracts; W18 adds outcome/iteration contracts. Version the action schema before exposing the new analysis tool. Preserve candidate/experiment lineage, immutable predictions, accepted-evidence checks and live/replay/synthetic modes across every new contract.
