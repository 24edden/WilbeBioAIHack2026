# 24 possible London AI × Bio projects

Prepared for Scott Ogden, 17 September 2026. Ideas for a team of 2–5 forming on Friday. These are proposed projects, except AssayGuard, which already has a local CPU prototype. None is a Genmab project or endorsement. Inspiration comes from public research and platform descriptions.

## The five I would take into team formation

| Choice | Best reason to pick it | Weekend scope | Recruit first |
|---|---|---|---|
| **Target Reality Check** | Strongest Genmab-inspired story with an understandable scientific decision | Five oncology targets, one disease, evidence and normal-tissue expression audit | Translational scientist or single-cell bioinformatician |
| **CellScope QC** | Clearest visual demonstration and natural GPU workload | One image collection, three quality defects, review queue | Computer-vision builder |
| **Cell Census Detective** | Strong combination of useful biology, agents and GPU computation | One tissue, two studies, reproducible cell-type comparison | Single-cell analyst |
| **AssayGuard** | Lowest delivery risk because a baseline already runs | Extend existing split/leakage audit with a live bounded agent and measured GPU integration | Cheminformatics or GPU engineer |
| **Trial Criteria Compiler** | Easy to explain to pharma/clinical-operations people | Twenty public trials, structured criteria, synthetic cohort accounting | Clinical scientist plus NLP builder |

My preference: pitch **Target Reality Check** if you meet an oncology/data scientist; **CellScope QC** if you meet a vision engineer; keep **AssayGuard** as the executable fallback. Trial Criteria Compiler has a weaker natural GPU fit at this small scale, so choose it for the domain problem, not to win a speed contest.

Ratings below are judgments about a weekend prototype, not forecasts of clinical or commercial success. “GPU fit” means a substantive candidate computation; no speedup is assumed until measured. “High effort” projects need a teammate who already knows the data and tools.

## A. Genmab-inspired: antibodies, oncology and translation

Genmab's public work includes bispecific antibodies, ADCs and antibody platforms such as DuoBody and HexaBody. The ideas here focus on evidence quality and research workflows around those areas, using public inputs. [Genmab antibody science](https://www.us.genmab.com/research/antibody-science), [2025 annual report](https://ir.genmab.com/static-files/7b4cfa98-94f5-49f5-b08a-8631759dd23e).

### 1. Target Reality Check — recommended

**Question:** What evidence makes an apparently attractive oncology target less convincing?

**Weekend demo:** Select five targets for one cancer; produce linked cards separating disease association, normal-tissue expression, cell-type specificity and missing evidence. A researcher can change an assumption and see which conclusion changes.

**Data and tools:** Open Targets + Human Protein Atlas; optionally a tightly scoped CELLxGENE slice. OpenAI plans queries and writes source-linked conclusions; NVIDIA RAPIDS/CuPy computes donor-level expression summaries and sensitivity analyses on the cell slice.

**Evaluation:** Twenty manually checked factual claims, exact provenance, no unsupported “safe target” conclusion, stable results on rerun. Compare agent output against a fixed template baseline.

**Constraint:** RNA is not surface protein or a toxicity measurement. Without the cell-level analysis, GPU fit is weak. Effort: medium. Team: 3.

### 2. Two-Target Evidence Map

**Question:** Do two proposed targets occur in the same cells, different interacting cell populations, or merely the same tissue?

**Weekend demo:** Inspect three preselected published target pairs in one annotated dataset. Clearly separate same-cell coexpression from cross-cell biology; never infer an AND gate simply from a bispecific format.

**Data and tools:** CELLxGENE and HPA; OpenAI selects documented checks and explains limitations; NVIDIA GPU aggregates cells and bootstraps donors.

**Evaluation:** Verify calculations by hand on a tiny subset; assess threshold sensitivity and donor variation. Show “not measurable here” for missing targets.

**Constraint:** Does not predict binding, efficacy or selectivity. Effort: medium/high. GPU fit: strong at realistic cell counts. Recruit: single-cell scientist.

### 3. ADC Evidence Gaps

**Question:** Which parts of a public ADC target rationale are measured, inferred or absent?

