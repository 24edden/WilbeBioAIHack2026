> Historical local snapshot. See [the documentation index](../../../../README.md) for the current reading order.

# Data and tool register

Reference architecture companion — 19 September 2026. IDs below are used in `REFERENCE-ARCHITECTURE.md`. This is an implementation specification and an availability audit, not an executed biological investigation.

## Locations and status vocabulary

Local data root: `<LOCAL_PROJECT>/outputs/dataset-acquisition/`.

Reported shared CPU data root: `agentic-takeoff-cpu:/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/`. This task did not reconnect to that host. `remote-audit/` contains saved remote manifests; their claims remain point-in-time records.

The accompanying `local-asset-audit.csv` contains absolute paths, actual byte counts, observed SHA-256, available manifest SHA-256 and comparison results for 129 selected local files. The snapshot found 76 manifest hash matches, 51 files hashed without a matching manifest entry under the audit's parser, and two excluded partial/corrupt files. No matched-manifest discrepancies were found. Files in acquisition may change after this snapshot. This is a selected-asset audit, not a census of all project data.

- **Local / hash matched:** actual selected files were read and matched an acquisition manifest. Does not imply scientific readiness.
- **Local / hashed:** actual selected files were hashed; a matching manifest entry was not found by this audit. Some earlier integrity evidence exists in narrative status documents or differently structured manifests.
- **Remote recorded:** a saved remote manifest reports the object; local data bytes are absent or incomplete and remote storage was not rechecked.
- **Potential:** a candidate source has been identified, but this architecture does not claim it is downloaded.
- **Generated:** an artifact the new harness must create from approved inputs.
- **Excluded:** incomplete or corrupt input; never used for biological inference.

## Dataset packages

### D00 — graph contracts and case metadata

**Present:** local biotech reference graph at `<REFERENCE_MODEL_WORKSPACE>/graph/model/graph.json`, reference model `0.3.0-draft`, schema `1.2.0`. Selected source nodes and hash are preserved in `<LOCAL_PROJECT>/outputs/process-simulation-design/graph-reference-extract.json`.

**Purpose:** work definitions, evidence requirements, role boundaries and review gates. **Needed:** a case manifest, actual reviewer assignment, permissible data scope, input versions, scientific endpoint and budget. The reference graph is not populated patient data or a biological ground-truth graph. Earlier live reads at `http://127.0.0.1:8773` failed; pin the saved snapshot unless a fresh database read succeeds.

### D01 — ALK functional atlas

