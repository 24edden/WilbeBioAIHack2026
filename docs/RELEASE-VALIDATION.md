# Full-stack release validation · 2026-09-20

The default pet frontend is connected to the authoritative Team TBD `/api/runs`
engine. The earlier API is retained only through `legacy_app.py`. No paid
scientific runthrough, model probe, sequence search or NVIDIA inference was
submitted for this release.

## Final frontend and integration checks

- Complete repository suite: **318 passed**. This includes 61 transport/API
  contract tests, 22 independently authored scientific-UI tests, and the prior
  backend/frontend regressions. Two upstream FastAPI/Starlette deprecation
  warnings do not affect results.
- Four JavaScript suites passed: composer, microphone, client controls and voice.
- All 41 saved-study adapter/UI checks passed with the sealed private capsule
  and explicit real GET opt-ins. The capsule retains all twelve snapshots; the
  displayed picker remains Ana then CD19. Existing source runs, artifacts and
  preview bytes were read only; no production POST was made.
- Real browser verification: the question homepage retains the black/lime pet
  design; unsupported upload/demo controls are absent; frozen Ana navigation
  opens its recorded results. On a separate test frontend and actual isolated
  scientific API, create plus feedback produced immutable decisions 1 and 2,
  preserved leading/trailing hypothesis whitespace, and recorded zero model/tool
  calls. The fixture disabled the scientific worker, blocked outbound connections,
  and used its own marked disposable database.
- Successful mutation, stale version rejection, uncertain-write same-key
  reconciliation, cancellation/resume, briefs, sequences, follow-ups, measurement
  IDs, modeling attestation and frozen no-write routes are covered by isolated
  contract/UI tests. Acceptance of a request is never labeled completed inference.
- Saved NVIDIA images automatically render only when exact recorded CIF hashes
  match. The CAR-T Overview and NVIDIA views each show two images; Ana Overview
  shows zero. Both PNG hashes and source metadata were verified.

## Scientific engine and release review

See [the backend validation record](../scientific_backend/RELEASE-VALIDATION.md)
for the complete preserved-engine suite and packaging tests, including the
optional installed scientific runtime and deterministic input preparation.

An independent reviewer compared all 91 imported engine/instruction/original-test
files against the authoritative source: identical bytes. Source packaging excludes
credentials, databases, full private traces, sealed capsules, installed proprietary
plugin bytes, and six external raw/reference input files. Public input installation
uses unchanged exact pins; the prepared BCMA table has a deterministic public-source
preparation recipe. Original scientific behavior, models, budgets and history are
preserved.

The review scanned inherited public branch history (327 unique blobs) and final
public candidate paths/content for secrets and private state. No actual credentials,
private keys or account identifiers were found. Original author history is retained.
The static prediction images contain only labeled molecular structures and scope.

Review defects corrected before release: returning from live controls to the
frozen route; Streamlit widget state after accepted mutations; historical-brief
versus current-decision labeling; scientific-specific claims on unrelated runs;
and legacy upload/demo controls exposed by CSS.

## Reproduction and limits

Install both environments as documented in the root README. Root tests select
`scientific_backend/.venv/bin/python` for the isolated scientific API subprocess;
`TEAM_TBD_TEST_PYTHON` can point to another properly installed scientific environment.
Missing scientific dependencies fail instead of being silently skipped. Full engine
verification uses its network-blocked `scripts/check.py` with authorized optional
runtime available; explicit public-only checks are described separately.

For private existing-data checks, set `TEAM_TBD_TEST_CAPSULE` to the external sealed
capsule and `TEAM_TBD_TEST_LIVE_READS=1`. Leave deployment `TEAM_TBD_CAPSULE` unset
during the root suite. These opt-ins make GET requests only. Default UI tests use
synthetic fixtures and forbid network.

The production scientific service, Ana service, old preview and sealed files were
not stopped, migrated or replaced. The new preview uses a separate loopback port.
A fresh installation requires documented evidence hydration, provider credentials,
verified capability receipts and optional licensed scientific tools for their
supported operations. This release adds no public-host authentication layer.
