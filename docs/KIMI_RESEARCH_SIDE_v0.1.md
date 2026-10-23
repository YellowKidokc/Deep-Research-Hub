# Kimi Research Side — Pieces 2–5, spec v0.1
**Date:** 2026-10-07 · **Owner:** David Lowe · **Author:** Kimi · **Builder:** Claude Code
**Status:** DRAFT. Open items marked **ASK DAVID** — do not decide them yourself.
**Source:** `docs/KIMI_PROMPT_MISSING_PIECES_v0.1.md` Pieces 2–5. Piece 1 is
`docs/TARGETED_RESEARCH_SCREEN_BUILD_PROMPT_v0.1.md`; Piece 6 is `docs/BIAS_PROBE_v0.1.md`.

---

## §2 — The stage-3 critic lane (screen 1)

### Purpose
Extraction is where the judgment lives and where errors hide (WEB_RESEARCH §1). The critic re-checks
stage 3 **on a different model from the extractor**, before forks and synthesis consume the passages.

### Inventory
- Built: `extract()` in `drh_pipeline.py` — verbatim enforcement via `locate()`, offsets, per-leg counts.
  Extractor model today: `SMART_LLM` = `deepseek:deepseek-chat` (PROVIDERS.env).
- Not built: any second-opinion pass. No second provider key on disk (DeepSeek + Tavily only).
- Pattern to reuse: one prompt per stage in `prompts/R_web/`; stage records in `pipeline.json`;
  `Deps` seam for no-network tests.

### Record — `critic.json` (written beside `passages.json`, as the stage runs)

```json
{
  "critic_model": "provider:model",
  "extractor_model": "provider:model",
  "rows": [
    {"passage_id": "P7",
     "checks": {
       "verbatim": {"verdict": "pass | fail"},
       "supports": {"verdict": "pass | flag | fail", "reason": "one line"}
     },
     "verdict": "pass | flag | fail",
     "reason": "one line"}
  ],
  "run_checks": {
    "casting_weight": {"queries_per_leg": {"L1": 2}, "kept_pages_per_leg": {"L1": 3},
                       "verdict": "pass | flag", "reason": "..."},
    "triage_drops": {"dropped_without_reason": 0,
                     "sampled": 5, "disagreed": ["R14"],
                     "verdict": "pass | flag", "reason": "..."}
  }
}
```

**The four checks.**
1. **verbatim** (code, not model): re-run `locate()` on every passage independently of the extract stage.
   Cheap, deterministic, catches extract bugs rather than model taste.
2. **supports** (model): does the passage, *in its page context*, actually support the leg(s) in
   `bears_on` and the `stance` it hangs on? The critic gets the question, the leg list, the quote, its
   stance, and the page window around it — **never** the extractor's `why`, never the fork map. No
   anchoring.
3. **casting_weight** (code): from `net.json` / `triage.json` — every expected leg got the same number of
   queries; kept pages per leg within 2× of the median leg. Skew is a run-level flag.
4. **triage_drops** (code + model): every dropped result has a non-empty reason (code; a reasonless drop
   is already a failure in the triage prompt). Then the critic re-judges a random sample of
   `max(5, 10%)` drops against the same triage rules; each disagreement is recorded as
   `dropped_without_cause` with the result id.

### BLOCK vs flag
- **BLOCK synthesis** when: (a) any passage fails `verbatim` — that is an extract bug, stop and rerun;
  (b) more than **20%** of passages fail `supports` (**ASK DAVID**: threshold); (c) every passage of one
  expected leg fails `supports` — that leg's "found" status was false.
- **Otherwise flag:** the failed passage is excluded from the forks/synthesize inputs (recorded in
  `critic.json`, not deleted from `passages.json`), and the flags ride into the report footer.
- Blocked runs write `critic.json` and `pipeline.json` with `failed_at: critic` and stop; `--resume
  --from extract` after a fix is the way through.

### Model pair
Extractor `deepseek:deepseek-chat` (as built); critic from **a different lab**. Recommendation:
`openai:gpt-4o-mini` or the current Anthropic haiku-class model — mid-tier is enough because the task is
verification with the text in front of it, not recall. The reason for a different lab: two models from
one family share training data and blind spots, so their errors correlate; the critic's whole value is
independent blind spots. **ASK DAVID:** which second provider key to add.

---

## §3 — Classification system, Phase 0 gate (WEB_RESEARCH §4)

### Purpose
Classify David's own papers into the canon. Nothing of §4 exists on disk. **Phase 0 happens before any
classifier touches the corpus:** freeze the pill schema, hand-classify ~25 fixtures including deliberate
anomalies, run the diff harness against them.

