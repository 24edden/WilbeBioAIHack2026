# BioNeMo engineering service check

This separate check makes one real NVIDIA-hosted Boltz2 monomer request using
the exact protein sample from [NVIDIA's version 1.7.0 Getting Started guide,
step 5](https://docs.nvidia.com/nim/bionemo/boltz2/1.7.0/getting-started.html).
The [official hosted API reference](https://docs.api.nvidia.com/nim/reference/mit-boltz2-infer)
specifies the endpoint and protein-polymer schema. Both sources were checked on
2026-09-19. The example has one 110-residue protein chain, three recycles,
50 sampling steps, one diffusion sample, step scale 1.638, and mmCIF output.

**This is an engineering integration check. It does not test CD19/CAR-T
resistance, validate target retention, compare binders, or establish affinity
or therapeutic benefit.** The script does not update production capability
records or attach this result to a scientific investigation.

Run only when a real external inference is authorized:

```sh
.venv/bin/python scripts/verify_bionemo_service.py --check-id UNIQUE_NEW_CHECK_ID
```

The existing `app.config` loader reads the application's private `.env`.
`NGC_API_KEY` or `NVIDIA_API_KEY` is used in memory, never printed or included
in request artifacts. The command writes a unique directory under
`runtime/engineering/` and refuses an existing directory. Changing the ID is
a new inference, not a retry or reconciliation operation.

Before dispatch, it durably saves the exact request and an immutable intent.
`receipt.json` records dispatch, HTTP status, vendor request ID, response and
artifact hashes, and final validation. Exactly one POST is attempted with no
automatic retry, redirect, polling, or fallback. HTTP 202 remains `pending`;
transport interruption remains `unknown`. Neither authorizes resubmission.

A completed check requires one finite confidence score within [0,1], exactly
one mmCIF model with chain A, the exact full submitted amino-acid sequence,
complete residue numbering/alpha-carbon coverage, and finite atomic
coordinates. The original prediction artifact and redacted response remain
available even when validation fails. Confidence is a model output; these
checks verify artifact identity and basic integrity, not structural accuracy.

The CLI emits compact receipt location/status/ID JSON and exits zero even for
a recorded failure, because the Brev command wrapper can retry nonzero exits.
Read the receipt status to determine success. If invoking through Brev, also
wrap the remote shell with `exit 0` to avoid a transport wrapper mistaking a
recorded script failure for permission to repeat work. An existing intent is
never removed or overwritten to permit another submission.

The scientific molecular branch remains independently gated on the exact
qualified CD19 target construct, reference CAR-binding construct, separately
qualified candidate, and source-backed evidence of accessible retained target.
The existing 7JIC structure is CD19–CD81–coltuximab context, not an FMC63 CAR
comparison, and cannot supply those missing inputs by substitution.

## Actual completed check

On 2026-09-19 at 18:12 UTC, check
`bionemo-monomer-20260919-5a38419a` made exactly one hosted POST and completed
with HTTP 200. NVIDIA request ID:
`51bed1f8-3e19-47a3-bdab-37d4b3fef082`.

The returned mmCIF contains one model, chain A, all 110 exact input residues,
complete alpha-carbon coverage and 838 atoms with finite coordinates. The
returned confidence score is **0.4335459768772125**. Passing identity and
integrity validation does not make that score a claim of structural accuracy
or successful biology.

The receipt records `monomer_service_verified=true`,
`matched_comparison_verified=false`, and `cart_hypothesis_tested=false`.
It is retained on Brev at
`runtime/engineering/bionemo-monomer-20260919-5a38419a/receipt.json`.
Review copies of the unchanged receipt and prediction are in the project
workspace's `outputs/team-tbd-bionemo-service-check/` directory.

| Artifact | SHA-256 |
|---|---|
| `receipt.json` | `e28182dbed9668c4ba549391de22e3364bd165b3a1f8fc45e2eaec0bdd9a8d3c` |
| `prediction.cif` | `8d97359361dcadb273b2f61de819a6025d7595dfee49f5a9544efdcde356e1fa` |
| Submitted sequence | `99603f8fb1e9872e2d24ee1e9f85108c2bddea6b148a0f1099e16ba2715c8263` |
