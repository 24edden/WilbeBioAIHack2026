# Rosalind investigation agent — engineering plan

Prepared 19 September 2026. **PRD + technical architecture + delivery plan, grounded in the inspected local workspace, GitHub, and the running Brev CPU machine.** This package specifies work to build; it does not claim the proposed agent has been deployed.

## Shared team locations

- GitHub: [agent development plan on the documentation branch](https://github.com/24edden/WilbeBioAIHack2026/tree/docs/project-knowledge-library/docs/architecture/agent-development-plan), included in [pull request #1](https://github.com/24edden/WilbeBioAIHack2026/pull/1).
- Brev CPU: `/home/ubuntu/rosalind-shared-files/agent-development-plan/2026-09-19/README.md` on `agentic-takeoff-cpu`; also linked from the shared `START-HERE.md`.

`<LOCAL_AI_X_BIO_ROOT>` means the original local Ai X Bio workspace; `<LOCAL_GRAPH_ROOT>` means its separately maintained process-graph directory. Set local paths for your own machine. Paths in inspection records describe the inspected environment. This package is an engineering specification with explicit implementation backlog items.

## Recommended implementation

Build a Python application using the **OpenAI Agents SDK**, with **GPT-Rosalind (`gpt-rosalind-research`)** as the intended scientific reasoning model. Run the application, deterministic analyses, job state, and evidence store on the existing **`agentic-takeoff-cpu`** Brev instance. Develop and replay small cases on the local Mac. Call NVIDIA-hosted BioNeMo NIMs from the CPU worker; add a separate Brev GPU machine only if hosted access or workload requirements justify it.

Start with **ALK L1196M assay adjudication**, then use the prepared **BCMA GSE164551** package to test patient-level ingestion. Keep **Maynard TH266 residual disease** as the harder follow-on case. Each is a separate case pack with its own scientific question and limitations.

**The hypothesis to investigate is supplied by the user**, through a direct message, a prompt, a user-selected Markdown/text file, a structured brief, or a combination of these. The agent preserves that hypothesis and its source, clarifies material ambiguities, and investigates it. Agent-proposed alternatives and follow-on design hypotheses are labeled separately; they do not silently replace the user's research objective. A [hypothesis input template](contracts/hypothesis-template.md) is included.

The first useful product takes that hypothesis, its investigation question and a pinned case packet, checks the data, evaluates competing explanations, performs justified analyses, challenges its draft, and produces a source-linked decision with a discriminating next experiment. **One required output is an R&D design package:** turn the findings into a testable therapy-improvement proposal within the supplied objective, use BioNeMo to model eligible molecular designs, and return the designs, predicted structures, comparisons and proposed experiments to the research team. The team's measurements feed the next investigation and design round. A scientist can also correct the exact decision and obtain a new version.

**The intended process is: user-supplied hypothesis + available evidence → investigation → design objective → BioNeMo structural modeling → R&D candidate/test package → experimental results → updated assessment and proposed next designs.** CAR-T is the worked example: predict and compare a candidate CAR antigen-binding domain bound to its target, then ask R&D to test whether the proposed change improves the relevant measured endpoint. This models a molecular component/interface; it does not simulate an entire CAR-T cell or establish that the therapy is better. The [R&D feedback-loop specification](07-RD-FEEDBACK-LOOP.md) defines the outputs, return path and engineering work.

## Read and implement in this order

| Document | Purpose |
| --- | --- |
| [01 — PRD](01-PRD.md) | Users, scope, case choice, requirements, user journey, success criteria |
| [02 — Technical architecture](02-ARCHITECTURE.md) | Components, execution flow, OpenAI SDK integration, persistence, recovery, APIs |
| [03 — GPT-Rosalind and BioNeMo](03-MODELS-AND-TOOLS.md) | Verified features, capability gates, exact tool contracts, scientific boundaries |
| [04 — Local and Brev runbook](04-LOCAL-BREV-RUNBOOK.md) | Paths, environments, deployment profiles, startup contract, GPU option |
| [05 — Delivery backlog](05-DELIVERY-PLAN.md) | Work packages, dependencies, owner roles, estimates, acceptance checks, scope cuts |
| [06 — Verification and sources](06-VERIFICATION-AND-SOURCES.md) | What was actually inspected/tested, source precedence, unresolved decisions |
| [07 — R&D feedback loop and CAR-T example](07-RD-FEEDBACK-LOOP.md) | Evidence → candidate structures → R&D experiments → next design round; concrete records and acceptance gates |
| [Contract files](contracts/README.md) | Initial JSON schemas, SQL schema, example configuration, and an example case manifest |
| [Validation record](validation-report.json) | Package consistency, schema, database, and prototype-test checks |

## What is already real

- Local `rosalind/` contains a deterministic BioNeMo prototype: validated tool routing, an evidence ledger, Evo 2 generation/scoring adapters, and a paired protein-complex Boltz-2 adapter. **All 20 existing offline/loopback tests passed in this review.**
- Brev has **4 CPU cores, 31 GiB reported RAM, approximately 973 GB free disk**, Python 3.10.12, Docker, and no working NVIDIA GPU. No running Docker containers were shown during inspection.
- The shared catalog reports **469 assets / 63,435,795,039 bytes**, with a saved successful SHA-256 read-back at 13:55 UTC. I inspected that report; I did not rehash all 63 GB.
- Leon's prepared BCMA case contains an input manifest and validation records, including the corrected S5/S6 mapping and replacement for a truncated allele-count source.
- GitHub `main` is `ae2d11e`. The newer documentation is on **`docs/project-knowledge-library` at `8891b522`**. That branch contains documentation, not the prototype Python source. The inspected Brev checkout still tracks `main`.

## Decisions and assumptions

The requested model is interpreted as GPT-Rosalind. Access to it and to NVIDIA endpoints remains **unverified**, because this planning review made no live inference calls. OpenAI's official catalog establishes the model ID; public documentation does not establish all model-specific runtime limits. The first implementation milestone probes the exact account/model/tool combination.

The initial delivery including an explicit R&D handoff is estimated at **36–52 engineer-hours**: the original 33–47-hour investigation slice plus 3–5 hours for the design brief and handoff. The first CAR-T structural comparison and measured-outcome return add **9–16 hours**, plus 4–6 hours if the BCMA case adapter is included. Candidate preparation, domain review, actual laboratory work and entitlement delays are outside those estimates. The delivery plan distinguishes these increments from the first demonstration.

Pending answers to the questions sent during review, the schedule assumes **three engineers, two working days for the first vertical slice, no wet-lab access, and a five-minute hackathon demo**. A shorter remaining weekend has a defined reduced scope in the delivery plan. The proposed product is a treatment-resistance research workflow, following the newer project documents; the platform remains extensible through case packs.

**Critical first actions:** bring the prototype code into the team's repository, create an isolated runtime on Brev, validate GPT-Rosalind tool calling, prepare the ALK source packet, and implement durable action records. Hosted Evo 2 7B forward support and ALK–ligand Boltz support are explicit adapter tasks, not existing capabilities.

The plan uses the [OpenAI Agents SDK runtime](https://developers.openai.com/api/docs/guides/agents) and the [official GPT-Rosalind model listing](https://developers.openai.com/api/docs/models). The [hosted Evo 2 7B forward endpoint](https://docs.api.nvidia.com/nim/reference/arc-evo2-7b-infer) provides a potential CPU-hosted application path, subject to entitlement and a successful contract test.