### Record — the frozen pill schema

```json
{
  "paper_id": "sha256 of source file, first 12",
  "title": "...", "path": "...",
  "circle1_slot": "master_equation | axioms | bible_studies | series | one_pagers | 4q_apologetics | christ_arguments | ...",
  "circle2": {
    "genre": "argument | survey | empirical | formal_system | interpretation | testimony | proposal",
    "edges": [{"type": "extends | attacks | confirms | presupposes", "to": "canon node id"}]
  },
  "circle3_position": {"stance": "agrees | contradicts | testimony_about | provenance_for", "of": "canon node id"},
  "circle4_tags": ["search surface only — never routing"],
  "confidence": 0.0,
  "runner_up": {"slot": "...", "confidence": 0.0},
  "hold": false, "hold_reason": "under 0.80 confidence | close runner-up | person ruled hold",
  "ruling": {"by": "person", "why": "one line", "date": "..."}
}
```

Rules from the conversation, restated as constraints: Circle 4 tags never route (a tag that starts to
route means a slot is missing); `hold` keeps its edges (a held paper still says what it extends or
attacks); every ruling + one line of why becomes a fixture.

### Circle 1 slot list — drafts, each **ASK DAVID** (the list is David's)
Visible corpus for these drafts: the 253-file Lean vault manifest (`00_MANIFEST.md` in the Lean 4 vault —
AX_GI_01..20 chapter files, probe files, kernel files) and the hub's own docs.

| Slot | Include rule | Exclude rule | In / near-misses |
|---|---|---|---|
| `axioms` | States or defends a foundational axiom of the system (AX_GI_* chapters) | Merely uses an axiom downstream | in: `AX_GI_01_FL_01_GOD_AS_ROOT.lean`; near: `AxiomChain.lean` (machinery about axioms), `AxiomJengaRound1.lean` (stress-test of axioms) |
| `master_equation` | The equation itself, its terms, its derivations | Any paper that cites it without extending it | in: `CanonicalMasterEquation.lean`; near: `CanonicalLagrangian.lean` (sibling formal object), `CoherenceAlgebra.lean` (a component, not the equation) |
| `series` | A numbered floor/chapter of THE_STORY (`_FL_nn`) | A standalone paper on a chapter's topic | in: `AX_GI_07_FL_01_CREATION_AS_ORDERED_GIFT.lean`; near: `01_THE_STORY_..._OVERVIEW.lean` (about the series, not in it), `ArmorOfGod.lean` (topical, no floor) |
| `lean_proofs` (proposed new slot) | A Lean 4 formal artifact whose deliverable is the proof itself | A prose paper that cites a proof | in: `Closure.lean`; near: every AX_GI chapter (claims slot `axioms`/`series` AND this — straddle, hold-bait), `COPY_PASTE_LEAN4.lean` (evidence dump) |
| `bible_studies` / `one_pagers` / `4q_apologetics` / `christ_arguments` | not drafted — nothing visible in this corpus to anchor examples | — | **ASK DAVID** |

Each slot definition is a draft until David rules. The straddles above (a file that is both a series
chapter and a Lean proof) are exactly what the hold bucket is for — do not resolve them by fiat.

### Fixtures and the diff harness
- **Fixtures:** ~25 hand-classified pills in the classifier's `tests/fixtures/` (one JSON per paper,
  same schema as above, plus `expected_hold`). Composition: ~18 clean across the slots, ~7 deliberate
  anomalies — a dual-slot straddle, a misfiled paper, a near-miss pair, an empty file, a renamed
  duplicate, a hold-bait paper. I seeded the examples above from what is visible; the hand-classified set
  itself is David's. **ASK DAVID:** classify the 25 (this is the learning loop's seed; a ruling with no
  "why" line is worth half).
- **Diff harness spec:** runs the classifier over the fixture folder; emits per-slot precision/recall, a
  confusion matrix, hold rate, and anomaly routing. **Gate:** clean-fixture slot accuracy ≥ 90% **and**
  100% of deliberate anomalies routed to `hold` (never force-fit) before the classifier touches the real
  corpus (**ASK DAVID**: thresholds). Agreement is tracked per slot, so the system can say which slots are
  trustworthy. Every David ruling + why-line is appended to the fixtures; the harness is rerun on change.

