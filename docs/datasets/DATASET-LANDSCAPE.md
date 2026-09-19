# Rosalind dataset landscape and acquisition guide

Research snapshot 19 September 2026

This catalog supports the attached Rosalind architecture: investigate acquired therapeutic resistance, preserve competing hypotheses, integrate molecular evidence, and evaluate whether the agent rejects false discoveries. It also covers larger translational-response studies, perturbation ground truth, structures, imaging and reference knowledge bases that could extend the project.

**Recommendation:** retain CD20 splicing as the smallest clinical demo; use BCMA antigen escape for the most natural genomic and structural extension; use CD19 minigene experiments for measured variant-to-splicing labels; use I-SPY2 for a larger RNA–protein–response demonstration. Add fresh blinded fixtures for the primary evaluation.

## What was verified

GEO series metadata and supplementary-file listings were retrieved directly. Four small files from GSE243919/GSE164551 were downloaded, decompressed and inspected. Other resources were checked through their official pages, primary publications or author repositories; access labels distinguish public listings from completed downloads. This is a discovery and acquisition guide, not a completed harmonized dataset. Public visibility does not establish every redistribution or commercial-use right; retain each resource’s terms.

The catalog contains **43 GEO accessions and 50 additional cohort or resource entries**. Several GEO entries are parent/child series from the same study. Knowledge bases, simulators and portals are explicitly labeled; these totals are not counts of independent clinical cohorts.

## Findings that change the architecture

1. **The CD20 anchor is a splicing and RNA–protein contradiction case.** GSE243919 describes four paired patients with CD20 protein loss, while RNA abundance/coding variants do not necessarily explain it. Its associated paper is Ang and colleagues, PMID 37683180. The downloaded file contains gene-level counts, not splice-junction counts. A count-only implementation must request junction/isoform evidence rather than announce a splicing mechanism.
2. **BCMA escape is a stronger natural route to genomic and interface analysis.** GSE226336 and its children support target deletion and extracellular target alteration as distinct branches. Public GEO components do not automatically include every WGS assay described in the paper. GSE164551 has unusually useful public derived genomic files, but eight longitudinal samples come from one patient.
3. **CD19 minigene mutagenesis supplies experimental labels.** GSE182891 and GSE182892 provide variant and isoform files. They are suitable for testing a sequence-scoring component against measured splice behavior; they do not establish that every splice-changing variant causes clinical relapse. The associated article has a confusing accession label in its availability text; the GEO records resolve DNA to GSE182891 and RNA to GSE182892.
4. **I-SPY2 is unusually rich for a broader translational agent.** The paired resource includes baseline expression and treatment-response information for 987 patients, with a 736-patient protein/phosphoprotein subset. It expands the demo into treatment-specific biomarker reasoning; it does not replace longitudinal resistance data.
5. **Assay records, cells and patients are different denominators.** Some accessions contain thousands of individual-cell records; others package thousands of cells as a single GEO sample. The catalog reports denominators explicitly wherever verified.
6. **A public processed release can bypass a raw-data bottleneck.** SU2C-MARK has a public author-deposited source package despite controlled raw sequencing. Similar distinctions apply to CAR-T cohorts and CoMMpass. DAISY and Hartwig require requests for important patient-level components.

