# Existing-artifact molecular interpretation

`app/molecular_interpretation.py` adds a read-only audit after an investigation.
It does not make another NVIDIA or OpenAI call, edit a decision, accept new
scientific evidence, or change a hypothesis state. A newly generated GPT research
brief can cite this separately hashed derived audit. It must distinguish these new
calculations from what the original investigators saw.

## Integration

```python
from app.molecular_interpretation import audit_molecular_evidence

audit = audit_molecular_evidence(run, artifact_root=RUNTIME)
# Supply as extra_context={"molecular_audit": audit} to the research-brief model.
```

For a downloaded/exported structure, pass `artifact_paths={accepted_sha256: path}`.
The map is an explicit server-side input, never model-written file paths. Runtime
resolution uses only the run's registered artifact URLs under `runtime/artifacts`.
No absolute runtime paths, headers, credentials or raw job/request bodies are
returned to the model or browser.

The public result contains:

- `schema_version`, `run_id`, `status`, `audit_sha256`: deterministic audit identity.
- `sequence_inventory`: exact verified sequences, length, chain, stable ID
  (`sequence-` plus the first 20 sequence-SHA256 characters), role, evidence and
  artifact identity, request ID and source/mapping provenance. A saved isolated
  public target is `role=target`; an unqualified role is `unassigned`. This version
  audits accepted public monomer follow-ups, so it never invents a binder entry.
- `comparisons[].predictions`: individual artifact checks, model-level confidence,
  local metric values/regions and saved request audits.
- `settings_comparison`: exact submitted non-sequence fields compared by hash.
- `alignment_sensitivity`: reproducible geometric comparisons with exact selected
  sequence positions, fit definition and limits.
- `method_sources`, `limitations`: explicit interpretation rules and official references.

`status=completed` means the available artifact audit succeeded, not that a
mechanism, binding claim, study result or clinical cause is established. Missing
CIFs produce `partial` with empty/unverified sequences; missing job/request files
leave settings `unavailable` while a SHA256-matched CIF can still be interpreted.
There is no fallback to assumed sequences or advertised provider defaults.

## Sequence and artifact integrity

The accepted evidence content hash must match and its follow-up result must be
completed. Published artifact hashes must match the evidence inventory. Each CIF
must match its recorded hash and unique label/request receipt, contain a bounded
single protein chain with finite coordinates, a complete C-alpha backbone and
standard amino acids, and reproduce the exact recorded sequence hash and length.
Symlink traversal, cross-run URLs and path traversal are rejected.

The resulting sequence registry is authoritative only about those saved modeling
inputs. Target retention is always `false` as an *established evidence flag*;
it does not mean the target is known to be absent. Do not automatically check the
form's retention checkbox. A deleted target is another target sequence, not an
alternative CAR-binding domain. A binder design form remains incomplete until
real, qualified reference/candidate binder sequences and relevant retention
evidence are supplied.

## Confidence and request semantics

The audit reads `_ma_qa_metric_local` only when its declaration explicitly names
local pLDDT, and checks residue/model identity, coverage, uniqueness, finiteness
and range. It never treats arbitrary B factors as pLDDT. The raw values and their
observed range remain unchanged.

The ModelCIF dictionary defines generic pLDDT on 0–100 and has distinct normalized
pLDDT names for 0–1. The saved NVIDIA files in this run use generic `pLDDT` while
values are all below 1. This is reported as `scale_ambiguous=true`, not silently
converted to percentages. Means and regions are summaries of raw fields. A
numeric cutoff is a descriptive sensitivity choice, not a calibrated accuracy
threshold. [ModelCIF metric types](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_ma_qa_metric.type.html).

NVIDIA's structure-level confidence is kept separately from local pLDDT. The
current API documentation describes those as different output fields and makes
full PAE optional; none is invented if absent. The documentation version does
not establish the deployed endpoint version for an old request.
[NVIDIA Boltz2 inference reference](https://docs.nvidia.com/nim/bionemo/boltz2/1.8.0/inference.html).

Saved `job.json` must match the successful accepted request/model/sequence/artifact
receipt. Its request hash must match `request.json`, whose polymer sequences must
match the CIF. Every submitted request field except polymer sequence participates
in the settings-comparison hash, including supplied MSA/template material. The
public summary exposes selected numeric settings and presence flags. Unrecorded
backend version, effective defaults or seed remain unknown. Two matching requests
do not establish identical sampling realizations or calibrate their errors.

## Alignment method

A pair is eligible only when its recorded canonical bounds/deletion exactly
reproduce the longer and shorter verified sequences. No unrelated sequence
alignment is guessed. The same sequence correspondence is used for all proper
rotation Kabsch C-alpha fits; no outliers are trimmed.

The fixed report includes all shared residues, the segments before/after the
recorded deletion, and each consecutive third of the shared sequence. These
thirds are computational subsets, not annotated protein domains. If local fields
exist, it also reports a subset using raw metric >= 0.7 when all observed values
are <= 1, otherwise >= 70. The ambiguity flag travels with that fit. Selected positions
are retained so another analyst can reproduce or reject the cutoff.

Each subset is fitted independently. Subset RMSD answers a different geometric
question from whole-construct RMSD. A favorable local fit does not establish
that either predicted structure is accurate, that a functional epitope is
preserved, or that binding is unchanged. These are post hoc descriptive checks,
not new independent samples or significance tests.

## Actual saved run check (2026-09-20)

The local exported files from run `b5898d6c3b3940ee9eac90f01b8b8e19` were checked
without a service call or changes to the run:

| Result | Reference | Exon-2-deleted target |
|---|---:|---:|
| Exact target length |272 aa|183 aa|
| Native local pLDDT-field mean |0.624603|0.571508|
| Provider structure confidence |0.499681|0.457193|

The sequence mapping removes canonical residues 30–118 from the modeled 20–291
region. Both sequences are target monomers; neither is a binder.

Whole shared-backbone RMSD reproduced **12.470842 Å across 183 positions**. The
explicit raw-field >= 0.7 sensitivity subset contained 46 positions and fitted at
**0.567024 Å**. Because the pLDDT encoding has the ambiguity described above, this
subset is not labeled a validated high-confidence core. The large difference
between all-residue and subset fits demonstrates sensitivity to the modeled
regions included; a broad claim that the service proved global unfolding or
binding loss is unsupported. These findings can refine the next experiment
without concealing the biological hypothesis supported by other assay results.

The exported CIFs lacked their adjacent private job/request records, so that
local-export check correctly reported settings as unavailable. On Brev, the
same callable additionally verifies the saved request files if present. Do not
claim a live settings check until its returned result is inspected.

## Validation

`python -m pytest -q tests/test_molecular_interpretation.py` exercises synthetic
receipts/CIFs and numerical invariants. Tests cover source/artifact and sequence
corruption, missing local confidence, invalid values, metric scaling, saved
settings mismatch, non-sequence request differences, absent files, explicit
export paths, cross-run/path traversal and symlink refusal, absent correspondence,
rigid-motion invariance, and no mutation of historical decisions. Synthetic
fixtures are never represented as NVIDIA or biological validation.
