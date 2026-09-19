# Pitch and content pack

All copy is draft material for Scott to use. Nothing has been sent or posted. Team name and direction are provisional.

## Friday team pitch — about 55–60 seconds

I'm Scott, and I'd like to build AssayGuard: an agent that checks what a drug-discovery benchmark really tells us.

A model can score well when its test molecules resemble its training set. But a scientist needs to know whether that result holds for unfamiliar chemistry—and what evidence would change their confidence.

We have a small public-data baseline ready: it audits molecules, compares random and scaffold splits, and saves every result. This weekend, I'd like to connect OpenAI's scientific reasoning to those tools and use NVIDIA's molecular computing tools on Brev for the similarity checks.

The goal is a reproducible five-minute demo: one dataset, two evaluation policies, and a clear explanation of what we can and cannot conclude.

I'm looking for a computational chemist or biologist, an engineer comfortable with GPU tools, and someone who enjoys making scientific evidence understandable. If that sounds interesting, come find me.

If the organizers disallow pre-event code, replace the third paragraph with: “We have a focused plan using public data. This weekend we will build the audit, connect OpenAI's scientific reasoning to its tools, and use NVIDIA's molecular computing tools on Brev for the similarity checks.”

## Pitch signup row

- Person: Scott Ogden
- Affiliation: enter your preferred affiliation; not submitted automatically.
- Project idea: AssayGuard is an agent that audits molecular benchmark splits, checks train/test similarity, and produces a reproducible evidence brief before scientists trust a model score.

## Team recruiting message

I'm exploring AssayGuard for London AI × Bio: a small agentic workflow that audits molecular model evaluation, compares random/scaffold splits, and makes the evidence and limitations inspectable. A public-data CPU baseline is prepared; weekend work would connect an OpenAI agent and NVIDIA nvMolKit on Brev. Looking for a computational chemistry/biology teammate and an engineer interested in GPU workflows. Scope is one useful, reproducible demo. Happy to adapt around a stronger problem from the team.

## Five-minute presentation script

**0:00–0:45 · Slide 1 — problem.** “A benchmark number is only useful if its test matches the decision. AssayGuard helps a discovery team inspect that assumption before trusting a molecular model.” Describe unfamiliar chemistry as the motivating question; do not imply all random splits are invalid.

**0:45–1:35 · Slide 2 — workflow.** Show public BACE inputs, quality checks, fingerprints, two split policies, predictions and report. Explain the live OpenAI and NVIDIA roles only to the extent supported by the final trace and GPU result. As prepared, state: “The CPU audit works; the live adapters are ready for event integration.”

**1:35–3:20 · Demo.** Open the offline report, show the dataset count, all five seeds and the chart. If live integrations pass during the event, start from the agent's question and show its tool trace before the report. Keep the cached report available if venue Wi-Fi fails, and explicitly identify it as a saved run.

**3:20–4:20 · Slide 3 — results.** “Our initial run found mean ROC-AUC of 0.897 for random splits and 0.886 for scaffold splits. That is a modest gap. But roughly 66% of random-test molecules shared a scaffold with training data; scaffold holdouts removed that overlap and had greater score variability. The tool helps us inspect the evaluation, rather than forcing a failure story.” Mention that the test populations differ and the variation is across correlated splits.

**4:20–5:00 · usefulness and limits.** “This is a review step for a computational discovery team. It leaves behind the data hash, split membership, predictions and reasoning evidence. It does not establish prospective performance or clinical utility. Our next check is an independent assay and a stronger held-out-series evaluation.” Close with the actual completed contribution. The technical appendix remains available for judges, not part of the timed narrative.

## Judge Q&A

**Is scaffold overlap leakage?** Not automatically. It can make a test less representative of novel-series use. Exact duplicate/label leakage is a different issue; this file had no exact duplicates under our stated canonicalization.

**Is the drop significant?** We have not established that. Five repeated splits are correlated, and the test populations/sizes differ. We report a descriptive difference and sample SD.

**What is novel?** The proposed workflow and evidence trail, not the splitting algorithm. Usefulness and workflow originality still need to be demonstrated.

**Why a GPU on only 1,513 molecules?** This is a correctness and integration demonstration. We will report measured throughput, including transfers. A speedup is not guaranteed; larger independent workloads are needed for scaling claims.

**Why an agent rather than a script?** The script supplies numerical reliability. The agent's proposed value is making the workflow usable from a scientific question, choosing appropriate checks, and explaining limitations. The initial agent is deliberately narrow; compare its output with a human-reviewed checklist.

**Did you use GPT-Rosalind?** Say yes only after a recorded run with confirmed access. Otherwise: “Built with Codex; the live scientific-model integration remains pending.”

**How do we reproduce it?** Exact versions, data hash, fixed seeds, split membership and predictions are saved. The README reruns the audit. Add the team GitHub link before submission.

## Pre-event social draft

Heading to London AI × Bio at WilbeLABS this weekend, co-hosted by OpenAI and NVIDIA. I'm interested in a practical question: how can agents help scientists inspect the assumptions behind a model result, not just generate another score?

Exploring a small, reproducible molecular benchmark audit—and looking forward to testing the idea with scientists and builders. If you're there and interested in evaluation, computational chemistry or scientific workflows, let's compare notes.

## Post-event draft — fill only with actual outcomes

At London AI × Bio, our team built [final project name] to help [specific user] with [specific decision].

We tested [dataset and evaluation] and found [measured result, including an important caveat]. The most useful lesson was [actual lesson].

OpenAI contributed [verified role]; NVIDIA contributed [verified role]. Reproduction materials: [repository link].

Thanks to [actual teammates] and the organizers at WilbeLABS, OpenAI and NVIDIA. Next step: [concrete test].