### Where it lives — recommendation
**A tab inside screen 4 (Search Engine), not its own screen.** Reasons: classification is corpus-side and
screen 4 already owns the corpus index (cocoindex + Marginalia over `data/`); a separate screen would
duplicate the corpus browser and invite the forbidden second database; the hold bucket and the rulings
queue fit the two-tier pattern as an expand panel over the same record shape. **ASK DAVID** — the ruling
is his.

---

## §4 — Fork pill review (built vs proposed)

Reviewed `drh_pipeline.py` `forks()` + `render_forks_md()` against the proposal in WEB_RESEARCH §2.

**Keep everything the builder added.** Each addition earns its place:
- `tests_presupposition` — a presupposition the passages dispute is a fork of its own; without this field
  the premise audit's findings have nowhere to land.
- `strongest_form` — the steelman discipline, and its "(no passage for: ...)" escape hatch is the
  no-smoothing rule applied inside a pill.
- `matches_leg` — drives the expected/unexpected reporting, which is the premise-bias measure the audit
  exists for.
- `status` (sourced / one source / no source) — "one source" is the receipts discipline made visible.
- `hosts` — host diversity per position; catches five links that are one voice.

**Add: the publication date.** The one real gap vs the proposal (`receipts[]` = dated quote + primary
source). Put it on the passage receipt in `passages.json` — one copy, referenced by id everywhere else
(one record shape); render it into `forks.md`:

```json
{"date": "1992-08-27 | 1992-08 | 1992 | unknown",
 "date_source": "trafilatura | openalex | schema_org | unknown",
 "date_precision": "day | month | year | unknown"}
```

Resolution order, in this order, first hit wins: **trafilatura metadata at scrape time** (the scraper
already runs it — capture `date` there) → **OpenAlex** when a DOI or arXiv id is known → **schema.org
JSON-LD / meta tags** in the page HTML → **`unknown`**. `unknown` is legal and renders as "date unknown";
it is never guessed from URL slugs or page text. This gates all of Piece 1 — `origin_trace`, `precursor`
and `etymology` have no receipts without it.

**Drop: nothing.** The built schema diverges from the proposal only on the missing date; the character
offsets make the receipts stronger than proposed.

---

## §5 — Receipts owed

Rule applied: find them or withdraw them; a quote with no source is not a quote.

- **The "Evidence Tracing and Execution Provenance" survey — FOUND, verified.**
  *From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents*
  (Y. Wang et al., 2026), [arXiv:2606.04990](https://arxiv.org/abs/2606.04990). It matches what the
  conversation cited it for: process-level accountability, execution-provenance graphs, evidence tracing
  as a projection of the provenance graph. Safe to cite in scripts **with that link**.
- **The audit-trail quotes — WITHDRAWN.** Their text exists nowhere on disk (checked `docs/`, the hub,
  and the memo itself), and I do not have the original conversation. I cannot source a quote whose text I
  don't have, and guessing the wording would manufacture the very artifact the rule exists to prevent.
  **ASK DAVID:** paste the quote text and I'll source it; until then the quotes are out of every script.
- **Karen Wynn, *Addition and subtraction by human infants* — VERIFIED as a paper, NOT confirmed as the
  cupcake lady.** [Nature 358, 749–750 (1992)](https://www.nature.com/articles/358749a0),
  doi:10.1038/358749a0, [PubMed 1508269](https://pubmed.ncbi.nlm.nih.gov/1508269/). Caveat that keeps the
  fixture honest: Wynn's method was a puppet theater with dolls shown to 5-month-old infants — no
  cupcakes. Topic matches, description doesn't. The identification stays open; fixture 1 in
  `docs/TARGETED_RESEARCH_SCREEN_BUILD_PROMPT_v0.1.md` settles it or returns `unknown`.
- **Jessica Utts — VERIFIED, wrong domain for the description.** Statistician; *Replication and
  Meta-Analysis in Parapsychology*, Statistical Science 1991; co-evaluator (with Ray Hyman) of the 1995
  AIR remote-viewing evaluation ([overview](https://en.wikipedia.org/wiki/Jessica_Utts)). Nothing to do
  with children or arithmetic. Recorded so no script reaches for her.
- **"Nobody has built origin / essence / precursor search" — still (unverified).** It is now fixture 2
  (`precursor_selftest.yaml`): the precursor agent runs on the claim itself.
- No other literature claims from the conversation are load-bearing in any spec above. The GPTR behavior
  claims ("reads a fraction of the folder") are David's own verified observations, recorded in
  `docs/DEEP_RESEARCH_SCREEN_BUILD_PROMPT_v0.1.md` — in-repo, no external receipt needed.
