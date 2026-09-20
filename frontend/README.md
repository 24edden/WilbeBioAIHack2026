> **Earlier pet prototype.** The default app now uses the authoritative scientific engine. See [current integration](../docs/FULL-STACK.md) and [startup](../README.md). This document applies to `frontend/legacy_app.py`.

# TRACE frontend

TRACE has exactly three screens:

1. **Prompt** — write a question and drag files into the same rounded composer.
2. **Running** — one scientist pet displays the current public agent update while the investigation is active.
3. **Results** — the conclusion, with evidence, limitations and supporting details on the same page.

The TRACE logo always returns to the prompt. An active investigation continues in
the background; its Return to investigation button takes you back to the same run.
New submissions are blocked until that run ends. Draft text and files are preserved.
When a run ends while you are watching it, Results opens automatically. There is no
post-completion replay queue. If you deliberately went home, completion does not
interrupt your draft; View last results becomes available instead.

## Run locally

From the repository root:

```bash
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -r requirements.txt -r frontend/requirements.txt
python -m streamlit run frontend/legacy_app.py --server.address 127.0.0.1 --server.port 8502 --browser.gatherUsageStats false
```

Open http://127.0.0.1:8502. **Play the pet demo** needs no backend server, GPU or API
key. It computes the bundled sample with the actual local engine and explicit mock
providers, then paces the unmodified public events over approximately **25 seconds**.
The saved outcome does not change. Cancellation interrupts the pacing immediately.
Configuration and execution failures are returned immediately instead of being hidden
behind the demo timer. Starting with your own files uses those files, not the sample.

To connect the same interface to the actual backend, set `TRACE_BACKEND_URL` before
starting Streamlit. Without that setting, ordinary submissions use the local mock
demo. No source selector, model wizard, alternate theme screen or legacy navigation
is exposed. `TRACE_START_SCREEN=classic` no longer changes the interface.

**Live runs have no presentation delay**: the pet screen stays active until the
source finishes, then the application shows the resulting report or execution error.
The existing upload, investigate, SSE and cancellation adapter remains in use.
There is no silent fallback from a failed connected run to mock findings.

## Input and state behavior

- Supported extensions come from `ui/config.py`: VCF, CSV, TXT, TSV and JSON.
- The browser and Python validate limits: 20 files, 20 MB per file, 40 MB total.
- Files are stored in the frontend session; they reach the investigation source only
  on an explicit submission. Pending text and attachments remain editable during
  another run; submitted requests are independent snapshots.
- Light/dark mode applies to all three screens and does not restart a run.
- Cancellation remains Running until cleanup is acknowledged. Canceled, incomplete
  and failed execution states are not displayed as biological insufficient evidence.
- Retry is explicit and starts a new attempt. Previous results remain inspectable in
  a collapsed section on the Results screen. Follow-ups use the same workflow and
  carry prior claims as untrusted context, not as new evidence.
- State is session-local, not durable server storage. Refresh/restart behavior follows
  Streamlit's session lifetime. Do not use this demo as permanent research storage.

## Relevant modules

| Concern | File |
|---|---|
| Three-state controller and natural navigation | `app.py`, `ui/workspace.py` |
| Single prompt/drop surface | `static/composer.{html,css,js}`, `ui/composer.py` |
| Request creation | `ui/pet_start.py` |
| Event-to-pet projection | `ui/pet_activity.py`, `ui/pets.py` |
| Mock-only 25-second pacing | `ui/demo_pacing.py` |
| Existing source adapters and background execution | `ui/adapters.py`, `ui/runtime.py` |
| Preserved scientific result components | `ui/components.py` |
| Shared theme | `ui/appearance.py`, `static/workspace.css` |
| Permanently right-facing images | `static/scientist-pets/` |

The UI renders normalized `Event` records folded into `RunState`. It does not rename
backend fields or invent opinions from private reasoning. Pet text is a short excerpt
of public events; full text and source references remain available with the result.
Unknown roles get the generic pet. The PNG/WebP/GIF assets have already been mirrored;
never add another CSS flip. Reduced-motion uses still PNGs.

## Verification

```bash
python -m pytest -q
python frontend/smoke_test.py
node tests/composer_browser_test.mjs
```

See `QA.md` for the current audit and its limits. Restart a development preview after
changing Python module interfaces so that cached old imports cannot mix with new code.
