# Team TBD

**Repository release:** start with [SETUP.md](SETUP.md) for the isolated backend
environment, required external source hydration, optional proprietary plugin
installation and safe offline checks. This directory is the authoritative engine
behind the new frontend; the repository-root legacy `app/` is a different service.
The handbook below describes a hydrated private installation. Historical service
receipts are preserved as documentation, not included live runtime data.

A scientific investigation workbench: **user hypothesis → scoped analysis → specialist handoffs → independent review → selected next test → accepted evidence → revised decision**. Wet-lab experiments remain proposals until actual measurements return.

The scientist supplies the question in a message or imported brief. Its wording, source and hash remain intact. The website shows persisted work, source locators, actual model usage, blocked branches and decision history.

## Start locally

Requires Python **3.12 or newer**. From this directory:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
cp .env.example .env
.venv/bin/python -m app doctor
./scripts/start.sh
```

Open **http://127.0.0.1:8080**. If this workspace is already configured, keep its private `.env` and run `./scripts/start.sh`; do not overwrite credentials with the template.

Live investigation is selected by default. A successful explicit connection probe is required before a live run. The optional **Offline walkthrough · no model calls** uses pinned source evidence and a scripted interpretation. It is selected explicitly and cannot adjudicate an edited hypothesis.

## Model identity and credentials

The user authorized **GPT-6 Astra with high reasoning as a temporary GPT-Rosalind placeholder**. Configure the server's private `.env` for that mode:

```dotenv
OPENAI_API_KEY=your-project-key
TEAM_TBD_MODEL=gpt-6-astra
TEAM_TBD_BUDGET_MODE=advisory
TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS=24000
TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS=48000
TEAM_TBD_MAX_INPUT_TOKENS=2000000
TEAM_TBD_MAX_OUTPUT_TOKENS=300000
NGC_API_KEY=your-nvidia-key
ROSALIND_MAX_SECONDS=1200
ROSALIND_MAX_TOOL_CALLS=80
```

For an entitled GPT-Rosalind account, explicitly set `TEAM_TBD_MODEL=gpt-rosalind-research` and verify it. The selected model is never silently substituted. The website distinguishes configured identity from actual returned model/request metadata; an Astra result is not a GPT-Rosalind result.

`TEAM_TBD_MODEL` takes precedence over legacy `ROSALIND_MODEL`. A nonempty private `.env` value overrides the inherited environment; blank template values do not erase exported credentials. `NVIDIA_API_KEY` is accepted when `NGC_API_KEY` is absent. Restart after changing server configuration. Keys stay off the browser and exports. The research engine panel shows the configured usage thresholds. Shared budgets generate alerts and allow work to continue by default; select `TEAM_TBD_BUDGET_MODE=enforced` to stop at them. The per-response API output allowance includes reasoning tokens and remains a real response limit. Stage scope, scientific acceptance, cancellation and provider errors still apply. Coordinator/reviewer use a separate 48,000-token synthesis allowance by default; specialists receive 24,000. An explicitly selected [synthesis recovery](docs/SYNTHESIS-RECOVERY.md) can reuse seven verified handoffs after a known coordinator output-limit result, while unknown submissions remain ineligible.

The connection probe makes a small real model/tool round trip. A configured key or successful model-list request alone does not prove inference access. See [provider contracts](docs/PROVIDERS.md) and the [validation record](docs/VALIDATION.md) for implementation details and the evidence actually collected.

The [scientific red-team review](docs/SCIENTIFIC-REDTEAM.md) evaluates the reasoning and final answer separately from software checks, including the weight given to NVIDIA predictions, competing explanations and the proposed next experiment.

## Investigation and data

- **CAR-T discovery**, when its registry is installed, inventories registered Brev collections. The model chooses question-relevant files, inspects schemas and requests bounded executable analyses. Indexed files are not automatically all read or analyzed.
- **CD19 CAR-T**, **ALK L1196M** and **BCMA** retain compact, source-pinned cases for focused questions. The CD19 hypothesis preserves the team's Brev source text.
- Seven specialist roles, a coordinator and an independent reviewer produce structured work products. Clinical science can frame the research question without a patient timeline, while patient-specific claims remain blocked. Pharmacology records a blocked product without model inference when actual exposure data is absent.
- The reviewer can request bounded follow-up diagnostics for a concrete gap and reassess returned evidence. Decisions and tool choices can vary; numerical results are computed by approved tools.
- The **Skills** view shows registered workflow versions and persisted load receipts. A loaded skill is distinct from a model call, a completed analysis and scientific validation.
- Specialists receive the case's actual analysis and BioNeMo options early and can pass source-qualified proposals through accepted handoffs. Molecular science consumes bioinformatics mapping/QC; the coordinator and reviewer prioritize or explain deferral. See [discovery planning](docs/DISCOVERY-PLANNING.md). A proposal itself does not execute work.
- New live runs track **possible**, **probable** and **clearly ruled out** hypotheses within an explicit evidence scope. Under their pinned policy, the reviewer can select one qualified registered follow-up, then the team reviews its accepted result and decides whether to continue. Missing data and failed tests do not rule out a mechanism. See [hypothesis governance](docs/HYPOTHESIS-GOVERNANCE.md) for stopping rules, history, manual selection and cancellation. Older runs retain their original execution policy.

The dashboard includes a source catalog, nine-role architecture, event trail, evidence locators, work products, decisions, R&D handoff, correction and outcome forms, and Markdown/JSON exports. User-written or imported hypotheses survive changing the selected evidence collection.

Completed investigations lead with concise **findings and insights**: what was found, why it matters, cited evidence and the next step. **Follow-up analyses** turn model recommendations or registered methods into executable actions. Each action is tied to the current decision, validates its source versions, accepts the computed evidence and returns through specialist and independent review to create a new decision version. See [follow-up contracts](docs/FOLLOWUPS.md).

**Explain these results** generates a separate, independently AI-reviewed **Working answer**: the best-supported explanation, simple specialist findings, why decisions changed, what NVIDIA added and the next discriminating test. A read-only molecular audit supplies exact sequences and checks the existing structures and request records. A saved brief automatically fills verified molecular fields only while the form is untouched; **Prepare from this investigation** can explicitly reapply them. Missing binder sequences remain absent, and target retention is never asserted automatically. Historical decisions remain unchanged. See [research interpretation](docs/RESEARCH-INTERPRETATION.md).

**Find missing sequences with AI** uses the installed OpenAI UniProt/RCSB source skills, exact deposited sequences and independent model review to prepare molecular fields. The architecture panel distinguishes applied Team TBD Rosalind-informed guidance, installed OpenAI/NVIDIA skills and the actual Astra model. See [sequence discovery and private plugin setup](docs/SEQUENCE-DISCOVERY.md), [model capacity](docs/MODEL-CAPACITY.md) and [Ana’s paired study](docs/GSE28460-PAIRED-DATA.md).

For CD19, the paper-guided discovery recipe qualifies the wild-type controls before estimating variant–splicing effects. A missing row in a variant-only table is not automatically an unidentified construct. Historical results are preserved; an old source snapshot may require a fresh investigation before using newly registered evidence.

[Stage contracts and evaluations](docs/STAGE-CONTRACTS.md) specify each role's inputs, tool authority, acceptance checks, one-repair limit, diagnostic loops and stopping conditions. The Work products view exposes the actual persisted checks; accepted software contracts do not establish scientific validity.

## BioNeMo branch

A real NVIDIA service check returned a validated structure on 19 September 2026. The live CD19 follow-up also returned two verified public-isoform predictions, with actual coordinates, request receipts and a separate scientific evidence record; see [execution and scope](docs/NVIDIA-STRUCTURAL-FOLLOWUP.md). [Its receipt and reproduction guide](docs/BIONEMO-SERVICE-CHECK.md) distinguish that engineering monomer example from a qualified CAR-T comparison.

The app now renders actual returned structure coordinates with rotatable backbone views and artifact fingerprints. The [public CD19 isoform follow-up](docs/NVIDIA-STRUCTURAL-FOLLOWUP.md) offers a separate source-qualified comparison of normal and exon-2-deleted ectodomains. It predicts structural context; it does not simulate splicing, cell trafficking, CAR recognition or efficacy.

See [How to use BioNeMo for our CAR-T project](docs/HOW-TO-USE-BIONEMO.md) for skill selection, required inputs, and the investigation-to-design workflow.

Boltz-2 is the implemented molecular comparison path. Supply exact target, reference binder and candidate binder sequences, provenance and target-retained attestation. A live run can request a relevant comparison from qualified intake inputs; the R&D form also supports an explicit comparison after a decision. Real requests may incur provider usage.

The executor preserves action intents and input hashes, checks returned structure content against submitted sequences, and publishes matched artifacts only after validation. Missing constructs, failed jobs and incomplete pairs remain visible. Bundled hypothesis packets do not invent molecular constructs. No live NIM success is claimed solely from adapter tests or a configured credential. Structural confidence is not measured affinity or CAR-T efficacy.

## Corrections and learning

Corrections and exact experiment/candidate-linked outcomes create a new operation and immutable decision version while preserving the original objective. Submitted measurements are labeled `user_report`; identity checks do not establish experimental validity.

The **Learning** view proposes case-derived procedures with conditions and scope. Reuse requires attributed scientist review, matching baseline/candidate runs on a disjoint case, an excluded-case check and explicit release. Live and offline modes cannot mix. Released guidance stays procedural, can be suspended, and is never evidence for a biological claim. See [handoff](docs/HANDOFF.md) for the release API.

## Verify and present

```sh
.venv/bin/python scripts/check.py
.venv/bin/python casepacks/build_cases.py --check
.venv/bin/python -m app doctor
.venv/bin/python -m app verify-export path/to/export.json
```

Tests use isolated runtime state and mocked vendor transports where stated. They do not prove vendor entitlement or scientific validity. Follow [the presentation guide](docs/DEMO.md); model calls vary in duration, so keep a completed real run available beside the new live run.

## Deploy and maintain

See the [Brev runbook](docs/BREV.md), [engineering handoff](docs/HANDOFF.md), [scientific boundaries](docs/SCIENCE.md) and [case provenance](casepacks/README.md). The same service can run on Brev with hosted endpoints; the website itself does not require a GPU. Existing shared data and research workspaces remain read-only.

This is a private, single-team service. Bind to loopback and use a private tunnel. Public authentication, multi-tenant authorization, arbitrary model-generated code execution, automatic vendor-job reconciliation and clinical validation are outside this release.
