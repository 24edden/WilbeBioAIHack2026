> **Historical prototype deployment.** These commands launch the earlier backend and `frontend/legacy_app.py`. For the current scientific release use [the root startup guide](../README.md) and [scientific backend setup](../scientific_backend/SETUP.md).

# Brev deployment record

Verified on 19 September 2026. This record was written after packaging the release;
it is an audit note, not a file inside that immutable source archive.

## Access and runtime

- Service: <https://trace-z484f0h2c.gobrev.dev>, with NVIDIA authentication and access
  restricted to the deploying user's account.
- Instance: `agentic-takeoff-cpu`, organization `London-AI-Brev`, CPU only.
- Directory: `/home/ubuntu/trace-service/current` points to
  `releases/20260919T215157Z-13c08cd69960`.
- Compose project: `trace-demo`; one FastAPI worker and one Streamlit container.
- API is private. UI listens on `127.0.0.1:8501` and the private Brev mesh address
  `100.73.140.211:8501`. No public-interface port binding was added.
- Providers run in **mock mode**. The editable demo executes orchestration with
  simulated model outputs. No live Rosalind or BioNeMo inference is claimed.
- Uploads, runs and UI sessions remain in memory and are lost on process restart.
  Teammates' other workspaces and services were left separate.

For the presenter's private browser preview, keep this process running and open
<http://localhost:18501>:

```powershell
wsl -d Ubuntu -- ssh -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -N -L 127.0.0.1:18501:127.0.0.1:8501 agentic-takeoff-cpu
```

The Secure Link reaches NVIDIA sign-in. A complete signed-in HTTPS session was not
available in the test browser; the presenter still needs to check that path. The
deployed UI itself was exercised through the private SSH forward. Additional viewer
accounts need their own access-policy entry.

## Reproducible identity

| Item | Value |
|---|---|
| Release | `20260919T215157Z-13c08cd69960` |
| Git base | `4b2d2e1a968a43ecbcf24feb962db845d1de9085` |
| Working tree | Uncommitted changes explicitly included; the Git base alone does not reproduce this release |
| Source manifest SHA-256 | `13c08cd699608ea1854a9abeefc8993c2493c72654f9e2393bf8fa80d0fbcd8a` |
| Archive SHA-256 | `fa7cb3e7a6057d0b182cd295a80db4f75fb6cf0e9ef8e9e4da3490724e0159cf` |
| API image ID | `sha256:6bcc9005678ec16a1ab68ff7b178067d2214c79082fd848de60abd0bada1b073` |
| UI image ID | `sha256:d82fd4cb2549148c3ca8353822a4672c652b8bf4042ca731b9bda8edca4d1dc7` |
| Python base digest | `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` |

The 125-file archive contains source, tests, presentation scripts and bundled synthetic cases. Personal
credentials, uploads and evaluation outputs were excluded. Each source file's hash
is in `release-manifest.json`. Exact installed package versions and image IDs are
saved as `deployed-requirements.txt` and `deployed-images.txt` in the release.
Both Docker images also have a tag equal to the release ID.

## Checks completed

- **168 tests passed, one skipped** in the final Linux UI image before activation.
  The skipped test requires Node.js for browser-voice lifecycle mocks; it passed
  locally in the 169-test Windows suite. The two warnings were dependency
  deprecations from the Starlette test client. Actual microphone recognition and
  perceived voice quality were not measured.
- Both deployed containers became healthy. UI health succeeded on loopback and the
  Brev mesh address.
- Connected API smoke test uploaded three synthetic files, consumed 53 events,
  produced 13 findings and completed successfully in mock mode. Run ID:
  `6520a91b-e9f0-451d-a8f9-f034c0ca9cae`. The same deployment check verified actual
  cancellation, repeated cancellation, and exactly one terminal event.
- Question-only Auto review completed with the five-role team and five discussion
  phases, without fabricated scientific findings. Run ID:
  `20e10b64-1bf5-4957-b8d0-6e96256a04dc`. Report and SSE discussion/metrics/weak-point
  payloads were checked for parity.
- Hosted browser verification exercised the Astral light toggle, retained theme
  across stages, readable native controls/help, task routing, idea-review discussion,
  and the directed supporter/challenger graph. The original dark theme remains.
  Local browser checks also exercised reviewed voice text, navigation commands,
  the device voice picker/preview, draft editing during a run and cancellation.
- Earlier release checks covered unsupported BRCA2 abstention and the Weak points
  tab with its rationale, next evidence and references; regression tests remain.
- Weak points use the same backend payload in `GET /report/{run_id}` and the
  `run_complete` event; regression tests cover assessment and frontend handling.

The browser checks validate the workflow and rendering. They do not validate
scientific model performance or biological conclusions.

The public audience URL and QR code have not been published. The recommendation
for a free branded URL and roughly 50 viewers is recorded in
[Plan/public-demo-hosting.md](../Plan/public-demo-hosting.md). It distinguishes a
static audience explorer from simultaneous live investigations; no 50-user load
capacity claim has been established for the current Streamlit deployment.

Operational commands, updates and future live-provider setup are in
[README.md](README.md). Keep the tested images for the presentation; rebuilding can
resolve newer packages because dependency requirements currently use lower bounds.
