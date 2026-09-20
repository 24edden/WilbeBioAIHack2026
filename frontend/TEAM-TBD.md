# Team TBD: connected pet frontend

This integration starts from `codex/pet-ui-integration` and reuses its pet assets,
open layout and pet characters, with a black and lime-green connected-workspace theme. It presents the existing Team TBD
scientific records without modifying the scientific backend, agents, instructions,
models, budgets, governance, methods or saved history.

The connected workspace is read-only. It offers completed studies, findings, team
work products, evidence, NVIDIA artifacts, exact sequences, handoffs, review,
proposed next steps and recorded history. Its controls do not launch investigations,
submit follow-ups, regenerate briefs, discover sequences, attest target retention,
change settings on the backend or submit provider jobs.

## Start a private preview

Run from the repository root so the branch's `.streamlit/config.toml` is applied:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r frontend/requirements.txt
export TEAM_TBD_CAPSULE="/absolute/path/to/private/team-tbd-results-capsule-2026-09-20-v1"
.venv/bin/python -m streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8504 --browser.gatherUsageStats false --theme.base dark --theme.primaryColor '#d6fb73' --theme.backgroundColor '#080b09' --theme.secondaryBackgroundColor '#101612' --theme.textColor '#f0f5ee'
```

Open <http://127.0.0.1:8504>. Port 8504 is a separate frontend process. Leave the
existing scientific services and tunnel on 8081 and 8082 running unchanged. If 8504
is already occupied, select another free loopback port rather than stopping an
unrelated service.

`TEAM_TBD_CAPSULE` points to the existing, private, external capsule directory;
do not copy it into Git, `frontend/static`, or a public hosting bundle. Retain its
complete original directory layout. This consumer supports the
`team-tbd-results-capsule/1.0` schema, not the separate `team-tbd-archive/1.0.0`
format. Those packages contain the same historical runs under different readers;
they must not be combined as additional studies.

The connected workspace is enabled only when `TEAM_TBD_CAPSULE` is set. Unset it
before launching to use the branch's original prompt/running/results interface:

```bash
unset TEAM_TBD_CAPSULE
```

The original interface retains its existing backend configuration and behavior.
The read-only guarantees in this document describe the Team TBD connected workspace.

## Frozen replay and live reads

**Frozen replay** is the default. Every scientific value and event comes from the
sealed capsule. The History slider steps through recorded events; it does not
simulate new scientific work. The snapshot time and replay status remain visible.
The platform picker contains only the two selected completed studies: Ana’s
GSE28460 diagnosis–relapse study first, then the CAR-T/CD19 investigation. Historical
capsule records remain intact but are not exposed by the platform picker or old
run bookmarks. Unknown/older run bookmarks open the Ana study instead.

**Live reads** fetch the selected existing run from its original service. The UI
labels these as live backend reads, shows the fetch time, and preserves the run's
actual status. A completed run is not shown as newly executing. Choose **Refresh
now** for another read, or enable **Refresh existing run every 15 seconds** for
optional polling. Reads are cached for up to 15 seconds between refreshes. A live
connection error stays visible; the UI never silently substitutes frozen data.

The capsule's run catalog supplies the picker and source routing in both modes:

| Source ID | Default origin | Location |
| --- | --- | --- |
| `brev-main` | `http://127.0.0.1:8081` | Existing private Mac tunnel to Brev |
| `mac-ana-isolated` | `http://127.0.0.1:8082` | Separate native Mac Ana service |

Optional `TEAM_TBD_MAIN_URL` and `TEAM_TBD_ANA_URL` overrides must be explicit HTTP
loopback IP origins. The adapter rejects public origins, hostnames, credentials,
paths, queries and redirects. No server keys are requested or sent by this frontend.

Bookmarks can choose `?mode=replay` or `?mode=live`, plus `&run=<selected-run-id>`
and `&view=<page-label>`. The two selected run IDs are explicitly allowlisted in
`CURATED_STUDIES`.
Artifacts load only when requested and can then be downloaded. Frozen artifact
bytes come from the capsule; live artifact bytes come from the run's recorded URLs.

## Exploring agent collaboration

The overview includes direct entry points into agent collaboration, findings and
predictions. **Agent collaboration** is also the second main navigation option.
Choose an agent to inspect sent and received handoffs, then follow a saved handoff
into its result, method, limitations, evidence, skill/model receipts and linked
acceptance evaluation. Upstream and downstream links follow recorded input IDs;
routes show recorded recipients and do not infer spawning or extra model activity.
The communication map provides route selection and links back into the same records.
Findings link directly to individual evidence records. **Decisions & review** retains
immutable decision versions and governance details; **History** holds event replay
and usage/model receipts.

## Adapter contract

`ui/team_tbd_adapter.py` contains two synchronous readers:

- `Capsule(root, expected_manifest_sha256=None)` exposes `.manifest`, `.runs`,
  `.artifacts`, `.list_runs()`, `.read_bytes(path)`, `.read_json(path)`,
  `.load(run_id)` and `.artifact_bytes(item)`.
