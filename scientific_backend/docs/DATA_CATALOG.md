# Live CAR-T data tools

The `cart-discovery` workspace lets the live bioinformatician choose studies,
inspect files, and compute new evidence. The reviewer can request another
analysis when a named evidence gap could change the decision. The server records
each accepted result before another specialist can cite its evidence ID. Study
and analysis choices come from the live agent; the underlying numerical readers
are deterministic and allowlisted.

The starting question remains the exact user-provided CD19 hypothesis. The
catalog contains source inventory evidence only. Opening the workspace, listing
files, or reading a schema does not become a completed biological analysis.

## What is available

The registry was built from read-only Brev source inventory on 2026-09-19:

* 19 GEO study groups, the prepared `LEON-BCMA` packet, and `TEAM-HYPOTHESES`.
* 726 registered files and archive members; 50,920,476,296 top-level bytes.
* GEO groups: GSE125881, GSE143317, GSE150992, GSE151511, GSE164551,
  GSE182891, GSE182892, GSE182893, GSE182894, GSE197215, GSE210079,
  GSE217245, GSE226327, GSE226335, GSE226336, GSE234261, GSE235760,
  GSE241783, GSE273170.

The selection matched CAR-T, CART, chimeric antigen, CD19, BCMA, or GPRC5D in
the shared study title/summary/design catalog. It deliberately includes related
mixed CAR-T/T-cell-engager studies and parent metadata series. Agents must
qualify sample-level treatment, cell population, timepoint, and cohort identity
before making a biological comparison. Archive members overlap their parent
files, and Leon's prepared matrices overlap their GEO source. These counts are
neither independent observations nor patients.

Metadata inputs are `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/integration/data_catalog.tsv`
(SHA-256 `efc2b5733a0d25d94d3c83fcd8012bb8ffc09bf42b9b2f2e08063338c63ad209`)
and `geo_series_attributes.tsv`
(`2ddc27cc04a7508e5f80931d77e7a43c0df533b36dfc0de7ab7632d0690aa8ee`).
The actual archive member names/sizes were enumerated read-only; source files
were not renamed, extracted into source folders, modified, or deleted.

The sanitized registry is `casepacks/sources/brev-cart-catalog.json`, itself
pinned in `casepacks/MANIFEST.json`. The registry includes expected shared-source
hashes from the acquisition catalog and direct hashes of the small Leon packet.
The entire 50.9 GB collection was not rehashed during inventory. Catalog entries
stay `catalog-unverified` until a selected file's bytes are verified.

## Tools and returned evidence

| Tool | Purpose |
|---|---|
| `list_datasets()` | Study titles, descriptions, size and file counts. |
| `get_dataset(dataset_id)` | Registered opaque file IDs, format, availability and applicable readers. |
| `inspect_data_file(file_id)` | Bounded text preview, HDF5 schema, MTX dimensions or archive member metadata. |
| `analyze_data_file(file_id, analysis_kind, parameters)` | Execute an allowlisted reader and return a source-linked `derived` evidence record. |
| `validate_catalog_evidence(evidence)` | Recheck recipe identity, canonical result hash and raw-source references against the registry. |

Analysis kinds:

* `table_profile`: source-order prefix, 1–100,000 rows (`max_rows`, default
  10,000), optional up to 20 `selected_columns`. Reports missingness, malformed
  row count, numeric summaries and whether the source was fully scanned. A
  prefix is explicitly not a random sample. JSON receives a bounded structural
  summary.
* `gene_summary`: 1–20 exact `genes` (symbols or feature IDs), optional
  `feature_type` (default `Gene Expression` for sparse matrices). Supports 10x
  HDF5, coordinate Matrix Market with registered features, nested matrix
  bundles, and qualified gene-by-observation text matrices. Missing genes are
  reported as missing, never replaced with zero-expression claims.
* `sparse_summary`: dimensions, stored sparse entries and sum of numeric values
  for supported HDF5/MTX/bundle sources. No parameters. All-feature totals can
  include multiple feature types; they are not automatically RNA-only totals.

