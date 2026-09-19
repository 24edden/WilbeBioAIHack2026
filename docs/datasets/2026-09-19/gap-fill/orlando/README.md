# Orlando CAR19 CD19-relapse supplementary package

Source article: Orlando *et al.*, “Genetic mechanisms of target antigen loss
in CAR19 therapy of acute lymphoblastic leukemia,” *Nature Medicine* (2018),
DOI [10.1038/s41591-018-0146-z](https://doi.org/10.1038/s41591-018-0146-z).

The official publisher workbook is Supplementary Data Table 1. It contains one
sheet, `Count Data`, with 30,901 gene rows and 24 labelled samples. The columns
include screening, month-4/month-7, and relapse samples for several patients;
the header is the only sample-label source retained in the workbook. The two
publisher PDFs provide supplementary tables/figures and the reporting summary.

`MANIFEST.tsv` records direct publisher URLs, timestamps, byte counts, and
SHA-256 values. The XLSX was ZIP-integrity tested and the PDFs were checked for
their final-file PDF signature before the local mirror was hash-verified.

The related SRA project **SRP141691** contains targeted BAM files for immune
genes. Published reanalyses state that these files underwent GATK Split’N’Trim,
which prevents junction-preserving, genome-wide de novo splicing analysis. They
were deliberately not downloaded: the supplement is the usable compact public
expression package; the BAMs remain a precise limitation for a future
junction-level investigation.

Publisher supplementary-material terms apply. Do not infer a splice event from
these gene-level counts alone.
