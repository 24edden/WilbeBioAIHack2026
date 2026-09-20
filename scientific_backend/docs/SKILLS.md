# Scientific skills used at runtime

Team TBD loads versioned scientific instruction modules into the actual specialist model context. Each module has a registered ID, applicable roles, content SHA-256, version and provenance. The worker accepts a durable receipt before the model works. Handoffs must cite the same role's current-operation receipts and versions. Unknown IDs, role mismatches and modified files are rejected.

The nine role modules translate the scientist-supplied architecture into instructions for clinical framing, bioinformatics, statistics, pharmacology, molecular science, translation, assay design, coordination and independent review. These are Team TBD modules, not proprietary OpenAI model weights or an entitlement mechanism.

The molecular role additionally loads the installed NVIDIA BioNeMo toolkit's **Boltz2 NIM** skill, including the hosted/local request contract and the limits of structural inference. Its original attribution and license identifiers are retained in `skills/bionemo-boltz2/SKILL.md`; supplemental API/science/validation references are included. The executable provider implementation enforces exact sequence inputs, server-owned destinations and validated returned mmCIF artifacts.

The Skills view distinguishes the available registry from the receipts loaded during an actual run. The run export includes those receipts; work products include their IDs and hashes. An applied skill does not prove that a related external service was invoked. Model calls and BioNeMo actions have separate provider receipts and status.

The user authorized **GPT-6 Astra, high reasoning**, as the temporary reasoning model. This activates the scientific workflow and tools while GPT-Rosalind API entitlement is unavailable. The UI must name Astra when Astra returned the result; it must not label that inference GPT-Rosalind. Once an entitled project is available, set `TEAM_TBD_MODEL=gpt-rosalind-research`, run the capability probe, and inspect the returned model identity.

NVIDIA inference remains a separate acceptance gate: supply `NGC_API_KEY`/`NVIDIA_API_KEY` or a trusted running `BOLTZ2_NIM_URL`, supply exact qualified constructs, and receive a complete validated matched prediction. A missing service or incomplete job remains visible, without fabricated artifacts or scores.
