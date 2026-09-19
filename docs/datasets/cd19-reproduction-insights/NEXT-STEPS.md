# General skill guidance for data preparation and analysis

The current scope is to improve reusable role instructions. The app's bioinformatics, statistics and discovery-planning skills now suggest useful preparation and analyses according to the question, assay, study design and available capabilities. No study-specific cleaning pipeline, new reader or analysis recipe is introduced.

- [Bioinformatician, v1.2.0](skills/bioinformatician.md): consider identifier/type/units reconciliation, reliable joins, explicit missingness, lossless versioned derivatives and relevant integrity checks. Explain which preparation enables the analysis and which assumptions remain unresolved.
- [Statistician, v1.2.0](skills/statistician.md): match contrasts and uncertainty to the biological unit, pairing and repeated measurements; consider appropriate count-aware or other models and sensitivity analyses. Protect held-out evaluation from preprocessing, feature-selection and answer-key leakage.
- [Discovery planning, v1.1.0](skills/discovery-planning.md): choose proportionate preparation or analysis only when it can change the current decision. Separate recommended work, implemented capabilities and actual results.

These are conditional suggestions. Reusable skills do not prescribe a fixed study sequence, sample exclusions, thresholds, expected result counts or a particular fitted model. Case-specific choices and citations belong in the qualified data record or versioned recipe. Report unresolved discrepancies rather than changing measurements to reproduce an answer.

[Data references](DATA-REFERENCES.md) link the primary papers, deposited datasets, frozen author code and access qualifications. The live app's `docs/DATA_ANALYSIS.md` has the same reference table, and `docs/DATA_CATALOG.md` links to it. The detailed data-bearing audit remains on [Brev](DATA-ACCESS.md).

The files under `skills/` mirror three changed role modules from the existing application. Their [release entries](skills/skill-release.json) record versions and hashes; this fragment is not a standalone replacement for the full skill registry. Role tool names assume the existing app's registered capabilities.

Validation: all six native skill integrity/receipt tests and the full 296-test suite passed in an isolated application copy. An independent scenario review found no forced study-specific rule or claim of execution. No scientific data transformation, new analysis or paid model call was performed for this instruction update.
