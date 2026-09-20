Agent-facing CD19/BCMA resistance evidence bundle

Use each module separately. They are complementary evidence sources, not one pooled patient cohort.

cd19_tumour_pairs/
  Nine matched baseline/relapse tumour RNA-read pairs. Files are targeted, aligned SRA Lite archives. They cover a limited immune-gene panel and can support CD19 RNA/splicing and selected lineage-marker analyses. They cannot establish a whole-transcriptome tumour state or surface-protein loss.

car_t_function/
  Four compressed Seurat R objects: CD19-target stimulation, non-target stimulation, TCR stimulation, and unstimulated controls. Use donor-aware comparisons. Do not treat individual cells as independent patients. This module evaluates CAR-T function; it does not measure a matched relapse tumour.

bcma_genomic/
  Cell metadata, a tumour/normal mutation table, and tumour/normal allele counts for one longitudinal BCMA CAR-T case. The allele-count file is not a ready-made segmented copy-number result. This module cannot independently establish BCMA surface protein or CAR-T function.

Required behaviour
  Cite filenames, case IDs, rows, cell clusters, or computed outputs for every claim. Keep unsupported branches unresolved. Do not use web search, publication lookup, accession lookup, or external outcome knowledge.
