# Weekend timeline

Idea-independent schedule. The finalist plans in [finalists/](finalists/) fill in the middle;
this is the frame and, more importantly, the checkpoints.

**Times are placeholders** — correct them against the real agenda on Friday.

## Friday evening — the hours nobody uses well

Most teams treat Friday as social. The teams that do these five things start Saturday two
hours ahead:

- [ ] Brev instance launched and confirmed working. **Run something. An account is not access.**
- [ ] BioNeMo containers identified and pulling overnight if possible
- [ ] Rosalind access confirmed, and its nature established: API, UI, or both
- [ ] Repo created, everyone has push access, `AGENTS.md` and `Context/` in place
- [ ] Candidate datasets downloaded, not just bookmarked
- [ ] Collect failure anecdotes from mentors and scientists over drinks. Ask: *"what is a
      mistake you have seen an AI tool make on biological data?"* Those answers are slide
      material for any of the three finalists, and they cost nothing to gather

## Saturday

| Time | Phase | Note |
|---|---|---|
| 09:00–10:30 | **Choose.** Run [00-decision-framework.md](00-decision-framework.md) | Commit out loud. Named owners per component |
| 10:30–11:00 | Skeleton: repo, entry point, one end-to-end stub that runs and does nothing useful | The stub matters more than it looks |
| 11:00–13:00 | Build the risky part first | Never the easy part. The unknown is what needs the daylight |
| 13:00 | **Checkpoint 1: is the risky part alive?** | Kill criteria fire here. Be honest |
| 13:00–16:00 | Build out | |
| 16:00 | **Checkpoint 2: does anything run end to end?** | If not, cut scope now, not tonight |
| 16:00–18:00 | Finish the MVP | |
| 18:00 | **Checkpoint 3: MVP complete.** Stop adding features | Feature freeze on the demo path |
| 18:00–20:00 | The finding, the chart, the comparison | The thing that makes it a project |
| 20:00–22:00 | Slides drafted end to end. **Demo recorded** | Both, tonight |
| 22:00 | **Checkpoint 4: could we present tomorrow if we stopped now?** | If no, something went wrong at 16:00 and we should have cut |
| 22:00+ | Optional stretch work, on a branch, by whoever still has energy | Never on the demo path |

## Sunday

| Time | Phase | Note |
|---|---|---|
| 09:00–10:30 | README, reproduction instructions, one-command run | See [05-reproducibility.md](05-reproducibility.md) |
| 10:30–11:30 | Rehearse twice with a timer. Cut a slide each time | You will be 90 seconds over. Everyone is |
| 11:30–12:00 | Freeze. No code changes | |
| 12:00 | Buffer for the schedule slipping, which it will | |
| Afternoon | Present | |

## The three rules that actually matter

1. **Build the risky part first.** If the GPU model does not work, you want to discover that at
   11:00 Saturday when you can still change plan, not at 22:00 when you cannot.
2. **Record the demo Saturday night.** A recording converts every Sunday disaster — dead
   laptop, dead wifi, expired credits, a model that decides to behave differently today — from
   fatal to survivable. Almost nobody does this, and some team every hackathon loses to a live
   demo failure.
3. **Feature freeze at 18:00 Saturday.** Everything after is evidence, narrative and polish.
   The marginal feature is worth less than the marginal rehearsal, always.
