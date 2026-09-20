# Runtime data analysis

The scientific data analyst has a bounded catalog of computations that read the actual pinned source files when invoked. These computations are separate from the prepared case narrative and `demo_decision`. They run locally on CPU; neither GPT-Rosalind nor BioNeMo is used to calculate table counts or numerical ratios.

`app.analysis_tools.analysis_catalog(case_id)` returns available `{id, title, description}` records. `analyze_case(case_id, analysis_id)` synchronously returns a fresh evidence object with `kind: derived`. The harness/provider integration runs this computation through its data-analysis tool, persists the evidence before making it citable, and records the action in the investigation trail. The model selects a catalog task and interprets the resulting evidence; it cannot supply arbitrary Python, paths, shell commands, URLs or new extraction parameters.

| Case | Analysis ID | Evidence ID |
| --- | --- | --- |
| CD19 CAR-T | `cd19-barcode-qc` | `ANALYSIS-CD19-QC` |
| CD19 CAR-T | `cd19-isoform-summary` | `ANALYSIS-CD19-ISOFORMS` |
| ALK L1196M | `alk-assay-extraction` | `ANALYSIS-ALK-ASSAY` |
| BCMA GSE164551 | `bcma-sample-variant-qc` | `ANALYSIS-BCMA-QC` |

The analyst's useful job is to make an explicit calculation, qualify its inputs and state what it cannot resolve. The investigator can then update its assessment, the reviewer can challenge an interpretation against the exact result, and the R&D coordinator can select a discriminating measurement or qualified molecular request. An analysis tool does not establish a new clinical mechanism by itself.

## General preparation and analysis guidance

The bioinformatician, statistician and discovery-planning skills suggest preparation and analyses based on the question, assay, measurement scale and experimental unit. Relevant options include identifier/type/units reconciliation, explicit missingness and mapping QC, versioned lossless derivatives, replicate checks, paired or blocked contrasts, count-aware models and leakage-aware validation. These are conditional recommendations, not a prescribed sequence or additional callable tools.

Keep study-specific labels, exclusions, thresholds, fit choices and expected results in cited data records or explicit analysis recipes. Reusable skills should not contain a paper's answer key. A derived dataset must retain source hashes/locators, transformation version, units and exclusions; whether an analysis is appropriate still depends on its design. A source being acquired or parsed does not establish that the app can read it or that an analysis ran.

