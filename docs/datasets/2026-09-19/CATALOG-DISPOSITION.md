# Non-GEO catalog disposition

Audit date: 19 September 2026. This reconciles the 50 entries under
“Additional cohorts and supporting resources” in
`DATASET-SOURCE-CATALOG.md` with the CPU integration catalog and the current
gap assessment. A status of **acquired subset** means the named source has a
usable, validated portion on the CPU; it does not claim the entire portal or
study was mirrored. “Optional” means the resource can extend a defined
analysis but is not needed to close a current substantive gap.

The live CPU catalog and its summary record physically present, manifested assets. Incomplete and deferred objects are excluded from available counts.

## Additional clinical cohorts

| # | Catalog entry | Disposition | Evidence on CPU and remaining scope |
|---:|---|---|---|
| 1 | Maynard lung therapy evolution / PRJNA591860 | **Acquired subset** | Sample metadata, processed expression, and sample-to-cell mapping are present. This supports treated lung evolution analysis; raw reads and a complete study mirror are not claimed. |
| 2 | Orlando CD19 relapse / SRP141691 | **Acquired subset** | Official Orlando 2018 Supplementary Data Table 1 is now present: a 30,901-gene × 24-sample read-count matrix with screening, month-4/7, and relapse labels. Publisher supplementary PDFs are also retained. SRP141691 remains targeted Split’N’Trim BAM rather than an analysis-ready genome-wide junction package, so this supports paired expression and assay-identity checks but not de novo splice-junction calling. |
| 3 | SU2C MARK NSCLC | **Acquired subset** | `Source_Data_3.zip` (1.18 GB) is present and ZIP-validated. It covers the public author source package; controlled raw WES/RNA remains outside scope. |
| 4 | IMvigor210 | **Acquired subset** | Official Genentech/Roche Core Biologies v1.0.0 package, 122 MB, with expression and response/survival/sample annotations, is on Brev and SHA/archive-verified. It is not a serial pre/post cohort. |
| 5 | Beat AML | **Optional not acquired** | Adds ex-vivo AML drug response, not clinical treatment response. No versioned release was selected. |
| 6 | POG570 | **Access restricted** | Public directory found, but its README imposes research-only/controlled handling and no redistribution without express permission. No team data transfer; exact terms in gap-fill/pog570/ACCESS-NOTE.md. |
| 7 | GLASS | **Optional not acquired** | Useful longitudinal glioma extension; no named study or portal terms/version were selected. |
| 8 | MMRF CoMMpass | **Access restricted** | Public expression does not supply the controlled genomic component. It is disease context rather than a BCMA CAR-T cohort, so no partial release was selected. |
| 9 | DAISY | **Access restricted** | The clinical data require request and WES is controlled. No approval bypass or partial patient-level acquisition was attempted. |
| 10 | Hartwig Medical Foundation | **Access restricted** | Patient-level access requires an application and data-access agreement. |
| 11 | TRACERx | **Access restricted** | A publication-specific public processed release would need selection; broader patient sequencing is mixed/controlled. |

## Functional perturbation and model systems

| # | Catalog entry | Disposition | Evidence on CPU and remaining scope |
|---:|---|---|---|
| 12 | DepMap and CCLE | **Acquired subset** | DepMap 24Q4 model/gene/profile metadata, integrated Chronos CRISPR gene effect, protein-coding log1p TPM expression, and portal compounds are present and SHA-256 verified. This is not a full current portal mirror. |
| 13 | PRISM Repurposing | **Acquired subset** | PRISM 19Q4 primary replicate-collapsed viability and secondary dose-response data with treatment and model metadata are present and verified. |
| 14 | CTRP | **Optional not acquired** | An orthogonal screen, but it is redundant for the immediate functional gap now covered by PRISM. Select a release only for a planned cross-screen reproducibility analysis. |
| 15 | GDSC through PharmacoDB | **Optional not acquired** | Useful comparator, but legacy GDSC endpoint provenance/version needs resolution before use. |
| 16 | DrugComb | **Optional not acquired** | Combination data are only needed after a specific combination hypothesis and a compatible synergy definition are chosen. |
| 17 | scPerturb | **Acquired subset** | The Frangieh–Izar 2021 protein `.h5ad` subset is present and transfer-verified. It is a selected perturbation slice, not the entire compendium. |
| 18 | Genome Wide Perturb-seq | **Optional not acquired** | Valuable model-system ground truth, but no particular experiment or transfer question was selected. |
| 19 | Tahoe 100M | **Optional not acquired** | The catalog correctly recommends a small selected partition; no line/drug/control partition was chosen. |
| 20 | JUMP Cell Painting | **Optional not acquired** | Morphology is an orthogonal extension, not a missing molecular resistance measurement. |
| 21 | Cell Model Passports | **Overlaps acquired** | DepMap 24Q4 already supplies the model identity and context needed for the acquired functional matrices. Passport-specific organoid annotations remain available if a model-selection task requires them. |
| 22 | PDXNet | **Optional not acquired** | Study-level PDX choice and terms need to be fixed before acquisition; it is preclinical validation, not a missing primary evidence layer. |

## Protein structure and quantitative benchmarks

