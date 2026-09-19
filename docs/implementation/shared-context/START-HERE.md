# Rosalind shared team context

Prepared 19 September 2026. Start here for the scientific use case, agent workflow, and scientist-feedback learning design.

## Read in this order

1. [Current implementation boundary](CURRENT_IMPLEMENTATION.md) — what the local prototype record says was implemented and what remains proposed.
2. [Hypotheses and agent architecture](../../../Context/TRANSLATIONAL_SCIENCE_HYPOTHESES.md) — Easy / Stretch / Novel roadmap, competing mechanisms, datasets, experiments, specialist debate, and four Mermaid diagrams.
3. [Scientist-feedback learning loop](../../../Context/AGENTIC_SCIENTIFIC_LEARNING_LOOP.md) — correcting a case, saving bounded lessons, measuring transfer, versioning memory, and rollback.
4. [Original dataset landscape](../../datasets/DATASET-LANDSCAPE.md) — broader dataset reference previously uploaded to this folder.
5. Original architecture document (`Rosalind_Translational_Scientist_Hackathon_Architecture.docx`, outside this Markdown collection) — earlier design reference previously uploaded to this folder.

## Event references

- [Challenge brief](../../../Context/challengeWeb.md)
- [Judging criteria](../../../Context/judgingCriteria.md)
- [Tooling preparation](../../../Context/tooling.md)

The tooling notes contain explicitly marked inferences and open questions. Verify those before making implementation commitments. Use the current implementation boundary for the prototype status; use the newer hypotheses and learning-loop documents for the design developed in the discussion. If older references conflict, record the conflict rather than treating all documents as equally current.

## Suggested agent context

Read this guide and CURRENT_IMPLEMENTATION.md first, then the hypotheses document. Read the learning-loop document when working on scientist feedback or persistent memory. Load dataset and event details only when needed. Treat proposed mechanisms as hypotheses, retain scientific uncertainty, and keep synthetic demonstrations separate from experimental evidence. The full archive does not need to be inserted into every prompt.

## Source and maintenance

The five Context documents are copied from local repository commit `a361695` on `docs/translational-science-hypotheses` in [24edden/WilbeBioAIHack2026](https://github.com/24edden/WilbeBioAIHack2026). At the time this snapshot was prepared, that commit had not been published to GitHub. This collection now preserves those documents; the original commit history is separate. These shared files are a context snapshot; they do not replace the team's working code repository.

The original dataset and architecture files were already present and are retained. CONTEXT-MANIFEST.json records source details and SHA-256 values for this upload and the originals. Future updates should refresh the guide and manifest together and preserve any team edits. No automatic synchronization is configured.