For the supporting publications, data accessions, code releases and qualification reports, see [Data references](#data-references). The runtime recipes and limits below describe existing implementation; this skill update adds guidance, not a new cleaning engine or analysis adapter.

## CD19 barcode qualification

The tool reads the compressed GSE182891 DNA variant table and GSE182892 RNA junction-count table anew. It counts source rows, exact barcodes, source replicate labels and duplicate `(replicate, barcode)` keys, then joins DNA `RNA_BARCODE` to RNA `barcode` by exact identity.

The pinned inputs reproduce:

- 100,135 DNA variant rows, representing 10,295 distinct RNA barcode identities.
- 19,043 RNA rows and 9,722 distinct barcodes; source replicate labels contain 9,671 and 9,372 rows.
- 9,527 RNA barcodes with an exact DNA match, and 195 unmatched RNA barcodes.
- No duplicate RNA barcode/replicate keys; total source `readcount` 21,866,465.

Unmatched barcodes remain reported and cannot be assigned a variant implicitly. The output includes the first ten unmatched examples and a deterministic hash of the entire sorted unmatched list. These are reporter-library observations, not independent patients or patient-specific escape evidence.

## CD19 prespecified junction summaries

The source coordinate columns `(219 475)(743 1040)`, `(219 1040)` and `(219 475)` are fixed in analysis version 1.0.0 before runtime aggregation. The tool retains their exact source labels and gives them no new exon, epitope or protein interpretation. It pools integer counts within each source replicate label, without selecting interesting barcodes or fitting mutation effects.

| Source replicate | Rows | Reported readcount | First fixed junction | Second fixed junction | Third fixed junction | Reported count minus all listed junctions and discarded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 9,671 | 10,739,439 | 7,335,688 | 1,689,848 | 297,594 | 95,712 |
| 2 | 9,372 | 11,127,026 | 6,316,523 | 3,034,767 | 442,146 | 76,683 |

The output audits every numeric junction column plus `discarded`. In 8,021 rows of replicate 1 and 7,246 rows of replicate 2, these listed counts do not exhaust `readcount`. No row in these pinned inputs has a listed total exceeding `readcount`. The tool reports this gap without assigning a biological explanation or silently filling it.

Each selected column's coverage ratio is its summed count divided by summed source `readcount` in the same replicate. The denominator remains explicit. These read-weighted descriptive ratios are not normalized isoform probabilities, independent replicate effect sizes, differential-splicing p-values or a mutation-causality test. A downstream analysis that needs complete isoform assignments must first resolve the coverage meaning using the originating methods.

## ALK assay extraction

The tool opens the pinned workbook, reads Table S2, searches for `ALK_E23_C70A`, requires exactly one matching row, asserts the protein label `L1196M` and validates the source field headers. It returns the drug classifications and scores with exact cells and source decimal strings; fitness remains separate.

The source row resolves to 1331. Alectinib and lorlatinib classifications are `Resistance`; zotizalkib is `Sensitive`. Scores are `7.7445209372741202`, `11.4128982028548` and `0.23868446278806199`, respectively. Fitness is `-0.106903137030655`. The tool computes whether the classifications differ, without treating score magnitudes as comparable across drugs or claiming an IC50, mechanism or clinical rescue. The unresolved Table S5 exposure discrepancy remains a limitation.

## BCMA sample and variant qualification

The tool reads the prepared case JSON, sample manifest and post-second-infusion variant table. It checks sample/GSM uniqueness, returns the corrected matrix/metadata alias records, retains the CD138-depleted baseline note and preserves DNA timing. It searches by `TNFRSF17`, requires a unique source row and validates nonnegative allele counts against stated depth.

The source has one patient, eight samples and two corrected S5/S6 alias records. Variant line 438 is `p.Q38*`, `Nonsense_Mutation`, with tumor alternate count 10 at depth 41. The derived alternate-read fraction is `10 / 41`; it is not a cancer-cell fraction, purity estimate or biallelic-loss proof. Copy-number inference, surface-protein adjudication and raw H5 barcode reconciliation are explicitly marked as not performed. The truncation does not qualify a simple missense-pair model, and no molecular constructs are supplied by this analysis.

## Provenance, bounded execution and errors

Each invocation loads source paths from application constants, checks source containment and byte limits, and verifies the bytes against the case-pack manifest. It does not trust a path supplied by a model or browser. Files are limited to 2 MB compressed/on disk, expanded tables to 8 MB and 120,000 data rows, XML members to 3 MB, and the manifest to 100 KB. These limits admit the current 2.7 MB source bundle while preventing accidental large-file or decompression workloads.

Every returned evidence object includes analysis ID/version, parameters, all raw source hashes and locators, actual computed values, limitations and `inference_performed: false`. `source.sha256` is the SHA-256 of canonical JSON for the complete `values` object (`sort_keys=True`, compact separators, UTF-8, no NaN). It identifies the derived result, while `values.input_sources[*].sha256` identifies the original source bytes. Repeating the same analysis on the same pinned sources yields the same evidence and hash; no timestamp is added to the scientific value record. The harness records execution time separately.

Unknown cases, cross-case analysis IDs, altered source bytes, missing columns, malformed rows, invalid counts and exceeded limits stop the analysis. Missing values never become zeros, and malformed rows are not silently discarded. Runtime source reads are repeated even when an analysis has run previously, so a subsequently altered file cannot pass through a process cache.

## Verification

```sh
python -m pytest tests/test_analysis_tools.py -q
```

The eleven tests cover independent numerical anchors, exact precision and cells, barcode exclusions, count-coverage gaps, BCMA timing and alternate-depth calculation, deterministic hashes, fresh source verification, case-scoped allowlists, decompression/row limits and malformed inputs. The broader harness tests cover persistence, revisions, cancellation and export identity. These computations expand the working product's analytical behavior; they do not claim a general arbitrary-dataset pipeline or an executed wet-lab experiment.


## Data references

These references identify the studies, deposited inputs, methods and published reference outputs. They do not prescribe study-specific filters or expected answers. Preserve source versions, original units, assay identity, biological units and access restrictions when preparing data. Published predictions and figure results should be labeled as reference material when evaluating an independent analysis.

| Source | What it supports and relevant boundary |
|---|---|
| Cortés-López et al. (2022), *Nature Communications*: [paper and methods](https://doi.org/10.1038/s41467-022-31818-y), [PMC9500061](https://pmc.ncbi.nlm.nih.gov/articles/PMC9500061/), [original Source Data archive](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-31818-y/MediaObjects/41467_2022_31818_MOESM11_ESM.zip) | Primary CD19 splicing study. Supplements and Source Data provide assay measurements, annotations and published analysis outputs. Workbook values need sheet/cell provenance; a figure summary is not necessarily a release of individual replicates or original instrument files. |
| [GEO GSE182891](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182891) — DNA library; BioProject PRJNA758171 / SRA SRP334379 | PacBio sequencing of the CD19 minigene plasmid library and barcode–variant dictionary. Sequenced material is the plasmid pool; it must not be interpreted as patient DNA or as the RNA assay. |
| [GEO GSE182892](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182892) — reporter RNA; BioProject PRJNA758173 / SRA SRP334380 | NALM-6 reporter RNA sequencing and deposited isoform/count tables. Preserve biological replicate, barcode identity, count denominators and discarded/artifact categories. This accession distinguishes the RNA arm from the DNA deposit. |
| [GEO GSE182893](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182893) — PTBP1 iCLIP; SRA SRP334381 | NALM-6 PTBP1 binding data, library-processing metadata and strand-specific BigWig tracks. Retain biological replicate and RNase treatment as separate fields. This is not the PTBP1-depletion surface-staining assay in the other cell lines. |
| [Author code, Zenodo v1.0](https://doi.org/10.5281/zenodo.6614455), cited [concept DOI](https://doi.org/10.5281/zenodo.6614454) | Frozen CD19 analysis release, associated with commit `d827c59c70b67364343fe27f971bf40ef75a17d8`. Supports inspection of available transformations and analysis conventions; the release does not establish that every original fitting or preprocessing step is supplied. |
| Orlando et al. (2018), *Nature Medicine*: [paper](https://doi.org/10.1038/s41591-018-0146-z), [SRA SRP141691](https://www.ncbi.nlm.nih.gov/sra?term=SRP141691), BioProject PRJNA451298 | Clinical screening/relapse CD19 data and supplementary expression measurements. Public read exports originate from targeted submissions and must not be assumed to be whole-transcriptome raw reads. Match samples and timepoints within each assay; gene-level expression does not itself measure intron retention. |
| TARGET B-ALL: historical dbGaP [ALL Phase 1, phs000463.v21.p8](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000463.v21.p8) and [ALL Phase 2, phs000464.v21.p8](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000464.v21.p8); [GDC API](https://api.gdc.cancer.gov/) | Clinical RNA and variant source cohorts. Historical read, splice-junction and annotated-variant inputs require controlled-access authorization. Public metadata and open expression products do not establish identity with a historical source snapshot or substitute for controlled reads; distinguish samples from participants. |
| Bai et al. (2022), *Science Advances*: [paper](https://doi.org/10.1126/sciadv.abj2820), [GEO GSE197215](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE197215), [BioProject PRJNA809371](https://www.ebi.ac.uk/ena/browser/view/PRJNA809371), [supplementary methods/figures](https://pmc-oa-opendata.s3.amazonaws.com/PMC9177075.1/sciadv.abj2820_sm.pdf), [supplementary Table S2](https://pmc-oa-opendata.s3.amazonaws.com/PMC9177075.1/sciadv.abj2820_table_s2.zip) | Separate CAR-T infusion-product stimulation cohort with RNA/ADT objects, clinical context and published expression comparisons. Supports donor-aware complementary analysis; it is not a matched cohort or a replication of the primary CD19 reporter/PTBP1 study. Raw count assays, normalized assays, absent modalities and missing annotations require distinct handling. |
| Black et al. (2018), *Nucleic Acids Research*: [paper](https://doi.org/10.1093/nar/gky946), [GEO GSE115655](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE115655), SRA SRP150315 | Normal developing B-cell comparator metadata, RNA reads and processed TMM CPM expression. Preserve donor and maturation stage. CPM is not interchangeable with TPM, and neither replaces junction-based splicing measurements. |
| Fernández et al. (2016), [The BLUEPRINT data analysis portal](https://doi.org/10.1016/j.cels.2016.10.021) | Provenance for the mature B-cell comparator component cited by the primary study. Use the primary study's source identifiers to select the intended samples and check the applicable EGA access policy before treating raw data as accessible. |
| Gu et al. (2019), [PAX5-driven subtypes of B-progenitor acute lymphoblastic leukemia](https://doi.org/10.1038/s41588-018-0315-5) | B-ALL expression-cohort provenance for RBP prioritization. Released aggregate expression/rank tables in the primary paper's Source Data can support aggregate analysis; they are not individual-sample expression matrices and cannot supply cohort-level variance or independent reaggregation. |
| [DepMap Public 21Q2, version 2](https://doi.org/10.6084/m9.figshare.14541774.v2); Barretina et al. (2012), [Cancer Cell Line Encyclopedia](https://doi.org/10.1038/nature11003) | Release-specific cell-line expression and sample metadata, including NALM-6/K562 context. Pin the release and units of `CCLE_expression.csv` and join through `sample_info.csv`; a newer release or a broader gene universe is not automatically equivalent to the authors' selected subset. |

Reference entries were assembled from the already verified paper, deposit metadata and acquisition receipts. No new downloads or patient-level tables are included here.


Detailed acquisition/qualification receipts and source hashes are available on Brev in `/home/ubuntu/rosalind-shared-files/cd19-reproduction-data/2026-09-20/source-package/`. Those records supplement provenance; they do not silently alter the existing case-pack snapshots, app reader limits or skill instructions.
