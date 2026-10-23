# Targeted Research Screen — Build Prompt v0.1
**Date:** 2026-10-07 · **Owner:** David Lowe · **Author:** Kimi (spec) · **Builder:** Claude Code (sole builder on this repo)
**Status:** DRAFT. Open items marked **ASK DAVID** — do not decide them yourself.
**Source:** `docs/KIMI_PROMPT_MISSING_PIECES_v0.1.md` Piece 1, against `docs/WEB_RESEARCH_v0.1.md` §3.

## Purpose
Screen 2 is a fixed battery of specialist job types — `origin_trace`, `precursor`, `essence_paper`, plus
`etymology` (the etymology / first-use arm the original hub spec put on screen 2). One definition each,
used by both screens: screen 1's queue runs them as `job_type:` values in `data/jobs/*.yaml`; screen 2 is
a form that writes those job files with the type's defaults filled in. One record shape, one
`visited_urls` ledger, one queue folder. No second database.

Every type inherits the queue / receipt / ledger discipline from
`docs/DEEP_RESEARCH_SCREEN_BUILD_PROMPT_v0.1.md` and the visible-pipeline machinery from `drh_pipeline.py`.
The standing rules apply without exception: discovery before construction; receipts written as the stage
runs; pills, not prose; **"unknown" is a legal answer**; never smooth a weird origin into a clean one.

## Inventory (what's on disk)
- **Built:** queue + claim + ledger (`drh_queue.py`: `JOB_TYPES`, `BUILT_TYPES` = standard, fork_map);
  folder-per-job output under `data/deep_research/<job>/<stamp>/`; `_defaults.yaml` merge.
- **Built:** the fork_map pipeline (`drh_pipeline.py`): premise audit → balanced neutral cast → triage
  with recast → verbatim extract with character offsets → forks → synthesize. Prompts in
  `prompts/R_web/`. `Deps` seam for no-network tests (`tests/test_drh_pipeline.py`).
- **Built:** retrievers via GPTR: tavily, arxiv, openalex, semantic_scholar, pubmed_central, exa, others.
- **NOT built — hard dependency:** publication-date capture on passages. `origin_trace`, `precursor` and
  `etymology` are dead without dated receipts. Spec and resolution order in
  `docs/KIMI_RESEARCH_SIDE_v0.1.md` §4. **Build dates first.**
- **NOT built:** Marginalia as a retriever. It is screen 4's engine; GPTR has no adapter for it.
  **ASK DAVID:** Marginalia retriever adapter + API key, or academic tier only for v1?
- **NOT built:** the critic lane (`docs/KIMI_RESEARCH_SIDE_v0.1.md` §2). These types inherit it when it lands.

## Shared machinery
Each type is the same skeleton with a different cast pattern, success test and kill condition:

```
premise audit (light) → cast (type-specific) → triage → extract (verbatim + offsets + dates) → <type stage> → render
```

- Reuse `Pipeline`'s stage drivers where they fit; add the type's own stage beside `forks()`.
  Prompts live in `prompts/R_web/` (`origin.md`, `precursor.md`, `essence.md`, `etymology.md`).
- **The dated receipt** (one shape, used by every hop / precursor / paper below):

```json
{
  "quote": "verbatim passage, found in the page by the same locate() check as fork_map",
  "url": "https://...",
  "start": 12345, "end": 12890,
  "date": "1992-08-27",
  "date_source": "trafilatura | openalex | schema_org | unknown",
  "date_precision": "day | month | year | unknown"
}
```

  A receipt with `"date": "unknown"` is **not** a receipt for these job types. Date resolution order and
  the no-guessing rule: `docs/KIMI_RESEARCH_SIDE_v0.1.md` §4.

---

## Job type: `origin_trace`
**Asks:** where did this concept / phrase first appear, and how did it travel?
**Why it is the dangerous one (WEB_RESEARCH §3):** search ranks by relevance and recency — the opposite of
first attestation. A model asked for an origin will produce a plausible, smooth, wrong family tree. The
receipts rule is the guard.

**Inputs (YAML, on top of `_defaults.yaml`):**

