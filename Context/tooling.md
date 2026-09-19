---
title: Tooling & Prep — Wilbe Bio x AI Hack 2026
source: event website (pre-hackathon prep instructions), plus team analysis marked INFERRED
purpose: Accounts to create, what each tool is for, and which tools actually earn judging points
related: Context/judgingCriteria.md, Context/challengeWeb.md
---

# Tooling & Prep

## 1. Prep checklist

Do these before the hackathon starts.

### Accounts

- [ ] **NVIDIA Brev** — provides the GPU compute for all teams throughout the hackathon.
  - Sign up for an account.
  - Read the Brev Getting Started doc.
  - Install the Brev CLI.
  - Note: **no GPU credits are issued until the hackathon starts**, so expect an empty
    balance when you first log in. Don't debug this, it's expected.
- [ ] **OpenAI Codex**
- [ ] **GPT-Rosalind** (OpenAI Rosalind)

### Community

- [ ] Join the **NVIDIA Developer Discord**: <https://discord.gg/nvidiadeveloper>
- [ ] Join the **`#london-ai-bio-hack`** channel there. This is where event comms happen.

### Reading

- NVIDIA BioNeMo
- NVIDIA Agent Toolkit
- OpenAI Codex Developer Docs
- OpenAI Rosalind Workbench

The source page linked each item; the URLs weren't captured except the Discord invite.
Paste the real ones in here as you sign up.

## 2. Two kinds of tool, and why the difference matters

> **INFERRED — this section is team analysis, not text from the event page.**

The prep list above mixes two categories that the judging rubric treats very differently.
`Context/judgingCriteria.md`, criterion 2, reads:

> *Does the project use NVIDIA and OpenAI technologies in a meaningful way? Are the
> technologies **central to the solution rather than incidental**?*

"Central rather than incidental" is the operative phrase. A judge watching a five-minute
demo can only see tools that are **inside the thing being demoed**. Tools used to build it
are invisible unless we explicitly narrate them, and even then they read as incidental.

### Build-time tooling — necessary, but scores ~nothing on criterion 2

| Tool | What it does for us | Why it doesn't score |
|---|---|---|
| **NVIDIA Brev** | GPU dev environments (launchables, `brev shell`, `brev open`). This is where our code runs during the event. | It's the venue, not the work. Every team uses it. A project that "uses NVIDIA" only by renting NVIDIA GPUs is the textbook definition of incidental. |
| **OpenAI Codex** | Coding agent (CLI, IDE extension, cloud) that writes and refactors our code. | It accelerates us, but it isn't in the product. Judges see the artifact, not the commits. |

Both are worth using hard — Brev is the only GPU access we have, and Codex is the reason
a small team can ship in a weekend. Just don't count them as our answer to criterion 2.

Note the prizes are **Brev credits + Codex credits**. That tells us what the sponsors want
us *consuming*; it is not the same as what they're *scoring*. Don't confuse the two.

### In-product technology — this is what criterion 2 actually rewards

| Tool | Vendor | What it is | How it can be central |
|---|---|---|---|
| **NVIDIA BioNeMo** | NVIDIA | Biomolecular AI platform. Two halves: the **BioNeMo Framework** (training/fine-tuning bio foundation models on GPU) and **BioNeMo NIMs** (containerised inference microservices for published models — protein structure, docking, protein design, genomics, single-cell). | Any step in our workflow that predicts structure, docks a ligand, designs a sequence, or embeds biological data can be a BioNeMo call instead of a hand-rolled model. Makes the NVIDIA dependency scientific rather than infrastructural. |
| **NVIDIA Agent Toolkit** | NVIDIA | Framework for composing agents, tools and workflows, with profiling, tracing and an evaluation harness. Framework-agnostic — wraps existing agent stacks rather than replacing them. | The orchestration spine of the project. Also the natural fit for the **Benchmarking** track, since its eval/profiling side produces exactly the "representative tests, baselines, robustness checks" the track asks for. Called the *BioNeMo Agent Toolkit* in the event brief; treat as the same product. |
| **GPT-Rosalind** | OpenAI | OpenAI's life-sciences model, with the **Rosalind Workbench** as its interface. | Likely the reasoning/hypothesis layer: interpreting results, proposing experiments, reading the literature, deciding what to run next. See the open question in §4. |
| **OpenAI models via API** | OpenAI | General frontier models. | Fallback for the reasoning layer if Rosalind doesn't fit the task. Weaker on criterion 2 than Rosalind, since it's the same thing every team has. |

### The rule this gives us

A project scores well on criterion 2 when you can point at the architecture diagram and
say: *this box is BioNeMo, this box is the Agent Toolkit, this box is Rosalind, and if you
removed any of them the system stops working.* If the honest answer is "we used NVIDIA
GPUs and wrote it with Codex", that criterion is a 3 or 4, and it's a fifth of the score.

Corollary: the criterion says NVIDIA **and** OpenAI. A project built entirely on one
vendor's stack is exposed on this criterion even if it's excellent. Aim for at least one
load-bearing component from each.

## 3. Track-to-tool fit

> **INFERRED.** Tracks are from `Context/challengeWeb.md`; the mapping is ours.

| Track | Most natural in-product stack |
|---|---|
| **01 OSS Build** — modernise bioinformatics software | Weakest fit for criterion 2, since the deliverable is a repackaged tool. Needs a deliberate hook: wrap the tool as an Agent Toolkit tool, or add a BioNeMo-backed component, so there's something vendor-central to point at. |
| **02 Orchestration** — specialist models + deterministic tools into repeatable workflows | Strongest fit. Agent Toolkit as the spine, BioNeMo NIMs as the specialist models, Rosalind for the reasoning and human-decision points. Hits criterion 2 almost by construction. |
| **03 Benchmarking** — make performance and failure modes visible | Agent Toolkit's eval/profiling harness, BioNeMo models as the systems under test, Rosalind as either a system under test or the judge. Note Anna Gogleva (speaker) works specifically on *how agent reasoning fails* — a failure-mode benchmark has a sympathetic audience. |
| **04 Open Track** — smallest useful prototype around a real problem | Whatever fits, but pick the problem so that at least one BioNeMo/Rosalind component is load-bearing rather than bolted on afterwards. |

## 4. Open questions to resolve on day one

Ask a mentor or TA, then update this file:

- **What is GPT-Rosalind, concretely?** Is it an API, a hosted workbench UI, or both? Can
  it be called programmatically from inside a workflow, or is it an interactive research
  environment? This determines whether it can be a *component* of our system or only a
  tool we used while thinking. That distinction is worth real points on criterion 2.
- **Which BioNeMo models are available to us on Brev during the event**, and are they
  pre-pulled? NIM containers are large; a first-time pull can eat a meaningful chunk of a
  weekend.
- **What GPU are we allocated, and how many hours?** Sets the ceiling on anything that
  involves fine-tuning rather than inference.
- **Does "NVIDIA Agent Toolkit" here mean the general toolkit or a BioNeMo-specific
  distribution of it?** The brief says "BioNeMo Agent Toolkit", the prep page says
  "NVIDIA Agent Toolkit".

Model-derived details in §2 (product structure, capabilities) are from training data and
may be out of date — verify against the live docs and the on-site mentors before betting
the project on any of them.
