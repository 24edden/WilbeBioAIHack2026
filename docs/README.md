# Project knowledge library

Research and planning documents collected on 19 September 2026 from the local Ai X Bio project, the shared Brev workspace, and Ana’s case-study folder. This publication contains documentation, proposed JSON/SQL/YAML application contracts and reusable skill templates. Dataset payloads, prototype code, credentials, private arrival details, and binary artifacts are not included.

## Start here

1. [Agent development plan](architecture/agent-development-plan/README.md): current PRD, architecture, local/Brev runbook, backlog and starting contracts; user-supplied hypothesis → investigation → BioNeMo design comparison → R&D experiments → measured feedback.
2. [Implementation status](implementation/shared-context/CURRENT_IMPLEMENTATION.md): what the prototype record reports, and which capabilities remain proposals.
3. [Study priorities](research/case-studies/STUDY_PRIORITIES.md): the two ALK cases, followed by BCMA, CD20 and CD19 options.
4. [Scientific hypotheses](../Context/TRANSLATIONAL_SCIENCE_HYPOTHESES.md): competing mechanisms and experiments.
5. [Reference architecture](architecture/reference-architecture/2026-09-19/REFERENCE-ARCHITECTURE.md): earlier roles, evidence, decisions and feedback design.
6. [Dataset landscape](datasets/DATASET-LANDSCAPE.md) and [remaining data gaps](datasets/2026-09-19/GAPS.md).
7. [How to use BioNeMo for CAR-T](HOW-TO-USE-BIONEMO.md): skill priorities, target-retention requirements, molecular inputs, binder design and experimental validation.

## Browse by topic

| Topic | Documents |
| --- | --- |
| Case studies | [Easy: ALK L1196M](research/case-studies/HYPOTHESIS_01_EASY_ALK_L1196M.md); [open: TH266 residual disease](research/case-studies/HYPOTHESIS_02_HARD_MAYNARD_TH266.md); [priorities and evaluation](research/case-studies/STUDY_PRIORITIES.md) |
| Agent design | [Current engineering plan](architecture/agent-development-plan/README.md); [CAR-T R&D feedback loop](architecture/agent-development-plan/07-RD-FEEDBACK-LOOP.md); [earlier architecture](architecture/reference-architecture/2026-09-19/REFERENCE-ARCHITECTURE.md); [data and tool register](architecture/reference-architecture/2026-09-19/DATA-AND-TOOLS.md); [simulation harnesses](architecture/simulation/HARNESS-DESIGN.md); [scientist-feedback learning loop](../Context/AGENTIC_SCIENTIFIC_LEARNING_LOOP.md) |
| Datasets | [Landscape](datasets/DATASET-LANDSCAPE.md); [acquisition guide](datasets/2026-09-19/START-HERE.md); [source catalog](datasets/DATASET-LANDSCAPE.md); [delivery record](datasets/2026-09-19/DELIVERY-REPORT.md); [gaps](datasets/2026-09-19/GAPS.md) |
| Implementation records | [Shared context](implementation/shared-context/START-HERE.md); [prototype guide](implementation/prototype/README.md); [detailed implementation record](implementation/prototype/docs/IMPLEMENTATION.md) |
| Reusable skills | [Skill guide](../skills/README.md); [agent harness building](../skills/agent-harness-building/SKILL.md); [benchmark creation](../skills/benchmark-creation/SKILL.md); [harness research playbook](../skills/agent-harness-building/references/harness-playbook.md) |
| Event preparation | [Preparation guide](event-prep/START-HERE.md); [project portfolio](event-prep/PROJECT-PORTFOLIO.md); [build plan](event-prep/BUILD-PLAN.md); [pitch/content drafts](event-prep/CONTENT.md); [earlier team planning](../Plan/README.md) |
| Provenance | [Every source and its published location](SOURCE-INVENTORY.md); [historical local snapshots](archive/local-snapshots/) |

## Reading the snapshots

These files preserve work at different stages. Event-preparation documents describe earlier candidates such as AssayGuard; they are not a declaration of the current team choice. Prototype test counts and delivery records are historical reports, not checks rerun during this publication. The case studies are proposed analyses, not completed biological findings.

For the two-case plan, the specific case-study documents and their source-workbook corrections take precedence over broader earlier hypothesis narratives. In particular, preserve the P1153R screen-versus-validation distinction and the TH266 residual-disease timing correction in the study-priorities document.

Exact duplicates have one published copy. Distinct historical local versions remain in the archive. The source inventory records original hashes; publication copies have portable Markdown links and generic placeholders for personal Mac paths. Brev paths remain operational references to external data. References to unavailable non-Markdown artifacts are explicitly labelled.
