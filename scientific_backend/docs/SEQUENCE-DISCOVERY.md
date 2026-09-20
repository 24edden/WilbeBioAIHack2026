# AI sequence discovery and attributable scientific skills

The R&D panel's **Find missing sequences with AI** action runs a molecular-science agent and an independent reviewer. They use the current scientist question and accepted findings to search UniProt and RCSB PDB, retrieve exact deposited constructs, and propose target/reference/candidate inputs. The question, accessions and sequence bytes are not hard-coded for CD19. Three complete inputs are not guaranteed: a missing qualified comparator remains a visible gap.

The public source tools execute the actual installed OpenAI Life Sciences Databases 0.1.5 source-specific skill scripts. Their source URLs, returned record hashes, retrieval times, exact sequence hashes, construct identities and attributed instruction versions are saved. The model selects trusted record IDs and never supplies amino-acid bytes. An isolated Fab heavy/light chain, a target isoform, an unresolved sequence or an unrelated binder cannot fill a complete binder field. Deposited complex context alone does not establish a patient's construct or superior binding. No target-retention checkbox or NVIDIA job is submitted by discovery.

A saved result fills empty fields and preserves user edits. Explicit role-selection actions can replace a field. The editable provenance field allows 6000 characters; all full source qualification remains in the saved discovery record. The completed monomer comparison stays separate from a proposed new binder comparison.

## Actual skill attribution

- **Rosalind-informed scientific workflow** is Team TBD-authored guidance based on [OpenAI's public Rosalind workflow description](https://openai.com/index/introducing-gpt-rosalind/). It is loaded with a version/hash receipt by the scientific investigation roles and both sequence-discovery roles. The separate interpretation writer and reviewer load their attributed role, research-interpretation, molecular-interpretation and BioNeMo guidance. It is not proprietary Rosalind model instructions.
- **UniProt and RCSB PDB** are actual OpenAI-authored installed Life Sciences Databases plugin instructions and client scripts, applied by molecular science and independent review during sequence discovery.
- **BioNeMo Boltz2** is the attributed installed NVIDIA skill. A skill receipt establishes instruction use; separate provider receipts establish actual NVIDIA inference.
- The actual research model remains **GPT-6 Astra/high**, the user-authorized placeholder. No skill grants GPT-Rosalind model access or changes the returned model identity.

The website distinguishes applied receipts from the registered catalog and verifies the external plugin installation before marking it available. Historical receipts are not silently relabeled when a current skill changes.

## Private plugin installation

The installed OpenAI package declares a proprietary license. Its selected installed files are kept in private `runtime/life-sciences-databases` (or the operator-configured `TEAM_TBD_LIFE_SCIENCES_PLUGIN_ROOT`) and excluded from source archives. `skills/external-runtime-manifest.json` pins the exact files and retains package author/version/provenance. Use your existing authorized installation; the app does not download executable plugin code.

Run `python scripts/install_scientific_runtime.py /path/to/installed/life-sciences-databases/0.1.5` to verify and copy the required installed subset into private runtime. The application requires `requests==2.34.2`, already included in the lockfile. Missing or changed runtime bytes fail closed before model dispatch. The deployment performed in this workspace uses the user's already installed package on their private Brev instance.

## Runtime handoff

`POST /api/runs/{id}/sequence-discoveries` accepts only `decision_version` and `idempotency_key`. Selection freezes the original hypothesis, current scientific evidence/decision/handoffs, interpretation context and exact instruction/model identity. The durable action is recorded before any model submission. Unknown external outcomes are never retried automatically; successful cached results publish without another search or model call.

`app/sequence_operations.py` owns selection, journaling and immutable publication. `app/sequence_discovery.py` owns the two real Agents SDK roles and strict source-ID selection. `app/sequence_sources.py` exposes four bounded public-source tools and runs the pinned source clients without vendor credentials. `sequence_discoveries` stores independently AI-reviewed results; `sequence_discovery_operations` records lifecycle, usage and partial readiness. Scientific decisions remain separate and human review remains pending.

Only allowlisted public endpoints are queried; callers cannot provide URLs, headers, filenames, scripts or amino-acid sequences. Complete public source response bytes are saved privately with content hashes. Credentials are excluded from the source client environment and public exports. Export verification checks discovery versions, source decision and exact sequence hashes.