```yaml
query: "the concept or phrase to trace"        # required
job_type: origin_trace
report_source: web
retrievers: [openalex, semantic_scholar, arxiv, pubmed_central, tavily]   # academic tier FIRST, general web last
pipeline:
  anchor_queries: 3        # phase A: how the concept is named today
  queries_per_hop: 2       # phase B: per candidate hop, per walk-back round
  max_rounds: 5            # walk-back rounds before "no earlier attestation found" is recorded
```

**Cast pattern.**
- **Phase A — anchor:** `anchor_queries` neutral queries naming the concept as used today. No verdict
  words (same `VERDICT_WORDS` guard as fork_map) and no assumed answer: "earliest recorded use of X" is
  legal, "X was invented by Y" is not.
- **Phase B — walk back:** from the earliest dated candidate hop, `queries_per_hop` queries targeting
  *earlier* attestation: `"<concept>" before <year>`, `"<claimant>" "<concept>" earlier work`, scholar
  queries sorted **date-ascending** (OpenAlex `sort=publication_date:asc`; Semantic Scholar year filters).
  Stop when a round finds nothing earlier — record `no earlier attestation found in N casts` — or at
  `max_rounds`.
- Academic tier and Marginalia run **before** general web on every leg of the cast, because
  relevance+recency ranking is the opposite of first attestation.

**Pill (`origin.json`):**

```json
{
  "subject": "the concept as asked",
  "chain": [
    {"hop_id": "H1", "date": "...", "date_precision": "...",
     "claimant": "person or text this hop attests",
     "claim": "what this hop shows, one sentence",
     "receipt": { "quote": "...", "url": "...", "start": 0, "end": 0,
                  "date": "...", "date_source": "...", "date_precision": "..." },
     "status": "attested"}
  ],
  "chain_status": "complete | broken | contested | unknown",
  "first_attestation": "the earliest hop with a dated receipt, or 'unknown'",
  "anomalies": ["anything weird, recorded as found — never smoothed"],
  "rejected": [{"claimant": "...", "reason": "no dated receipt | quote not verbatim in page"}]
}
```

**Hard validation (REJECTED, not softened).**
- A hop whose quote is not found verbatim in the page (same `locate()` check as extract) → rejected.
- A hop with `date: unknown` → the chain **ends** at the previous hop:
  `chain_status: broken`, `first_attestation: "unknown before <last good date>"`.
- A claimant named from model memory with no receipt → `rejected[]`, never `chain[]`.
- Two dated attestations in the same era with no earlier resolution → `chain_status: contested`, both kept.

**Kill / legal "no":** `unknown` (no hop with a dated receipt) and `contested` are first-class results.
The run is a success when it returns `unknown` with the full cast record behind it.

**Output files** under `data/deep_research/<job>/<stamp>/`: `premise.json`, `net.json`, `triage.json`,
`passages.json` (same as fork_map), then `origin.json`, `origin.md`, `pipeline.json`, `llm_calls.jsonl`;
ledger line same shape as fork_map with `receipt: {hops, chain_status, first_attestation}`.

---

## Job type: `precursor`
**Asks:** who said this — or predicted this — long before its time?

**Inputs:**

```yaml
query: "the claim, one full sentence, in today's words"   # required
job_type: precursor
report_source: web
retrievers: [openalex, semantic_scholar, arxiv, pubmed_central, tavily]
pipeline:
  before_year: 1900          # optional; only candidates strictly before this count
  paraphrases: 3             # neutral rewordings of the claim, generated and recorded in net.json
  queries_per_candidate: 2
  candidate_rounds: 3
```

**Cast pattern.** Academic tier first, **date-ascending**. The model writes `paraphrases` neutral
rewordings of the claim (recorded in `net.json`); each paraphrase gets queries with explicit year ranges
(`"<paraphrase>" 1850..1900`). General web last, only for candidates the academic tier surfaced.

**Pill (`precursors.json`):**

```json
{
  "claim": "the claim as asked",
  "candidates": [
    {"person": "...", "work": "...", "date": "...",
     "receipt": {"quote": "...", "url": "...", "start": 0, "end": 0,
                 "date": "...", "date_source": "...", "date_precision": "..."},
     "match": {"states_the_claim": true, "evidence_quote_id": "P7"},
     "status": "confirmed | weak"}
  ],
  "rumours": [{"person": "...", "why_recorded": "named by sources but no dated quote from that person"}],
  "finding": "confirmed | rumour_only | unknown"
}
```

