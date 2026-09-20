---
name: molecular-interpretation
version: 1.0.0
---

# Interpret returned molecular predictions

Before interpreting a prediction, separate the scientific question into sequence identity, local fold, relative domain arrangement, molecular recognition and cellular function. State which of these the executed method actually tested. Preserve target, binder, ligand and isoform roles; exact target variants must never be relabeled binder designs.

Consume validated returned-artifact audits when supplied. Report the exact sequence and provenance, request settings, coordinate coverage, confidence semantics and artifact hash. Do not guess that crystallographic B factors are pLDDT; use declared metric semantics or report them as uninterpreted. Do not infer equal settings from missing receipt fields. Compare only aligned corresponding residues; report mapping scope, residue count and fit method. Distinguish whole-chain and local/window fits, domain orientation and local distortion. State window boundaries explicitly and do not name a biological domain without a qualified mapping.

Describe what the service added beyond the sequence difference already known before inference. A changed predicted structure can motivate a mechanism or experiment; it does not establish affinity, antigen retention, trafficking, CAR recognition, killing or patient resistance. Low confidence makes a structural conclusion uncertain rather than falsifying a biological mechanism. A prediction of retained geometry likewise does not rule out cellular mechanisms.

Give translation a plain-language working interpretation, strongest quantitative observation, principal alternative explanation and one discriminating next step. Prefer auditing existing artifacts before repeating identical inference. Where the audit is unavailable, name the missing method or field precisely. Any new deterministic audit is a separate method/version with its own result receipt; do not imply that prior reviewers consumed it. Functional hypotheses remain tied to measured controls and experimental acceptance criteria.
