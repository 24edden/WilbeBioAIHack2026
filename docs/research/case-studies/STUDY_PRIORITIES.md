# Rosalind study priorities and two-case plan

Prepared 19 September 2026. Design recommendation; no agent debate, expression analysis or biological validation has been run.

## Recommendation

Prioritize **treatment-defined studies with traceable samples, measured functional outcomes, orthogonal assays and genuine competing explanations**. More rows or modalities are useful only when their identities, timing and experimental meaning can be reconciled. For the current ALK-focused roadmap, start with the ALK functional atlas, then a small patient-level therapy-state investigation. Retain CD20 as the smallest alternative clinical demo and BCMA as the strongest antigen-escape expansion.

Use two separate datasets:

1. **Easy: ALK L1196M, 2026 functional atlas.** A bounded, published variant-by-drug result with direct table evidence. Test whether agents extract the right result and respect its assay scope.
2. **Hard/open: TH266 in Maynard PRJNA591860.** Paired ALK-fusion liver biopsies before treatment and during residual disease on alectinib. Test whether agents distinguish tumor-cell adaptation from composition, sampling, genetic selection and exposure explanations, then propose a falsifiable experiment.

The second case has an unresolved causal question, not a claim that its public dataset is unknown to models. It concerns early persistence, not proven acquired resistance. If both cases must strictly concern established resistance, substitute P1153R mechanism adjudication from the atlas; that keeps both cases in one source study and loses the independent-dataset comparison.

## Ranked study families

| Priority | Study/package | Details that make debate useful | First bounded task | Main limitation |
|---|---|---|---|---|
| 1 | ALK functional atlas, DOI 10.1186/s13059-026-03977-4 | Variant IDs, drug-specific scores/classifications, fitness, guide designs, individual validation and construct sequences | L1196M evidence adjudication; then P1153R disagreement | Cell-model outcomes are not patient resistance or mechanistic proof |
| 2 | Maynard PRJNA591860, especially TH266 | Patient/sample IDs, biopsy site/type, therapy state, treatment history, single-cell expression and annotations | TN-to-RD tumor-state versus composition analysis | One selected patient, two biopsies; no causal label or complete exposure history |
| 3 | GSE164551; subsequently GSE226336 family | Longitudinal BCMA case; derived genomic evidence; deletion versus epitope escape in the larger family | One provenance-complete antigen-escape case | GSE164551 is one patient; allelic counts are not finished absolute copy numbers; larger-family assays need explicit joins |
| 4 | GSE243919, with appropriate orthogonal splice evidence | Four paired patients, eight biological RNA columns, documented CD20 protein-loss context | Does total RNA explain the phenotype, and what is missing? | Gene counts cannot establish splicing; reported protein loss is not a quantitative matched proteomics matrix |
| 5 | GSE182891/GSE182892 | Experimental CD19 variant/isoform labels | Evaluate variant-to-splice predictions | Minigene effects are not clinical relapse labels; split related constructs together |
| 6 | I-SPY2 GSE194040/GSE196093 | Landscape reports 987 expression patients and a 736-patient protein/phosphoprotein subset, treatment arms and response | One arm contrast in the verified overlapping baseline subset | Richest broad RNA/protein/response option here, but baseline response differs from acquired resistance; overlap must be measured |
| 7 | GSE197215 and GSE217245 | Target/non-target/unstimulated controls and immune-state alternatives | Separate antigen response from generic activation or dysfunction | Donor, therapy and timepoint dependencies; late sampling is not automatically relapse |
| Later | Shiba-Ishii 2022 tissue supplement and ALK MSK 2026 portal | Clinical mutation context; some pre/post molecular states | Candidate corroboration and paired-state audit | Incomplete dated exposure/response; repeat portal samples are not established baseline/progression pairs |

The ranks are project-fit judgments, not measured performance or exhaustive rankings of data volume. Source counts above come from the supplied landscape and acquisition documents, unless specifically identified below as directly checked.

## What counts as a detailed, usable study

Require stable study/patient/sample/assay IDs; disease and target; exact drug; baseline/on-treatment/progression definitions; specimen site; assay units and preprocessing; QC and missingness; biological versus technical replicates; controls; release and checksum; and exact evidence locations. Prefer matched DNA/RNA/protein or function, dose-response measurements, negative controls and a validation route. Record missing exposure, sequencing or protein fields explicitly.

