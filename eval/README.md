# Evaluation runner

From the repository root, using the existing Python environment:

```powershell
.venv/Scripts/python.exe -m eval --output eval/results/comparison-001.jsonl
.venv/Scripts/python.exe -m pytest tests/test_evaluation.py -q
```

No additional dependencies, GPU or keys are needed for the default mock comparison.
Choose a fresh output filename for every run. Use `--manifest`, `--configurations`,
`--concurrency` (1–16), `--repeats` (1–20), and `--timeout` to configure a comparison.
Output is one JSON record per case/configuration/repetition, written as trials finish.

The runner depends only on an adapter's async `run(inputs, config) -> Outcome` method;
optional `snapshot()` preserves partial measurements on errors/timeouts. Each trial
gets a fresh adapter and deep-copied inputs. Expected labels are passed only to the
grader. Replace `InvestigationAdapter` or supply your own factory to `compare()` when
the backend changes. This isolates coroutine failures, not arbitrary executed code;
terminal tools require separate sandbox infrastructure.

Example live configuration file, after substituting accessible model identifiers:

```json
[
  {"id":"candidate-a", "settings":{"run_mode":"live", "reasoning_model":"MODEL_A", "reasoning_api":"responses", "specialists":["clinical"], "reasoning_max_output_tokens":4000}},
  {"id":"candidate-b", "settings":{"run_mode":"live", "reasoning_model":"MODEL_B", "reasoning_api":"responses", "specialists":["clinical"], "reasoning_max_output_tokens":4000}}
]
```

`--live` explicitly enables billable calls; both credentials and endpoint settings
remain environment variables. CLI configuration does not load `.env` automatically.
The shown one-specialist roster often abstains under the current gate; select a frozen
roster appropriate to the task before comparing models. Model identifiers above are
placeholders, not claims of availability.

Tokens are provider-reported reasoning usage, not whole-system billing. Missing token
fields remain null; mock zeros mean no token-consuming inference. Cost, scientific
correctness and entailment are not assessed. Read
[the evaluation recommendation](../Plan/model-evaluation.md) before presenting scores.

Saved artifacts include source references and reports; use synthetic/publicly permitted
evaluation inputs. Keep secrets out of configuration dictionaries. Input file checksums
and code revision are recorded; commit/archive a dirty working tree before claiming
an exactly reproducible published result.
