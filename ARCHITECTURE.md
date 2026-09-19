# Architecture — Patient failure-investigation agent system

> Written by the `main` session for the `hack-infra` session. This worktree owns the
> **backend**: FastAPI service, orchestration, providers, event emission. The
> `hack-frontend` worktree owns the Streamlit UI. **The shared contract between the two is
> the event schema below — treat it as the interface and don't change it unilaterally.**

## What the system does

Upload patient files (VCF, labs CSV, clinical notes). Ask a question or state a hypothesis
in a chat box — "Why did this patient fail?" / "Did the patient fail because of X?". An
orchestrator agent decomposes the question, spawns specialist agents that investigate in
parallel, they communicate, and a critic/synthesis agent produces a verdict **with a
confidence level and an explicit ABSTAIN when the evidence is thin**. The UI shows the
agents spawning and messaging live, then the final report with provenance.

The framing is deliberate: this is *failure analysis*, which is the originality thesis of
the whole project (a working workflow + an honest account of when it breaks). The critic /
abstention step is what separates this from "an LLM guesses" — protect it.

## The two seams that carry the design

### 1. Provider interface — this is mock mode

Every model/tool call goes through a provider. Two implementations, chosen by `RUN_MODE`:

- `RUN_MODE=live` → real BioNeMo NIM calls / Rosalind / OpenAI.
- `RUN_MODE=mock` → returns fixtures keyed by input, with **simulated latency** so the
  agent graph animates realistically.

In mock mode the **real orchestrator still runs** — real agent spawning, real control flow,
real events — only the model *outputs* are faked. This gives the full visual with zero
tokens and no GPU/Rosalind dependency. It is both the daily dev loop and the token-free
rehearsal path.

```
ReasoningProvider   .plan() .step() .synthesize()      live: Rosalind/OpenAI | mock: fixtures
BioProvider         .score_variant() .embed() ...      live: BioNeMo NIMs    | mock: fixtures
```

A factory reads `RUN_MODE` and returns the right impl. Nothing above the provider layer
knows which mode it's in.

### 2. Event bus — this is the visualization

Every agent action emits a structured event onto a stream. The UI subscribes via SSE and
renders the live graph + timeline. The engine never imports or knows about the UI. This is
also why `hack-infra` and `hack-frontend` can be built independently.

## Event schema (SHARED CONTRACT — coordinate changes with hack-frontend)

```json
{
  "type": "run_started | agent_spawned | agent_message | tool_call | tool_result | finding | run_complete | error",
  "ts": 1234567890,          // ms, monotonic within a run
  "run_id": "uuid",
  "agent_id": "genomics-1",
  "agent_role": "orchestrator | genomics | literature | clinical | stats | critic",
  "parent_id": "orchestrator-0 | null",   // who spawned it / who a message is to
  "payload": {}              // message text, or {tool, args}, or {finding, provenance[], confidence}
}
```

`finding` payloads carry `provenance` (source refs — file+line, PMID+sentence, NIM output
id) and a `confidence` in [0,1]. The final `run_complete` payload carries the synthesized
verdict, overall confidence, and an `abstained` boolean.

## Transport (FastAPI)

- `POST /investigate` — body: `{question, file_ids}` → returns `{run_id}`. Kicks off the run.
- `GET  /events/{run_id}` — Server-Sent Events stream of the schema above.
- `GET  /report/{run_id}` — final structured report (also derivable from the event log).
- `POST /upload` — accepts patient files, parses to a normalized `PatientBundle`, returns ids.

SSE (not WebSocket) because the event flow is one-way engine→UI and SSE is far simpler to
build and reproduce. Chat submit is a plain POST.

## Agents

| Role | Job | Provider used |
|---|---|---|
| Orchestrator / Planner | Parse question + PatientBundle, plan sub-investigations, spawn specialists | ReasoningProvider |
| Genomics | Variant scoring / annotation | BioProvider (BioNeMo NIM) |
| Literature | Embedding search over a corpus subset for supporting/contradicting evidence | BioProvider (embed) |
| Clinical | Reason over uploaded labs/notes/history | ReasoningProvider |
| Stats (optional) | Cohort comparison if multiple patients uploaded | deterministic |
| Critic / Synthesis | Cross-check findings, produce verdict + confidence, **ABSTAIN if evidence thin** | ReasoningProvider |

## Orchestration spine

Use the **NVIDIA (NeMo) Agent Toolkit** as the spine — agent composition, tool calling,
tracing, eval. Its trace/observability output is the natural source for the event stream;
tap it rather than hand-rolling a parallel event system if the Toolkit exposes hooks.

> Verify on-site (open questions in `Context/tooling.md`): whether the Toolkit exposes
> per-step callbacks we can turn into events, and whether Rosalind is callable
> programmatically. If the Toolkit fights back, fall back to a plain async orchestrator that
> emits events directly, and keep the Toolkit for tracing only — note it honestly on the
> slide (costs a point on Tech, saves the project).

## Criterion-2 mapping (both vendors load-bearing)

- **NVIDIA**: Agent Toolkit = spine; BioNeMo NIM = genomics specialist. Remove either → no
  orchestration / no real bio prediction.
- **OpenAI**: GPT-Rosalind = orchestrator reasoning + critic. Remove it → no planning, no
  synthesis.

## Build order (risky-first, per Plan/01-weekend-timeline.md)

1. **Skeleton**: event schema + FastAPI SSE + a run that emits 2 fake agents end-to-end,
   rendered in the UI. Prove the pipe before anything else.
2. **Mock provider**: full investigation animates in `RUN_MODE=mock`. This is the demoable
   MVP — built before spending a token or needing GPU/Rosalind confirmed. De-risks the
   `tooling.md` open questions directly.
3. Wire **one** real specialist (Genomics via BioNeMo) behind the live provider.
4. Add Rosalind orchestrator + critic/abstention.
5. More specialists only if time allows. Feature-freeze at Sat 18:00.

## Data layer

Uploaded files → normalized `PatientBundle` (parsed VCF, labs table, free-text notes).
Cache any deterministic annotation lookups to a static file so live runs don't refetch.
Fixtures for mock mode live under `fixtures/`, keyed so a given PatientBundle + question
replays a consistent investigation.
