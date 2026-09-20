# Pinned evidence case packs

The public repository intentionally omits six larger/raw input/reference files.
Before following the hydrated-case instructions below, use the hash-checked
[source installation steps](../SETUP.md#install-pinned-scientific-inputs-privately).
`EXTERNAL-INPUTS.json` lists the omitted files; `MANIFEST.json` preserves all
original source pins. Their absence is an explicit setup requirement, never a
reason to weaken integrity checks or fabricate evidence.

Three portable packs ship with real public evidence and source provenance:

| ID | Starting point | Current supported scope |
| --- | --- | --- |
| `cd19-car-t` | Exact Brev hypothesis with H1–H5 | Qualify CD19 library evidence; distinguish what measurements would select escape versus retained-target failure |
| `alk-l1196m` | Project's assay hypothesis | Extract and adjudicate drug-specific source labels |
| `bcma-gse164551` | Prepared Brev patient-case question | Preserve sample corrections, post-treatment timing and truncation limits |

`build_cases.py` rebuilds the JSON packs offline from `sources/`. `MANIFEST.json` pins source and pack hashes. `python casepacks/build_cases.py --check` verifies reproducibility without rewriting files. `app.cases.get_case(id)` validates integrity and returns a fresh dictionary; `list_cases()` returns selection cards. See `docs/SCIENCE.md` for interpretation boundaries.

The compact packet is already hydrated; no network connection is required for a demo. It includes the 946 KB ALK workbook, the two CD19 minigene tables, original CD19 text, compact BCMA input tables and an exact source-metadata excerpt. Large single-cell objects remain in the team's existing Brev workspace.

`demo_decision` is a curated deterministic assessment for the demonstration mode. It is not a captured GPT-Rosalind response. `data_mode=public_evidence` describes the source data, independently of whether the application runs a live model or displays the curated demonstration. No fabricated patient observations or candidate structures are included.

Each handoff contains a planned `experimental_arm` in the shared `candidates` collection so an outcome can refer to a server-assigned experiment/arm ID. Its status is `planned`, exact construct sequences are missing, and BioNeMo modeling remains blocked. These assay plans must not be presented as generated molecular candidates or completed experiments.

## Brev source handoff

Original read-only locations:

- `/home/ubuntu/ana-workspace/hypothesis/CD19_CAR_T_.txt`
- `/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19/input/`
- `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/` (shared scientific datasets)

The compact remote files were copied on 19 September 2026 and verified against `sha256sum` output from Brev. Refresh a source only as a deliberate case version change. Copy into a new staging folder, inspect identity/timing, compare the old hash, rebuild derived evidence, run checks and preserve the previous manifest in the investigation's export. Do not mutate the shared scientific workspace during service execution.

Keep study attribution and original reuse terms with any redistributed source files. Public accessibility is not a replacement for source-specific license review. This bundle is for the team's research demonstration and makes no new licensing claim.
