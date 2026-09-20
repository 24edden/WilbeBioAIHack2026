# Source-qualified CD19 discovery

`cd19-variant-splicing-discovery` is a fast, deterministic runtime analysis of the actual pinned GEO DNA and RNA tables. It is available in CD19 CAR-T and the broader CAR-T discovery workspace. It produces `ANALYSIS-CD19-DISCOVERY`, version `cd19-discovery-1.0`. Computation takes about two seconds locally; no vendor inference is invoked. Numerical findings come from the source tables, not a prepared answer or a language-model prediction.

The primary publication is Cortés-López, Schulz, Enculescu et al., **High-throughput mutagenesis identifies mutations and RNA-binding proteins controlling CD19 splicing and CART-19 therapy resistance**, Nature Communications 13, 5570 (2022), [DOI 10.1038/s41467-022-31818-y](https://doi.org/10.1038/s41467-022-31818-y). The pinned full article is [PMC9500061 via Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9500061/fullTextXML). Author resources come from [the authors' repository at commit edd69ccba3a193ca13ee66a5a4b191d980a940a1](https://github.com/mcortes-lopez/CD19_splicing_mutagenesis/tree/edd69ccba3a193ca13ee66a5a4b191d980a940a1). `casepacks/sources/cd19-discovery/SOURCES.json` records download locations and hashes.

## The barcode issue is resolved

The DNA table lists variant calls; it is not a list of every control construct. All 195 RNA barcodes absent from that variant table carry the explicit `mutations=-` annotation. There are 195 such control rows in replicate 1 and 194 in replicate 2, matching the paper's Methods. A missing dictionary key with a nonempty mutation annotation would remain unresolved. This implementation never labels it wild type.

Exact DNA reverse-complement barcode identities and RNA mutation sets are checked. All 100,135 DNA rows pass barcode orientation validation. The released barcodes include 14-, 15- and 16-nt sequences; those exact identities are retained. Mutation calls with penetrance below 0.8 are excluded before comparing the DNA and RNA mutation sets. There are 0 discordant or unresolved RNA rows in the pinned release, and 9,321 barcodes shared across replicates, including 9,127 mutated constructs.

A second apparent mismatch also has a documented explanation. The author FASTA has G at minigene position 748, while the assay baseline was deliberately engineered to G748T, as described in the paper's cloning Methods. Reference alleles are checked against this explicitly recorded, in-memory assay reference; all original files remain unchanged. All DNA REF alleles then match. “Wild type” and “single mutant” below are relative to that engineered assay baseline. They must not be presented as native genomic wild type or an isolated patient genotype.

Earlier accepted QC evidence remains immutable. Newly computed `cd19-barcode-qc` and `cd19-isoform-summary` use recipe version 1.1.0 and explicitly distinguish control annotations and unlisted residual counts from missing source data. Fresh generated case packets also contain the corrected interpretation.

## Freshly computed results

The primary recipe uses the paper's five major isoform identities, preserves source readcount denominators, and reports a residual category containing every non-major or unlisted count. It does not silently renormalize selected columns. Seven processed rows have 99 reported reads despite the paper's upstream 100-read criterion; they remain visible in direct summaries and are excluded by the optional regression filter.

The 56 observed single-mutant constructs present in both replicates are compared with each replicate's own control distribution. Eight have at least one major-isoform fraction outside the respective 2.5th–97.5th empirical control percentiles in the same direction in both replicates. This is an exploratory control-range criterion, not an FDR-adjusted significance test or an effect confidence interval. The evidence returns the 12 largest replicated inclusion differences, exact barcode/source-line identities, readcounts and a hash of all 56 computed records.

| Reporter variant, relative to engineered baseline | Observed isoform | Replicate 1 | Replicate 2 | Baseline means, replicate 1/2 |
|---|---|---:|---:|---:|
| A746G | Exon 2 skipping | 339/375 = 90.40% | 942/1022 = 92.17% | 7.16% / 14.27% |
| C1052A | Alternative exon 3 | 77.14% | 72.71% | 2.53% / 2.39% |
| T465C | Exon 2 skipping | 42.15% | 74.33% | 7.16% / 14.27% |

A746G uses the same exact barcode `GGTCACATTCGGTT` in both experimental replicates (RNA TSV lines 5895 and 15400, header counted). It is one reporter construct measured twice, not two independent patient observations or a replicated set of mutant barcodes. Its location is intron 2 nucleotide 4, adjacent to the exon 2 donor region; increased exon 2 skipping supports a mechanistic follow-up but does not prove loss of accessible CD19 in a tumor.

For the 96 cryptic isoforms, the recipe reproduces the paper's prevalence-score formula:

`P(mutation | isoform fraction > 0.05) × P(isoform fraction > 0.05 | mutation)`

It computes this separately in the shared barcode cohort and retains pairs with score > 0.25 and at least three mutation-containing barcodes in each replicate. Thirty pairs meet this explicitly stricter replicated criterion. C864G with junction pattern `(219 475)(864 1040)` has score 1.0 in each replicate, with five joint/high/mutation barcodes. G1005A with `(219 1006)` has score 0.9412 in each, based on 16 joint-positive among 17 mutation-containing barcodes. A827T with `(219 475)(826 1040)` has scores 0.9512 and 0.9024. These are associations in combinatorial constructs; other mutations in the same barcodes can confound attribution. They are not patient frequencies or newly reproduced wet-lab validations.

## Paper findings are separate evidence

The publication reports 193 splicing-affecting mutations from 4,255 inferred single-mutation effects and tenfold model validation. These are explicitly labeled paper-reported facts, not claims about the primary runtime computation.

Its PTBP1 experiments are also labeled literature-only: the authors report intron 2 binding and increased intron retention following depletion, with reduced surface CD19 in separate cell-line experiments. The mutation/count tables do not reproduce those perturbation, binding or flow-cytometry experiments. The corresponding hypothesis is distinct from a cis-acting sequence mutation and needs appropriate transcript and surface-protein measurements.

## Optional statistical follow-up

`cd19-softmax-followup` produces `ANALYSIS-CD19-SOFTMAX` with the same pinned inputs. Its catalog marks it `followup_only:true`; initial agents cannot execute it implicitly. An explicit approved follow-up action can run it. It may take several to tens of minutes on CPU.

The implementation follows the published six-output multinomial/L1 approach and C = 10. It uses a sparse binary mutation design, fractional labels expanded into six weighted categories, equal total weight per barcode, fixed seed 182892, SAGA, tolerance 0.001 and at most 1500 iterations per replicate. It fits the two replicates separately and includes indel indicators to avoid silently treating them as absent. Readcount must be at least 100; non-major residual must be at most 5%; only the common barcode cohort is considered. Candidate rankings require support in at least three eligible barcodes in both replicates and direction-consistent control-range exceedance. Failed convergence produces an incomplete status and no candidate claims.

The exact author's optimization script, weighting and random split were not present in the retrieved code. Our conservative residual, declared weighting and solver choices do not establish exact reproduction of the 193 reported calls. Training correlations are labeled training fit, never held-out validation. The full public-data fit has **not been completed as part of this release validation**; only the small synthetic software fixture verifies this optional optimizer path. No optional fit is silently substituted for the fast primary analysis.

## Qualified molecular follow-up

The author GTF identifies exons 69–218, 476–742 and 1041–1244 in the 1274-nt minigene. Splicing and translating from the first CDS start gives 186 complete amino acids identical to the canonical P15391 prefix. Exon 2 skipping yields 97 complete amino acids, uniquely matching deletion of canonical residues 30–118 inclusive. That is a 267-nt, 89-aa in-frame deletion. The intronic G748T baseline does not change this coding-sequence mapping.

This validates a sequence-based comparison of canonical extracellular residues 20–291 (272 aa) against the corresponding exon 2-deleted construct (183 aa), with explicit canonical extension beyond the partial minigene. See `docs/NVIDIA-STRUCTURAL-FOLLOWUP.md` for the separate qualified structural route. A monomer prediction does not measure folding stability, glycosylation, trafficking, cell-surface abundance, CAR binding, affinity or killing. The appropriate next experiment measures isoform usage together with surface-accessible CD19 and functional recognition.

## Integrity and validation

Every run rereads bounded input files and verifies both manifest and recipe-pinned hashes before computing. The catalog exposes exact `input_sources` requirements. Older run snapshots missing author references must start a new investigation; a follow-up cannot silently import newer science into an old source version. Source values, parameters and recipe version are included in a canonical derived-evidence hash. Primary evidence is approximately 35 KB, within the 80 KB acceptance boundary.

Focused tests cover actual control and mutation counts; barcode orientation and assay-reference errors; refusal to call missing mutation annotations WT; exact single-mutant fractions and locators; cryptic prevalence arithmetic; source tampering; canonical exon deletion; deterministic content hashes; bounded evidence size; no regression in the primary recipe; optional synthetic fit and nonconvergence behavior. No patient causality, new clinical outcome or full paper 193-hit reproduction is claimed.