**Weekend demo:** Compare three published target rationales using an explicit checklist: expression, heterogeneity, normal tissues, internalization evidence and clinical evidence. Link every cell to a source or label it unknown.

**Data and tools:** HPA, Open Targets, selected open-access papers and trial records. OpenAI extracts and reconciles evidence; GPU analysis can quantify expression heterogeneity in a selected public cell dataset.

**Evaluation:** Blinded review of thirty extracted fields; especially reward correctly reported missing evidence.

**Constraint:** No payload/linker design and no inference that expression proves ADC efficacy. Effort: medium. GPU fit: conditional on quantitative analysis.

### 4. Antibody Evidence Passport

**Question:** Can a scientist inspect the provenance and structural coverage of a public therapeutic antibody in one place?

**Weekend demo:** Twenty public antibody records with chain identities, sequence-source dates, exact versus approximate structure matches and missing-data flags.

**Data and tools:** Thera-SAbDab and linked PDB records. OpenAI orchestrates retrieval and discrepancy checks; an available BioNeMo protein model on an NVIDIA GPU supplies exploratory embeddings for neighborhood inspection.

**Evaluation:** Correct chain matching, preserved source dates, reproducible nearest-neighbor results. Compare embeddings with simple sequence similarity.

**Constraint:** Embedding similarity is not binding or developability validation. Model access is a first-hour gate. Effort: medium. Recruit: protein ML researcher.

### 5. Biomarker Definition Translator

**Question:** Are two oncology studies using the same biomarker name to mean different things?

**Weekend demo:** Extract assay type, specimen, scoring system, cutoff and sampling time from fifteen public studies; flag comparisons that cannot be justified.

**Data and tools:** ClinicalTrials.gov plus accessible linked publications. OpenAI converts text to a constrained schema, retains quotations and handles unknowns. A GPU document encoder/reranker could support larger evidence retrieval, but is optional and unproven.

**Evaluation:** Field accuracy on a hand-labeled set and precision of incompatibility flags.

**Constraint:** Abstracts and registry entries often omit assay details; missing information must stay missing. Effort: low/medium. GPU fit: weak for fifteen studies. Recruit: biomarker scientist.

### 6. Resistance Evidence Map

**Question:** Which claimed resistance mechanisms have direct evidence, and in what model system?

**Weekend demo:** One oncology treatment class, twenty open-access papers, an evidence graph distinguishing cell-line, animal and human observations.

**Data and tools:** Curated papers and optional DepMap downloads. OpenAI extracts causal language and counterevidence; NVIDIA GPU runs a bounded dependency/expression analysis if a compatible public matrix is available.

**Evaluation:** Relation precision and source entailment on twenty withheld claims; show contradictory results without forcing agreement.

**Constraint:** Correlation in a cell-line panel does not establish clinical resistance. DepMap download access has not been tested. Effort: high. Recruit: oncology domain expert.

### 7. Tumor Neighborhood Explorer

**Question:** Does an apparent cell-cell association survive comparison with randomized spatial neighborhoods?

**Weekend demo:** One annotated tissue section, two cell populations, real versus shuffled neighborhood plots with uncertainty.

**Data and tools:** One public spatial dataset selected from CELLxGENE's spatial documentation. OpenAI coordinates QC and interpretation; GPU spatial-neighbor and permutation calculations use suitable rapids-singlecell functionality.

**Evaluation:** Recover a planted spatial pattern, reject a null example, rerun with different radii.

**Constraint:** Spatial proximity does not prove molecular interaction; this data path is still a setup risk. Effort: high. GPU fit: strong. Recruit: spatial-omics scientist.

### 8. Trial Criteria Compiler

**Question:** Which eligibility rules make a study cohort narrow, and can those rules be made auditable?

**Weekend demo:** Twenty oncology trial records become structured constraints, with a visual explanation of exclusions against a clearly synthetic cohort.

**Data and tools:** ClinicalTrials.gov. OpenAI extracts rules and points to source text; NVIDIA RAPIDS applies structured filters to a sufficiently large synthetic table and reports CPU/GPU timings.

