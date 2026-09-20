# Scientific evidence and R&D handoff

This demo investigates a hypothesis that a user writes or explicitly selects. Selection preserves the original text and source; the agent's alternatives remain separate. The bundled data are real public sources and prepared project metadata. The `demo_decision` records are **curated demonstration assessments**, not transcripts of prior GPT-Rosalind inference. A live run must record its actual model/provider actions separately. No synthetic measurement, molecular candidate, structure, affinity or improvement score has been added to these cases.

## CD19 CAR-T: the primary walkthrough

The source is the exact 1,968-byte file `/home/ubuntu/ana-workspace/hypothesis/CD19_CAR_T_.txt` read from `agentic-takeoff-cpu` on 19 September 2026. Its SHA-256 is `03918c91a6905f28249ae9d4b5069548e5b18d10e5543a11c6293a8bea395a88`. The entire file, including H1–H5, is preserved in `casepacks/sources/cd19/CD19_CAR_T_.txt` and in the case's `hypothesis` field. Its opening question asks whether failure is more consistent with loss of functional CD19 recognition or inadequate antigen-specific CAR-T activity, persistence or expansion.

The pack connects that question to two kinds of source:

- The public [GSE182891 DNA minigene table](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182891) and [GSE182892 RNA minigene table](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182892), already acquired in this project, are copied byte-for-byte. The build script re-extracts 100,135 DNA variant rows; 19,043 RNA barcode–replicate rows; 9,722 RNA barcodes; and replicate labels 1 and 2. Exact DNA `RNA_BARCODE` to RNA `barcode` matching covers 9,527 RNA barcodes. The other 195 remain unassigned. This is an input qualification result; unmatched entries do not automatically indicate corrupt data.
- Pinned metadata from [GSE197215](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE197215) describes antigen-specific CAR-T stimulation alongside TCR, non-target and unstimulated controls. The demo does not analyze its large expression object. It is a distinct study, not a patient-matched extension of the minigene experiment.

The exact first RNA barcode, `AAAAAAAGCACGTGG`, demonstrates traceable retrieval across two replicate rows. It was chosen by table order, not by an interesting outcome. Its six listed mutations prevent attribution to a single mutation without a qualified model and controls. Junction coordinate strings are preserved as source columns; the demo does not silently assign them new biological meanings.

**Valid conclusion:** the pack can qualify library evidence and define discriminating tests, but it cannot choose a mechanism for a specific patient. There is no patient-specific relapse specimen, tumor surface protein result, reference CAR sequence or qualified candidate in this pack.

**Design routing:** if functional surface recognition is absent, return an antigen-selection or multi-target research question and the necessary measurements. A stronger binder to an absent epitope does not establish rescue. If target recognition is retained, a reference/candidate comparison may become appropriate after exact target and binder constructs are supplied. If retention is unknown, establish it first. The demonstration handoff records these requirements instead of presenting fictitious candidates.

## ALK L1196M: measured assay adjudication