**Local / hash matched:** `alk-atlas/13059_2026_3977_MOESM1_ESM.docx` and `13059_2026_3977_MOESM2_ESM.xlsx`; originals and sidecar manifests present. Source DOI: [10.1186/s13059-026-03977-4](https://doi.org/10.1186/s13059-026-03977-4).

**Use:** functional variant/compound evidence and measured-label evaluation after table interpretation. **Prepare:** workbook-sheet dictionary; construct and variant IDs; reference sequence; drug, concentration and assay units; replicate/control mapping; measured response fields and uncertainty. Parse the methods before choosing the label. Preserve the original supplements and their recorded terms.

**Boundary:** functional assay evidence is not a longitudinal patient cohort, and an assay phenotype does not identify its mechanism. Split variant families/experimental series before evaluating generalization; keep test labels outside retrieval.

### D02 — Maynard therapy-state single-cell package

**Local / hash matched:** `gap-fill/longitudinal/maynard_prjna591860/Maynard_Table_S1_sample_metadata.xlsx`, `PRJNA591860_processed_expression.RDS`, `PRJNA591860_sample_cell_names.RDS`.

**Use:** clinical-science → translational → bioinformatics handoffs using sample treatment state and cell-state evidence. The acquisition README describes a small ALK subset, not a comprehensive ALK baseline/progression cohort. **Prepare:** reproduce sample-to-cell mapping, patient namespace, treatment state, collection interval, assay scale and annotated cell type; identify actual eligible pairs and exclude unmatched observations from paired analyses. The RDS is a processed reuse; inspect its measurement scale before choosing a count model.

**Boundary:** treatment-naive, residual disease and progressive disease are distinct states. A repeated biopsy alone is not a progression pair. Patient-specific concentration/exposure records are not supplied by this package. Provenance: [Maynard et al. primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/) and [processed release/mirror](https://zenodo.org/records/7860559), as documented in the acquisition README.

### D03 — ALK tissue mutation and portal packages

**Local / hash matched:** `gap-fill/longitudinal/alk_cbioportal_2026/ShibaIshii2022_Supplementary_Tables.pdf`; `alk_msk_2026_clinical_patient.json`, `alk_msk_2026_clinical_sample.json`, `alk_msk_2026_mutations.json`, plus study/profile metadata.

**Use:** the publisher supplement's pre/post-lorlatinib mutation table supports molecular-state comparisons where both states and methods are recorded. The cBioPortal export supplies a separate resistance-associated mutation collection. **Prepare:** extract and visually verify Table S2; normalize alleles, transcript/protein coordinates and assay method; distinguish missing pretreatment assessment from absence of a mutation. For the portal data, establish collection timing before treating repeat samples as longitudinal progression.

**Missing:** complete patient-level exposure and response timing. Do not join the publisher and portal records by similar IDs or count possible overlaps as independent evidence. Sources: [Shiba-Ishii et al.](https://doi.org/10.1038/s43018-022-00399-6), [cBioPortal study metadata endpoint](https://www.cbioportal.org/api/studies/alk_msk_2026).

### D04 — CD20 RNA/protein-discordance clinical anchor

**Local / hash matched:** `geo-resistance/GSE243919/GSE243919_FFPE_samples_raw_read_counts.csv.gz`. Saved remote metadata are available through D16.

**Use:** small paired clinical investigation where gene-level RNA need not explain protein loss. **Prepare:** select the biological sample columns, exclude the undetermined-read column, verify patient/timepoint pairing and blank-cell semantics; obtain the actual protein measurement/source if making a protein claim.

**Missing:** junction/isoform evidence for a direct splice analysis, potentially requiring selected raw reads and reference annotation. Gene counts alone cannot establish a splice mechanism. The [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243919) describes the paired cohort and assay purpose.

### D05 — BCMA longitudinal case with derived genomics

**Local / hash matched:** `geo-resistance/GSE164551/` contains `GSE164551_AllCellsMetaData.txt.gz`, the `...mergedAll_PASS_DP10.maf.txt.gz` mutation file and `...facets.out.txt.gz` allelic-count file.

**Use:** variant provenance and an alternative antigen-escape scenario. **Prepare:** clinical mapping of S1–S8, genome build/transcript validation, expression acquisition and valid copy-number derivation if required. The acquisition catalog describes a single patient; longitudinal samples are not independent patients. The FACETS-related file is not automatically segmented absolute copy number. [GEO source](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164551).

### D06 — CD19 minigene variants and isoform labels

**Local / hash matched:** `geo-resistance/GSE182891/GSE182891_CD19_minigene_variants.tab.gz` and `geo-resistance/GSE182892/GSE182892_CD19_minigene_isoforms.txt.gz`, with source README files.

**Use:** sequence-to-assay evaluation and an experimental-label scenario. **Prepare:** join by the documented construct/barcode/variant scheme; recover exact construct reference sequence and orientation; check controls and replicate units. Use assay-specific labels to assess T07; do not translate splice effects directly into clinical relapse labels. [DNA accession](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182891), [RNA accession](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182892).

### D07 — I-SPY2 expression, RPPA and response branch

**Local / hashed:** `geo-response/GSE194040/files/` contains gene/probe expression and annotation/normalization files; `GSE196093/files/` contains RPPA measurements and normalization parameters; `GSE196096/files/` contains the RPPA endpoint-name workbook. SOFT files are present.

**Use:** a separate multimodal treatment-response investigation. **Prepare:** patient/sample/platform crosswalk; arm/outcome fields; assay-specific normalization; actual overlapping baseline subset and missingness report. The expression component is an Agilent microarray resource: use a method appropriate to its scale, not a raw RNA-seq count model. RPPA panels must retain target identity, scale and platform metadata.

**Boundary:** choose the endpoint actually released (for example response if present); do not invent survival follow-up. Do not merge patients with PRINCE or ALK cohorts. [Parent series](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196096).

### D08 — functional context: DepMap 24Q4 and PRISM 19Q4

**Local / hash matched:** `gap-fill/functional/` contains `Model.csv`, `Gene.csv`, `OmicsProfiles.csv`, `CRISPRGeneEffect.csv`, processed expression, and PRISM primary/secondary matrices and model/treatment annotations. Fifteen files matched the current manifest; two source metadata files were additionally hashed.

**Use:** select experimental models and seek orthogonal dependency/drug-response context. **Prepare:** map stable model IDs, gene IDs, compound identity, dose, screen and assay quality; document overlap. Compare within the defined screen and preserve missing values.

**Boundary:** these are cell-line screens, not the patient's outcome or an isogenic test of a specific variant. Release sources: [DepMap 24Q4](https://doi.org/10.25452/figshare.plus.27993248.v1), [PRISM 19Q4](https://doi.org/10.6084/m9.figshare.9393293.v4).

### D09 — perturbation protein measurements

**Local / hashed:** `external/scperturb/FrangiehIzar2021_protein.h5ad`.

**Use:** an independent perturbation scenario and cross-modal reasoning tests. **Prepare:** inspect AnnData observations, perturbation labels, controls, donor/batch and measured-protein panel; establish the independent experimental unit. Do not assume this protein subset also contains its paired RNA modality. [Release](https://zenodo.org/records/13350497).

### D10 — structures and molecular inputs

**Local / hashed:** `external/structures/6VJA.cif` and `7JIC.cif`. Prior acquisition documentation identifies these as CD20–rituximab and CD19–CD81–coltuximab complexes respectively.

**Use:** structural inspection of the matching target/partner context. **Missing for ALK:** the exact ALK sequence/construct and mutation mapping, relevant inhibitor chemical identity, appropriate experimental structures and optional MSA/templates. Retrieve from pinned UniProt/Ensembl, RCSB and PubChem/ChEBI records after specifying the case. An ALK fusion construct must not be silently replaced with an unrelated full-length sequence.

**Boundary:** rituximab is not mosunetuzumab, and coltuximab is not a CAR binder. A convenient structure cannot establish the geometry of a different therapeutic interaction. [6VJA](https://www.rcsb.org/structure/6VJA), [7JIC](https://www.rcsb.org/structure/7JIC).

### D11 — pathway/reference knowledge

**Local / hashed:** `external/references/ReactomePathways.gmt.zip` and `ReactomePathwaysRelation.txt`.

**Use:** gene-set/pathway context with explicit species, identifier mapping and analysis universe. **Potential:** frozen UniProt, Ensembl, ClinVar/CIViC, gnomAD or Open Targets subsets only when the question needs them. Their evidence types differ; they are not interchangeable causal labels. [Reactome downloads](https://reactome.org/download-data).

### D12 — pharmacology reference labels

**Local:** `gap-fill/pharmacology/` includes source XML, search responses, derived text and manifests for brands including LORBRENA, ALECENSA, ALUNBRIG, ZYKADIA and XALKORI and relevant antibody/cell-therapy products. Forty-two source assets matched per-brand manifests; derived files were hashed separately.

**Use:** versioned drug identity and pharmacology context. **Missing:** actual patient dose administration, interruptions, sampling times, concentrations and relevant covariates. Labels cannot establish that an individual was adequately exposed. Reconcile distinct labelers and SPL versions. [DailyMed API](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm).

### D13 — clinical trial registry context

**Local:** the root `clinical-context/clinicaltrials/` holds a failed request and error summary, not study data. **Remote recorded:** its saved remote manifest reports 5,041 studies over 51 pages; this task did not recheck the remote pages.

**Use:** protocol/arm/eligibility context after selecting exact studies and verifying the snapshot. **Boundary:** registry records are trial-level information, not patient outcomes, sequencing or dosing histories. [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api).

### D14 — SU2C-MARK

**Excluded locally:** `external/su2c_mark/Source_Data_3.zip.part`; README present. The partial archive cannot be analysed. **Potential:** complete the versioned [author release](https://zenodo.org/records/11179623), verify archive integrity and identify relevant processed clinical/molecular tables. Useful as a future multimodal cohort, not a dependency of the first ALK/CD20 implementation.

### D15 — additional BCMA/CD19 immune-state packages

**Remote recorded:** saved manifests report GSE197215 CD19, CD3/CD28, mesothelin and unstimulated RDS objects, plus a GSE217245 archive. GSE226327's large archive was deferred in the inspected record. **Excluded locally:** the corrupt GSE197215 RDS file. Other selected local folders contain metadata/manifests rather than assay data.

**Use:** immune dysfunction and target-specific versus generic stimulation alternatives after retrieving/verifying the exact remote objects and their sample/control mappings. Archive presence is not ingestion readiness. [GSE197215](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE197215), [GSE217245](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE217245), [GSE226336 family](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE226336).

### D16 — sample identity and overlap index

**Local saved audit outputs:** `remote-audit/integration/geo_series_samples.tsv`, `geo_sample_attributes.tsv`, `geo_series_attributes.tsv`, `geo_cross_series_sample_overlap.tsv` and `sample-index-manifest.json`.

**Use:** starting inventory for source IDs, metadata and parent/child overlap checks. **Needed:** selected-study patient/sample/assay crosswalk with adjudicated timepoints. A GSM identifier can represent different biological units across studies; this index is not a harmonized patient table.

### D17 — PRINCE branch, potential acquisition

No filenames identifying PRINCE or its paper DOI were found in the inspected project tree. Treat this as **not located**, not proof it exists nowhere. The [primary publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC9205784/) identifies available clinical and processed biomarker data.

**Acquire:** exact de-identified clinical release, processed baseline CyTOF and sample metadata; optional released RNA/mIF tables after matching is established. **Require:** patient ID, phase/population, treatment assignment, collection timing, survival time/event definition, baseline covariates, feature denominator and assay version. Freeze the eligible population and candidate feature family. Analyse this as a distinct case pack; I-SPY2 is not a silent replacement.

### D18 — new laboratory results and scientist feedback, generated

Create `experiment_spec`, `sample_manifest`, raw/readout files, control/QC results, `review_event`, `lesson_candidate`, `memory_release` and `evaluation_manifest`. These records do not currently exist merely because the reference graph defines assays or reviews. Synthetic outcomes require an explicit simulation label, hidden-world version and seed; they never become observed biological evidence.

## Tool register

**Status:** “prototype” means inspected local implementation; “available skill” means a workflow guide is installed; “proposed” means a function/environment still needs implementation or verification. No new analyses, API inference or GPU jobs were executed for this document.

| ID | Tool / implementation route | Required inputs → outputs | Role and boundary |
| --- | --- | --- | --- |
| T01 | Rosalind coordinator and specialist prompts; model adapter proposed | Bounded question + evidence references + action schema → proposed action/review/brief | Reasoning and integration. Configure the model actually accessible. GPT-Rosalind availability is access-dependent; the local package named `rosalind` does not prove that model is being called. |
| T02 | Local Python `Ledger`, `Registry`, JSON Schema validation; durable runner proposed | Typed question + tool args → validated result, evidence event and hashed artifact | Existing prototype foundation. Add stable resumable jobs, transactional state and cancellation. It currently is not a full LLM orchestrator. |
| T03 | pandas/Arrow or R table import; schema/join validators; CSV/JSON/XML readers, reviewed PDF/XLSX extraction | Source bytes + dictionary + manifest → cohort/sample/assay tables and exclusion report | CPU preparation. Validate join cardinality, units, timing and reference versions. Table-extraction uncertainty requires source review. Environment not verified here. |
| T04 | Bulk RNA: DESeq2/edgeR for suitable counts; limma for suitable normalized microarray/protein data | Matrix + feature annotation + design → contrasts, intervals, multiplicity and diagnostics | Bioinformatics/statistics. Select by assay scale; gene counts do not replace splice counts. Proposed adapters. |
| T05 | Single-cell: Scanpy/AnnData or Seurat; donor-aware aggregation and suitable downstream statistical model | Matrix + cell/sample/donor annotations → QC, cell states, donor-level summaries | Optional CPU branch; GPU acceleration only after equivalence and need are assessed. Do not treat cells as independent patients. |
| T06 | Statistics: R `survival`, model/interaction/diagnostic functions; appropriate regression or paired summaries | Endpoint-ready analysis table + frozen spec → effects, uncertainty and sensitivity results | Deterministic CPU calculations. Survival only with verified time/event data. Keep small designs proportionate to available independent observations. |
| T07 | Evo 2 NIM; prototype `evo2_score_snv` | Reference DNA context + mapped ref/alt SNV → model likelihood contrast | Sequence plausibility/experimental-label benchmarking. Existing scoring route uses local forward outputs; generation smoke tests are a different task. No calibrated resistance probability. |
| T08 | Boltz-2 NIM; prototype `boltz2_compare_complex` | Mapped WT/mutant proteins + correct partner → paired predicted structures and model confidence | Current adapter targets protein/binder comparisons. ALK–small-molecule prediction needs a separately validated ligand-capable adapter. Optional affinity output is a model prediction, not measured clinical resistance. |
| T09 | DiffDock NIM, available skill; proposed adapter | Prepared receptor structure + valid small-molecule ligand → poses and confidence | Optional ligand-pose question only. Does not dock antibody therapeutics as if they were small molecules or establish affinity/causality. |
| T10 | MSA Search + OpenFold2/OpenFold3, available skills; optional adapters | Suitable sequence/complex + required MSA/template inputs → structural prediction | Use if the scientific question requires this alternative. Not all folding models need to run on every case. Endpoint, hardware and output validation remain to be verified. |
| T11 | Structure Viewer / PyMOL-style geometry tools; Sequence Viewer | Real structure/sequence files + residue mapping → inspectable selections, contacts and comparison artifacts | Inspect and verify the relevant chain/construct. A rendered picture is not a quantitative effect or functional assay. |
| T12 | NGS Analysis Workbench; conventional QC/alignment/quantification; optional Parabricks | Selected raw FASTQ/BAM + sample sheet + compatible reference → validated QC/alignment/count or variant outputs | Raw-data branch only. Discover a compatible workflow and current compute first. Do not reprocess raw reads just to analyse an already suitable matrix. Parabricks is optional GPU execution, not the reasoning layer. |
| T13 | Local label parser; timeline checks; selected PK/PD model if data support it | Actual dose/time/concentration observations + covariates → exposure assessment with diagnostics | Pharmacology. Label-only inputs yield reference context and an exposure-data gap, not an individual exposure estimate. |
| T14 | Life-science connectors / pinned HTTP retrieval: GEO/Entrez, UniProt, Ensembl, RCSB, PubChem/ChEBI, Reactome, cBioPortal, ClinicalTrials.gov | Explicit accession/entity and version → cited reference records and source manifests | Retrieval, identity and background evidence. Cache source versions; segregate withheld labels. Connector availability is not proof every query succeeded. |
| T15 | Graph read adapter, SQLite event store, artifact store and memo renderer | Case events + contracts → navigable claim-to-source evidence and decision versions | Proposed operational layer. Existing graph HTTP service is read-oriented; do not invent analysis-write endpoints. |
| T16 | Simulation/replay backend + deterministic validators + blinded scientist rubric | Frozen case pack, hidden world, tool recordings and policy → trace and scored results | Same runner interfaces as live execution; hidden truth separate from agent access. No automatic switch from live to synthetic results. |
| T17 | Feedback capture, scoped lesson retrieval, release/evaluation service | Exact reviewed decision + feedback + disjoint cases → candidate lesson or approved release | Proposed. Case corrections and shared-memory activation are separate transitions. Reviewer simulation tests mechanics, not biological validity. |

The official [OpenAI life-sciences guidance](https://learn.chatgpt.com/use-cases/collections/life-sciences) describes GPT-Rosalind access for qualified users and scientific plugin workflows. This design requires an explicit model/access check before choosing an execution adapter; it does not assume a new Workbench endpoint.

The [DESeq2 vignette](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html) documents count-based models and design/contrast handling; [Scanpy documentation](https://scanpy.readthedocs.io/en/stable/) describes its single-cell toolkit. The exact population, design and independent unit remain study-specific implementation choices.

NVIDIA documents [Evo 2 forward outputs](https://docs.nvidia.com/nim/bionemo/evo2/latest/endpoints.html), [Boltz-2 structure and affinity prediction](https://docs.nvidia.com/nim/bionemo/boltz2/latest/overview.html), [DiffDock](https://docs.nvidia.com/nim/bionemo/diffdock/latest/index.html) and [Parabricks tools](https://docs.nvidia.com/clara/parabricks/about-parabricks/software-overview/software-tools). Pin the exact endpoint/container/model used. The installed BioNeMo skills and local prototype may target an earlier contract; current documentation does not retroactively validate the local adapter.

BioNeMo Agent Toolkit supplies biological tool skills. NeMo Agent Toolkit is a distinct orchestration/evaluation option. Neither replaces the statistical model, case store or independent scientific review. Binder generation/design tools are outside this resistance-investigation reference architecture until there is a separate design objective.

## Potential acquisition backlog, in dependency order

| Priority | Missing input | Source / action | Unlocks |
| --- | --- | --- | --- |
| 1 | Validated selected-cohort sample/assay/clinical crosswalk | Derive from D02/D03/D04/D16 and original supplements; manually adjudicate ambiguous timing | S02–S06; prevents fabricated pairing |
| 1 | Exact molecular reference package for selected ALK variants | Frozen UniProt/Ensembl sequence and mappings; RCSB structures; correct inhibitor identity from PubChem/ChEBI | S07; enables valid Evo/Boltz/DiffDock inputs |
| 1 | Patient-specific exposure and response timeline | Selected publication supplements or an authorized clinical data source; the documented Dagogo-Jack plasma supplement is a potential public addition | S03/S08; partial clinical metadata alone cannot resolve exposure |
| 1 for splice claim | CD20 junction/isoform or appropriate raw-read evidence | Selected study supplement/SRA read subset and reference annotation | S04/S09; direct splice investigation |
| 1 for PRINCE branch | Clinical + baseline CyTOF and assay/sample dictionary | PRINCE paper's data-availability route; freeze exact release and population | D17 → S03–S06; survival branch |
| 2 | Complete remote immune-state objects | Verify D15 remote recorded files and extract only required members | Immune dysfunction/activation alternatives |
| 2 | Measured binding/functional benchmark for the relevant system | Assay-specific ChEMBL/BindingDB, MaveDB/ProteinGym or permitted SKEMPI subset, with frozen release | Model-output calibration; current binding manifest has no acquired records |
| 3 | Complete SU2C-MARK processed package | Resume selected official archive then validate integrity and join contracts | Additional external cohort |

Acquire only the inputs needed by the selected case pack. Different diseases, therapeutics, cell lines and cohorts supply separate evidence contexts; they must not be joined into a fictitious multimodal patient.
