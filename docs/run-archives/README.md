# Team TBD frozen investigation results

This directory documents the portable, read-only archive format for another visual app to consume Team TBD investigation results. JSON is the structured entry point; tables, structures, images, and other files remain separate assets with relative paths and SHA-256 checksums.

The archive is a snapshot of completed and unsuccessful runs. Opening it does not restart agents, execute tools, contact model providers, or require an API key. Recorded summaries are scientific work products and review findings, not hidden model reasoning. Failed or partial runs retain their original status.

## Find a frozen run

The public `archive-index.json` lists only run IDs, titles, statuses, case IDs, execution environments, decision counts, and relative frozen-view paths. It intentionally excludes full prompts, evidence rows, provider request/account identifiers, and credentials.

The full trace bundle is held in the project's local workspace and shared Brev workspace. This GitHub repository is public; its import contract and safe index do not imply that the full internal trace bundle is public.

Current freeze: **`team-tbd-frozen-runs-20260920T110942Z`** · sealed 2026-09-20T11:16:38.130597+00:00.

- Brev directory: `/home/ubuntu/team-tbd-frozen-runs/team-tbd-frozen-runs-20260920T110942Z/`
- Brev ZIP: `/home/ubuntu/team-tbd-frozen-runs/team-tbd-frozen-runs-20260920T110942Z.zip` (33,666,287 bytes)
- Local project copy: `outputs/team-tbd-frozen-runs-20260920T110942Z/` and `outputs/team-tbd-frozen-runs-20260920T110942Z.zip`
- Start importing at `manifest.json`; see the [public run index](archive-index.json).
- ZIP SHA-256: `5da9f98f2857de91d9f0e93e3cf3bbc204e293bb58bbbaa2f523496831bb10d6`
- Manifest SHA-256: `68c450d7636bde8cff63577cde998fb17b6f1c92f91e5b2067c6aa72f70daa31`

With the existing authenticated Brev SSH alias, obtain the private bundle without either live service:

```sh
scp agentic-takeoff-cpu:/home/ubuntu/team-tbd-frozen-runs/team-tbd-frozen-runs-20260920T110942Z.zip .
shasum -a 256 team-tbd-frozen-runs-20260920T110942Z.zip
unzip team-tbd-frozen-runs-20260920T110942Z.zip
cd team-tbd-frozen-runs-20260920T110942Z
python3 tools/verify.py .
```

The freeze contains **12 histories**: 6 completed, 3 failed, 2 budget-exhausted and 1 blocked. One historical blocked request remains unresolved; archive creation did not retry it. All 17 published result artifacts and 8 frozen coordinate previews are included, plus supporting runtime payloads, public sequence responses and the eight GSE input files. Independent import checks matched 4,639 source records and 390 recorded model receipts.


## What belongs where

| Location | Purpose | Provenance boundary |
| --- | --- | --- |
| Brev `/home/ubuntu/rosalind-hackathon-demo`, service port 8080 | Original application and its persisted investigation history; accessed from the Mac through localhost:8081 | This deployed application has no Git checkout. Its source identity comes from a content-hash manifest, not a GitHub commit. |
| Local `team-tbd-ana-isolated`, service port 8082 | Separate Ana investigation runtime, database, source copy and frozen input copies | This fork ran on the Mac. Its data came from Brev, but that does not make its model/analysis execution a Brev run. Its source also has a content-hash identity. |
| Brev `/home/ubuntu/ana-workspace/datasets/agent_access/GSE28460` | Prepared GSE28460 inputs for the Ana cohort investigation | Eight pinned files were copied into the isolated app. The hypothesis wording and input versions are preserved in the full bundle. |
| This GitHub repository | Import contracts, public index, existing source references and team documentation | A publication commit identifies the archive documentation or snapshot. It must not be labeled as the commit that generated historical runs when the generating application had no Git history. |

Localhost links only work on the machine running the corresponding service. A frozen visual app should read the archive's relative paths; it should not depend on port 8081 or 8082 staying alive.

## Data references on GitHub