Sources: [GSE243919](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243919), [CD20 splicing paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10667349/), [CD19 mutagenesis paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9500061/), [I-SPY2 parent](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196096), [SU2C-MARK source release](https://zenodo.org/records/11179623).

## Priority shortlist

| Priority | Data package | Why select it | First usable slice | Effort estimate |
|---|---|---|---|---|
| 1 | GSE243919 | Small, directly aligned clinical anchor | Eight-column patient count matrix plus paired metadata | Low for counts; higher for splicing |
| 2 | GSE164551 | Longitudinal BCMA case with public derived genomics | Cell metadata, expression subset, mutation table and CN-related evidence | Medium |
| 3 | GSE182891 and GSE182892 | Experimental variant and splice labels | Minigene variants joined to isoform output | Low to medium |
| 4 | GSE226336 family | Deletion versus epitope escape | One published case with verified available assay components | Medium to high |
| 5 | GSE197215 | Real target/non-target/unstimulated controls | One donor-matched stimulation comparison | Medium |
| 6 | GSE194040 and GSE196093 | Large clinical RNA/protein/response resource | Matched subset in one treatment contrast | Medium |
| 7 | GSE217245 | Immune dysfunction alternative to target loss | One pre/late matched TCE subset | Medium |
| 8 | GSE234261 | Blood/marrow RNA, surface protein and repertoire | One tissue and a small matched donor subset | Medium to high |
| 9 | GSE65185 or GSE50509 | Acquired targeted-drug resistance beyond immunotherapy | Verified baseline/progression pairs | Low to medium |
| 10 | SU2C-MARK v3 | Clinical + exome-derived + RNA evidence | Public source tables with author README | Medium; package is 1.2 GB |
| 11 | scPerturb or a Tahoe subset | Perturbation outcomes and real control distributions | One cell line, selected perturbations and controls | Low to medium if preprocessed |
| 12 | SKEMPI 2 plus exact relevant PDB structures | Measured binding effects for structural evaluation | A small family-separated mutation subset | Medium |

Effort is an implementation judgment for a small processed subset, not a measured runtime or promise of immediate compatibility.

## Empirical GEO catalog

All accession links lead to the primary series record. Supplementary links are reproduced from that record in the acquisition section. Most listed series expose processed files publicly; consult the limitation column for raw-data restrictions. A filename containing `RAW.tar` is a GEO packaging convention and does not itself mean that raw FASTQ sequencing is available.


### CD20 loss and splicing

| Accession | Data and scale | Rosalind use | Important constraint |
|---|---|---|---|
| [GSE243919](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243919) | Four NHL patients; eight paired pre-mosunetuzumab and relapse FFPE RNA-seq samples. | Primary CD20 demo; RNA–protein contradiction and splice-hypothesis branching. | Gene counts are public and downloaded; junctions require read-level analysis. Protein loss is documented in study metadata, not a matched quantitative proteomics matrix. |
| [GSE243920](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243920) | Raji cell direct long-read RNA sequencing. | Orthogonal validation of CD20 transcript isoforms and reverse-transcription artifact checks. | One cell-line sample; not independent clinical replication. |
| [GSE212312](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212312) | Normal tonsil B-cell subsets and REH perturbation experiments; 23 GEO records. | Reference splicing and cell-state context. | Mixed normal and engineered conditions; select the correct subset. |
| [GSE115655](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE115655) | Normal marrow pro-B, pre-B and immature B cells; 16 records. | Developmental-state control for CD19/CD20 expression and isoforms. | Normal reference rather than a treatment cohort. |

### BCMA and GPRC5D resistance

| Accession | Data and scale | Rosalind use | Important constraint |
|---|---|---|---|
| [GSE164551](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164551) | Eight longitudinal samples from one BCMA CAR-T patient; cell metadata, mutation and FACETS-related files. | Best compact acquired-resistance investigation with expression and genomic evidence. | Eight timepoints/samples are not eight independent patients. Raw human data are directed to dbGaP; public mutation file is not a complete paired multi-timepoint mutation matrix. |
| [GSE143317](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143317) | BCMA deletion relapse case; two scRNA-seq sample records. | Independent published BCMA-loss sanity check. | Case-level inference; map the public matrices to the paper’s timepoints. |
| [GSE226336](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE226336) | Antigen-escape study SuperSeries; 39 records across child series; paper describes a 30-patient investigation. | Top mechanistic extension: target deletion versus extracellular epitope alteration. | Do not equate 39 records with 39 patients or assume all paper assays are in GEO. |
| [GSE226327](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE226327) | Single-cell copy-number child series; 37 records. | Clonal loss, biallelic events and selection of pre-existing clones. | Child of GSE226336; not an independent replication cohort. |
| [GSE226335](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE226335) | Single-cell RNA child series; two records. | Expression component of the same antigen-escape study. | Not the entire study’s WGS or single-cell data; inspect each modality separately. |
| [GSE217245](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE217245) | 45 records; marrow T-cell RNA/VDJ under BCMA T-cell engagers and CAR-T. | Immune exhaustion versus tumor-intrinsic antigen escape; pre/late comparisons. | Only some late samples are relapse samples. Different therapies must remain distinct. |
| [GSE234261](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE234261) | 100 assay/sample records; blood and marrow at leukapheresis and approximately day 30 after BCMA CAR-T. | RNA, surface protein, TCR and BCR integration; early resistance correlates. | Day 30 is not automatically relapse. Resolve libraries to donors and tissues. |
| [GSE210079](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE210079) | 24 records; marrow tumor and immune cells before/after BCMA CAR-T. | Durability-of-response context and tumor versus immune-state decomposition. | Verify which protein/cytometry outputs accompany the public sequencing files. |

### CD19 escape and CAR T cell function

| Accession | Data and scale | Rosalind use | Important constraint |
|---|---|---|---|
| [GSE182894](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182894) | CD19 mutagenesis and RNA-binding protein SuperSeries. | Best experimental sequence-to-splicing benchmark family. | Parent groups the following three assays; do not count them as independent studies. |
| [GSE182891](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182891) | Two DNA-seq records; public CD19 minigene variant table. | Construct variant inputs with exact sequence identity. | Engineered minigene context differs from endogenous patient chromatin. |
| [GSE182892](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182892) | Two RNA-seq records; public CD19 minigene isoform table. | Measured splice outcomes for scoring variant-effect predictions. | Split by variant neighborhood or construct; correlated variants can leak across random splits. |
| [GSE182893](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182893) | Four PTBP1 iCLIP2 records in NALM-6. | Mechanistic support for RNA-binding protein involvement. | Binding evidence is not proof of clinical resistance. |
| [GSE197215](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE197215) | 120 records; CAR-T scRNA/CITE-seq under CD19, TCR, non-target and unstimulated conditions. | Excellent real negative controls; investigate CD19-positive relapse and T-cell dysfunction. | Stimulation conditions share products/donors; split by patient, not cell. |
| [GSE241783](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241783) | Infusion-product scRNA/TCR profiles from 59 axi-cel patients. | Product-state correlates and external CAR-T comparison. | Infusion-product data do not establish acquired tumor antigen loss. |
| [GSE151511](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE151511) | 24 scRNA infusion-product records. | Efficacy/toxicity and T-cell-state benchmark. | Raw data are EGA-controlled; possible overlap with later cohorts needs checking. |
| [GSE150992](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE150992) | Companion CapID infusion-product dataset; 40 GEO records. | Complementary assay/context for the Deng study. | Series title and design use different counts; resolve sample-level mapping before combining. |
| [GSE125881](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE125881) | 32 records from four patients; infusion product and early/late/very late blood. | Longitudinal CAR-T clonal persistence. | Repeated measurements within four individuals. |
| [GSE235760](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE235760) | 40 records from five patients; CAR-positive and CAR-negative infusion/expansion cells. | Matched cellular controls and within-patient contrasts. | CAR-negative cells are not interchangeable with untreated independent donors. |
| [GSE273170](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE273170) | 81 records; apheresis, product and days 7/14; CITE-seq and TCR. | Baseline immune state, clonal expansion and durable response. | Raw reads are dbGaP-controlled; day 7/14 samples are not progression biopsies. |
| [GSE203610](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE203610) | 20 follicular lymphoma and three reactive lymph-node biopsies; 67 assay records. | Relevant lymphoma microenvironment reference with TCR/BCR. | Cross-sectional context, not a bispecific-treated relapse cohort; raw data in EGA. |

### Checkpoint response and immune escape

| Accession | Data and scale | Rosalind use | Important constraint |
|---|---|---|---|
| [GSE91061](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE91061) | 109 RNA-seq samples from 65 melanoma patients; 51 pre and 58 on treatment. | Larger longitudinal expression demo; response-associated changes. | On-treatment does not imply progression; only matched subsets support paired analysis. |
| [GSE78220](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE78220) | 28 pretreatment melanoma biopsy records with anti-PD-1 response context. | Small, easily loaded response benchmark. | FPKM spreadsheet, not raw counts; no longitudinal acquired-resistance claim. |
| [GSE115978](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE115978) | Melanoma ecosystem single-cell counts, TPM and annotations; 7,186 cell records. | Separate malignant-cell programs from immune composition. | Cell count is not patient count; raw sequencing under controlled access. |
| [GSE120575](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE120575) | 48 melanoma tumor samples; single-cell T-cell state and immunotherapy context. | Immune-state generalization and response association. | Public TPM and patient mapping; raw reads in dbGaP. |
| [GSE123813](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123813) | 86 assay records; paired single-cell RNA/TCR in skin cancers under PD-1 blockade. | Clonal replacement versus reinvigoration; treatment-time reasoning. | Map cell types, patients, cancer types and timepoints before comparison. |
| [GSE135222](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE135222) | RNA-seq from 27 advanced NSCLC patients receiving anti-PD-1/PD-L1. | Independent tumor-type validation of response signatures. | Small cohort; do not interpret association as treatment-specific causality. |
| [GSE119144](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE119144) | 60 methylation-array records linked to the same lung cancer study. | Epigenetic mechanism versus high-mutation-load narrative. | The methylation and RNA cohorts are not guaranteed to have identical membership. |

### Targeted therapy and non genetic resistance

| Accession | Data and scale | Rosalind use | Important constraint |
|---|---|---|---|
| [GSE65185](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE65185) | 70 melanoma RNA-seq records before MAPK inhibitors and after resistance. | Strong non-immunotherapy acquired-resistance branch. | Processed FPKM; resolve matched patients, lesions and drugs. |
| [GSE50509](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE50509) | 61 melanoma array records before BRAF inhibitors and at progression. | Independent resistance mechanism and expression analysis. | Potential overlap with other melanoma studies must be ruled out. |
| [GSE99898](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE99898) | 38 melanoma expression-array records under BRAF or BRAF/MEK treatment. | Immune escape accompanying targeted-drug resistance. | Treatment mixtures and cohort reuse can confound validation. |
| [GSE134836](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE134836) | Two PC9 cell-line conditions with erlotinib single-cell profiling. | Fast drug-tolerant state fixture using a real experimental background. | This accession is cell-line data, not eight patient biopsies, despite misleading secondary descriptions. |
| [GSE110894](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE110894) | Single-cell counts and a cell-information workbook for BET-inhibitor resistance. | Non-genetic resistance, state switching and rescue hypotheses. | Model-system experiment; one GEO record packages many cells. |
| [GSE75367](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE75367) | 74 single candidate circulating tumor cells in a breast-cancer study. | HER2 state heterogeneity and contamination controls. | Includes candidate cells later excluded as likely white blood cells; follow original annotations. |

### Clinical response and matched protein data

| Accession | Data and scale | Rosalind use | Important constraint |
|---|---|---|---|
| [GSE196096](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196096) | I-SPY2 parent combining transcriptomic and RPPA components. | Best broader translational-study family beyond relapse. | 1,724 combined GEO records do not equal 1,724 patients. |
| [GSE194040](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE194040) | I-SPY2 expression and clinical data: 987 patients, 10 arms, 988 array records. | Treatment response, biomarker interactions and RNA–protein concordance. | Baseline biomarkers and pCR, not serial acquired resistance. Adaptive randomization, subtype and platform effects matter. |
| [GSE196093](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196093) | I-SPY2 RPPA: 736 patients across eight arms; 139 signaling endpoints. | Matched protein/phosphoprotein evidence; pathway activation versus RNA abundance. | The 736-patient subset is not identical to all 987 expression patients; inspect platform annotation, including 140-endpoint parent file. |
| [GSE25066](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE25066) | 508 breast-cancer records in a neoadjuvant chemotherapy predictor SuperSeries. | Response/survival analysis and explicit discovery/validation split evaluation. | Preserve original child-cohort split; this is not an ADC-resistance dataset. |

### Perturbation compendia in GEO

| Accession | Data and scale | Rosalind use | Important constraint |
|---|---|---|---|
| [GSE70138](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE70138) | LINCS L1000 Phase II perturbational profiles and metadata. | Drug/signature matching and hypothesis-generating pathway rescue. | Select processed level and cell/dose/time subset; measured landmark genes differ from inferred genes. |
| [GSE92742](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE92742) | LINCS L1000 Phase I perturbational profiles and metadata. | Broader perturbation background and reproducibility checks. | Large files; overlap and protocol effects mean Phase I/II are not naive independent replicates. |

## Additional cohorts and supporting resources

These entries deliberately separate clinical data from model-system experiments, general reference data and evaluation software. Resource-level listings require a specific study/release selection before ingestion.


### Additional clinical cohorts

| Dataset or resource | Content | Access and verification | Proposed use and limitation |
|---|---|---|---|
| [Maynard lung therapy evolution](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/) | PRJNA591860; treated human lung cancer single-cell study | Open study/code route; processed-file download not tested | Treatment-naive, residual and progressive disease context; useful EGFR/ALK branch. Verify matched subjects. |
| [Orlando CD19 relapse](https://pmc.ncbi.nlm.nih.gov/articles/PMC9500061/) | SRP141691; targeted aligned read evidence used in the CD19 splicing paper | Paper-confirmed archive route; files not downloaded | Nine usable matched screening/relapse RNA pairs in the reanalysis after excluding one mislabeled DNA sample. Restricted gene coverage; excellent assay-identity trap. |
| [SU2C MARK NSCLC](https://zenodo.org/records/11179623) | Public clinical, exome-derived, RNA and analysis-source package | Open Zenodo v3; 1.2 GB listing and README checked; raw data controlled | Strong multimodal response benchmark. Paper’s raw WES/RNA uses dbGaP phs002822; public processed outputs can be used separately. |
| [IMvigor210](https://research-pub.gene.com/IMvigor210CoreBiologies/) | Atezolizumab urothelial-cancer expression and response data | Mixed; official processed-package endpoint found, download not verified | Popular response benchmark, hence high contamination risk; do not substitute lung-cancer labels or trust unofficial repackaging. |
| [Beat AML](https://www.nature.com/articles/s41586-018-0623-z) | Primary AML molecular profiles plus ex vivo drug sensitivity | Public published/portal route; release-specific files need checking | Connect mutation/expression to measured drug sensitivity. Ex vivo response is not patient response. |
| [POG570](https://www.bcgsc.ca/downloads/POG570/) | Advanced-cancer genomic and transcriptomic cohort; 570 tumors | Open processed download directory checked | Copy-number, expression and therapy-history context; chiefly advanced-cancer profiling, not a universal paired relapse series. |
| [GLASS](https://glass-consortium.org/datasets/) | Longitudinal primary/recurrent glioma resource | Processed resource with portal terms; raw data not generally available | Tumor evolution, recurrence and treatment effects; keep collection sites and repeat samples explicit. |
| [MMRF CoMMpass](https://registry.opendata.aws/mmrf-commpass/) | Longitudinal newly diagnosed myeloma cohort | Mixed; open expression plus controlled human genomic data | Disease context, treatment trajectories and relapse. It is not intrinsically a BCMA CAR-T cohort. |
| [DAISY](https://www.nature.com/articles/s41591-023-02478-2) | HER2-variable breast cancer under trastuzumab deruxtecan | Public paper/code; clinical data on request; WES EGAD00001011110 controlled | Excellent future ADC resistance investigation with baseline/resistance biopsies. Do not make hack completion depend on approval. |
| [Hartwig Medical Foundation](https://www.hartwigmedicalfoundation.nl/en/data/data-access-request/) | Metastatic-cancer WGS and treatment/outcome context | Application and data-access agreement required | High-value long-term real-world validation; not immediate hack data. |
| [TRACERx](https://clinicaltrials.gov/study/NCT01888601) | Prospective lung-cancer evolutionary sampling and recurrence | Mixed paper/source outputs and controlled patient sequencing | Spatial versus temporal evolution and ctDNA/relapse context; select a publication-specific release. |

### Functional perturbation and model systems

| Dataset or resource | Content | Access and verification | Proposed use and limitation |
|---|---|---|---|
| [DepMap and CCLE](https://depmap.org/portal/download/all/) | Cell-line CRISPR dependency, expression, mutation and copy number | Public releases; download-page bot check encountered | Prioritize bypass mechanisms and experiments. Freeze release; dependency in cell lines is not resistance in patients. |
| [PRISM Repurposing](https://depmap.org/repurposing/) | Broad cell-line compound-sensitivity screens | Public portal reached; files not downloaded | Test whether nominated rescue mechanisms predict sensitivity to alternative perturbations. |
| [CTRP](https://portals.broadinstitute.org/ctrp.v2.1/) | Cancer Therapeutics Response Portal compound-response data | Public portal reached | Orthogonal compound sensitivity with matching cell-line features; reconcile drug aliases and dose units. |
| [GDSC through PharmacoDB](https://pharmacodb.ca/) | GDSC and other pharmacogenomic screens | Conditional: legacy GDSC download URL returned 410; PharmacoDB reachable | Useful standard comparator; resolve provenance/version and current downloadable route before selecting. |
| [DrugComb](https://academic.oup.com/nar/article/47/W1/W43/5486743) | Curated combination and monotherapy screening data | Public resource; individual study reuse terms apply | Evaluate proposed combination experiments using measured synergy/sensitivity; avoid mixing synergy definitions. |
| [scPerturb](https://github.com/sanderlab/scPerturb) | Harmonized single-cell perturbation datasets | Open standardized files via project and linked Zenodo releases | Best quick perturbation subset for hidden response and negative-control tasks. Underlying studies overlap with other compendia. |
| [Genome Wide Perturb seq](https://gwps.wi.mit.edu/) | CRISPR perturbation single-cell transcriptomes | Official study portal reached | Gene-to-expression ground truth for pathway hypotheses and next-experiment selection. Model-system transfer is a separate test. |
| [Tahoe 100M](https://huggingface.co/datasets/tahoebio/Tahoe-100M) | Over 100 million cell profiles; 50 cancer cell lines; 1,100 small-molecule perturbations | Open dataset card and partitioned files; not downloaded | Broad drug-response cell-state atlas. Select a small drug/line/control subset; these are cell lines, not 100 million patients. |
| [JUMP Cell Painting](https://jump-cellpainting.broadinstitute.org/) | Perturbational cell morphology imaging/profiles | Public consortium portal reached | Orthogonal phenotype and rescue screening; morphology is not a molecular mechanism label. |
| [Cell Model Passports](https://cellmodelpassports.sanger.ac.uk/) | Cell-line/organoid model identities and molecular annotations | Public portal reached | Choose biologically suitable validation models and harmonize identifiers. |
| [PDXNet](https://www.pdxnetwork.org/) | Patient-derived xenograft studies and treatment-response resources | Resource located; study-level availability varies | Preclinical validation of hypotheses and response signatures; mouse context and passage effects matter. |

### Protein structure and quantitative benchmark data

| Dataset or resource | Content | Access and verification | Proposed use and limitation |
|---|---|---|---|
| [CD20 rituximab complex](https://www.rcsb.org/structure/6VJA) | PDB 6VJA experimental complex | Open structure record verified; 3.3 angstrom cryo-EM | Interface mapping and structural tool checks. Rituximab is not mosunetuzumab: never imply the exact therapeutic interface is interchangeable. |
| [CD19 CD81 coltuximab complex](https://www.rcsb.org/structure/7JIC) | PDB 7JIC experimental complex | Open structure identity verified | CD19 assembly and interface context; coltuximab is not the FMC63 CAR binder. |
| [SKEMPI 2](https://life.bsc.es/pid/skempi2/) | Measured mutation effects on protein–protein binding; 7,085 mutations listed | Open database and download page verified | Useful independent biophysical labels for structure triage; split by complex/family, not mutation row. |
| [ProteinGym](https://github.com/OATML-Markslab/ProteinGym) | Deep mutational scanning and curated protein fitness benchmarks | Official open repository and downloads | Calibration and variant-ranking tests; generic fitness is not automatically antibody binding or drug resistance. |
| [MaveDB](https://www.mavedb.org/) | Experimental multiplexed variant-effect score sets | Public resource; select and verify individual assay | More assay-specific labels for DNA/protein variants; use binding or splicing endpoints appropriate to the question. |
| [SAbDab](https://sabdab.opig.stats.ox.ac.uk/) | Antibody experimental structures and complex annotations | Public site reached; now redirects to SAbDab2 | Find exact binder sequences and comparable structures; benchmark split must prevent homologous-complex leakage. |
| [AlphaFold DB](https://alphafold.ebi.ac.uk/) | Predicted protein structures | Public reference resource | Context for unmapped protein regions; a predicted monomer is not an experimentally measured therapeutic complex. |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | Curated compound, target and activity data | Open; CC BY-SA terms shown on site | Small-molecule assay evidence, target mapping and alternative-tool evaluation. Preserve assay type and units. |
| [BindingDB](https://www.bindingdb.org/) | Measured protein–ligand binding data | Public resource; select assay-level records | Small-molecule binding calibration. Do not treat it as a complete antibody-antigen affinity benchmark. |

### Reference atlases and multimodal context

| Dataset or resource | Content | Access and verification | Proposed use and limitation |
|---|---|---|---|
| [TCGA through GDC](https://gdc.cancer.gov/access-data/data-access-processes-and-tools) | Multi-cancer molecular profiles, pathology and clinical annotations | Mixed open derived and controlled raw data | Background prevalence, purity and tumor-type context. TCGA is not a systematic treatment-resistance cohort. |
| [cBioPortal](https://www.cbioportal.org/datasets) | Study-specific processed molecular and clinical tables | Public studies; study-level terms and cohort duplication matter | Convenient integration of mutations/CNA/clinical attributes. Count source cohorts once across mirrors. |
| [CPTAC and Proteomic Data Commons](https://pdc.cancer.gov/pdc/) | Tumor proteomics and phosphoproteomics with linked genomic studies | Public proteomic data; linked genomic access varies | RNA–protein discordance and pathway activation. Join actual sample IDs instead of assuming patient-level modality completeness. |
| [Human Tumor Atlas Network](https://humantumoratlas.org/) | Spatial, single-cell and multimodal tumor atlases | Public resource with assay-specific access levels | Spatial heterogeneity, immune exclusion and sampling-location alternatives; choose a named atlas. |
| [CELLxGENE Discover and Census](https://cellxgene.cziscience.com/) | Downloadable single-cell collections and queryable census | Open curated data; collection licensing and duplicate donors need checking | Cell identity and normal/malignant reference profiles. It is a discovery index, not a single independent cohort. |
| [Human Protein Atlas](https://www.proteinatlas.org/about/download) | Tissue, blood, single-cell and protein-expression references | Download page verified | Normal lineage expression and protein localization; does not supply matched relapse protein assays. |
| [GTEx](https://www.gtexportal.org/home/downloads/adult-gtex) | Normal-tissue expression and regulatory associations | Open summaries; individual genomic data controlled | Tissue specificity and regulatory context; normal postmortem samples are not clinical tumor controls. |
| [Expression Atlas](https://www.ebi.ac.uk/gxa/home) | Curated differential and baseline expression studies | Open study-specific downloads | Broader independent expression studies; retain original accession lineage. |
| [ENCODE](https://www.encodeproject.org/) | Regulatory genomics and RNA-binding assays | Public portal reached | Promoter, enhancer and RNA-binding hypotheses; tissue/cell-line match is essential. |
| [PRIDE](https://www.ebi.ac.uk/pride/archive/) | Mass-spectrometry proteomics studies | Public archive; choose individual PXD study | Independent target-protein measurements and assay context. No specific relapse PXD accession was validated in this sweep. |
| [TCIA NSCLC Radiogenomics](https://www.cancerimagingarchive.net/collection/nsclc-radiogenomics/) | Paired imaging and molecular/clinical lung-cancer resource | Collection page reached; image downloads not tested | Imaging–omics joins and phenotype context; not primarily acquired-resistance data. |

### Genomics controls and evidence knowledge bases

| Dataset or resource | Content | Access and verification | Proposed use and limitation |
|---|---|---|---|
| [Genome in a Bottle](https://github.com/genome-in-a-bottle/giab_data_indexes) | Reference human sequencing and benchmark variant calls | Official data indexes verified | Parabricks technical precision/recall and difficult-region tests; germline truth is not acquired resistance truth. |
| [SEQC2 HCC1395](https://pmc.ncbi.nlm.nih.gov/articles/PMC8532138/) | Somatic tumor/normal reference material and sequencing benchmark | Primary study identified; exact release download not tested | Better somatic-call benchmark than a patient cohort without truth labels. Not longitudinal clinical evolution. |
| [Splatter](https://github.com/Oshlack/splatter) | Single-cell count simulation framework | Open software, not an empirical dataset | Create hidden null, batch and cell-composition fixtures from a calibrated real background. |
| [CIViC](https://civicdb.org/) | Curated cancer-variant evidence | Public evidence database | Evidence-ledger support and conflicting interpretations; not independent experimental ground truth. |
| [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) | Submitted variant interpretations | Public reference database | Interpretation/provenance controls; germline pathogenicity does not imply acquired treatment resistance. |
| [gnomAD](https://gnomad.broadinstitute.org/) | Population variant frequencies and gene constraint | Public summaries | Passenger/germline plausibility checks; rarity alone is not a resistance mechanism. |
| [Open Targets](https://platform.opentargets.org/) | Target–disease and supporting evidence | Public platform | Knowledge graph context and hypothesis prioritization; not patient-level treatment data. |
| [Reactome](https://reactome.org/download-data) | Curated pathways and downloadable gene sets | Download page verified | Mechanism grouping and enrichment; freeze release and use assay-appropriate gene universe. |

## Packages to build from these sources

### Package A CD20 contradiction demo

Use GSE243919 for the real clinical observation, GSE243920 for orthogonal isoform evidence, and a carefully selected normal B-cell subset from GSE212312/GSE115655 for context. Keep these as separate evidence sources, not a pooled case/control matrix. The agent should compare target-RNA change, tumor purity and broader B-cell markers, then identify the missing junction/translation/protein evidence needed to distinguish hypotheses. If only gene counts are loaded, abstaining from a definitive splice claim is a success.

### Package B BCMA genomic escape demo

Start with GSE164551 and extend to GSE143317 or a single verified GSE226336 case. Distinguish homozygous deletion, selection of a pre-existing clone, transcriptional change and extracellular target alteration. Inspect the actual timepoint represented in each public mutation file. Evo 2 can score sequence candidates with correct reference and allele context; gene deletion is a copy-number event and should not be forced into a point-variant ranking. Only add a structure call if a real interface hypothesis and the relevant therapeutic binder sequence are available.

### Package C Measured falsification benchmark

Use the CD19 minigene DNA and RNA tables, GSE197215’s non-target and unstimulated controls, and a small perturbation subset. Hide outcomes from the agent, then score recovery and uncertainty. These published data can still be memorized; add newly generated hidden perturbations to realistic backgrounds for the primary contamination-resistant evaluation. Keep observed labels separate from intentionally implanted ground truth.

### Package D Broader translational scientist

Use I-SPY2 expression, RPPA and response metadata. Begin with an explicitly matched patient subset and a prespecified biomarker question. Compare RNA abundance with protein/phosphoprotein measurements and test whether associations differ by treatment context. Preserve treatment arms, receptor subtype, assay platform and the original trial design. This demonstrates evidence integration at a more substantial scale while avoiding the claim that baseline response analysis explains acquired resistance.

## Tool and evaluation mapping

| Component | Best data | What the evaluation should test |
|---|---|---|
| Python or R paired expression | GSE243919, GSE65185, paired GSE91061 subset | Correct pairing/direction, count versus normalized-data methods, patient-level uncertainty and null handling |
| Splicing analysis | GSE243920, GSE182892, targeted SRP141691 | Correct isoform/junction inference; no inference from total counts alone |
| Evo 2 | CD19 variant constructs; carefully selected acquired DNA variants | Variant-ranking association with experimental outcome; correct reference strand/build; comparison with a task-specific baseline |
| Parabricks | GIAB for germline; SEQC2 for somatic; patient reads only if authorized and available | Technical variant-call accuracy in truth regions, not clinical mechanism accuracy |
| Boltz or OpenFold-family structural workflow | Exact relevant complexes plus SKEMPI labels | Correct routing to interface-relevant cases; structural confidence separated from measured binding effects |
| Multimodal evidence graph | GSE164551, GSE234261, I-SPY2, SU2C-MARK | Correct patient/sample/assay joins; contradictions retained rather than averaged away |
| Next-experiment selection | GSE197215, CD19 mutagenesis, scPerturb, DepMap | Whether the selected intervention distinguishes competing mechanisms |
| Provenance and retrieval | All sources; CIViC/Reactome as context | Every claim linked to a specific data object, analysis and version; curated prior knowledge not mislabeled as new evidence |

Generic protein-structure confidence is not a calibrated antibody-binding or resistance score. Verify the selected model endpoint’s supported molecule types and scoring claims before using any affinity output.

## Evaluation designs enabled by the catalog

| Test | Real biological background | Hidden change or held-out outcome | Expected behavior |
|---|---|---|---|
| RNA protein contradiction | GSE243919 and separately I-SPY2 | Conceal protein results until the agent requests them | Avoid equating stable RNA with stable protein |
| Variant to splicing | CD19 minigene tables | Hold out measured isoform changes | Rank credible splice-affecting variants with calibrated uncertainty |
| Target present but therapy fails | BCMA extracellular-variant cases; GSE197215 | Contrast retained target with immune/epitope alternatives | Branch beyond target loss |
| Null discovery | Real count/control distributions | Patient-level label swaps or prespecified no-effect simulations | Decline to call a mechanism |
| Composition confounding | Single-cell lymphoma/myeloma atlases | Change cell-type proportions with constant within-cell-type target expression | Recognize composition rather than intrinsic downregulation |
| Batch confounding | Multi-assay or multi-platform data | Associate a batch variable with the outcome | Diagnose non-identifiability or downgrade the claim |
| Temporal leakage | Longitudinal BCMA/CAR-T cohorts | Mix progression features into baseline prediction inputs | Detect invalid temporal availability |
| Assay identity error | SRP141691-inspired test | Include DNA-like data labeled as RNA | Check assay identity before splicing analysis |
| Structural passenger | Relevant complex and measured mutation assays | Match interface and remote-site candidate salience | Use actual interface evidence and uncertainty |
| Treatment context | I-SPY2 or targeted-therapy series | Change arm labels or supply incompatible therapy context | Avoid treating every association as universally predictive |

For GSE243919 there are only four biological pairs: exhaustive within-pair sign swapping has 16 assignments, so a one-sided exact permutation tail cannot be below 1/16 under the usual finite enumeration. Do not promise small p-values from thousands of genes or cells. Use it for transparent case-level reasoning and add independent data for generalization.

Use donor-level train/test partitions, preserve repeated timepoints in one partition, and deduplicate parent/child series and portal mirrors. For structural assays, split by protein/complex family. Measure false discoveries on an adequate number of newly generated null tasks; a single null example does not estimate a reliable false-positive rate.

## Acquisition details verified from GEO

The entries below reproduce selected supplementary-file links from the primary records. All links are HTTPS equivalents of the recorded NCBI FTP URLs. Listings were checked, but only the four files explicitly documented in the download-check section were downloaded. Some series expose detailed data inside per-sample records or series matrices in addition to these files. The first link is an acquisition starting point, not always the smallest or best processed file.


**GSE243919** — RNA-seq analysis of paired Non-Hodgkin's lymphoma (NHL) tumor samples at pretreatment and after mosunetuzumab relapse coinciding with the loss of CD20 protein

- [GSE243919_FFPE_samples_raw_read_counts.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243919/suppl/GSE243919_FFPE_samples_raw_read_counts.csv.gz)

**GSE243920** — Direct long-read RNA sequencing of Raji cells

- [GSE243920_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243920/suppl/GSE243920_RAW.tar)

**GSE212312** — Transcriptomes of normal human mature B cells and REH B-cell acute lymphoblastic leukemia cells: effect of FBXW7 isoform knockdown or knockout followed by reconstitution

- [GSE212312_REH_controls_raw_counts.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE212nnn/GSE212312/suppl/GSE212312_REH_controls_raw_counts.csv.gz)
- [GSE212312_SYY53_54_123_141_raw_counts.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE212nnn/GSE212312/suppl/GSE212312_SYY53_54_123_141_raw_counts.csv.gz)
- [GSE212312_Tonsil_raw_counts.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE212nnn/GSE212312/suppl/GSE212312_Tonsil_raw_counts.csv.gz)

**GSE115655** — Bone marrow derived human B cells [normal proB]

- [GSE115655_BCells.TMM.cpm.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE115nnn/GSE115655/suppl/GSE115655_BCells.TMM.cpm.txt.gz)

**GSE164551** — Biallelic loss of BCMA as a resistance mechanism to CAR T cell therapy in a patient with Multiple Myeloma

- [GSE164551_AllCellsMetaData.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE164nnn/GSE164551/suppl/GSE164551_AllCellsMetaData.txt.gz)
- [GSE164551_CRB_401_MS7856.sorted.rmdup.bam.bqsr.facets.out.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE164nnn/GSE164551/suppl/GSE164551_CRB_401_MS7856.sorted.rmdup.bam.bqsr.facets.out.txt.gz)
- [GSE164551_CRB_401_MS7856_mergedAll_PASS_DP10.maf.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE164nnn/GSE164551/suppl/GSE164551_CRB_401_MS7856_mergedAll_PASS_DP10.maf.txt.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164551).

**GSE143317** — Homozygous BCMA gene deletion in response to anti-BCMA CAR T cells in a patient with Multiple Myeloma

- [GSE143317_README.txt](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE143nnn/GSE143317/suppl/GSE143317_README.txt)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143317).

**GSE226336** — Tumor Intrinsic Mechanisms of Antigen Escape to Anti-BCMA and Anti-GPRC5D Targeted Immunotherapies in Multiple Myeloma

- [GSE226336_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE226nnn/GSE226336/suppl/GSE226336_RAW.tar)

**GSE226327** — scCNVseq Datasets Supporting Tumor Intrinsic Mechanisms of Antigen Escape to Anti-BCMA and Anti-GPRC5D Targeted Immunotherapies in Multiple Myeloma

- [GSE226327_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE226nnn/GSE226327/suppl/GSE226327_RAW.tar)

**GSE226335** — scRNAseq Datasets Supporting Tumor Intrinsic Mechanisms of Antigen Escape to Anti-BCMA and Anti-GPRC5D Targeted Immunotherapies in Multiple Myeloma

- [GSE226335_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE226nnn/GSE226335/suppl/GSE226335_RAW.tar)

**GSE217245** — The Preexisting T Cell Landscape Determines Response to T Cell-Engagers Therapy

- [GSE217245_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE217nnn/GSE217245/suppl/GSE217245_RAW.tar)

**GSE234261** — Single cell multi-omic dissection of response and resistance to chimeric antigen receptor T cells against BCMA in relapsed multiple myeloma

- [GSE234261_MXMERZ002A_01_barcodes.tsv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE234nnn/GSE234261/suppl/GSE234261_MXMERZ002A_01_barcodes.tsv.gz)
- [GSE234261_MXMERZ002A_01_features.tsv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE234nnn/GSE234261/suppl/GSE234261_MXMERZ002A_01_features.tsv.gz)
- [GSE234261_MXMERZ002A_01_matrix.mtx.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE234nnn/GSE234261/suppl/GSE234261_MXMERZ002A_01_matrix.mtx.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE234261).

**GSE210079** — Changes in bone marrow tumor and immune cells correlate with durability of remissions following BCMA CAR T therapy in myeloma

- [GSE210079_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE210nnn/GSE210079/suppl/GSE210079_RAW.tar)

**GSE182894** — Mutations and RNA-binding proteins controlling CD19 splicing and CART-19 therapy resistance

- [GSE182894_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE182nnn/GSE182894/suppl/GSE182894_RAW.tar)

**GSE182891** — Mutations and RNA-binding proteins controlling CD19 splicing and CART-19 therapy resistance: Minigene library DNA-seq

- [GSE182891_CD19_minigene_variants.tab.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE182nnn/GSE182891/suppl/GSE182891_CD19_minigene_variants.tab.gz)
- [GSE182891_README.txt](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE182nnn/GSE182891/suppl/GSE182891_README.txt)

**GSE182892** — Mutations and RNA-binding proteins controlling CD19 splicing and CART-19 therapy resistance: Minigene library RNA-seq

- [GSE182892_CD19_minigene_isoforms.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE182nnn/GSE182892/suppl/GSE182892_CD19_minigene_isoforms.txt.gz)
- [GSE182892_README.txt](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE182nnn/GSE182892/suppl/GSE182892_README.txt)

**GSE182893** — Mutations and RNA-binding proteins controlling CD19 splicing and CART-19 therapy resistance: PTBP1 iCLIP2 in NALM-6 cells

- [GSE182893_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE182nnn/GSE182893/suppl/GSE182893_RAW.tar)

**GSE197215** — Single-cell antigen-specific landscape of CAR T infusion product identifies  determinants of CD19-positive relapse in patients with ALL

- [GSE197215_Integrated_object_of_CD19_3T3_condition.rds.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE197nnn/GSE197215/suppl/GSE197215_Integrated_object_of_CD19_3T3_condition.rds.gz)
- [GSE197215_Integrated_object_of_CD3_CD28_beads_condition.rds.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE197nnn/GSE197215/suppl/GSE197215_Integrated_object_of_CD3_CD28_beads_condition.rds.gz)
- [GSE197215_Integrated_object_of_mesothelin_3T3_condition.rds.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE197nnn/GSE197215/suppl/GSE197215_Integrated_object_of_mesothelin_3T3_condition.rds.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE197215).

**GSE241783** — A single cell atlas of CD19 chimeric antigen receptor T cells

- [GSE241783_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE241nnn/GSE241783/suppl/GSE241783_RAW.tar)

**GSE151511** — Single-cell transcriptomics of chimeric antigen receptor T-cell infusion products

- [GSE151511_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE151nnn/GSE151511/suppl/GSE151511_RAW.tar)

**GSE150992** — CapID sequencing of 40 chimeric antigen receptor T-cell infusion products were reported

- [GSE150992_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE150nnn/GSE150992/suppl/GSE150992_RAW.tar)

**GSE125881** — Clonal kinetics and single cell transcriptional profiling of adoptively transferred CD19-specific CD8+ CAR-T cells in adults with B cell malignancies

- [GSE125881_raw.expMatrix.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE125nnn/GSE125881/suppl/GSE125881_raw.expMatrix.csv.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE125881).

**GSE235760** — Integrative single-cell multi-omics of CD19-CARpos and CARneg T cells suggest drivers of immunotherapy response in B-ALL

- [GSE235760_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE235nnn/GSE235760/suppl/GSE235760_RAW.tar)

**GSE273170** — Baseline Immune State and T cell Clonal Kinetics are Associated with Response to CAR-T Therapy in Large B-cell Lymphoma

- [GSE273170_details_for_the_ADT_HTO_antibodies.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE273nnn/GSE273170/suppl/GSE273170_details_for_the_ADT_HTO_antibodies.txt.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE273170).

**GSE203610** — Follicular lymphoma microenvironment characteristics associated with tumor cell mutations and MHC class II expression

- [GSE203610_FL-gex-meta.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE203nnn/GSE203610/suppl/GSE203610_FL-gex-meta.csv.gz)
- [GSE203610_FL-matrix.mtx.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE203nnn/GSE203610/suppl/GSE203610_FL-matrix.mtx.gz)
- [GSE203610_FL_meta_bcr.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE203nnn/GSE203610/suppl/GSE203610_FL_meta_bcr.csv.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE203610).

**GSE91061** — Molecular portraits of tumor mutational and micro-environmental sculpting by immune checkpoint blockade therapy

- [GSE91061_BMS038109Sample.hg19KnownGene.fpkm.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE91nnn/GSE91061/suppl/GSE91061_BMS038109Sample.hg19KnownGene.fpkm.csv.gz)
- [GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE91nnn/GSE91061/suppl/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz)
- [GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE91nnn/GSE91061/suppl/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE91061).

**GSE78220** — mRNA expressions in pre-treatment melanomas undergoing anti-PD-1 checkpoint inhibition therapy

- [GSE78220_PatientFPKM.xlsx](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE78nnn/GSE78220/suppl/GSE78220_PatientFPKM.xlsx)

**GSE115978** — Single-cell RNA-seq of melanoma ecosystems reveals sources of T cells exclusion linked to immunotherapy clinical outcomes

- [GSE115978_cell.annotations.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE115nnn/GSE115978/suppl/GSE115978_cell.annotations.csv.gz)
- [GSE115978_counts.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE115nnn/GSE115978/suppl/GSE115978_counts.csv.gz)
- [GSE115978_tpm.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE115nnn/GSE115978/suppl/GSE115978_tpm.csv.gz)

**GSE120575** — Defining T cell states associated with response to checkpoint immunotherapy in melanoma

- [GSE120575_Sade_Feldman_melanoma_single_cells_TPM_GEO.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE120nnn/GSE120575/suppl/GSE120575_Sade_Feldman_melanoma_single_cells_TPM_GEO.txt.gz)
- [GSE120575_patient_ID_single_cells.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE120nnn/GSE120575/suppl/GSE120575_patient_ID_single_cells.txt.gz)

**GSE123813** — Clonal replacement of tumor-specific T cells following PD-1 blockade [single cells]

- [GSE123813_bcc_all_metadata.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE123nnn/GSE123813/suppl/GSE123813_bcc_all_metadata.txt.gz)
- [GSE123813_bcc_scRNA_counts.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE123nnn/GSE123813/suppl/GSE123813_bcc_scRNA_counts.txt.gz)
- [GSE123813_bcc_tcell_metadata.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE123nnn/GSE123813/suppl/GSE123813_bcc_tcell_metadata.txt.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123813).

**GSE135222** — DNA methylation loss coupled with mitotic cell division promotes immune evasion of tumours with high mutation load [RNA-seq]

- [GSE135222_GEO_RNA-seq_omicslab_exp.tsv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE135nnn/GSE135222/suppl/GSE135222_GEO_RNA-seq_omicslab_exp.tsv.gz)

**GSE119144** — DNA methylation loss coupled with mitotic cell division promotes immune evasion of tumours with high mutation load

- [GSE119144_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE119nnn/GSE119144/suppl/GSE119144_RAW.tar)

**GSE65185** — RNAseq changes in pre MAPKi treatment and post MAPKi resistance Melanomas

- [GSE65185_CuffnormFPKM.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE65nnn/GSE65185/suppl/GSE65185_CuffnormFPKM.txt.gz)

**GSE50509** — Spectrum, clinical correlates and clinical implications of BRAF-inhibitor resistance mechanisms in melanoma

- [GSE50509_non-normalized.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE50nnn/GSE50509/suppl/GSE50509_non-normalized.txt.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE50509).

**GSE99898** — PD-L1 expression and immune escape in melanoma resistance to MAPK inhibitors

- [GSE99898_Non-normalized_data.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE99nnn/GSE99898/suppl/GSE99898_Non-normalized_data.txt.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE99898).

**GSE134836** — Profiling non-small cell lung carcinoma cell line PC9 treated with erlotinib using 10x Genomics

- [GSE134836_RAW.tar](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE134nnn/GSE134836/suppl/GSE134836_RAW.tar)

**GSE110894** — Targeting enhancer switching overcomes non-genetic drug resistance in acute myeloid leukaemia [single cell RNA-seq]

- [GSE110894_SingleCellInfo.xlsx](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE110nnn/GSE110894/suppl/GSE110894_SingleCellInfo.xlsx)
- [GSE110894_gene_count.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE110nnn/GSE110894/suppl/GSE110894_gene_count.csv.gz)

**GSE75367** — HER2 expression identifies dynamic functional states within circulating breast cancer cells

- [GSE75367_annotation_file.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE75nnn/GSE75367/suppl/GSE75367_annotation_file.txt.gz)
- [GSE75367_readCounts.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE75nnn/GSE75367/suppl/GSE75367_readCounts.txt.gz)

**GSE196096** — I-SPY2-990 mRNA/RPPA Data Resource

- [GSE196096_RPPA_140endpts_PlusNames_GPL28470.xlsx](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE196nnn/GSE196096/suppl/GSE196096_RPPA_140endpts_PlusNames_GPL28470.xlsx)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196096).

**GSE194040** — I-SPY2-990 mRNA/RPPA Data Resource: mRNA component

- [GSE194040_ISPY2ResID_AgilentGeneExp_990_FrshFrzn_meanCol_geneLevel_n988.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE194nnn/GSE194040/suppl/GSE194040_ISPY2ResID_AgilentGeneExp_990_FrshFrzn_meanCol_geneLevel_n988.txt.gz)
- [GSE194040_ProbeAnnotation_ISPY2Edit_GPL30493_wasGPL16233.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE194nnn/GSE194040/suppl/GSE194040_ProbeAnnotation_ISPY2Edit_GPL30493_wasGPL16233.txt.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE194040).

**GSE196093** — I-SPY2-990 mRNA/RPPA Data Resource: RPPA component

- [GSE196093_ISPY2_990_RawToNorm_Params_RPPA1b.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE196nnn/GSE196093/suppl/GSE196093_ISPY2_990_RawToNorm_Params_RPPA1b.csv.gz)
- [GSE196093_ISPY2_990_RawToNorm_Params_RPPA2.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE196nnn/GSE196093/suppl/GSE196093_ISPY2_990_RawToNorm_Params_RPPA2.csv.gz)
- [GSE196093_ISPY2_990_RawToNorm_Params_RPPA3b.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE196nnn/GSE196093/suppl/GSE196093_ISPY2_990_RawToNorm_Params_RPPA3b.csv.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196093).

**GSE25066** — Genomic predictor of response and survival following neoadjuvant taxane-anthracycline chemotherapy in breast cancer

- [GSE25066_Genelist_weights.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE25nnn/GSE25066/suppl/GSE25066_Genelist_weights.txt.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE25066).

**GSE70138** — L1000 Connectivity Map perturbational profiles from Broad Institute LINCS Center for Transcriptomics LINCS PHASE *II* (n=354,123; updated March 30, 2017)

- [GSE70138_Broad_LINCS_Level2_GEX_n113012x978_2015-12-31.gct.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE70nnn/GSE70138/suppl/GSE70138_Broad_LINCS_Level2_GEX_n113012x978_2015-12-31.gct.gz)
- [GSE70138_Broad_LINCS_Level2_GEX_n345976x978_2017-03-06.gctx.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE70nnn/GSE70138/suppl/GSE70138_Broad_LINCS_Level2_GEX_n345976x978_2017-03-06.gctx.gz)
- [GSE70138_Broad_LINCS_Level2_GEX_n78980x978_2015-06-30.gct.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE70nnn/GSE70138/suppl/GSE70138_Broad_LINCS_Level2_GEX_n78980x978_2015-06-30.gct.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE70138).

**GSE92742** — L1000 Connectivity Map perturbational profiles from Broad Institute LINCS Center for Transcriptomics LINCS Pilot PHASE I (n=1,319,138; updated March 03, 2017)

- [GSE92742_Broad_LINCS_Level2_GEX_delta_n49216x978.gctx.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE92nnn/GSE92742/suppl/GSE92742_Broad_LINCS_Level2_GEX_delta_n49216x978.gctx.gz)
- [GSE92742_Broad_LINCS_Level2_GEX_epsilon_n1269922x978.gctx.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE92nnn/GSE92742/suppl/GSE92742_Broad_LINCS_Level2_GEX_epsilon_n1269922x978.gctx.gz)
- [GSE92742_Broad_LINCS_Level3_INF_mlr12k_n1319138x12328.gctx.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE92nnn/GSE92742/suppl/GSE92742_Broad_LINCS_Level3_INF_mlr12k_n1319138x12328.gctx.gz)
- Additional files in the [series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE92742).

## Download checks and ingestion observations

Four files downloaded and decompressed successfully. These checks establish byte availability and basic table structure, not scientific validity of every row.

| File | Compressed bytes | Observed contents | Ingestion consequence |
|---|---:|---|---|
| GSE243919 FFPE raw read counts | 1,748,081 | 47,935 data rows; eight patient/timepoint columns plus annotation and an undetermined-read column | Select the eight biological samples explicitly; exclude Reads_Undetermined_S0; inspect blank-cell meaning before filling values |
| GSE164551 cell metadata | 620,576 | 37,658 data rows; cell barcode index and sample/QC/cluster fields | Parse the implicit row-name column correctly; resolve S1–S8 to clinical timepoints |
| GSE164551 FACETS-related file | 15,867 | 1,788 data rows; chromosome/position and allelic read counts | Despite filename, this is not a ready-made table of segmented absolute copy numbers; inspect the full CN evidence path |
| GSE164551 mutation file | 108,945 | MAF format; 585 data rows; GRCh38, alleles, depth and transcript/protein fields | Preserve build and transcript; file labels identify tumor/normal samples, not eight complete longitudinal variant callsets |

SHA256 checksums:

- GSE243919 counts: `0274fb542ed214e690fd62f877e15d9b0687d3d74f0c02e27b128adc8836282b`
- GSE164551 metadata: `94fe5a7d77d0790998ab9023fbce948f953119b1270f51ed672c1b02c2c811da`
- GSE164551 FACETS-related file: `eff7ba407eb6f64ab822483fba0f3008c0a0b3cdae8ca8545e6f52515c2bd19c`
- GSE164551 mutation file: `0cd18f59458d24a89e6308b033b2333ee4ead15e6b296a99c104e8afd89f7e3b`

## Minimum acquisition manifest

For each selected asset preserve: source accession and parent study, exact URL and filename, retrieval date, file checksum, release/version, access status, reuse terms, disease, treatment, donor, specimen, anatomical site, timepoint definition, assay/library, genome/transcript reference, processed-data units, outcome availability, and known overlap with other sources. Use separate identifiers for patient, sample and assay. Record missing modalities as missing; do not manufacture matched records across different patients or studies.

The first build should ingest one clinical anchor and one experimental-label source, with four fresh blinded fixtures. Add a second clinical cohort only after pairing and provenance work end to end. The breadth in this catalog is a selection menu for a coherent investigation, not a requirement to ingest everything during the hackathon.