**Hard validation.**
- A candidate without a **dated verbatim quote from that person or their text** is a rumour: it goes to
  `rumours[]` and is **never** written as a finding. Not softened, not "attributed to".
- `states_the_claim` needs its own verbatim quote from the receipt showing the claim is actually stated,
  not a neighboring idea.
- `before_year` is enforced in code against the receipt date, not trusted to the model.

**Kill / legal "no":** `unknown`, `rumour_only`.

**Output files:** the shared four, then `precursors.json`, `precursors.md`, `pipeline.json`; ledger
`receipt: {candidates, rumours, finding}`.

---

## Job type: `essence_paper`
**Asks:** which study, experiment or paper captures the core of this question?

**Gate (hard):** refuses to run without a fork map for the question — the fork map says what the
question's structure is. Input: `pipeline.fork_map_from: <run folder>` containing `forks.json`.
**ASK DAVID:** explicit run folder, or auto-resolve the latest `fork_map` run under the same ledger key?
(Recommendation: explicit path. Auto-latest silently changes what a rerun means.)

**Inputs:**

```yaml
query: "the question"                # must match the fork map's question
job_type: essence_paper
report_source: web
retrievers: [openalex, semantic_scholar, arxiv, pubmed_central]
pipeline:
  fork_map_from: "data/deep_research/<job>/<stamp>"   # required
  queries_per_fork: 2
  max_candidates: 12
  essence_threshold: 6               # of 8; ASK DAVID
```

**Cast pattern.** Two queries per fork from the fork map's core questions and load-bearing claims,
academic tier only. General web only for a fork that surfaced nothing (recorded as such).

**The rubric (rubric-scored, never citation-ranked).** Each candidate is scored 0–8, every score backed
by a receipt quote from the paper itself or a later source:

| Criterion | Points | Receipt required |
|---|---|---|
| Central-claim match: the paper's central claim matches the fork's load-bearing claim | 0–3 | verbatim quote from the paper's own abstract or body |
| Primary evidence: experiment / data / derivation in the paper, not a review or meta | 0–2 | verbatim quote of the method or result |
| Still standing: one recency cast for replication / critique / retraction | 0–2 | quote from the later source, or recorded "no later challenge found in N casts" |
| Independence: not a self-citation cluster | 0–1 | OpenAlex authorship overlap check, recorded |

Citation counts may be recorded for context and are **never** a criterion.

**Pill (`essence.json`):**

```json
{
  "question": "...",
  "fork_map_from": "data/deep_research/<job>/<stamp>",
  "fork_refs": ["F1", "F3"],
  "candidates": [
    {"paper": {"title": "...", "authors": ["..."], "year": 1992, "venue": "...", "doi_or_url": "..."},
     "scores": {"central_claim_match": {"score": 3, "receipt": {...}},
                "primary_evidence": {"score": 2, "receipt": {...}},
                "still_standing": {"score": 1, "receipt": {...}},
                "independence": {"score": 1, "detail": "..."}},
     "total": 7, "status": "essence | below_threshold"}
  ],
  "selected": "the candidate at or above threshold, or null",
  "famous_but_rejected": [{"paper": "...", "total": 4, "reason": "review, not primary evidence"}],
  "finding": "found | none"
}
```

**Hard validation.** A candidate whose central-claim score lacks a verbatim quote from the paper itself →
rejected (moves to `famous_but_rejected` with the reason). **Kill / legal "no":** `finding: none`.

**Output files:** the shared four, then `essence.json`, `essence.md`, `pipeline.json`; ledger
`receipt: {candidates, selected, finding}`.

---

## Job type: `etymology` (the first-use arm)
**Asks:** first use and sense history of a word or phrase. Same receipts discipline as `origin_trace`,
phrase-specific cast.

**Inputs:** `query` = the word/phrase; `job_type: etymology`; same retriever default; pipeline:
`sense_rounds: 3`, `queries_per_round: 2`.

**Cast pattern.** Academic tier first for coined technical terms; then dictionaries and corpora via web:
OED (**ASK DAVID:** subscription access, or free sources only?), etymonline, Merriam-Webster "First Known
Use", Google Ngram / COHA / Hansard for political terms. Marginalia is valuable here (old, non-SEO web) —
blocked on the adapter question above.

**Pill (`etymology.json`):**

