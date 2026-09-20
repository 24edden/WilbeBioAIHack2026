# Team TBD frozen run import contract

Version **1.0.0**. Start with **`manifest.json`** in the exported bundle. JSON is the interchange format; large tables, images and molecular files stay as separate, hashed assets. An independent visual application needs no Team TBD backend, API key or model access to read the archive.

This directory is safe to publish as integration documentation. It contains no run traces, hypotheses, sample data or credentials. The full archived bundles may contain unpublished research and belong in the access-controlled locations recorded by the project owner.

## Two layers of evidence

1. **Raw export:** The complete application JSON export, including `run` and `case_manifest`, preserved unchanged and hashed as exact bytes. It is authoritative for what that run recorded. It is the application's public export, not a claim that every private database table or provider-side trace was exported.
2. **Run view:** A versioned navigation index for another UI. Every copied record keeps its original `data` and an RFC 6901 `raw_pointer` into the raw export. Decisions, failures, qualifications, source versions and review states remain available. A normalization cannot upgrade a scientific claim or execution status.

`manifest.schema.json` describes the bundle entry point. `run-view.schema.json` describes the normalized run. Both are standalone JSON Schema Draft 2020-12 documents. `types.ts` provides interfaces; `reader.mjs` provides a dependency-free browser importer with byte-hash and identity checks. It does not replace full JSON Schema validation.

## Recommended layout

```text
manifest.json
CHECKSUMS.sha256
runs/<environment-id>/<run-id>/raw-export.json
runs/<environment-id>/<run-id>/view.json
runs/<environment-id>/<run-id>/report.md
assets/sha256/<sha256>/<safe-filename>
contract/manifest.schema.json
contract/run-view.schema.json
contract/types.ts
contract/reader.mjs
```

Every `FileRef.path`, even inside a nested run view, resolves from the **directory containing `manifest.json`**. It never resolves from the run view's own directory. Paths are relative and cannot contain parent traversal, a scheme, a query or a fragment. Filenames and layout are illustrative: readers follow the references, not a guessed path convention.

Each `FileRef` contains the exact-byte SHA-256, byte length and nullable media type. These hashes differ from the application's `content_sha256`, which hashes a canonical subset of the raw export. Preserve both. The manifest cannot hash itself; use a separate checksum/release record for that. Hashes detect changes against the recorded manifest; without a separately trusted digest or signature they do not authenticate an archive's author.

Assets are content-addressed when collected. Multiple logical asset records can share one `FileRef`. If a file is missing, excluded, unavailable or only an external reference, retain that asset record with `file: null` and its explicit status. Never create a placeholder image that looks like a successful scientific result. A source hash and provenance record can exist even if the corresponding input dataset was intentionally not bundled.

## Import example

Serve the extracted bundle over HTTP(S), including a localhost static server. Opening it directly with `file://` will not provide consistent browser fetch/Web Crypto support.

```js
import { loadArchive, loadRun, resolvePointer, readVerified } from './contract/reader.mjs';

const archive = await loadArchive('/frozen-runs/manifest.json');
const preferredId = archive.manifest.recommended_run_ids?.[0];
const entry = archive.manifest.runs.find(r => r.run_id === preferredId)
  ?? archive.manifest.runs[0];
const { view, raw } = await loadRun(archive, entry);

// Preserve exact wording and display the snapshot's recorded status.
document.querySelector('#hypothesis').textContent = view.hypothesis.text ?? 'Not captured';
document.querySelector('#status').textContent = view.state.status ?? 'Not captured';

for (const decision of view.decisions ?? []) {
  const original = resolvePointer(raw, decision.raw_pointer);
  console.log(original.version, original.assessment, original.limitations);
}

const image = view.artifacts?.find(a => a.status === 'included'
  && a.file.media_type?.startsWith('image/'));
if (image) {
  const bytes = await readVerified(archive.baseURL, image.file);
  // Render from verified bytes; sanitize or sandbox SVG and HTML first.
}
```

