# TRACE overnight closeout

20 September 2026, approximately 10:00 Europe/London.

The overnight automation is paused. The first resumed check after the cutoff
found the prior receipt-download browser call interrupted and the local preview
process stopped. No further feature iteration was started. The frontend was
restarted at http://localhost:8502 and its initial UI was checked.

## Completed and checked

- Client-side theme changes preserve layout; animated microphone controls and
  immediate help were improved, including keyboard-focus retention during polls.
- Capability discovery and API parsing no longer block the same UI/event-loop
  paths. Waiting shows observed phases and a browser-owned elapsed clock.
- Drafts survive navigation and completion notices. Follow-ups expose exact
  bounded prior context, omissions and shortening before explicit submission.
- Earlier arguments and exact finding references are inspectable. Saved results
  use stable identities, truthful outcomes and a preview before opening.
- Every retained activity summary is reachable in bounded pages. The bundled
  recording's earliest planner activity was checked without new inference.
- Research, rejected ideas, validation and conditional demo scripts are recorded
  in the overnight logs and Presentation/ux-demo-script.md.

Final automated validation: **313 tests passed**, two existing dependency
deprecation warnings. `git diff --check` passed. The command was:

```powershell
.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider --basetemp .deploy/overnight-final-tests
```

## Request-receipt status

Implemented for current and selected saved results. Tests cover ownership, exact
question/context, allowed requested settings, omitted connection/upload data,
legacy cases, lazy preparation and download without rerun. Before interruption,
the browser verified a closed panel had no download control and opening it showed
the correct current identity and download button. Actual downloaded bytes,
selected-record browser download and receipt-specific mobile checks remain
unverified. The presentation receipt beat remains conditional.

## Outstanding release work

- Overnight changes have not been deployed to Brev or a public branded URL.
- Live provider execution, audience capacity and a 50-user load test were not
  validated by this work. No scientific-quality or model-performance claim follows
  from UI tests.
- The earlier long-tab stall remains unresolved; the renderer still paints every
  poll because skipping paints previously erased content. No latency/INP speedup
  is claimed from the focus correction.
- A scientist walkthrough and rehearsal against the exact deployed release remain
  necessary. Changes remain in the shared working tree; no overnight commit or
  merge was made.