```json
{
  "word": "...",
  "first_use": {"date": "...", "text": "the work it appears in", "author": "...",
                "receipt": {"quote": "...", "url": "...", "start": 0, "end": 0,
                            "date": "...", "date_source": "...", "date_precision": "..."}},
  "sense_changes": [{"date": "...", "sense": "...", "receipt": {...}}],
  "status": "attested | partial | unknown"
}
```

**Hard validation / kill:** as `origin_trace` — no dated receipt, no hop. `unknown` is legal.

---

## Screen 2 form (two-tier)
One box (the question / claim / word) and the job-type picker; every other field defaults from
`_defaults.yaml` plus the type's preset above; expand for retrievers, thresholds, `before_year`,
`fork_map_from`. The screen writes `data/jobs/<name>.yaml` and shows a Runs view filtered to these four
types. It stores nothing else.

## First fixtures (jobs the builder can run on day one)

1. **`cupcake_lady.yaml`** — `job_type: precursor`.
   `query: "A researcher showed that children know the answer is wrong when one cupcake minus two is shown as a possibility — who is the 'cupcake lady', and what did she actually show, when?"`
   Neither candidate name appears in the job file. What the spec already owes this fixture
   (`docs/KIMI_RESEARCH_SIDE_v0.1.md` §5): Karen Wynn's Nature 1992 paper is **real and dated**
   ([doi:10.1038/358749a0](https://www.nature.com/articles/358749a0)) but its method is a puppet theater
   with 5-month-old infants, not cupcakes — a match on topic, not yet on description. Jessica Utts is a
   real statistician in a different field entirely. Legal outcomes: `confirmed` (with dated receipt),
   `rumour_only`, `unknown`.

2. **`precursor_selftest.yaml`** — `job_type: precursor`. Runs the claim on itself:
   `query: "Nobody has built origin / essence / precursor search as a research tool."`
   The agent either finds dated prior art (which refines the claim with a receipt) or returns `unknown`,
   which upgrades the claim from (unverified) to *tested, with the cast record attached*.

3. **`origin_trace` from THE_STORY — AX_GI_06 (Logos / Kolmogorov).** Picked as the chapter most likely
   to break the agent. `query: "Where does Logos as the rational ordering principle through which the
   world is knowable first appear, and how did it travel?"`
   Why this one breaks it: recency-ranked search will serve John 1:1 commentary and modern textbooks; the
   real first attestation is Heraclitus (~500 BC), surviving **only as quotations inside later authors**
   (the doxographers) — so the primary source is itself a quotation, which stress-tests the verbatim-receipt
   rule; and the model will want to smooth a clean Heraclitus → Philo → John family tree without a dated
   receipt for each hop. If the agent survives this one with receipts or an honest `broken`, the guard works.

## Build order
1. **Date capture on passages** (`docs/KIMI_RESEARCH_SIDE_v0.1.md` §4) — blocks everything here.
2. `origin_trace` (and `etymology` beside it — see ASK DAVID below).
3. `precursor`.
4. `essence_paper` (needs `fork_map_from`).
5. Screen 2 form (thin: writes job files, reads run folders).

Each type lands with: its prompt in `prompts/R_web/`, its stage in `drh_pipeline.py` (or a sibling module
reusing `Pipeline`), `JOB_TYPES`/`BUILT_TYPES` entries and validation in `drh_queue.py`, a no-network test
in the style of `tests/test_drh_pipeline.py`, and its fixture above **run for real**, with the run folder
kept as the reference receipt.

## ASK DAVID
- Marginalia retriever adapter + API key, or academic tier only for v1?
- OED access for `etymology`, or free sources only?
- `essence_threshold` at 6 of 8?
- `essence_paper`: explicit `fork_map_from` path (recommended) or auto-latest by ledger key?
- Academic retriever default set (this resolves the open "exact academic retriever set" item in
  `docs/DEEP_RESEARCH_SCREEN_BUILD_PROMPT_v0.1.md`): proposed
  `[openalex, semantic_scholar, arxiv, pubmed_central]` with tavily last.
- `etymology`: separate `job_type` sharing `origin_trace`'s code path (recommended — the cast pattern and
  sources differ enough that one prompt would serve both badly), or a `subject_kind` switch inside
  `origin_trace`?
