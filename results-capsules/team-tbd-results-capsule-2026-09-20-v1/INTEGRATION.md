# Frozen results consumer

This contract describes a read-only snapshot of Team TBD research outputs. Loading it performs no model inference, NVIDIA submission, analysis, scientific review or state restoration into a live app. Original exports remain separate from the presentation views. A frozen successful result does not make every proposed follow-up executed or every scientific conclusion proven.

The package identity is `team-tbd-results-capsule-2026-09-20-v1`; its schema is `team-tbd-results-capsule/1.0`. `manifest.schema.json` validates the manifest; `results.schema.json` validates the complete results catalog and exposes its `$defs.runView` contract for an individual run view. Its manifest, file and run-record fields are strict. Source/location metadata and view details permit additive fields. A new package identity or schema requires an intentional consumer update.

## Restore files and load

Extract the capsule into a new directory and retain its relative layout. Do not copy exports into an application's runtime database, overwrite a source run or submit saved actions. Serve the directory as static files over localhost or HTTPS; browser Fetch cannot reliably load a `file://` directory. Keep it private unless its owner explicitly authorizes publication.

```js
import { loadCapsule } from "./loader.mjs";

const capsule = await loadCapsule("http://127.0.0.1:8090/capsule/", {
  // Optional but recommended: independently recorded SHA-256 of manifest.json.
  expectedManifestSha256: trustedManifestHash,
});

for (const run of capsule.results.runs) {
  const title = document.createElement("h2");
  title.textContent = run.label;
  document.querySelector("main").append(title);
}

const view = await capsule.loadRun(capsule.manifest.featured_run_ids[0]);
const rawPath = capsule.manifest.runs.find(r => r.run_id === view.run_id).raw_export_path;
const originalExport = await capsule.readJson(rawPath);
```

Use `createCapsuleLoader(baseURL, options)` instead if the application should fetch individual views on demand. `readBytes(path)` returns verified bytes for a manifest-listed path; `readJson(path)` also checks valid UTF-8 JSON. `loadArtifactIndex()` reads the indexed artifact catalog. The consumer uses only GET requests, omits credentials, refuses redirects and never calls an app or provider API.

Both loader entrypoints accept injected `fetchImpl` and `cryptoImpl` for offline tests. Defaults use browser Fetch and Web Crypto. `maxManifestBytes` defaults to 5 MiB and `maxFileBytes` to 128 MiB. Raise the latter deliberately for a larger known artifact; a file exceeding it is refused before fetching. File reads are bounded while streaming, then checked against the manifest's exact byte count and SHA-256 before parsing or returning content.

The manifest is the integrity trust anchor, not a digital signature. It cannot authenticate itself or prove the scientific interpretation. Pass an independently obtained `expectedManifestSha256` to detect a replaced manifest; the manifest intentionally does not list itself. SHA-256 detects a changed file relative to that manifest. The run's `source_content_sha256` identifies the frozen source content according to the producer; it is distinct from a file's exact-byte hash.

## Rendering rules

- Show the preserved question and its provenance before the answer. Render findings with their evidence references, supported scope and caveats. Preserve separate decision versions and human-review status.
- Show specialist work products, handoffs, checks, debates and decision rationale as recorded outputs. These are scientific explanations and execution traces, **not private chain of thought** or a complete record of internal model reasoning.
- Distinguish proposed, queued, running, completed, failed, blocked and unknown outcomes wherever the source records them. A recommendation, prepared sequence form, installed skill or configured provider is not an executed experiment. Unknown external work must not be replayed by this consumer.
- Keep the actual model identity and applied-skill receipts visible. Locally authored Rosalind-informed guidance does not establish GPT-Rosalind model access. A successful NVIDIA receipt and verified artifact support an executed prediction; a prediction does not establish binding, clinical efficacy or patient causation.
- Preserve original identifiers and links to the immutable export for audit. A `source_reference` is an opaque provenance locator: it may describe a private host path, historical route or source record. It is **not a public URL** and must never be automatically fetched, made clickable or resolved against a browser location.
- Only manifest-listed capsule paths may be passed to this loader. Paths cannot contain traversal segments, URL schemes, backslashes, encoded characters, queries or fragments. Missing artifacts stay visibly unavailable; do not substitute an external source or invent a local file.
- Treat all titles, model text, source strings and reports as untrusted content. Use `textContent` or a safely escaped template. If Markdown is rendered, disable raw HTML and sanitize links. Do not insert exported HTML directly into the page or execute scripts embedded in artifacts.

The artifact index connects an output to its copied package path, hash and availability information. Read the verified index before selecting a file, and use its actual packaged path with `readBytes`. Do not infer success or availability from an artifact filename, a plot or a source URL. MIME metadata is a display hint, not permission to execute content. For image previews, create a Blob only from verified bytes and an appropriate non-executable image format; revoke temporary object URLs when finished.

## Testing and compatibility

Run `node --test test-loader.mjs` from this capsule contract directory. The tests use local in-memory Fetch responses; they make no network or provider calls. They cover successful catalog loading, traversal and unindexed files, changed bytes, size bounds, manifest identity and integrity, redirects, and run-identity mismatches.

The JSON schemas express document shape; the dependency-free loader additionally checks unique file/run paths, listed entrypoints, featured-run membership, catalog identity, exact bytes and hashes. It intentionally does not validate the scientific meaning of free-form view sections. The original run export and its own verifier remain the authoritative detailed record; rendering a capsule must not alter or silently upgrade that record.
