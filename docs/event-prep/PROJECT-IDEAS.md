# Six project directions

Recommendation: **AssayGuard**, unless a teammate brings a compelling, ready-to-use dataset and domain problem. This is a judgment about weekend feasibility, not a prediction of the winner. Do not commit the team before Friday's discussion.

| Rank | Idea and user | Weekend demonstration | OpenAI role | NVIDIA role | Main risk |
|---|---|---|---|---|---|
| 1 | **AssayGuard** — computational discovery teams auditing molecular benchmarks | Compare random/scaffold splits on BACE; retain evidence; agent explains what changes | Tool selection, evidence review and bounded follow-up planning | nvMolKit similarity/fingerprinting on Brev; parity and timing | Needs meaningful live agent/GPU work beyond the existing CPU baseline |
| 2 | **Evidence-to-assay brief** — scientist deciding what evidence to inspect next | One target, small cited evidence set, contradictory claims and ranked information gaps | Structured evidence extraction and synthesis | Specialist BioNeMo model on a tightly scoped public example | Can become a generic literature chatbot; relevance must be defined by a scientist |
| 3 | **Protein model scorecard** — researcher interpreting structure predictions | Fixed public, benign proteins; inspect confidence, failure modes and reproducibility | Select tools and translate model outputs into qualified conclusions | BioNeMo structure model through a provided endpoint | Provisioning, model runtime and misleading confidence claims |
| 4 | **Omics analysis concierge** — biologist with a small public expression dataset | Reproduce a known QC/analysis workflow with an inspectable report | Plan and explain analysis; surface assumptions | GPU analysis only where a matching library/workload justifies it | Batch effects and biological interpretation may dominate the weekend |
| 5 | **Hypothesis courtroom** — researcher comparing mechanistic explanations | Small hand-reviewed claim set; supporting/contradicting evidence; explicit abstention | Challenge hypotheses with cited evidence and bounded revisions | A specialist model supplies an independent computational observation | Subjective evaluation; GPU may be incidental without a strong example |
| 6 | **One-tool rescue** — scientist blocked by brittle legacy bioinformatics | Fix one real reproducibility issue; container, tests, example and coding-agent instructions | Codex implementation and user-facing workflow | NVIDIA-backed acceleration if the tool supports it | Finding a useful, bounded issue and satisfying both-platform criterion |

## AssayGuard: the minimum useful product

**Question:** What does this molecular model's benchmark score tell us about performance on unfamiliar chemical frameworks?

**Inputs:** public SMILES + binary assay labels. Start with one endpoint, one fixed classifier and two split policies. Do not expand into molecule generation, wet-lab execution or an entire discovery platform.

**Outputs:** data-quality summary; split overlap; ROC-AUC, average precision and Brier score; nearest-training similarity; exact predictions and split membership; an agent-written review whose numbers point to saved evidence.

**What makes it agentic:** the live runner inspects inputs, chooses from bounded scientific tools, observes results/errors, and produces a qualified next-step recommendation. The current runner supports a narrow tool sequence. Adaptive follow-up selection and broader recovery are stretch work, not current capabilities.

**Why NVIDIA belongs:** pairwise molecular comparison is a natural batched workload. Use nvMolKit to calculate similarity, verify parity against RDKit, and connect those results to the audit. Small BACE runs may not be faster on GPU; measure honestly. A larger, separately sourced public panel can test scaling if time permits.

**Why OpenAI belongs:** turn a scientific question into an auditable sequence of tool calls and a decision brief. Have the scientist evaluate whether the brief detects caveats that a single model score hides. Codex also builds/tests the reproducible workflow; distinguish this from a live GPT-Rosalind inference claim.

## Honest differentiation

Scaffold splits, molecular fingerprints, random forests and leakage diagnostics already exist. The proposed contribution is a reusable agent workflow that makes these checks accessible, joins CPU/GPU numerical evidence to a review, and preserves a complete run manifest. Validate this usefulness with a domain teammate. Avoid claiming “first,” a novel splitting method, or a newly discovered drug.

## Cut line

By Saturday noon, if live OpenAI access or NVIDIA setup is blocked, get a mentor to resolve the specific blocker. Keep the working deterministic demo. If still blocked by late afternoon, present it honestly as a narrower benchmark prototype; it would remain weaker on the equally weighted technology criterion. Never relabel cached CPU output as a GPU or Rosalind run.
