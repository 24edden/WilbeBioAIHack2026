# Reference architecture package

Prepared 19 September 2026. Proposed architecture, with a point-in-time audit of selected downloaded files.

- [Reference architecture](REFERENCE-ARCHITECTURE.md): original overview expanded with four loops, 15 step contracts, role exchanges, generated records, simulation trace and build sequence.
- [Data and tool register](DATA-AND-TOOLS.md): 19 data packages and 17 tool routes, availability, exact source locations, readiness checks and potential acquisitions.
- Overview Mermaid source (`./architecture.mmd`, outside this Markdown collection).
- Role handoff Mermaid source (`./role-handoffs.mmd`, outside this Markdown collection).
- Selected local asset audit (`./local-asset-audit.csv`, outside this Markdown collection): 129 actual local files with byte counts, observed hashes and manifest comparison status.
- Audit summary (`./local-asset-audit.json`, outside this Markdown collection) and documentation checks (`./documentation-checks.json`, outside this Markdown collection).

Start with the architecture, then resolve its Dxx/Txx references in the register. All original downloads and synced project reference files were left unchanged. No model inference, new dataset acquisition, clinical analysis, graph write or remote-host modification was performed.

## Brev CPU location

This package is deployed to `/home/ubuntu/rosalind-shared-files/reference-architecture/2026-09-19`. The shared data root is `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/`.

Internal document links have been made portable for this copy. The data audit remains the original source-machine snapshot; its absolute Mac paths and integrity results are provenance, not a fresh CPU inventory. Remote-recorded data availability remains qualified in the register.

The selected biotech graph contracts are included at references/graph-reference-extract.json (`./references/graph-reference-extract.json`, outside this Markdown collection). The complete company graph and its database are not included. The local prototype implementation references describe the source workspace; this documentation transfer does not install that runtime.

`PACKAGE-MANIFEST.json` and `SHA256SUMS` identify the transferred contents.
