# Inspection record and source precedence

Review date: 19 September 2026. This is the evidence supporting the plan, not a claim that planned capabilities are implemented.

## Directly inspected

| ID | Location | Finding and scope |
| --- | --- | --- |
| E01 | Local project `AGENTS.md` | Synced `sources/` files are read-only; no edits made there |
| E02 | GitHub main, `ae2d11e59350c39d7f4adbd70ea79a59dbb3ee0b` | Event context and early plan portfolio; repository instructions read |
| E03 | GitHub docs branch, `8891b522386844db6bc7ee5b832a0198fd596d0e` | Newer scientific context, architecture, case-study and implementation documents; no prototype Python payload |
| E04 | Local `rosalind/` code and tests | Deterministic registry/ledger/HTTP adapters and synthetic workflow; no OpenAI dependency in its pyproject |
| E05 | Local `outputs/reference-architecture/` | Existing S00–S14 design, D00–D18 data packages, T01–T17 tools, four learning loops |
| E06 | Brev inventory and read-only shell | `agentic-takeoff-cpu` running, x86_64, 4 cores, 31 GiB memory, no usable GPU, large free root disk |
| E07 | Brev shared START-HERE/CURRENT_IMPLEMENTATION and catalog reports | Shared context and data delivery are present; catalog report records 469 assets and historical read-back |
| E08 | Brev Ana checkout and case-study folder | Checkout on main `ae2d11e`; separate ALK case-priority documents exist |
| E09 | Brev Leon BCMA README, input/case.json, validation.json, reviewer notes and file inventory | Prepared case with corrected identity/truncated-source handling; biological interpretation remains qualified |
| E10 | Selected system Python package metadata | Required new app/science packages absent in that interpreter; separate virtual environments exist |
| E11 | Installed and vendored BioNeMo Evo/Boltz instructions; prototype lock | Reference contracts and toolkit pin are available locally |
| E12 | Official OpenAI/NVIDIA pages | Model identity, SDK surfaces, hosted 7B forward endpoint, hardware and connectivity documentation verified |

The Brev inspection was read-only. No team source, input data, service configuration or GPU instance was changed. Commands were scoped to the project workspaces and shared files; credentials and unrelated account data were not read.

## Fresh execution evidence

Ran the existing local command:

```text
.venv/bin/python -m unittest discover -s tests -v
Ran 20 tests in 0.824s
OK
```

The first sandboxed run passed 19 tests but blocked the loopback HTTP test because socket binding was disallowed. A permitted rerun completed all 20 tests. These include a real HTTP exchange with a local fake service, not NVIDIA inference. No OpenAI or NVIDIA model call occurred.

I did not rerun the BCMA preparation script, inspect every matrix, rehash the complete 63 GB delivery, reproduce FACETS, or analyze TH266 expression. BCMA cell/variant counts in this plan are taken from its inspected validation report. The 469-file integrity statement is from the inspected stored verification report, not a new full audit.

The prototype source remains unchanged. New files produced by this task are planning artifacts and starting contracts under `outputs/agent-development-plan/`.

The planning package was also checked: JSON Schema definitions, the ALK manifest against its schema and current workbook hash, rejection of mismatched action routes and unknown arguments, SQLite schema creation, immutable decision behavior, cross-run feedback rejection, YAML parsing and disabled unverified capabilities, and internal Markdown links. The machine-readable [validation report](validation-report.json) records these checks. This validates the supplied design artifacts, not the unimplemented service.

The subsequent 19 September documentation revision makes the user's requested R&D feedback loop explicit and adds [the CAR-T modeling example](07-RD-FEEDBACK-LOOP.md). It updates requirements, architecture, tool contracts and estimates. The installed BioNeMo protein-binder-design skill and the NVIDIA sources below informed the modeling boundary. This revision ran no design campaign, live inference or laboratory experiment; the existing prototype test results above belong to the original review. Added design/outcome record schemas and migrations remain implementation backlog items.

A further documentation clarification establishes the user-supplied hypothesis as the starting point, accepted through a message, prompt, selected Markdown/text file or structured brief. It adds an optional input template, source/version requirements and scope-preservation acceptance criteria. The `HypothesisSpec` schema and runtime integration remain planned work; this edit does not claim that intake is implemented.

## Source precedence and conflicts

1. Current source bytes, exact case contracts and validated sample identities outrank broad narrative summaries.
2. The newer ALK study-priority/case documents resolve early source interpretation issues: missing TH266 baseline day, residual disease versus progression, assay units, and nucleotide-ID-specific ALK labels.
3. The live prepared BCMA package supersedes older claims that only the damaged GEO allele-count file was available. Its reviewer interpretation remains separate from investigator input.
4. GitHub's documentation branch is newer than main. The Brev shared START-HERE still contains an older note that a prior context commit could not be published. That historical note does not override the observed newer published docs branch.
5. Local prototype implementation status is established by inspected code and fresh offline tests. Architecture prose is not evidence that durable agents, feedback learning or live inference already exist.
6. The installed Evo skill emphasizes hosted generation and self-hosted forward. The separately verified NVIDIA hosted **7B forward** documentation supports a new explicit adapter; it does not change the existing adapter's behavior.
7. Use the exact Boltz image support matrix for deployment capacity. The toolkit's weight size alone understates total image/cache storage.

## Operational source locations

Project root:
`<LOCAL_AI_X_BIO_ROOT>`

Local implementation and design:

