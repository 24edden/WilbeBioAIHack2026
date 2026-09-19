# IMvigor210 Core Biologies — official processed release

This directory contains the unmodified version 1.0.0 source package from the
Genentech/Roche IMvigor210 Core Biologies release.  It is a processed,
patient-level package for the atezolizumab IMvigor210 metastatic urothelial
carcinoma trial, not a trial-registry extract.

## Provenance and terms

* Direct primary release: `http://research-pub.gene.com/IMvigor210CoreBiologies/packageVersions/IMvigor210CoreBiologies_1.0.0.tar.gz`
* Study: Mariathasan *et al.*, *Nature* 2018, “TGFβ attenuates tumour response
  to PD-L1 blockade by contributing to exclusion of T cells” (PMCID: PMC6028240).
* The publication says its source code and processed data are freely available
  under the Creative Commons 3.0 license.  Retain the upstream package LICENSE
  when extracting or redistributing any contents.

## What the package provides

The package's `cds` object is a processed RNA-seq count matrix plus feature and
sample (`pData`) annotations. Its installed documentation explicitly lists:
anonymous patient ID (`ANONPT_ID`); independent-review RECIST 1.1 confirmed
response (PD/SD/PR/CR); derived binary response; overall survival in months
(`os`) and censoring (`censOS`, 0 alive / 1 dead); immune-cell and tumour-cell
PD-L1 levels; IC used for enrollment; molecular subtypes; immune phenotype;
sex, race, BCG, ECOG, smoking, metastatic status; mutation burden; sample age
and tissue; and platinum-exposure/sample-pre-platinum fields. It documents the
data as transcriptomes and sample annotations for the majority of IMvigor210
participants (NCT02108652/NCT02951767). This creates useful sample-to-clinical
linkage, but it is not a serial pre/post-treatment cohort; do not infer
longitudinal pairs from `ANONPT_ID`.

## Validation

`MANIFEST.tsv` records the exact retrieval URL, retrieval date, size, SHA-256,
and successful gzip/tar listing validation. The archive includes
`data/cds.RData`, `data/fmone.RData`, feature/signature objects, supplementary
tables, source code, and its upstream LICENSE. It was retained intact so its R
objects can be loaded with the package's documented R/Bioconductor dependencies.
