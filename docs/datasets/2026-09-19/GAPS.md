# Acquisition gaps and scientific priorities

Audit: 19 September 2026. Shared destination: `agentic-takeoff-cpu:/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/`.

Use `integration/catalog-summary.json` for the current completed-file count, `integration/data_catalog.tsv` for per-file status/provenance, and `CATALOG-DISPOSITION.md` for all 50 non-GEO source entries. Files, GEO sample identifiers, patients, and independent cohorts are different counts.

## Gaps repaired

- **Shared delivery:** data now live on the existing Brev CPU. Source manifests retain exact URLs, sizes and SHA-256 values; remote verification records are retained.
- **Functional and drug response:** DepMap 24Q4 gene effects, expression and model/gene metadata; PRISM 19Q4 primary and secondary screens with model/treatment metadata. These are frozen public releases, not the entire current portals.
- **ALK evidence:** the 2026 experimental ALK atlas; Maynard lung cohort metadata and a documented processed-expression reuse; cBioPortal ALK MSK 2026 clinical/mutation tables; and the 2022 lorlatinib-resistance supplement.
- **Curated evidence:** official 1 September 2026 CIViC clinical evidence, variant and molecular-profile summaries.
- **Binding evidence:** public SKEMPI 2 table (7,085 rows), experimental PDB 12ER, 2XP2 and 4MKC, plus previously acquired 6VJA and 7JIC. The earlier claim that SKEMPI required login was incorrect.
- **Clinical context:** 5,041 unique trial records for the recorded query, all 14 FAERS quarterly ASCII archives for 2023Q1–2026Q2, and 23 DailyMed labels covering 19 therapy queries.
- **Response cohorts:** complete SU2C-MARK v3 source ZIP, official IMvigor210 v1.0.0 expression/clinical package, selected GEO response packages and original source metadata.
- **Controls:** all four GSE197215 processed objects, including CD19 stimulation, CD3/CD28, mesothelin and unstimulated conditions, reacquired and validated. The earlier damaged partial is excluded.
- **Additional source context:** original GSE194040 I-SPY2 intensity tables and GSE50509 GPL10558 annotation tables acquired. GSE196096 shares the I-SPY2 sample files; GSE99898 references the same GPL annotation filenames. GSE25066 native CEL files remain optional because processed expression is available.
- **Discovery and joins:** all 43 catalog GEO accessions have SOFT metadata; 41 clinical/experimental series are in a sample index, excluding the two bulk LINCS releases. The index contains 12,530 series/sample memberships, 10,759 distinct GSM identifiers and 1,771 GSM identifiers shared across series. This supplies source joins and overlap flags, not completed patient harmonization.
- **Misclassified archives:** official GEO metadata confirms that several `RAW.tar` packages contain processed expression, TCR, protein or copy-number data. Their acquisition receipts override older blanket deferrals. GSE226327, GSE241783 and GSE273170 are complete and archive-validated; see `DELIVERY-REPORT.md` and its read-back audit.

## Remaining scientific and access gaps

| Gap | What is actually missing | Disposition |
|---|---|---|
| Longitudinal ALK validation | A sufficiently large cohort with matched baseline/progression molecular data, treatment exposure and response timing | Partially filled. Maynard has 30 patients/49 biopsies, nine ALK patients/13 biopsies and one confirmed ALK treatment-naive/residual-disease pair. The 2022 supplement has 47 patients/48 post-lorlatinib biopsies and some pre-treatment ALK mutation information; it lacks complete dated exposure/response. cBioPortal has 83 patients/90 samples but lacks the required treatment/timepoint fields. |
| CD19 clinical relapse splice evidence | Orlando SRP141691 clinical/processed relapse evidence with explicit assay and screening/relapse joins | Official publisher workbook and two PDFs acquired in `gap-fill/orlando/`: 30,901 gene rows across 24 labelled samples. Patient/timepoint joins need confirmation, and gene counts alone cannot establish splice junctions; raw read reanalysis is not included. |
| Matched protein measurements | A defined treatment-timed tumor proteomics cohort with patient/assay joins | PRIDE PXD012000 processed clinical and protein-abundance workbooks are acquired and validated: 35 clinical patient rows, 113 study specimens including pre/post-treatment and normal groups. This closes the general longitudinal proteomics acquisition gap; a target-specific ALK/BCMA resistance proteomics cohort is still missing. See `gap-fill/proteomics/PROTEOMICS-GAP.md`. |
| Patient harmonization | Verified patient, biopsy, cell, assay, drug, timepoint and outcome joins across sources | Source metadata and GEO overlap tables are available. Cohort-specific harmonization and leakage-safe split design remain analysis work. |
| POG570 | Permission for the intended shared use/redistribution under its explicit source terms | Public directory located; research-only/controlled handling and no-redistribution terms documented in `gap-fill/pog570/ACCESS-NOTE.md`. Data not transferred. |
| Controlled clinical sequencing | Hartwig, DAISY and relevant controlled components of other cohorts | Requires the applicable access route; public processed subsets do not imply access to controlled raw data. |
| 2019 ALK supplement | Dagogo-Jack primary supplemental DOCX | Primary URL identified; publisher/PMC automated access blocked. The 2022 supplement is already acquired via its official publisher. |
| Large perturbation expansion | Full LINCS bulk releases, Tahoe, additional CTRP/GDSC screens and broad atlas portals | Not fully mirrored. Selected LINCS data/metadata and PRISM/DepMap support current work; specific additions should answer a defined analysis need. |

ClinicalTrials.gov provides trial context and posted aggregate outcomes. FAERS provides spontaneous safety reports, not patient-level resistance labels, incidence or causal conclusions. Neither closes the longitudinal molecular gap. See https://open.fda.gov/apis/drug/event/.

## Interpretation and working rules

Original compressed inputs remain immutable. Partial files, quarantined files, metadata-only entries and deferred rows are not completed datasets. Preserve study licenses and therapeutic identities: 12ER contains the BCMA-targeted Fab of teclistamab with a helper Fab, 6VJA is rituximab–CD20, and 7JIC includes coltuximab; these are not interchangeable therapeutic complexes. Download completion is separate from clinical validity and analysis readiness.
