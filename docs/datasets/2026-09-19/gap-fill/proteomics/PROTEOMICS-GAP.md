# Actionable public treatment-timed tumour proteomics cohort

## Selected accession: PRIDE PXD012000

* **Primary publication:** Shenoy *et al.*, “Proteomic patterns associated with
  response to breast cancer neoadjuvant treatment,” *Molecular Systems Biology*
  (2020), PMID 32960509, PMCID PMC7507992.
* **Official repository record:** [ProteomeXchange PXD012000](https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD012000), hosted by PRIDE.
* **Why this fills the gap:** the primary paper and repository description state
  that 113 FFPE breast-tumour samples include matched tumours before and after
  neoadjuvant chemotherapy, plus tumour-adjacent normal tissue from partial
  responders. The study reports protein abundance for 7,180 proteins and links
  treatment response, pathological response, relapse/recurrence-free survival,
  and overall survival. It is a patient tumour cohort, not a cell-line treatment
  experiment.
* **Timing/exposure:** pre- and post-neoadjuvant chemotherapy; the exact drug,
  patient identifier, and timepoint linkage must be read from the deposited
  clinical-proteomics file and/or publication supplementary Dataset EV1 before
  an analysis-ready pairing table is claimed.

## Acquired publisher-derived processed tables

Two official Springer Nature supplementary workbooks are retained alongside
this note and listed in `MANIFEST.tsv`:

* `Shenoy2020_Dataset_EV1_clinical.xlsx` (23,666 bytes): 35 patient rows with
  patient code and affiliated sample triplets (for example `1A,1B,1C`),
  diagnosis/pre-treatment and surgery/post-treatment sections, Miller & Payne
  score, relapse date, death/last-follow-up, RFS and OS days.
* `Shenoy2020_Dataset_EV2_protein_abundance.xlsx` (14.5 MB): 7,602 rows × 355
  columns, with identified-protein H/L log2 normalized ratios and columns
  explicitly grouped as pre-treatment, post-treatment tumour, tumour-adjacent
  normal, and healthy breast-reduction samples.

Both open successfully as XLSX. The therapy exposure is AC-T (doxorubicin plus
cyclophosphamide followed by paclitaxel; HER2-overexpressing patients also
received Herceptin), as stated in the primary paper. This is now an
analysis-ready clinical/protein pairing source. No raw PRIDE MS files were
downloaded.

## Source evidence

* [Official PRIDE/OmicsDI record](https://www.omicsdi.org/dataset/pride/PXD012000)
  describes 113 samples, before/after chemotherapy matched tumours, and 7,180
  quantified proteins.
* [Open-access publication record](https://pmc.ncbi.nlm.nih.gov/articles/PMC7507992/)
  states that raw files and clinical proteomics data are available via PRIDE
  project PXD012000.