**Evaluation:** Human-reviewed extraction accuracy, correct handling of exceptions/unknowns, exact cohort-count agreement with a CPU reference.

**Constraint:** Synthetic exclusion counts are not estimates of real recruitment; no patient matching or clinical decisions. Effort: medium. GPU fit: moderate only at scale.

## B. Other areas of biology

### 9. Cell Census Detective — recommended

**Question:** Is a cell-type difference reproducible across donors and studies?

**Weekend demo:** One tissue, two studies, one predefined biological comparison; the agent retrieves a slice, checks metadata, computes summaries and produces an evidence report.

**Data and tools:** A version-pinned CELLxGENE slice; OpenAI controls a bounded analysis workflow; rapids-singlecell on NVIDIA handles QC, PCA and neighbors.

**Evaluation:** CPU/GPU numerical checks, donor-held-out stability, citation and metadata completeness.

**Constraint:** Do not count cells as independent biological replicates. Study effects and duplicate cells need explicit handling. Effort: medium. GPU fit: strong. Recruit: single-cell analyst.

### 10. CellScope QC — recommended

**Question:** Which microscopy images deserve review before a scientist trusts the downstream measurements?

**Weekend demo:** A few hundred fields of view, a contact sheet with suspicious images, and an explanation of focus, saturation or segmentation anomalies.

**Data and tools:** A small BBBC021 subset; OpenAI chooses checks and summarizes measured defects; NVIDIA GPU batches image metrics or segmentation inference.

**Evaluation:** Separate real manually labeled defects from deliberately injected distortions. Report per-defect precision/recall and CPU/GPU timing.

**Constraint:** BBBC021 is not a ready-made defect-label dataset. Budget time to label the small test set. Effort: medium. GPU fit: strong for batched inference. Recruit: vision engineer.

### 11. Morphology Mechanism Finder

**Question:** Do compounds with similar cellular effects cluster together when entire compounds are held out?

**Weekend demo:** Retrieve nearest phenotype examples and report mechanism-class performance for a small set of classes.

**Data and tools:** BBBC021 images or supplied profiles. OpenAI runs comparisons and explains counterexamples; an NVIDIA GPU computes image embeddings or profile-neighbor search.

**Evaluation:** Hold out complete compounds; compare with simple morphology features and include uncertainty.

**Constraint:** Readout similarity is not proof of a shared mechanism. Full image archives are large; choose a subset immediately. Effort: medium/high. Recruit: computational biologist or vision engineer.

### 12. RNA-seq Design Reviewer

**Question:** Did an analysis respect paired samples and the actual experimental unit?

**Weekend demo:** Detect three deliberately flawed sample sheets, then reproduce a documented analysis with the correct design.

**Data and tools:** Bioconductor airway counts and metadata. OpenAI audits the design and invokes a fixed statistical workflow; a GPU stress test could accelerate repeated simulations at larger scale.

**Evaluation:** Catch planted errors without inventing errors in the original dataset; compare reference results and provenance.

**Constraint:** The small airway dataset itself does not need a GPU. Strong science-quality project, weaker sponsor-compute fit. Effort: low/medium. Recruit: RNA-seq analyst.

### 13. Brain Cell Annotation Challenge

**Question:** When should a cell-type annotator abstain instead of assigning a confident label?

**Weekend demo:** A small brain-cell reference and a held-out donor/study; show uncertainty and conflicting marker evidence.

**Data and tools:** CELLxGENE subset. OpenAI coordinates marker review; NVIDIA GPU builds reference embeddings/neighbors.

**Evaluation:** Accuracy and coverage as abstention increases; donor-level splits and a simple nearest-centroid baseline.

**Constraint:** Reference labels are not infallible ground truth. Select an annotation level the team can review. Effort: medium. GPU fit: strong. Recruit: neuro/single-cell scientist.

### 14. Autoimmune Target Evidence Board

**Question:** Does a target's disease association align with its expression in the relevant immune cells?

**Weekend demo:** One autoimmune disease, five targets and one immune-cell reference; an evidence board separates association, expression and uncertainty.