HDF5/MTX gene summaries report sums, means over all source barcodes, and the
number of barcodes with nonzero values. HDF5 reads sparse arrays in chunks;
Matrix Market streams coordinates. Only the requested gene vectors are dense;
the complete expression matrix is never densified. The readers preserve source
units and do not infer normalization, malignant-cell identity, accessible
surface protein, CAR recognition, affinity, clinical response, or causality.
They perform no hypothesis tests or empirical p-value computation.

Evidence IDs are deterministic `DATA-<recipe digest>` values. Each evidence
record has `values.analysis_id = catalog:<kind>`, `case_id = cart-discovery`,
the registered file/study IDs, canonical parameters, raw `input_sources`, computed
`result`, and limitations. Its `source.sha256` hashes canonical compact JSON of
the derived values; it is distinct from the raw-file SHA-256 references. An
archive-member reference includes both member hash and enclosing archive hash.

## Runtime configuration and boundaries

Set the following only in trusted server configuration:

```text
TEAM_TBD_DATA_ROOT=/home/ubuntu/rosalind-shared-files
TEAM_TBD_LEON_ROOT=/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19/input
TEAM_TBD_HYPOTHESIS_ROOT=/home/ubuntu/ana-workspace/hypothesis
```

These are the defaults on Brev. Outside Brev, exact previously pinned compact
CD19 and BCMA files can run from their packaged copies. Other files correctly
report unavailable. Models supply registered IDs, never arbitrary paths,
shell commands, SQL or Python. Readers use read-only handles and do not extract
archives to disk. Hard-linked local HDF5 objects are required; soft/external
links, virtual datasets, unsafe tar paths and archive links are rejected.

Before selected-source analytics, the server verifies the expected full-file
SHA-256 (or enclosing archive hash). It rehashes selected enclosing files on
each verification: unchanged filesystem timestamps cannot prove immutable
content, particularly on network filesystems. Member digests may be reused only
after the enclosing archive's expected hash has just been reverified. Source
versions are checked again after analysis. Relevant limits are 10 GiB per
verified enclosing file, 512 MiB per archive member, 768 MiB expanded text or
nested-archive contents, 1,000 nested archive entries, 150,000 features,
300,000 barcodes, 80 million sparse entries, and 100 seconds per bounded scan.
Exceeding a bound raises an explicit failure, not a partial complete result.

Large Seurat/RDS objects, copy-number-specific HDF5, molecule-info HDF5,
bigWig and other unsupported formats remain discoverable metadata and require
dedicated adapters. The 35.4 GB GSE226327 CNV archive exceeds the automatic
enclosing-file verification limit. Listing every available study does not mean
every format has been analyzed. Missing inputs or unsupported formats must stay
visible in the scientific handoff.

## Validation and extension handoff

`tests/test_data_catalog.py` uses explicitly synthetic software fixtures to check
known HDF5/MTX numeric results, registered archive members, nested bundles,
missing genes, source mutation after cached verification, forged input hashes,
path/parameter bounds, malformed HDF5 shape/annotation arrays, external/virtual
HDF5 rejection, and archive bounds. These fixtures never enter production case
evidence. Existing compact case analysis tests cross-check actual pinned CD19,
ALK and BCMA inputs.

To extend source coverage, update the acquisition manifest and regenerate the
registry under review; preserve source hashes and stable IDs. Add a bounded,
format-specific reader with source-unit semantics and malformed-input tests.
For cross-sample biological inference, first add a qualified sample manifest,
patient/treatment/timepoint join and appropriate experimental-unit model. Do
not treat barcode totals or study membership as a clinical cohort analysis.


## Data preparation guidance and references

The scientific role skills recommend preparation and analysis according to the current question and experimental design; the catalog does not gain new readers from a skill change. See [general guidance and data references](DATA_ANALYSIS.md#general-preparation-and-analysis-guidance) for provenance, study/code links and the boundary between qualified external sources and implemented runtime recipes. Keep case-specific mappings, exclusions and expected results in those source records rather than reusable skill instructions.
