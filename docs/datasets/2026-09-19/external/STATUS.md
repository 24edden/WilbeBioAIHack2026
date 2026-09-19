# External source delivery status

Updated 19 September 2026. The current 50-resource disposition is in `../CATALOG-DISPOSITION.md`; current file availability is in `../integration/data_catalog.tsv`.

- SU2C-MARK v3: full `su2c_mark/Source_Data_3.zip` is on Brev, 1,180,232,016 bytes, ZIP-validated with a SHA-256 receipt. A leftover local partial is not the remote delivery state.
- Maynard processed data and ALK clinical/supplement tables: `../gap-fill/longitudinal/`.
- DepMap 24Q4 and PRISM 19Q4: `../gap-fill/functional/`.
- SKEMPI 2 and additional exact experimental complexes: `../gap-fill/binding/`. The earlier login-required statement about SKEMPI was incorrect; the public official CSV was acquired.
- Orlando CD19 relapse publisher counts and supplements: `../gap-fill/orlando/`.
- IMvigor210 and CIViC: see their own gap-fill manifests for acquisition state and exact release dates.
- scPerturb Frangieh–Izar protein subset, 6VJA, 7JIC and Reactome references remain present.
- POG570 was located, but its explicit usage/redistribution terms prevent treating it as an unrestricted team transfer. See `../gap-fill/pog570/ACCESS-NOTE.md`.

Source packages are selected subsets, not complete portal mirrors. Attribution and per-source terms remain attached to each package. The historical completed-object manifest below records the initial compact files; it is supplemented by the SU2C ZIP receipt and gap-fill manifests.

## Completed-object manifest

| File | Retrieved UTC | Bytes | Source URL | SHA-256 | Reuse/access terms |
|---|---:|---:|---|---|---|
| `su2c_mark/SU2C-MARK_Repository_Readme.txt` | 2026-09-19T13:31:44Z | 2,266 | `https://zenodo.org/api/records/11179623/files/SU2C-MARK%20Repository%20Readme.txt/content` | `4086aad63bb05ccfb6f44e528a428637ef84cfa06e5594809be91b2bb3b4b260` | Zenodo public record; retain record terms. |
| `scperturb/FrangiehIzar2021_protein.h5ad` | 2026-09-19T13:36:29Z | 24,714,445 | `https://zenodo.org/api/records/13350497/files/FrangiehIzar2021_protein.h5ad/content` | `1f85827b5afad11a30d8ac99399772231110a1c3723bed6ecf7981a12cc3dbcc` | Zenodo public record; underlying-study attribution required. |
| `structures/6VJA.cif` | 2026-09-19T13:37:38Z | 1,010,640 | `https://files.rcsb.org/download/6VJA.cif` | `3856afb5f77cfd54cf6adb67d5bd5bf2ce26373a812f8ea26efcd0c1d856d29b` | RCSB PDB public structure data; cite PDB entry. |
| `structures/7JIC.cif` | 2026-09-19T13:37:42Z | 738,913 | `https://files.rcsb.org/download/7JIC.cif` | `181ef15cb74cbaadad277499beb30492c0f723e0ea93587b358fc62fe92f0208` | RCSB PDB public structure data; cite PDB entry. |
| `references/ReactomePathways.gmt.zip` | 2026-09-19T13:38:15Z | 298,479 | `https://reactome.org/download/current/ReactomePathways.gmt.zip` | `8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4` | Reactome download terms and attribution apply. |
| `references/ReactomePathwaysRelation.txt` | 2026-09-19T13:38:16Z | 634,259 | `https://reactome.org/download/current/ReactomePathwaysRelation.txt` | `fd49a624d80c14eb37ae57a02e141d574d5ede3f60022bb99edbd909448a3f1e` | Reactome download terms and attribution apply. |