- `rosalind/rosalind/{core,nim,workflow,__main__}.py`
- `rosalind/{README.md,pyproject.toml,requirements-lock.txt}`
- `rosalind/docs/{IMPLEMENTATION.md,verification.json,upstream-lock.json}`
- `outputs/reference-architecture/{REFERENCE-ARCHITECTURE.md,DATA-AND-TOOLS.md}`
- `outputs/process-simulation-design/{HARNESS-DESIGN.md,graph-reference-extract.json}`
- `outputs/github-markdown-publication/repo/docs/research/case-studies/`
- `outputs/dataset-acquisition/alk-atlas/`

Brev:

- `/home/ubuntu/rosalind-shared-files/START-HERE.md`
- `/home/ubuntu/rosalind-shared-files/Context/`
- `/home/ubuntu/rosalind-shared-files/reference-architecture/2026-09-19/`
- `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/integration/{catalog.sqlite,data_catalog.tsv,catalog-summary.json,REMOTE-VERIFICATION.json}`
- `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/alk-atlas/`
- `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/gap-fill/longitudinal/maynard_prjna591860/`
- `/home/ubuntu/ana-workspace/rosalind-case-studies/`
- `/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19/{input,reference,source}/`

The earlier graph audit identifies the full local graph at `<LOCAL_GRAPH_ROOT>/model/graph.json`. This review read the architecture/register describing it, not the entire original graph. Start from the existing portable extract and verify its hash before packaging.

## Primary documentation used

| Source | Claim supported |
| --- | --- |
| [GitHub main](https://github.com/24edden/WilbeBioAIHack2026/tree/ae2d11e59350c39d7f4adbd70ea79a59dbb3ee0b) | Repository context and early planning |
| [GitHub knowledge library](https://github.com/24edden/WilbeBioAIHack2026/tree/8891b522386844db6bc7ee5b832a0198fd596d0e/docs) | Newer project architecture, implementation boundaries and case studies |
| [OpenAI models](https://developers.openai.com/api/docs/models) | GPT-Rosalind API ID |
| [OpenAI life sciences](https://learn.chatgpt.com/use-cases/collections/life-sciences) | Scientific specialization and access context |
| [OpenAI pricing](https://developers.openai.com/api/docs/pricing) | Rosalind token rates, billing date and approved research access |
| [OpenAI agent runtimes](https://developers.openai.com/api/docs/guides/agents) | SDK versus managed Agents API versus Responses |
| [SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart) | Python package/imports and basic tools |
| [SDK definitions](https://developers.openai.com/api/docs/guides/agents/define-agents) | Typed outputs, tools and local context |
| [SDK running agents](https://developers.openai.com/api/docs/guides/agents/running-agents) | Continuation/session/streaming semantics |
| [SDK models](https://developers.openai.com/api/docs/guides/agents/models) | Explicit model/provider configuration |
| [SDK orchestration](https://developers.openai.com/api/docs/guides/agents/orchestration) | Handoffs versus agents as tools |
| [SDK observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability) | MCP choices and tracing |
| [NVIDIA hosted Evo 2 7B forward](https://docs.api.nvidia.com/nim/reference/arc-evo2-7b-infer) | Exact URL, layer names, tensor shape and base indices |
| [NVIDIA Evo 2 40B support](https://docs.nvidia.com/nim/bionemo/evo2/2.0.0/prerequisites.html) | Self-hosted hardware requirements |
| [NVIDIA Boltz 1.6.0 support](https://docs.nvidia.com/nim/bionemo/boltz2/1.6.0/support-matrix.html) | GPU/CPU/RAM/storage/software requirements |
| [NVIDIA Boltz 1.6.0 inference](https://docs.nvidia.com/nim/bionemo/boltz2/1.6.0/inference.html) | Protein polymer/structure contract; ligand-affinity scope; R&D comparison adapter input/output boundary |
| [NVIDIA binder-design workflow](https://developer.nvidia.com/blog/accelerate-protein-engineering-with-the-nvidia-bionemo-blueprint-for-generative-protein-binder-design/) | General RFdiffusion → ProteinMPNN → complex-evaluation composition; not evidence of CAR-T efficacy |
| [NVIDIA Brev connectivity](https://docs.nvidia.com/brev/cli/connectivity) | CLI execution, private forwarding and tunnel behavior |
| [Pinned BioNeMo toolkit](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit/tree/0e67a612e4045f007e38fa77adc8f3ebfc5616b6) | Provenance of the locally inspected Evo/Boltz skill contracts |

The source publications, assay interpretation and case restrictions are already linked in the inspected project case documents. This task did not rederive their biological findings or use them as clinical advice.

## Decisions still to resolve

| Decision | Working assumption | When it must be resolved |
| --- | --- | --- |
| Product focus | Treatment-resistance investigator with explicit R&D feedback; ALK-first, CAR-T as the design-loop example | Before selecting the live demonstration packet |
| Deadline/team | Three engineers, two working days; reduced weekend option supplied | Before assigning W00–W11 |
| GPT-Rosalind entitlement | Unknown | W02; live model launch gate |
| NVIDIA entitlement and actual costs | Unknown | First live NIM probe/submission |
| Scientific reviewer | Not assigned | Before claiming scientific acceptance |
| Exact ALK construct/ligand mapping | Not yet qualified | W06; block molecular submission until valid |
| CAR-T target, reference/candidate and improvement endpoint | Not yet selected; use qualified target-retained scenario for the first comparison | W21; do not infer appropriate binder redesign from the BCMA loss case |
| Hosted NIM async retrieval behavior | Not live-validated | W07/W12; explicit pending/unknown until implemented |
| Code release location | Team repository; prototype promotion needed | W00 |
| External export/trace policy | Public approved case excerpts only; local traces by default | Before any private or controlled data enters the runtime |

None of these unknowns justifies inventing capability, biology or a successful result. They are explicit implementation gates with independent work available on either side.