| # | Catalog entry | Disposition | Evidence on CPU and remaining scope |
|---:|---|---|---|
| 23 | CD20–rituximab complex / PDB 6VJA | **Acquired subset** | The experimental 6VJA CIF is present. It supplies structural context only and is not the exact mosunetuzumab interface. |
| 24 | CD19–CD81–coltuximab complex / PDB 7JIC | **Acquired subset** | The experimental 7JIC CIF is present. It is not interchangeable with an FMC63 CAR binder. |
| 25 | SKEMPI 2 | **Acquired subset** | `skempi_v2.csv` is present and validated for measured protein–protein binding-effect evaluation. |
| 26 | ProteinGym | **Optional not acquired** | Generic fitness calibration is not needed while SKEMPI supplies the selected binding-effect benchmark. |
| 27 | MaveDB | **Optional not acquired** | No assay with the required resistance, binding, or splicing endpoint was selected. |
| 28 | SAbDab | **Overlaps acquired** | Exact structural records needed for the current examples are already present through PDB. SAbDab would be useful only for a new antibody-sequence discovery task. |
| 29 | AlphaFold DB | **Optional not acquired** | Predicted monomers would not close the absence of a measured therapeutic complex. |
| 30 | ChEMBL | **Optional not acquired** | PRISM treatment metadata supplies the current compound identifiers, mechanism, target, disease-area, indication, SMILES, and phase fields. ChEMBL would be selected for a later assay-level drug-target expansion. |
| 31 | BindingDB | **Optional not acquired** | Small-molecule binding calibration is not a current missing layer and does not substitute for antibody–antigen measurements. |

## Reference atlases and multimodal context

| # | Catalog entry | Disposition | Evidence on CPU and remaining scope |
|---:|---|---|---|
| 32 | TCGA through GDC | **Optional not acquired** | Background prevalence and tumor-type context do not repair a paired treatment-resistance gap. |
| 33 | cBioPortal | **Acquired subset** | The 2026 ALK MSK study metadata, clinical patient/sample records, and mutations for all 90 selected samples are present. This is a study-specific acquisition, not a portal mirror. |
| 34 | CPTAC / Proteomic Data Commons | **Optional not acquired** | The general processed longitudinal proteomics acquisition gap is now covered by PRIDE PXD012000. CPTAC/PDC remains an optional expansion; a target-specific ALK/BCMA longitudinal cohort has not been identified. |
| 35 | Human Tumor Atlas Network | **Optional not acquired** | A named atlas, modality, and donor-level license check are needed before it can be treated as an independent validation source. |
| 36 | CELLxGENE Discover and Census | **Optional not acquired** | This is a discovery index; a named collection and duplicate-donor review are needed before download. |
| 37 | Human Protein Atlas | **Optional not acquired** | Normal expression/localization reference is useful but does not supply matched relapse protein data. |
| 38 | GTEx | **Optional not acquired** | Normal postmortem regulatory context is not a treatment-response control. |
| 39 | Expression Atlas | **Optional not acquired** | A source-study accession must be selected to avoid duplicate cohorts and ambiguous provenance. |
| 40 | ENCODE | **Optional not acquired** | Regulatory or RNA-binding evidence needs a disease/cell-state-matched experiment. |
| 41 | PRIDE | **Acquired subset** | PXD012000 official processed clinical and protein-abundance workbooks are acquired and validated. The clinical workbook has 35 patient rows with sample mappings and outcomes; the study has 113 specimens. This is a breast-cancer chemotherapy comparator, not an ALK/BCMA resistance cohort. |
| 42 | TCIA NSCLC Radiogenomics | **Optional not acquired** | It is an imaging–omics context set, not an acquired-resistance molecular cohort. |

## Genomics controls and evidence knowledge bases

| # | Catalog entry | Disposition | Evidence on CPU and remaining scope |
|---:|---|---|---|
| 43 | Genome in a Bottle | **Optional not acquired** | Technical germline truth is not required for the acquired processed resistance evidence. |
| 44 | SEQC2 HCC1395 | **Optional not acquired** | A somatic calling benchmark is useful only if a new variant-calling workflow is introduced. |
| 45 | Splatter | **Optional not acquired** | Software for fixtures, not an empirical data source; select only when generating evaluation simulations. |
| 46 | CIViC | **Acquired subset** | Official 1 September 2026 Clinical Evidence, Variant and Molecular Profile summary TSVs acquired. This is a dated evidence knowledge base, not a patient cohort. |
| 47 | ClinVar | **Optional not acquired** | Germline submissions are not direct acquired-resistance evidence. |
| 48 | gnomAD | **Optional not acquired** | Population frequency is a plausibility control, not a resistance label. |
| 49 | Open Targets | **Optional not acquired** | Knowledge-graph context is secondary to the delivered experimental and clinical evidence. |
| 50 | Reactome | **Acquired subset** | Pathway GMT ZIP and pathway-relation table are on Brev with source checksums. |

## Remaining substantive holes

The remaining holes are not “all public data.” They are a small number of
evidence types that the delivered assets do not yet establish:

1. **A genome-wide, junction-preserving clinical CD19 relapse splice package**
   with unambiguous screening/relapse and assay identity. The Orlando
   supplementary count matrix now covers paired expression; its SRP141691 BAM
   data are targeted and Split’N’Trim, so they do not fill this specific
   junction-quantification gap.
2. **Target-specific ALK/BCMA longitudinal proteomics.** PXD012000 supplies a processed breast-cancer chemotherapy comparison with clinical sample mapping, but does not close this target-specific gap.
3. **Complete patient/sample/assay maps and overlap control** across the
   already acquired clinical and GEO assets. This is integration work, not a
   reason to download full portals.

CTRP/GDSC, broad atlas portals, and large perturbation compendia should remain
optional until a concrete analysis asks for their additional measurement rather
than the same evidence in another container.
