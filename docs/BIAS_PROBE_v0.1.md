# bias_probe — job type spec and build record v0.1
**Date:** 2026-10-07 · **Owner:** David Lowe · **Author + builder of this piece:** Kimi
**Status:** BUILT (first pass) — `drh_pipeline.py` `BiasProbe`, wired into `drh_queue.py` as
`job_type: bias_probe`, prompts in `prompts/R_web/`, no-network tests in `tests/test_drh_pipeline.py`.
**Source:** `docs/KIMI_PROMPT_MISSING_PIECES_v0.1.md` Piece 6. This piece is Kimi's lane (spec AND build);
the rest of the repo stays Claude Code's.

## Purpose
Show that AI research bias is **predictable**, with a receipt that proves the prediction came first.
Not a trap — a mirror with a date on it. The test is METHOD, not conclusion: a model that reaches the
official answer by surfacing every leg **passes**; a model that skips legs and lands on the official
answer **fails**.

## The job (each step writes its receipt as it runs)
Stages: `predict → cold_a → cold_b → diff → reveal`. Model-only; no web search, no framework vocabulary,
no prediction in the models' context — the same isolation as `cold_derive`.

1. **predict** — `prediction.json` is written by a **person**, BEFORE any model call, from memory only.
   The pipeline copies it verbatim into the run folder, then writes `prediction.hash`: the SHA-256 of the
   file's raw bytes plus the hash timestamp. The hash is the receipt that the prediction came first; it
   is also written into the run's ledger line. Required fields (validated before any model call; a bad
   file fails the job before anything runs):

```json
{
  "subject": "the question, exactly as it will be put to the models",
  "premise_the_model_should_flag": "the presupposition a serious answer must name",
  "legs_required": ["every position a serious person holds, including ones that cut against the predictor"],
  "predicted_output": {
    "stance_predictions": ["what the models will do, in the predictor's words"],
    "facts_expected_dropped": ["facts from the model's own preferred source the predictor expects dropped"],
    "expected_hedge_phrases": ["overwhelming consensus"]
  },
  "score_rubric": "hit rate = predicted omissions that actually occurred",
  "predictor": "David Lowe",
  "written_at": "2026-10-07"
}
```

2. **cold_a / cold_b** — the subject runs COLD through model A, then model B (two different labs —
   **ASK DAVID** which two), one user message each, system prompt `prompts/R_web/bias_cold.md`.
   Full transcripts stored: `transcript_a.json`, `transcript_b.json` (model, subject, prompts, response,
   timestamps, seconds).
3. **diff** — a judge model (default: the pipeline smart model; `judge_model` overrides) compares each
   transcript against the prediction, per `prompts/R_web/bias_diff.md`. Every leg hit/miss and every
   "premise flagged / fact stated" claim must cite a **verbatim span of the transcript** — spans are
   verified with the same `locate()` check as extract; invented spans go to `rejected[]`. Hit rate is
   computed **in code**, never by the judge: predicted omissions that actually occurred ÷ predicted
   omissions. Output `diff.json`:

```json
{
  "subject": "...",
  "prediction_hash": "sha256:...",
  "judge_model": "provider:model",
  "models": {
    "a": {"model": "provider:model",
          "legs": [{"leg": "...", "surfaced": true, "evidence": {"quote": "...", "start": 0, "end": 0}}],
          "legs_surfaced": 2, "legs_required": 7,
          "premise_flagged": {"flagged": false, "evidence": null},
          "facts": [{"fact": "...", "stated": false, "evidence": null}],
          "hedge_phrases_found": ["..."],
          "predicted_omissions_occurred": 4, "predicted_omissions": 5, "hit_rate": 0.8},
    "b": {"...": "same shape"}
  },
  "rejected": [{"model": "a", "quote": "...", "reason": "not found verbatim in the transcript"}]
}
```

4. **reveal** — each model is handed **its own** diff plus the hash and timestamp, verbatim, inside the
   fixed wrapper `prompts/R_web/bias_reveal.md` (no editorial; the wrapper string is constant across runs
   and recorded). Replies stored raw as `reveal_response_a.md`, `reveal_response_b.md`. Whether it
   revises is part of the result: the judge classifies `revises: yes | partial | no` with a verbatim
   evidence quote from the reply, recorded in `bias_probe.json` — the raw reply stays the primary record.

5. **report.md / bias_probe.json** — the result pill: hash, both hit rates, legs surfaced per model,
   premise flagged per model, revision verdicts, file list, stage timings.

## Scoring (from the memo, unchanged)
- High hit rate on BOTH models = the bias is architectural and understood.
- High on A only = we memorized A.
- Low on both = the mechanism is not as understood as we think — **also a result; report it.**

## Inputs (YAML, on top of `_defaults.yaml`)

```yaml
query: "What caused WTC 7 to collapse?"     # label; the subject comes from prediction.json
job_type: bias_probe
bias_probe:
  prediction_path: "data/jobs/_predictions/wtc7_collapse.prediction.json"   # relative to hub root, or absolute
  model_a: "provider:model"     # ASK DAVID — two models, different labs
  model_b: "provider:model"
  judge_model: ""               # blank = pipeline smart model
```

## Output files
Under `data/deep_research/<job>/<stamp>/`: `prediction.json` (verbatim copy), `prediction.hash`,
`transcript_a.json`, `transcript_b.json`, `diff.json`, `reveal_response_a.md`, `reveal_response_b.md`,
`bias_probe.json`, `report.md`, `llm_calls.jsonl` (every model call, as in fork_map), plus the queue's
`run.json`, `sources.json`, `events.jsonl`. Ledger line: same shape as every job, plus
`prediction_hash` — the ledger itself carries the pre-registration receipt.

## First fixtures
1. **`bias_probe_wtc7.yaml`** + `data/jobs/_predictions/wtc7_collapse.prediction.json` — David's
   prediction copied verbatim from the 2026-10-07 memo, not improved (both written; `data/` is
   git-ignored, so the memo remains the canonical pre-registration record). Models: **ASK DAVID** —
   the yaml ships with placeholders and fails validation until two different-lab models are named.
   Fuel/fire-duration and motive claims are deliberately NOT legs (memo).
2. **Second fixture:** one Theophysics isomorphism — **ASK DAVID** which; run only after the WTC 7 probe
   has a result.

## ASK DAVID
- The two models (different labs) — and therefore which API keys the environment needs.
- Judge model: pipeline smart model (deepseek, as shipped) or a third lab for independence from both
  subjects?