- `LiveSource(base, client=None)` exposes `.list_runs()`, `.load(run_id)` and
  `.artifact_bytes(item)`. It uses HTTPX GET requests only.

Both `load` methods return `{run, events, evidence, view, artifacts}`. The raw run
is retained alongside a presentation mapping; the adapter does not rewrite
scientific conclusions, execution statuses or review states.

| Presentation | Saved source |
| --- | --- |
| Question and provenance | `run.hypothesis` |
| Headline, summary, findings, role summaries, decision story, next step | Latest `run.research_briefs[].content` |
| Original decisions | `run.decisions[]` |
| Role work products and routed handoffs | `run.handoffs[]` |
| Acceptance checks | `run.stage_evaluations[]` |
| Evidence and measurements | `run.evidence[]` |
| Applied instruction provenance | `run.skill_receipts[]` |
| Model receipts | Decision metadata and action/brief/discovery provider metadata; exact copies deduplicated |
| Aggregate usage | `run.usage`; overlapping receipts are not summed |
| NVIDIA receipts | `run.followup_operations[].provider_receipts[]` |
| Artifacts | Follow-up, required-analysis and decision-modeling artifact records |
| Exact prediction inputs | `run.research_briefs[].molecular_audit.sequence_inventory[]` |
| Public sequence discovery | `run.sequence_discoveries[]` |
| Operational governance | `run.governance_state` and `run.governance_transitions[]` |

Frozen loading follows the manifest's raw export and view paths; `export.json.run`
is the raw record. Live loading reads `/api/runs/{id}/export.json` and maps its
`run` into the same presentation shape. Curated capsule labels remain available in
the picker. Historical studies without briefs retain their raw partial records.

Full handoffs retain `sender`, `recipient`, `operation_id`, scientific
`result_status`, claims, limitations and exact upstream IDs. Software acceptance
checks link through `handoff.acceptance_evaluation_id`. Brief and sequence-discovery
operations can reuse previous specialist work; they do not imply another nine-role
scientific cycle. Proposed next steps remain proposals.

## Integrity and privacy bounds

Capsule reads require a manifest-listed relative path, byte count and SHA-256.
Traversal, symlinks, encoded paths and unlisted files are refused. Manifest reads
are limited to 5 MiB; listed files and live responses are limited to 128 MiB.
`Capsule` optionally accepts an independently recorded manifest hash. File hashes
establish consistency with the supplied manifest, not its authenticity or the
scientific validity of its contents.

Live artifact requests must match recorded URLs from an already loaded run, under
that run's `/artifacts/` or `/structure-preview/` route. Recorded artifact hashes
and sizes are checked where available. A structure-preview JSON response is not
checked against the corresponding CIF hash: those are different byte streams.
External provenance references are displayed as records, not automatically fetched.
Scientific prose is escaped before presentation; artifact SVG/HTML is not inserted
as executable content by the artifact download interface.

Keep the Streamlit listener on `127.0.0.1`. This preview does not add authentication
and must not expose private research through an unauthenticated public host.

## Presentation guardrails

Keep operation status, scientific result status, individual provider receipts and
human review status separate. Successful prediction artifacts can coexist with a
subsequent workflow failure; neither status should overwrite the other. Preserve
missing inputs and proposed-versus-executed qualifications from the records.
Exact sequences retain their recorded roles, construct identity and hashes.
Model inference, applied Team TBD guidance and installed vendor skills have separate
provenance. The UI does not upgrade instruction provenance into model entitlement.
When studies share a cohort, the overview discloses this rather than implying
independent replication. Contract acceptance does not establish scientific validity.

## Validation

Install the test runner in the same environment, then run the focused checks:

```bash
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests/test_team_tbd_adapter.py -q
```

With `TEAM_TBD_CAPSULE` set, the suite also loads all 12 real snapshots and verifies
their packaged artifact bytes. Without it, that private-data test is skipped and
synthetic path, hash, origin, redirect and mapping tests still run.

Integration validation performed for this change: 18 adapter tests passed with the
actual capsule; both existing live runs loaded; all eight artifact downloads across
the two featured runs matched recorded hashes; both saved NVIDIA structure-preview
responses loaded. These were reads only. They establish connectivity and data
integrity, not new inference or scientific validation. Browser screenshot delivery
is tracked separately and is not implied by these checks.

The connected UI regressions live in `tests/test_team_tbd_ui.py`. Set
`TEAM_TBD_TEST_CAPSULE` to the same private capsule to enable actual-data UI checks.
Live artifact mode-switch tests also require `TEAM_TBD_TEST_LIVE_READS=1`; they make
GET requests to existing runs only. Default tests use synthetic data and no network.
The full repository suite passed: 225 tests, with these explicit private-data/read-only opt-ins. Leave the deployment variable TEAM_TBD_CAPSULE unset when running the full suite, so original-interface tests retain their default mode; use TEAM_TBD_TEST_CAPSULE for test-only activation.
Browser validation covered overview, findings, team detail, evidence, NVIDIA receipts,
artifact tables, exact sequences, handoffs/review, history, both live sources, dark
mode and a 390-pixel mobile breakpoint. Screenshots remain outside Git and are
provided privately through the task deliverables.
