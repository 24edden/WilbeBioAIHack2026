# Team TBD Results Capsule — 20 September 2026, v1

A frozen, read-only package for building another visual application from the completed scientific investigations and their preserved history. The private capsule contains **12 runs, 11 scientific decisions, 123 handoffs and 17 published artifact records**, plus eight structure-preview JSON files. Six runs completed; failed, blocked and budget-limited attempts retain their actual status.

## Where things live

| Location | Contents |
| --- | --- |
| This public GitHub folder | Safe catalog, JSON schemas, read-only JavaScript loader, offline verifier and integration guide |
| Brev `agentic-takeoff-cpu` | Full private capsule at `/home/ubuntu/team-tbd-frozen-results/team-tbd-results-capsule-2026-09-20-v1/`, with the ZIP and checksum beside it |
| Main live application | `/home/ubuntu/rosalind-hackathon-demo` on Brev; localhost:8081 is its private Mac tunnel |
| Isolated Ana application | Native Mac localhost:8082; its frozen results are copied into this capsule on Brev, but the application itself is not a Brev deployment |

The full capsule stays private because the exact exports include provider account identifiers and deployment paths. This repository does not contain the full results, credentials, raw omics data, runtime databases or proprietary installed plugin files. The catalog records trusted archive and manifest hashes without publishing the research payload.

## Start the visual app

1. Obtain the private ZIP through the existing team Brev access. Check its SHA-256 against `catalog.json`, extract it into a new private directory, then run `python3 verify.py .` inside that directory.
2. Serve the extracted directory as private static files. Load `manifest.json` and then `results.json`; use `loader.mjs` to verify files before rendering. It makes no inference calls and cannot submit saved actions.
3. Use `featured_run_ids` for the initial cards: the CD19 investigation with Ana relapse context, and the independent Ana hypothesis study. Both use the same GSE28460 cohort; do not label them independent clinical replication.
4. Read per-run `view.json` for presentation, `export.json` for the unchanged original, and `events.ndjson` for recorded activity. Resolve tables, CIF structures and preview geometry through `artifact-index.json`, not historical localhost URLs.

See [INTEGRATION.md](INTEGRATION.md) for the JavaScript example, rendering guidance and integrity model. Model outputs and source text must be escaped when rendered. Status `completed` is not proof of causation or human approval. Recommendations, prepared sequences, predictions and measured outcomes retain distinct status and scope. The same structure content can appear under separate successful NVIDIA request receipts; distinguish invocation counts from unique structures.

## Checks

The capture verified original export and decision hashes, all 17 artifact records, source stability and the absence of known credential patterns. Full traces remain private regardless of that credential scan. Four capture-boundary tests, four schema regression tests and eleven consumer tests passed. The final real package also passed schema validation for its manifest, results and all 12 views; an offline loader verified all 82 indexed files. Run the dependency-free consumer tests here with:

```sh
node --test test-loader.mjs
```

This folder describes one frozen version. New analyses should produce a new capsule version rather than modify this archive. It does not import records into either live database or disable the existing applications.