For each case, give agents a compact manifest and relevant tables. Broad archives can remain source material accessible by targeted retrieval. Do not join different studies' patients to manufacture a multimodal individual.

## Corrections found by inspecting source workbooks

**ALK atlas:** `13059_2026_3977_MOESM2_ESM.xlsx`, Table S2 row 1331 identifies L1196M as `ALK_E23_C70A` and supplies its three drug outcomes. This is the easy case's source key. Table S2 row 920 labels P1153R as Resistance / Intermediate / Resistance for alectinib / lorlatinib / zotizalkib. The project narrative's broad-resistance description must retain that screen-versus-validation distinction. Also, G1202R has two nucleotide IDs with different zotizalkib labels; amino-acid-only joins would erase evidence.

Table S5 headers use `uM` for several concentrations, while the local supplementary figure S10 legend describes corresponding alectinib/lorlatinib concentrations in nM. Preserve both sources and mark concentration reconciliation pending; do not silently correct the workbook or make exposure claims from those headings.

**Maynard:** clinical worksheet rows 49–50 identify TH266 samples LT_S75 (TN) and LT_S81 (RD). The baseline acquisition-day field is `NA`, not measured day zero, despite the acquisition README's shorthand “0/14 days.” RD is day 14. Both are metastatic liver core biopsies, ALK fusion, second-line alectinib context after chemotherapy. TN therefore must not be interpreted as no prior anticancer therapy. A demographic field differs between the two rows; preserve the discrepancy without using it for this mechanistic analysis.

## Multi-agent debate and evaluation

Use the project's role-specific workflow: independent initial briefs, one explicit challenge round, then an integrator decision. Bioinformatics owns identity/QC; clinical science owns time and phenotype; pharmacology owns exposure limitations; structural biology owns mechanistic predictions; pathology owns tumor-cell identity and sampling; wet lab owns a discriminating experiment; statistics owns the inference boundary. Unused roles may state why their evidence is unavailable. A majority vote is not independent biological support.

Compare a single-agent baseline with the structured team using identical source packets, tool access and total resource limits. Suggested pilot: three runs per case per system, frozen prompts/memory, maximum 30 minutes and a common token/tool budget declared before running. Report all trials, errors, tokens and time; do not select the best retry. Two cases test workflow behavior, not general improvement. Repeats are not additional biological samples.

Score five dimensions 0–3: source fidelity, relevant alternatives, uncertainty, experiment discrimination, and decision usefulness. Primary pilot endpoint: source-fidelity score, with unsupported consequential claims reported separately. Critical errors include fabricated patient facts, treating cells as patients, asserting causal discovery from an expression association, or claiming a structural prediction validates resistance. Have blinded scientific reviewers calibrate examples before scoring. Do not score the hard case against an invented true mechanism.

The files in this folder are **design documents**, and this priority document reveals source findings. They are not an isolated blind benchmark. For blind phenotype prediction, create separate agent input and evaluator stores, remove target answers from every accessible source including supplementary figures and retrieval, and enforce isolation through tools/filesystem permissions. Public-paper memorization remains possible. Newly generated confounder/null fixtures can test reasoning, but their artificial labels validate only the simulated task. Keep a real hard case with no ground truth in a separately scored challenge slice.

## Local project sources and precedence

Read `/home/ubuntu/rosalind-shared-files/START-HERE.md`, `CURRENT_IMPLEMENTATION.md`, `Context/TRANSLATIONAL_SCIENCE_HYPOTHESES.md`, and `Context/AGENTIC_SCIENTIFIC_LEARNING_LOOP.md` as the current design/boundary. The original architecture DOCX and `Rosalind_Dataset_Landscape-1.md` explain the CD20-first history. `reference-architecture/2026-09-19/DATA-AND-TOOLS.md` defines package/tool boundaries. `datasets/2026-09-19/GAPS.md` and the longitudinal README describe remaining acquisition/clinical gaps; old source-machine missing-file claims do not override newer delivery records. None establishes that the full debate or feedback-learning system is implemented.

Primary publications checked: [ALK atlas](https://link.springer.com/article/10.1186/s13059-026-03977-4) and [Maynard therapy-state study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/). Local original workbook cells were inspected directly. Expression RDS contents and biological outcomes have not been analyzed in this task.