The [ALK functional atlas](https://doi.org/10.1186/s13059-026-03977-4) workbook is bundled unchanged. The extractor finds `ALK_E23_C70A` by identity and asserts `L1196M`; row 1331 is a locator, not the sole join key.

| Source field | Exact source value | Cell |
| --- | --- | --- |
| Alectinib classification | Resistance | Table S2 D1331 |
| Alectinib resistance score | 7.7445209372741202 | Table S2 E1331 |
| Lorlatinib classification | Resistance | Table S2 F1331 |
| Lorlatinib resistance score | 11.4128982028548 | Table S2 G1331 |
| Zotizalkib classification | Sensitive | Table S2 H1331 |
| Zotizalkib resistance score | 0.23868446278806199 | Table S2 I1331 |
| Fitness score | -0.106903137030655 | Table S2 J1331 |

Values are stored as source strings so extraction does not silently round their precision. These are assay labels/scores, not IC50s or clinical resistance probabilities. Their cross-drug magnitudes need not be directly comparable. The source case flags an unresolved Table S5 concentration-header versus supplementary-legend discrepancy. The demo preserves that limitation and does not claim to have reanalyzed independent validation curves.

**Valid conclusion:** the narrow drug-specific source-assay hypothesis is supported. A causal interaction mechanism, transferable clinical benefit and a candidate therapy improvement remain unestablished. The R&D next step is a matched WT, mutant and revertant validation with qualified exposure, expression and independent biological replicates.

## BCMA GSE164551: timing and target-loss discipline

Three compact prepared input files were copied from `/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19/input/`: `case.json`, `sample_manifest.tsv` and `post_second_infusion_variants.tsv`. Each local SHA-256 matches the remote source. The package represents **one patient**, with eight longitudinal RNA samples; eight samples are not eight independent patients. The baseline was CD138-depleted.

The corrected prepared manifest maps sample_05/GSM5013825 to matrix S6 and metadata S5, and sample_06/GSM5013826 to matrix S5 and metadata S6. The compact demo preserves the manifest's reported barcode validation; it does not rerun the 10x H5 barcode reconciliation. The mutation table's line 438 reports `TNFRSF17 p.Q38*`, `Nonsense_Mutation`, `PASS`, with tumor alternate count 10 and depth 41. These values are extracted, not inferred. The DNA is post-second-infusion evidence and cannot establish pretreatment absence or acquisition time.

The full H5, cell metadata, gene-count and allele-count files remain on Brev. The compact demo does not claim a new copy-number call, tumor-cell expression analysis, surface-protein measurement or biallelic-loss proof. Although [GSE164551](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164551) and its publication discuss the mechanism, this walkthrough is open-book development, not a blinded mechanism benchmark.

**Design routing:** p.Q38* is a truncation, not a missense-pair input. The correct initial BioNeMo outcome is a reasoned block. A separate target-retained construct packet is required for a binder comparison; it must not be relabeled as an observed patient rescue.

## Meaningful BioNeMo use

Boltz-2 models a qualified molecular complex. A protein binder comparison requires exact chain sequences, molecular format and linker/boundary definitions, target construct, provenance, an identified reference/candidate and matched inference settings. Predictions do not directly measure protein–protein affinity, specificity, cytotoxicity or clinical benefit. The small-molecule affinity option is not a protein-binder affinity estimator. Record omitted glycosylation, membrane context and other material limitations. See NVIDIA's [Boltz-2 inference contract](https://docs.nvidia.com/nim/bionemo/boltz2/1.6.0/inference.html).

Evo 2 can inform a qualified nucleotide question; it does not independently establish patient causality or surface antigen availability. A forced NIM request on an irrelevant or unqualified case is not a successful integration. A visible blocked action with concrete missing inputs is an honest outcome.

The three bundled packs have no expert-provided target/reference/candidate sequence set. Each R&D handoff includes one **planned experimental arm**, typed `experimental_arm`, so a scientist can return an endpoint against an exact published experiment/arm ID. For CD19 this is a target-retention assay; for BCMA it is a target-retention assay with infusion-relative timing; for ALK it is a matched phenotype validation. These entries are measurement plans, not molecular candidates, completed constructs or completed experiments. Their exact sequences are explicitly missing, modeling stays blocked, and `artifacts` remains empty. The server assigns publication IDs; the source pack supplies only a stable semantic `design_key`.

Submitting a surface-recognition measurement against an assay arm does not qualify a molecular design or imply that BioNeMo ran. In demo mode, returned numbers are demonstration/user-reported inputs and the deterministic revision remains unresolved pending scientific review. When a separate eligible molecular request is run by the service, retain its original request, response, provider identity, returned artifacts and settings. Do not insert its result into a different case without explicit lineage.

## Reproducibility and extension

Run from the service directory:

```sh
python casepacks/build_cases.py --check
python -m unittest discover -s tests -p test_cases.py -v
```

The builder makes no network or inference calls. It reads the pinned source bytes and regenerates all numeric extractions, source locators and curated decision packets. `casepacks/MANIFEST.json` hashes both sources and generated case files. Runtime intake checks source bytes and derived packet hashes. Altered inputs block dependent analysis until a deliberate new packet/version is built.

Every evidence object has a type, source hash and exact locator. A source extract retains its original file path/hash alongside the hash of the bundled excerpt. `measured` indicates source measurements or deterministic table summaries; `literature` indicates source-study metadata or prepared contextual descriptions; `inference` identifies a derived interpretation. The original user hypothesis is not itself evidence.

New case builders should return the same schema, retain the independent experimental unit, keep missing measurements missing, and avoid silently changing the research objective. For genuine blinded evaluation, create a separate sanitized investigator packet and evaluator-only reference; these open-book packs are not that isolation boundary.

## R&D return contract

Each handoff names an experiment ID, objective, reference status, modeling block or result, and exact return requirements. Return data should include case/decision/hypothesis lineage, candidate/construct and sample IDs, raw artifact hashes, units, independent replicate identities, controls, timing and QC. Prespecify the endpoint and decision rule. Failed, negative and inconclusive results remain results; missing values do not become zero. New measurements create a new assessment version and keep predictions separate from observations. Actual clinical or wet-lab measurements must never be relabeled from demonstration fixtures.
