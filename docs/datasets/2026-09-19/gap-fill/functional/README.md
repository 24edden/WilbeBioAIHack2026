# Functional-screen gap fill

Acquired 19 September 2026 and mirrored to
`agentic-takeoff-cpu:/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/gap-fill/functional/`.

## Releases

- **DepMap 24Q4 Public** — official Broad Figshare article
  [27993248](https://doi.org/10.25452/figshare.plus.27993248.v1), published
  10 December 2024, CC BY 4.0. This is the versioned public release used for
  model metadata (`Model.csv`), gene metadata, profile mapping, integrated
  Chronos CRISPR gene effect, and processed protein-coding RNA expression.
  `PortalCompounds.csv` is retained for compounds that map to the broader
  DepMap portal.
- **PRISM Repurposing 19Q4** — official Broad Figshare article
  [9393293](https://doi.org/10.6084/m9.figshare.9393293.v4), published
  17 December 2019, CC BY 4.0. This stable, citable release provides the
  primary-screen replicate-collapsed log-fold-change matrix and treatment/model
  metadata, plus secondary-screen dose-response parameters and matching
  treatment/model metadata. The treatment and dose-response files contain the
  compound identifiers and annotations needed to join the response data.

The current DepMap portal advertises newer public releases, but its programmatic
bulk-download route returned an interactive access challenge in this acquisition
environment. No access control was bypassed. The two official versioned Figshare
release metadata responses are retained locally as JSON.

## Validation and provenance

`MANIFEST.tsv` records the release, direct publisher URL, acquisition time,
publisher byte count, SHA-256, terms, and status for every data file. Files were
downloaded to a `.part` path on the CPU, checked for the exact publisher byte
count and a nonempty final-file header, renamed atomically, and hashed. The local
mirror was subsequently checked against every recorded SHA-256. These datasets
are uncompressed CSV or text, so gzip CRC validation does not apply.

No CTRP or GDSC package was added in this pass: the requested DepMap/CCLE and
PRISM core data are complete, while an additional screen would add overlapping
scope rather than repair a remaining required gap.
