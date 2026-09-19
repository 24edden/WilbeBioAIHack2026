# Brev dataset delivery — 19 September 2026

Shared host: `agentic-takeoff-cpu`

Shared directory: `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/`

**469 available files, 63.44 GB, verified on Brev.** These counts include source data and essential metadata, not independent cohorts. All 469 catalogued files passed a full SHA-256 read-back against their acquisition manifests; the shared SQLite catalog passed its integrity check. Verification time: 2026-09-19T13:55:35.031830+00:00.

## Delivered

- GEO processed resistance and response packages, source metadata for all 43 catalog accessions, and 49 published series-matrix assets. The 35.4 GB GSE226327 single-cell copy-number archive, 6.48 GB GSE241783 CD19 CAR-T atlas and 222 MB GSE273170 longitudinal CAR-T RNA/TCR/protein archive are complete and validated.
- All four GSE197215 stimulation/control objects, including the previously missing unstimulated control.
- DepMap 24Q4, PRISM 19Q4, complete SU2C-MARK v3, official IMvigor210 v1.0.0, and the selected scPerturb protein subset.
- Maynard lung cohort metadata and processed expression reuse; ALK MSK 2026 clinical/mutation exports; 2022 lorlatinib-resistance clinical/mutation supplement; 2026 experimental ALK atlas.
- Orlando CD19 relapse publisher workbook (30,901 genes × 24 labelled samples) and accompanying supplements.
- PXD012000 breast-cancer pre/post-chemotherapy clinical and protein-abundance workbooks, with 35 clinical patient rows and sample identifiers.
- SKEMPI 2 (7,085 binding measurements), experimental PDB 12ER/2XP2/4MKC/6VJA/7JIC, Reactome references, and official September 2026 CIViC summaries.
- ClinicalTrials.gov: 5,041 unique studies matching the recorded query. FAERS: all 14 quarterly ASCII archives from 2023Q1 through 2026Q2. DailyMed: 23 source labels covering 19 therapy queries.

## Shared access for workers

Use `integration/data_catalog.tsv` or `integration/catalog.sqlite` to find available assets, source URLs and hashes. The SQLite tables also expose source GEO sample attributes and overlap flags. The index covers 41 experimental/clinical series (the two LINCS bulk releases are excluded), with 10,759 distinct GSM IDs and 1,771 IDs shared across series. These are assay/sample identifiers, not a patient count.

Each worker should keep original inputs immutable and write analysis outputs to its own directory. Preserve source patient/sample/assay identifiers and the original licenses. Downloads are ready for shared access; cohort-specific harmonization remains separate work.

## Remaining gaps

1. A sufficiently large, treatment-timed ALK baseline/progression cohort is still missing. The acquired public ALK datasets partially address it but do not provide complete longitudinal exposure and response fields.
2. Patient/biopsy/cell/assay/timepoint joins need study-specific validation. The overlap index prevents simple duplicate counting; it does not establish independent patients across publications.
3. Gene-level Orlando counts do not establish splice junctions. A suitable junction-preserving clinical assay is still needed for that claim.
4. A target-specific ALK/BCMA longitudinal proteomics cohort remains missing. PXD012000 supplies a breast-cancer chemotherapy comparison, with processed tables now acquired.
5. POG570 has explicit usage/redistribution restrictions; Hartwig, DAISY and other controlled components need their access routes. The 2019 ALK primary DOCX remains unavailable through the tested automated publisher/PMC routes.
6. Full LINCS bulk releases, additional CTRP/GDSC screens, and broad atlas portals are not completely mirrored. All 50 non-GEO catalog entries have a disposition in `CATALOG-DISPOSITION.md`.

Trials and FAERS add clinical and safety context; they do not replace longitudinal molecular evidence. This is a verified delivery of selected public packages, not a claim that all research gaps or every portal in the landscape are complete. See `GAPS.md` for exact qualifications and `integration/REMOTE-VERIFICATION.json` for the file-level read-back audit.
