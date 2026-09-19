# Access the detailed qualification package on Brev

This public directory contains only aggregate findings, limitations and implementation recommendations. It intentionally contains no individual clinical/sample maps, cell/barcode records, expression tables, model outputs, sequence files, model weights, original scientific payloads, source inventories or saved-run artifacts.

Authorized team members can connect to the existing instance with `brev shell agentic-takeoff-cpu` and read:

```text
/home/ubuntu/rosalind-shared-files/cd19-reproduction-data/2026-09-20/START-HERE.md
```

The `source-package/` subdirectory contains the full unchanged audit, complete source inventories, 20-group input matrix, sample maps, detailed reporter/PTBP1/stimulation reports and validation receipts. The sibling `NEXT-STEPS.md` and `readiness/` notes describe recommended conversion and workflow implementation. From `source-package/`, verify the snapshot using `sha256sum -c PACKAGE-MANIFEST.sha256`.

Large new raw data and model files remain in their original staged Brev locations, referenced by the inventories. Original datasets and accepted evidence are unchanged. A partial download or public URL is never evidence of an acquired usable source. No raw clinical data, original dataset or live application is changed by this documentation publication.

The full data-bearing GitHub publication was rejected by automatic approval review because this repository is public. This narrower edition publishes conclusions and implementation guidance only. No detailed payload was pushed in the rejected attempt.
