# Shared Rosalind data on Brev

Host: `agentic-takeoff-cpu`

Shared root: `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/`

Start with `integration/catalog-summary.json` for current counts, `integration/data_catalog.tsv` for available files and exact provenance, or `integration/catalog.sqlite` for querying assets and GEO sample attributes together. The database has `assets`, `geo_samples`, `geo_attributes` and `geo_sample_overlap` tables. An asset's `available=1` means a final physical file exists with a recorded SHA-256; consult source receipts for validation details.

Read `GAPS.md` for scientific/access gaps, `CATALOG-DISPOSITION.md` for the 50 non-GEO resources, and `DATASET-SOURCE-CATALOG.md` for the original landscape.

| Location | Contents |
|---|---|
| `geo-resistance/` | CD20, BCMA/GPRC5D and CD19/CAR-T packages and metadata |
| `geo-response/` | I-SPY2, checkpoint/targeted-therapy response studies and selected LINCS files |
| `external/` | Complete SU2C-MARK source ZIP, scPerturb subset, PDB structures, Reactome |
| `alk-atlas/` | Original 2026 experimental ALK atlas supplements |
| `gap-fill/functional/` | DepMap 24Q4 and PRISM 19Q4 screens and identifiers |
| `gap-fill/longitudinal/` | Maynard data, ALK MSK clinical/mutation tables and ALK primary supplement |
| `gap-fill/binding/` | SKEMPI 2 and exact experimental structure entries |
| `gap-fill/pharmacology/` | DailyMed source XML, query results and searchable derived sections |
| `gap-fill/orlando/` | Official CD19 relapse count workbook and publisher supplements |
| `gap-fill/proteomics/` | PXD012000 processed clinical and protein-abundance workbooks |
| `gap-fill/civic/` | Dated clinical evidence and variant knowledge-base snapshot |
| `gap-fill/imvigor210/` | Official IMvigor210 v1.0.0 processed expression/clinical package |
| `clinical-context/clinicaltrials/` | 5,041-trial query snapshot, raw pages and deduplicated records |
| `clinical-context/faers/` | 14 quarterly ASCII source archives, 2023Q1–2026Q2 |
| `integration/` | Shared catalog, GEO sample tables, published series matrices and overlap flags |

Treat original assets as immutable. Write each worker's analysis outputs to a distinct new directory, keeping source patient/sample/assay identifiers and input checksums. Shared GEO identifiers flag overlap, not independent validation. The index is not a harmonized clinical data model.

Source manifests and `archive-completion.json` files distinguish downloaded, validated, partial, deferred and inaccessible assets. Never analyze `.part`, `.partial`, `.assembling`, quarantined or incomplete objects. Older per-worker blanket deferrals may be superseded by archive-completion receipts and the shared catalog.

To refresh the catalog after another download completes, run `python3 integration/build_shared_catalog.py /home/ubuntu/rosalind-shared-files/datasets/2026-09-19` from the shared root. This rebuilds the catalog from receipts; it does not download or revalidate file contents.