**Data and tools:** Open Targets, HPA and optional CELLxGENE. OpenAI prepares traceable comparison cards; NVIDIA GPU computes cell-population summaries if the detailed slice is used.

**Evaluation:** Source-linked claims, correct gene identifiers, sensitivity to cell-type definitions.

**Constraint:** Healthy expression is not a disease mechanism. This reuses the Target Reality Check engine with a different biological question. Effort: medium. Recruit: immunologist.

### 15. PlantVision Reality Check

**Question:** Does a plant-image classifier rely on leaf appearance or irrelevant background cues?

**Weekend demo:** One crop, three categories, grouped train/test splits, then evaluate controlled lighting/background changes and abstention.

**Data and tools:** PlantVillage. OpenAI creates an audit plan and interprets measured failures; an NVIDIA GPU runs the image model and robustness tests.

**Evaluation:** Respect leaf grouping; report calibration and changes under controlled perturbations.

**Constraint:** Synthetic perturbations do not validate performance in real farms. Novelty lies in the agentic audit, not another leaf classifier. Effort: medium. GPU fit: strong. Recruit: vision/plant scientist.

### 16. Rare-Disease Evidence Navigator

**Question:** Can a researcher see which target-disease associations rely on direct versus indirect evidence?

**Weekend demo:** Three public disease examples, ranked evidence types and missing links, with a reproducible search trail.

**Data and tools:** Open Targets plus selected open-access studies. OpenAI plans retrieval and reconciles identifiers; NVIDIA GPU graph/search operations are an extension only if the data volume warrants them.

**Evaluation:** Correct entity resolution, supported citations and abstention when evidence is insufficient.

**Constraint:** No patient variants, diagnosis or treatment recommendation. Effort: low/medium. GPU fit: weak for this initial scope. Recruit: genetics researcher.

## C. Reusable scientific tools and infrastructure

### 17. AssayGuard — existing prototype

**Question:** Does a molecular model's evaluation expose it to genuinely different chemistry?

**Weekend demo:** Extend the current public BACE audit with an agent that inspects data, runs fixed evaluations and explains random versus scaffold splits. The current CPU baseline is already saved locally.

**Data and tools:** Existing BACE preparation; OpenAI bounded tool calls; candidate NVIDIA nvMolKit similarity computation. GPU integration remains untested.

**Evaluation:** Exact split provenance, no train/test duplicates, CPU/GPU parity and wall-clock timing. Current results show a modest mean difference, not a dramatic collapse.

**Constraint:** Pre-event code eligibility needs organizer confirmation. Effort: lowest. Recruit: cheminformatics/GPU builder. Working report (`assayguard/results/report.html`, outside this Markdown collection).

### 18. Paper-to-Reproduction Agent

**Question:** Can an agent recreate one published figure and explain every discrepancy?

**Weekend demo:** One open dataset, one figure, fixed methods, a fresh-environment rerun and a structured discrepancy report.

**Data and tools:** Choose a documented airway or BBBC analysis. OpenAI maps methods to controlled analysis steps; GPU computation is substantive only for an image-scale reproduction.

**Evaluation:** Predefine numerical agreement tolerances and preserve failures; compare against a human-prepared reference.

**Constraint:** Choose a figure with downloadable data and complete methods in the first hour. Effort: medium. GPU fit: varies. Recruit: reproducibility-minded scientist.

### 19. Biological Dataset Contract Checker

**Question:** Can an agent catch mismatched gene IDs, sample IDs, units and missing metadata before analysis?

**Weekend demo:** Ten small intentionally damaged public-data extracts, an explainable validation report and proposed repairs for review.

**Data and tools:** HPA and airway extracts. OpenAI explains schema conflicts; deterministic validators enforce contracts. NVIDIA GPU dataframe operations are a scale extension, not a necessity for the small cases.

**Evaluation:** Detection precision/recall against known defects; no silent identifier merging or destructive repair.

**Constraint:** A metadata correction can change scientific meaning; present ambiguous repairs for review. Effort: low. GPU fit: weak. Recruit: data engineer.

