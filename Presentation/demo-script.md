# TRACE: five-minute presentation

Working script, 19 September 2026. Use the exact release and prepared artifacts
checked in [the deployment record](../infra/DEPLOYMENT.md). The independent
[UX](ux-demo-script.md), [judge-impact](judges-wow-script.md) and
[technical](technical-demo-script.md) reviews hold the longer feature backlog.

**The story:** a scientist controls the question, inspects how agents challenge
an argument, and decides what evidence to seek next. Agent agreement does not
establish a causal mechanism.

## Main sequence

Use two runs at most. Prepare the completed evidence investigation before the
presentation; start the short idea review on stage. Show the provider-mode label.
The current CPU release uses simulated providers, not fresh Rosalind/BioNeMo
inference. Do not describe a recorded run as live computation.

| Time | Action | Spoken draft |
|---|---|---|
| 0:00–0:25 | Evidence screen with the synthetic case ready | “A fluent explanation is easy to produce. A scientist still needs to know which evidence supports it, what was assumed, and what would change their mind. TRACE makes that investigation inspectable.” |
| 0:25–0:55 | Open the persistent question and team controls | “I choose the question and the specialist team. The interface introduces controls as I need them. This demonstration uses synthetic records and simulated model outputs, running through the real orchestration.” |
| 0:55–1:35 | Prepared Results: one finding, its source, then Weak points | “Here is a claim and the reference attached to it. Here is the limitation the system identified: [read the actual item]. The next-evidence field tells us what would help resolve it. More agreeing agents would not make the missing evidence appear.” |
| 1:35–2:00 | Edit setup; enter the proposal below; select Review an idea | “Now I want to evaluate a research proposal. That needs a different team: research, a supporter, a challenger and a critic, coordinated by the planner.” |
| 2:00–2:55 | Start; show directed messages, then Review discussion | “The supporter develops the proposal. The challenger receives it and questions its assumptions. The supporter then revises it. These arrows are recorded messages. The useful output is the assumption we can now test.” |
| 2:55–3:25 | Inspect the real revision and one open question | “The research role inventories the supplied evidence. Proposal arguments remain separate from scientific findings. The scientist can inspect the reasoning and decide what to investigate next.” |
| 3:25–3:50 | Persistent draft; optionally point to Cancel in a separately rehearsed slow run | “I can prepare the next question while a submitted investigation continues. The original request remains unchanged. Cancellation stops work and preserves the partial record.” |
| 3:50–4:25 | Architecture and measured execution artifact | “The interface consumes a small event contract, so datasets and model services can change independently. Variant work has bounded concurrency and duplicate requests share a result within a run. Our repeated-input mock check reduced 60 scoring calls to five with the same findings. That is a resource saving, not a claim of twelve-times faster inference.” |
| 4:25–4:45 | Honest tooling status; replace only with retained verified evidence | “The service runs on the Brev CPU. We have a Rosalind Responses adapter, but this demonstration uses simulated providers. Live model validation and a central NVIDIA scientific or evaluation integration remain the next technical checkpoints.” |
| 4:45–5:00 | Repository and reproduction reference; return to Weak points | “The repository contains the synthetic case, event contracts, tests and deployment recipe. TRACE helps a scientist see the argument, its evidence and its weak points before choosing the next experiment.” |

Prepared question, designed for the current review path:

> Evaluate this research idea: compare two competing explanations for treatment
> resistance using a held-out dataset. Propose a simple baseline, identify the
> assumptions, and say which evidence would challenge each explanation.

Mock review responses demonstrate turn-taking and data flow with deterministic
templates. They are not a biomedical reasoning benchmark. If the team verifies a
live provider before presenting, retain its model ID, configuration, report and
events and update both the spoken disclosure and deployment record.

## Optional visual and voice beats

- Choose the white/blue Astral theme or the original dark theme before starting;
  rehearse on the projector. Avoid spending stage time on the theme toggle.
- Preview the selected browser voice in advance. At most one short stage cue
  should play; pause narration for it. Voice input requires reviewed text before
  applying it. Type the prepared question if recognition is unavailable.
- If the debate completes too quickly to narrate, inspect its completed graph and
  discussion. Do not claim the rendered graph has clickable evidence nodes.
- Keep the unsupported BRCA2 question as an optional Q&A demonstration of the
  mock abstention path, not a third main-stage run.

## Fallback and rehearsal

1. Verify the presenter's NVIDIA-authenticated URL and keep that session open.
   A private SSH preview can exercise the deployment but does not prove the
   audience's access. Keep the local mock setup ready as a backup.
2. Prepare the completed evidence report and review event log before the talk.
   Runs currently live in server memory and disappear on restart. Save the
   outputs externally before restarting services. Existing replay fixtures may
   not include newer discussion or weak-point fields.
3. If the service stalls, identify it and switch to a clearly labelled saved run
   or interactive mock. A backup recording must actually be captured before it
   is listed as available.
4. If time runs short, cut voice, theme and team-card commentary. Preserve one
   source, one challenge/revision, one weak point and the reproduction reference.
5. Put this narrative into the official Google Slides submission template and
   provide the single repository link. These Markdown notes are script material,
   not a completed slide submission.

## Highest-value follow-up work

These are proposals, not shipped promises:

1. A weak-point button that drafts the next question without automatically
   starting work or changing the prior run.
2. Side-by-side opening, challenge and revision using real discussion IDs.
3. A measured model-comparison view, with retained outputs and actual token and
   latency fields. Use a task-specific scientific baseline alongside generic
   agent benchmarks; Terminal-Bench alone cannot establish scientific validity.
4. One verified, necessary NVIDIA scientific or evaluation integration and one
   verified Rosalind reasoning run, chosen from the technical review. The current
   asyncio engine must not be presented as NVIDIA Agent Toolkit.

Numbers and status should be refreshed from the final release, not from memory.
The local resource comparison is in
[performance-check.json](../Plan/performance-check.json); the judging basis is
[the event rubric](../Context/judgingCriteria.md).