The **hyphenated** `hypothesis-dataset` branch contains Ana's GSE28460 package. Its pinned commit is `c4dc65124b573b17d5101eaf11b41827f9d62b4c`. All eight isolated-app input files matched that commit's Git blob identities byte-for-byte.

[Open the immutable eight-file GSE28460 input directory](https://github.com/24edden/WilbeBioAIHack2026/tree/c4dc65124b573b17d5101eaf11b41827f9d62b4c/ana-workspace/datasets/agent_access/GSE28460).

The **underscored** `hypothesis_dataset` branch contains a separate CD19 tumour-pair SRA package at `753c725a354ffb3ddf3aa52f77a1477319dae4bd`. The two branch names represent different datasets and must not be combined by name similarity.

The GSE28460 package also has evaluator materials elsewhere in that branch. Those materials were outside the eight-file agent input allowlist; they must not be presented as evidence the agents read. GSE28460 concerns paired diagnosis/relapse expression after conventional childhood B-ALL treatment. It is not a CAR-T response cohort.

## Import into a visual app

1. Obtain the full bundle from the verified local or Brev location above and verify its archive SHA-256 before extraction.
2. Read the bundle manifest and check its format version. Use the contract files in [`contract/`](contract/) to validate the data shape.
3. Populate the run picker from the bundle's index. Open each run's frozen visual view through its relative path; retain the original environment, status, evidence references, limitations, checks and decision versions.
4. Fetch referenced artifacts relative to the extracted bundle root and verify their SHA-256 values. Keep scientific measurements, derived analyses, model interpretations and NVIDIA predictions distinguishable in the UI.
5. Read recorded events in their stored order to display a replay. Label this as a frozen replay; do not show it as currently running agents or as new provider calls.

The supplied dependency-free reader validates asset bytes, run identity and original hypothesis identity. It performs focused checks; use the JSON Schemas for complete shape validation. A checksum manifest should come from the trusted frozen package: matching a checksum alone does not authenticate its author.

```js
import { loadArchive, loadRun, readVerified } from './contract/reader.mjs';

const archive = await loadArchive('/frozen-runs/manifest.json');
const recommended = archive.manifest.recommended_run_ids ?? [];
const entry = archive.manifest.runs.find(run => recommended.includes(run.run_id))
  ?? archive.manifest.runs[0];
const { view, raw } = await loadRun(archive, entry);

// Render untrusted text safely. Preserve null as “not captured.”
document.querySelector('#hypothesis').textContent = view.hypothesis.text ?? 'Not captured';
document.querySelector('#status').textContent = view.state.status ?? 'Not captured';

// Decisions retain versions, references and limitations in decision.data.
// The full source object remains accessible in raw through each raw_pointer.
const includedAsset = view.artifacts?.find(asset => asset.status === 'included');
if (includedAsset) {
  const bytes = await readVerified(archive.baseURL, includedAsset.file);
  // Select a safe renderer using includedAsset.file.media_type.
}
```

Do not derive chronology from opaque run IDs. Use the explicit index and recorded event timestamps/sequence. Missing assets and unsuccessful operations remain visible as recorded; a follow-up recommendation does not prove execution.

Contract-only checks require Node 20 or newer and make no provider calls:

```sh
node --test docs/run-archives/contract/reader.test.mjs
```

Serve an extracted bundle over local HTTP or a controlled project origin to use browser `fetch`. A browser may block requests from a `file://` page. The importer does not need the live application or model credentials.

Source and input inventories describe what is available at the freeze point. If exact historical generating-source bytes are unavailable for an older run, retain that limitation explicitly; current code must not silently be substituted as its historical source.

## Scope and interpretation

A successful integrity check shows that the files match the frozen snapshot. It does not validate a biological mechanism, endorse a model conclusion, or make an unsuccessful run successful. The scientific conclusions and limitations remain those recorded in each run's decisions and reviews. For service attribution, display the actual recorded model and actual executed NVIDIA tools; a skill being available or consulted is distinct from a service being executed.