### 20. Scientific Claim Courtroom

**Question:** Can an agent accurately distinguish “supported,” “contradicted,” and “not established”?

**Weekend demo:** Thirty prewritten claims about one benign biology topic; separate evidence collection, critique and final judgment, all with exact citations.

**Data and tools:** Curated open-access corpus. OpenAI coordinates structured roles and source checks; a GPU encoder/reranker retrieves candidate passages if available.

**Evaluation:** Blind scoring on held-out claims; compare with a single-prompt baseline and measure unsupported citations.

**Constraint:** Multiple model roles do not create independent evidence. Effort: medium. GPU fit: moderate at larger corpus sizes. Recruit: researcher/editor and NLP builder.

### 21. Agent Cost-to-Evidence Benchmark

**Question:** Which agent workflow answers a scientific question reliably with the fewest wasted tool calls?

**Weekend demo:** Ten fixed analysis tasks, three orchestration variants, a trace explorer showing accuracy, cost, latency and failed steps.

**Data and tools:** Small public slices from the selected projects. OpenAI tool-calling workflows; NVIDIA BioNeMo Agent Toolkit skills where applicable and a measured GPU scientific task.

**Evaluation:** Same input, tool permissions and budgets across variants; seeded tasks and clearly defined successful outcomes.

**Constraint:** This is an evaluation product, not a new biological discovery. Effort: medium. GPU fit: depends on the chosen scientific tasks. Recruit: agent/evaluation engineer.

### 22. GPU Worth-It Advisor

**Question:** At what workload size does a GPU help a real scientific workflow?

**Weekend demo:** One operation, increasing input sizes, parity tests and separate cold-start, transfer and steady-state timings; the agent chooses a backend from measured evidence.

**Data and tools:** BACE similarity or cell-neighbor analysis. OpenAI interprets measurements; NVIDIA nvMolKit or RAPIDS supplies the GPU backend.

**Evaluation:** Repeated timings, synchronization, peak memory and total end-to-end runtime.

**Constraint:** Small workloads may favor CPU; that is a valid result. Effort: low/medium if hardware works. GPU fit: central. Recruit: performance engineer.

### 23. Scientific Handoff Capsule

**Question:** Can the next scientist reproduce a result without knowing the author?

**Weekend demo:** Package one analysis into a capsule containing source hashes, environment, seeds, inputs, outputs and a short evidence summary; replay it on a second machine.

**Data and tools:** Existing AssayGuard results or one image analysis. OpenAI creates the narrative from verified artifacts; NVIDIA executes the replayed GPU stage on Brev.

**Evaluation:** Fresh-environment reproduction, numerical tolerances and a measured setup-to-result time.

**Constraint:** Avoid a generic folder generator; demonstrate a realistic broken handoff that the capsule fixes. Effort: low/medium. Recruit: research software engineer.

### 24. Scientific Model Disagreement Explorer

**Question:** Where do two scientific models disagree, and what evidence could distinguish their claims?

**Weekend demo:** Two accessible models on one fixed public benchmark, a disagreement gallery and a reproducible recommendation for further validation.

**Data and tools:** BBBC image tasks or a public benign protein benchmark selected with a domain teammate. OpenAI interprets the comparison; NVIDIA runs fixed model inference.

**Evaluation:** Calibration, agreement and performance on held-out examples; compare with simple baselines.

**Constraint:** Do not infer truth from model consensus. Model weights, licenses and runtime must be verified before committing. Effort: high. GPU fit: strong. Recruit: relevant ML specialist.

## Source and access map

These primary pages were checked on 17 September. Except for the existing BACE prototype, dataset downloads, schemas, licenses and runtime integrations remain to be tested for the chosen project. A public source page is not a guarantee that every desired field is available.

