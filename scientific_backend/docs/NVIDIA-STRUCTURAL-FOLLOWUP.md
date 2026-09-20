# Public CD19 isoform structural follow-up

`cd19-exon2-structure` executes two actual NVIDIA BioNeMo Boltz-2 monomer predictions: canonical CD19 extracellular residues 20–291 (272 residues), and the corresponding exon-2-deleted construct (183 residues). This is an exploratory structural follow-up, distinct from the existing qualified CAR-binder comparison.

## Input qualification

The pinned author minigene FASTA and exon annotation come from commit `edd69ccba3a193ca13ee66a5a4b191d980a940a1` of [the study repository](https://github.com/mcortes-lopez/CD19_splicing_mutagenesis). The independent protein reference is [UniProt P15391](https://www.uniprot.org/uniprotkb/P15391/entry), sequence version 6, entry version 241, downloaded 19 September 2026. All three raw files have immutable SHA-256 pins in `app/structural_followups.py`.

Before any provider call, the code reconstructs the author transcript from exon intervals 69–218, 476–742 and 1041–1244 (one-based inclusive), locates the coding start, and translates the complete codons. Its 186 amino acids must exactly match the canonical protein prefix. Skipping exon 2 must reproduce the same prefix with residues 30–118 removed, without a frameshift or altered junction residue. The extracellular boundary must match the pinned UniProt annotation. Any mismatch stops before inference.

## Execution and outputs

Each member has an intent, exact request, request hash, provider response identity, outcome receipt and validated mmCIF. There are no automatic retries or redirects. Pending jobs and interrupted waits retain their unknown/pending state; an existing comparison intent cannot be submitted again. Both members must have the exact requested sequence, complete C-alpha coverage and finite coordinates before a paired prediction becomes evidence.

The app displays backbone views derived from the returned coordinates, with rotatable views and links to the original mmCIF. Preview endpoints recheck artifact hashes and registered download scope. They do not generate illustrative protein pictures.

The comparison reports provider confidence and least-squares aligned C-alpha RMSD over the 183 shared residues. That number describes displacement between two predictions, not agreement with an experimental structure. One sample per member does not estimate prediction uncertainty.

## Interpretation

These isolated, unglycosylated ectodomain predictions can motivate structural or binding experiments. They do **not** predict splicing, membrane trafficking, glycosylation, CAR recognition, cytotoxicity or a patient's response. CD81, glycans, membrane and CAR binder are absent. The prediction is distinct from the paper's measured splicing and functional evidence; neither confidence nor RMSD is an efficacy score.

The unchanged original hypothesis and accepted scientific evidence remain available to the specialists and reviewer when a follow-up creates a new decision version. Model-generated recommendations must name an approved recipe and explain the decision it could change.

## Software verification

`tests/test_structural_followups.py` checks source-to-protein mapping, paired artifact validation, pending/unknown recovery, duplicate prevention, scope and altered output rejection. Its provider responses are synthetic test fixtures. `tests/test_structure_preview.py` checks visualization coordinates, hash validation and nonfinite rejection. Record real endpoint execution separately in `VALIDATION.md`.

## Actual execution on 19 September 2026

The website action on run `ff3c4fd47f1d408ab5bcdc89d1a07744`, linked to decision v1, submitted two real hosted requests and received HTTP 200 for both. Operation `3b695c934df542beab4c8f41017d6f9a` accepted prediction evidence `NVIDIA-CD19-d0f1533df0693f10` before starting specialist review. No synthetic fixture or prior engineering sample was used.

| Member | Residues | Request ID | Reported confidence | mmCIF SHA-256 |
|---|---:|---|---:|---|
| Canonical extracellular CD19 | 272 | `f9a68631-ad2e-4e67-bf4a-533e95718bd7` | 0.4996807277 | `ec0667e5dbe57c4666938e7fa78b09820f84f16b4632bcc8b3a668156f050b0a` |
| Exon-2-deleted extracellular CD19 | 183 | `2b5015d6-c6ff-4807-9fea-271b62d05e9f` | 0.4571934342 | `61be3a4739d6d6a436f67bee4b023f3763cb1eafe1bcb4d80b30b83ef2652641` |

The aligned displacement was 12.47084 Å over the 183 shared C-alpha positions. Both exact requested sequences, full C-alpha coverage and finite coordinates passed. Both download hashes and both preview coordinate counts were checked through the deployed API, and the actual structures were rendered in the browser. These confidence values and displacement are prediction outputs; they do not validate structural accuracy or demonstrate epitope loss. The follow-up retains the original hypothesis hash `03918c91a6905f28249ae9d4b5069548e5b18d10e5543a11c6293a8bea395a88`.
