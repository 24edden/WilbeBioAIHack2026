# Weekend build plan

## Team shape

For two people: one handles science/evaluation/presentation, one engineering/integration. For three: add a GPU specialist. For four or five: add a product/demo owner and a second scientist or evaluation owner. Scott can select his role after meeting the team; no professional specialty is assumed here.

## Friday

- 15:00: activate event access. Check permitted pre-work, exact model ID/interface, credits organization, GPU image/driver and submission path.
- 16:00: deliver the 60-second pitch if seeking teammates; use the organizer's signup tab.
- Before leaving: team of 2–5, one sentence problem, named owners, shared repository decision and a written scope. Save the known-good local demo.

## Saturday

| Time | Outcome | Owner |
|---|---|---|
| Before 10:00 | Everyone can reproduce baseline; scientist reviews what the label means | Science + engineering |
| 10:00–11:00 | Attend technical sessions; resolve model and Brev blockers | All |
| 11:00–12:45 | One real OpenAI tool-calling trace and one NVIDIA GPU smoke test | Agent + GPU |
| 13:45–15:00 | nvMolKit parity/timing; wire GPU similarity into audit only after parity | GPU + engineering |
| 15:00–16:30 | Add one meaningful negative control or independent assay; inspect failures | Science |
| 16:30–17:45 | Test agent's numerical fidelity and abstention; record actual role of both platforms | Evaluation |
| After dinner–19:30 | Integrate report, slide evidence and reproduction instructions | Demo + engineering |
| By 20:00 | Leave building; saved demo and results available offline | All |

## Sunday

09:30–12:00: attend the confirmed talk slot; fix only necessary issues. Freeze model/data choices by noon. 12:00–13:30: finalize result provenance and deck. 13:30–14:15: fresh-environment reproduction and five-minute rehearsal. 14:15–14:45: submission checks, cached demo, assign presenter/back-up. 15:00: judging starts. Confirm the actual submission deadline earlier.

## Acceptance criteria

1. A scientist can explain the assay label and limitations.
2. Saved raw-data hash, exact split membership, versions and predictions regenerate the headline result.
3. Every numerical claim in the agent's review is checked against a metric path.
4. Agent errors and absent tools result in explicit limits, not fabricated success.
5. NVIDIA evidence includes actual device/version, numerical parity and synchronized timings. CPU work remains identified as CPU.
6. The demo completes in five minutes with a working offline backup.
7. The final repository excludes credentials, private arrival details and the virtual environment.

## Evaluation additions worth doing

- **Agent fidelity:** annotate ten questions whose answers are in metrics.json; record incorrect numbers, missing caveats, and unsupported conclusions. A scientist reviews the output; do not let the same model grade itself as the only evaluator.
- **Negative control:** permute labels under a declared null model, rerun the full training/evaluation process, and inspect a distribution of results. Group-aware permutation requires careful specification; do not casually permute unequal scaffold labels and call it a valid test.
- **Independent assay:** use a second public binary molecular task with the same fixed procedure. Do not choose it because it makes the largest performance gap.
- **Practical value:** ask a domain teammate to compare the brief with the raw score. Record what decision or follow-up changes, if any; this is qualitative feedback, not proven time saved.

## Cut ruthlessly

No foundation-model training, no full discovery platform, no automatic experiment execution, no unsupported clinical conclusions. Drop cosmetic work before dropping provenance or a working demo. Do not add a second dataset until the first end-to-end path works.

## Submission checklist

- Final team members and affiliation approved by each person.
- State pre-event contribution if relevant; confirm eligibility with organizers.
- Replace pending GitHub link and grant judges the requested access.
- Preserve the organizer's three narrative slides plus technical appendix.
- Replace every pending integration label only with verified evidence.
- Confirm upload destination and deadline; submit once the team is ready.