| Source | Useful for | Practical first step |
|---|---|---|
| [Open Targets access](https://platform-docs.opentargets.org/data-access) | Target/disease evidence | Start with one entity through GraphQL or an exported table; pin the release |
| [Human Protein Atlas downloads](https://www.proteinatlas.org/about/download) | Tissue and cell-type expression evidence | Inspect a small gene set; retain assay type and original units |
| [Thera-SAbDab](https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/therasabdab/search/) | Public therapeutic antibody sequences and structure links | Download a dated subset; retain approximate-match labels |
| [CELLxGENE Census](https://chanzuckerberg.github.io/cellxgene-census/) | Public single-cell slices | Choose one tissue and pinned release; inspect donor/study metadata and primary-data flags |
| [BBBC021](https://bbbc.broadinstitute.org/BBBC021) | Compound-induced cellular morphology | Start from profiles or a small image subset; don't download every plate |
| [airway](https://bioconductor.org/packages/release/data/experiment/html/airway.html) | Small documented RNA-seq example | Inspect the sample design and reference vignette |
| [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api) | Public study records | Fetch a narrow query; manually inspect five records before extracting more |
| [PlantVillage](https://github.com/spMohanty/PlantVillage-Dataset) | Plant image classification audit | Use the documented grouped split and one crop |
| [DepMap downloads](https://depmap.org/portal/data_page/) | Optional cancer dependency analysis | Portal showed a verification gate; download path and selected release still need checking |
| [rapids-singlecell](https://rapids-singlecell.readthedocs.io/en/latest/) | GPU single-cell and selected spatial analyses | Match the environment to event hardware and compare a small CPU reference |
| [BioNeMo Agent Toolkit](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit) | Scientific tool skills | Choose one relevant skill; verify dependencies before integration |

## Choosing with a new team

Use the first 45 minutes to inspect an actual data sample, agree on one question and define one falsifiable evaluation. A strong project should have an obvious before/after demonstration, one meaningful OpenAI decision/tool loop, and one meaningful NVIDIA computation. A slide listing both vendors is not enough.

For any option, freeze the MVP Friday: one input → inspectable plan → controlled tools → numerical result → cited explanation → reproducible export. Saturday morning should produce a real result. Add polish only after the result is reproducible.

Suggested roles for three people: biological question/evaluation; data/GPU computation; agent/UI and integration. Do not wait for five people. If you recruit only one teammate, choose AssayGuard, CellScope QC or a tightly bounded evidence project.

## Three recruitment pitches

### Target Reality Check — about 40 seconds

I'm Scott, and I'm forming a team around a question: when an oncology target looks exciting, what evidence should make us pause? I want to build an agent that connects public disease evidence, normal-tissue expression and cell-type data, then shows which claims are supported and which are still assumptions. The weekend goal is five targets, one cancer and a reproducible evidence dashboard. OpenAI would coordinate the analysis, and NVIDIA would power the cell-data computations. I'm looking for a translational or single-cell scientist and someone who enjoys building useful interfaces. I'm also happy to adapt the idea with the team.

### CellScope QC — about 35 seconds

I'm Scott, and I'd like to build an agent that catches problems in microscopy images before they distort the science. We'll use public images, measure defects such as blur and saturation, and create a visual review queue that explains why each image was flagged. The demo will show real examples, measured accuracy and GPU performance, with an OpenAI agent coordinating the checks. I'm looking for someone with computer-vision experience and someone who knows how scientists actually use these images.

### Flexible team introduction — about 25 seconds

I'm Scott, joining solo and looking for teammates. I'm interested in practical AI tools for biology: antibody target evidence, microscopy quality control, or reproducible analysis. I've prepared several public-data project options and a working molecular benchmark we can use as a starting point. I'd love to team up with a biology specialist and a builder, and I'm open to joining an existing idea where I can help us get to a strong demo.

## Rosalind starter prompt for whichever project wins

We are a small team at the London AI × Bio hackathon. Our proposed project is [NAME]. Our scientific question is [QUESTION]. We have [PUBLIC DATASET AND VERSION]. First inspect the available inputs and list missing information. Propose one reproducible weekend analysis and an evaluation against a simple baseline. Distinguish observed measurements, assumptions and hypotheses. Identify one useful NVIDIA computation and the actual tools available in this environment. Do not assume a tool, model entitlement or dataset field exists. Return a bounded plan, expected artifacts and a stop condition; wait for our review before substantial compute.