Choose a run explicitly by `environment_id` and `run_id`, or use the curator's `recommended_run_ids` and `selection` rationale. Run IDs are opaque: their lexical order has no chronological meaning. Use recorded timestamps to implement a timeline and retain decision versions independently. Two environments may contain copies of the same run ID; preserve both environment identities.

## Fields for a visual app

| View field | Intended display | Source behavior |
| --- | --- | --- |
| `hypothesis` | Exact submitted question, source and hash | Preserve whitespace; never substitute a rewritten summary or case default |
| `state`, `as_of` | Recorded status and snapshot time | Failed, cancelled, stopped, partial and unknown states stay distinct |
| `datasets` | Inputs, versions and provenance | Prepared derivatives must not be labeled original downloads |
| `evidence` | Source and derived evidence browser | Evidence IDs resolve citations; artifacts have separate byte hashes |
| `findings`, `decisions`, `briefs` | Insights, decision history and concise narrative | Keep scope, limitations, human review status and originating decision version |
| `handoffs` | Sender → recipients and acceptance checks | Accepted work does not imply the conclusion is scientifically proved |
| `claims` | Observation/interpretation/prediction with citations | Retain literal evidence IDs and source URLs; no guessed citations |
| `timeline` | Recorded agent/tool events | Public rationale and work products, not private model chain of thought |
| `quality_checks` | Contract, citation and stage checks | Passing an engineering check is not biological validation |
| `followups` | Proposed analyses, modeling or wet-lab plans | A suggestion or draft request is not evidence of execution |
| `executions` | Actual recorded actions/operations and their statuses | An attempted/failed request is not a completed result |
| `artifacts` | Actual downloadable result tables, structures and images | Only `status: included` has a bundled, verified file |
| `skills` | Applied instruction identity, version and origin | A Rosalind-informed skill does not mean a GPT-Rosalind model call |
| `models` | Actual model/reasoning receipts and usage | A configured provider does not mean it was invoked; unrecorded effort is null |
| `source_locations` | Where the snapshot originated | Display source references; never fetch private source paths automatically |

Arrays are `[]` only when the source was captured and known empty. They are `null` when unavailable or not captured. Missing strings, IDs and measurements are `null`; never replace them with zero, an empty string, a plausible value or a neighboring run's information. `Record.id` can be null if the original record had no stable ID. Collector-generated wrapper IDs are navigation conveniences; do not mutate the source `data`.

A `raw_pointer` references the exact raw export, for example `/run/decisions/0`. RFC 6901 escapes `~` as `~0` and `/` as `~1`. A pointer may be null only for an external record, whose `data` must identify its bundled `source_file`. A field absent from a source version is not grounds to reconstruct a plausible record. The full raw export remains available to resolve implementation-specific fields that are intentionally not flattened.

## NVIDIA and Rosalind attribution

Display these separately:

- **Instructions consulted:** recorded skill receipt and source/version.
- **Model called:** recorded model identity, reasoning level when present, request/usage receipt and status.
- **Service proposed:** a recommendation or draft in `followups`.
- **Service attempted/completed:** an action in `executions` with its actual status.
- **Output collected:** an included asset with a verified file hash.
- **Scientific interpretation:** scoped conclusions and limits from the related evidence/decision.

A NVIDIA skill receipt, capability check, sequence search or modeling recommendation cannot be counted as successful NVIDIA inference. A returned predicted structure is a computational prediction, not an observed clinical mechanism or treatment benefit. If a run judged structural modeling unsuitable, display that disposition; do not borrow a structure from another run.

## Freeze and update behavior

The archive is an **as-of snapshot**. Freezing a bundle does not shut down its originating app or prevent future feedback in that app. Later runs or decisions create a new bundle/revision, leaving prior file bytes and references intact. Record collection start/end times, source code revision, source environment and any consistency checks in manifest provenance. If a source was still changing, explicitly record that limitation rather than label it a terminal, internally consistent freeze.

The public GitHub integration guide and run index may link to an access-controlled full bundle. Do not publish raw research traces, input datasets, credentials or internal service receipts merely because the contract itself is public. Source paths, source code repository, source revision and archive destination should remain separate fields so users can tell what lives on Brev, locally and on GitHub.
