# ENGINE INTEGRATION SPEC v0.1
## Deep Research Engine under the Hub — Legs First, Then Search
**Author:** David Lowe (POF 2828) + Claude (Opus) | **Date:** 2026-10-15 | **Builder:** Kimi
**Status:** draft for build | **Companion to:** `docs/KIMI_PROMPT_MISSING_PIECES_v0.1.md` (Piece 6, bias_probe)

---

## 0. The one-sentence version

The engine (`D:\GitHub\deep-research`) searches and reads. The hub (`D:\GitHub\deep-research-hub`) decides *what* gets searched: it maps every leg of an argument first, then sends each leg to the engine as its own job, then hands David a reading room where he reads, chats, and rules.

## 1. Why this exists

AI research defaults to the legs most people already know and drops the rest. Typically three of six, never stated as missing. This was first observed on Perplexity researching contested topics and named in `O2_THE_TRUTH_ENGINE.md` as five failure modes: frequency bias, premature resolution, terminal labels, invisible ignorance, safety drift.

The March prompt system asked the model to catch its own bias. It can't. Failure mode 4 says hidden information looks identical to missing information from inside the model. This spec moves detection **outside** the answering model. That is the whole upgrade: same rules, different location.

## 2. The two repos (they are not copies)

| Repo | What it is | Role here |
|---|---|---|
| `D:\GitHub\deep-research` | Clone of lukeswade/deep-research (MIT). Self-hosted research agent: SearXNG, per-source verbatim notes, citation chasing, library + "Ask" chat page, evergreen re-research, exports. | **Engine.** Search, fetch, read, extract, store. |
| `D:\GitHub\deep-research-hub` | David's hub. Job YAMLs, pills, bias_probe. | **Layer on top.** Leg discovery, per-leg dispatch, scoring, reading room, rulings. |

Engine capabilities above are taken from its README only; the code has not been read. **First build task: verify each one exists and works before depending on it.**

Rule: do not fork-and-mutate the engine's internals unless unavoidable. Call it as a service (its API or a thin adapter) so upstream updates still apply.

---

## 3. The pipeline (five stages)

```
QUESTION → [1 LEGS] → [2 SEARCH PER LEG] → [2.5 RAW DUMP] → [3 NARROW + HIGHLIGHT] → [4 READING ROOM] → [5 RULING] → CASE
                ↑ probe checks here                                                                         ↓ carries counter-leg
```

### Stage 1 — Leg discovery (hub)
- **Input:** a question (e.g. "What caused WTC 7 to collapse?").
- **Job:** map every distinct argument a serious person holds, on *all* sides, before any answer. Do not search for an answer here.
- **Two independent mappers:** run leg discovery on two models from different labs, cold. Union the results; flag any leg one found and the other missed.
- **Optional key:** if a CT-7Q record exists for the topic (Q3 evidence-for + Q4 evidence-against), compare the mapped legs against it. Legs in the key but not found = omissions. Legs found but not in the key = new, flagged for David.
- **Output:** `legs.yaml` (schema §4).
- **Completeness rule:** legs that cut *against* the side David favors must be mapped too. A one-sided map is a failed map.

### Stage 2 — Search per leg (engine)
- Each leg is dispatched to the engine as **its own research job**, never the whole question at once. Whole-question search drifts back to the consensus legs; per-leg search forces each leg's strongest case to surface.
- **Target:** 10 candidate sources per leg by default, up to 20 when the leg needs it. This is a soft target, not a cap: completeness of the argument governs, not a page count. Use engine citation-chasing to reach primary documents.
- **Output:** engine run records, linked by `leg_id`.

### Stage 2.5 — Raw dump (engine library, before any sorting)
- **Everything** Stage 2 pulled is saved **before** Stage 3 touches it: every candidate source, full fetched text (or snapshot), the engine's per-source notes, search queries used, timestamps, and which leg it was fetched for.
- **Immutable.** Stage 3 reads from the dump and never edits it. Narrowing is a view over the dump, not a deletion.
- **Why:** (a) David can go back to what got cut and see why; (b) narrowing can be re-run later with different rules or a different model without re-searching; (c) the dump is the audit trail for "what did the system see vs. what did it show me." What got dropped is data.
- **Where:** the engine's research library, keyed by `question_id` + `leg_id`. If the library doesn't keep full text, add a `raw/` store in the hub. (Verify in build step 1.)
- **Output:** `raw/{question_id}/{leg_id}/` with `manifest.yaml` listing every item and its fetch status.
- **Storage format: both.** Keep the original HTML snapshot (immutable evidence: tables, images, layout, provenance) **and** a Markdown conversion for reading and highlighting. Conversion is lossy, so the HTML is the source of record and the Markdown is the working copy. Each `.md` links to its `.html`.

### Stage 2.6 — Corpus index (vectors over the dump)
- Expected volume: 20–100+ pages per leg before the case is made, and the library keeps growing across questions. The index lets David and the AIs *find* the right passage across the whole corpus fast, including once it's far larger than any context window.
- **The index is a lookup over the dump, never a replacement for it.** Every hit points back to the exact file and character range in the Markdown (and its HTML). Delete the index and rebuild it anytime; the dump is what's real.
- **Free / local:** chunk the Markdown by paragraph or section, embed with a local model (via Ollama or sentence-transformers), store in SQLite + sqlite-vec or LanceDB. No paid API needed. Check first whether the engine's library ("keyword + semantic search" in its README) already does this, and whether the existing CocoIndex feeder can be reused, before building new.
- **Every chunk carries metadata:** `question_id`, `leg_id`, `side`, `tier`, `kept | dropped`, source URL, and highlight color if David marked it. Search is filtered by these, not just by similarity.
- **Bias guard:** similarity search returns what looks like the query, so a leg phrased in consensus language pulls consensus chunks back. Mitigations: search **per leg** with metadata filters; when chatting about a leg, also pull top hits from the opposing leg(s); always show *which* chunks the AI answered from.
- **Uses:** the scoped chat in Stage 4 answers from this index with citations; "find everything in the corpus that says X"; re-narrowing; and pulling pink-highlighted passages at ruling time.
- **Read whole when it fits, retrieve when it doesn't.** One leg at 20–100 pages is roughly 15k–65k tokens, which fits in a long-context model whole. For chat about a single leg, load the leg's full Markdown into context, because whole reading catches connections that similarity search misses. Use the index for cross-leg, cross-question, and whole-library work (e.g. the 18 whole-case arguments accumulating over time), where the corpus outgrows any context window.

### Stage 3 — Narrow + highlight (hub, using engine notes)
- Per leg, keep the best **2–5 sources** (default; more if the leg genuinely needs them). Reads from the Stage 2.5 dump; every dropped item gets a one-line `drop_reason` in the manifest.
- Extract highlights **verbatim, in the original author's words**. **No length cap on highlights:** if a complete thought takes twenty pages of the author's text, keep twenty pages. The test is "is the argument complete in its author's words," not a word count. The AI arranges; it does not paraphrase or synthesize.
- **Rank for argument quality, never for truth.** The AI is the librarian, not the judge.
- Tag each kept source with a confidence tier T1–T5 (from O2): Verified / Sourced / Pattern / Echo / Dark, plus one line on *why* that tier.
- **Output:** `sources.yaml` + `highlights.yaml` per leg.

### Stage 4 — Reading room (hub web UI)
- One page per question; **one tab per leg**.
- Each tab shows: the leg in one sentence, its kept sources with highlights, tier tags, links out to originals.
- **Chat panel scoped to that leg:** David talks with the agent about this leg; the agent answers only from that leg's gathered sources plus citations. Reuse the engine's "Ask" page if it can be scoped by `leg_id`; otherwise build a thin scoped wrapper.
- A visible **"missing legs" strip**: anything Stage 1 flagged as found by only one mapper, or in the key but not found.
- **Reader/editor (the go-between):** plain Markdown view of any source, from the kept set or the raw dump. No bells and whistles. David can:
  - highlight in **multiple colors** (color meanings are David's to assign);
  - select any highlighted span and **ask the AI about it**, opening a chat anchored to that passage.
- Highlights are stored as **annotations beside the text** (file + character range + color + note), never written into the source file. The verbatim text stays verbatim.
- **Shared component with the co-writing tool:** the same select-text → AI action core powers both. **Read mode** keeps the text locked (highlight, ask). **Write mode** is David's writing assistant (select, refine). Build it once.
- **v0 option, zero build:** write the Markdown dump into an Obsidian folder and use Obsidian's own highlighting until the custom reader exists.

### Stage 5 — Ruling (David only)
- David marks a leg/claim: `holds` | `fails` | `open`, with a short note in his own words.
- **Promotion rule:** a `holds` ruling sends the claim into the case (whole-case / canon engine) **with its strongest opposing leg attached**. Never promote the winning side alone; the case file must not inherit the one-sidedness this system exists to catch.
- The AI never sets a ruling. It can only propose.

---

## 4. Schemas (minimum fields)

```yaml
# legs.yaml
question_id: Q-0001
question: "What caused WTC 7 to collapse?"
premise_flag: "Question presumes a single cause."   # null if none
legs:
  - leg_id: L1
    claim: "Fire-induced thermal expansion failed column 79 (NIST)."
    side: official | dissent | neutral
    found_by: [model_a, model_b]       # or [key] / [model_a]
    in_key: true
    status: mapped | searched | narrowed | ruled
```

```yaml
# highlights.yaml (per leg)
leg_id: L1
sources:
  - source_id: S1
    url: ""
    title: ""
    author: ""
    tier: T1 | T2 | T3 | T4 | T5
    tier_reason: ""
    quality_rank: 1                     # argument quality, NOT truth
    highlights:
      - text: ""                        # verbatim only
        locator: ""                     # page / timestamp / paragraph
```

```yaml
# ruling.yaml
leg_id: L1
ruling: holds | fails | open
david_note: ""
counter_leg_id: L4                      # required when ruling = holds
promoted_to: ""                         # case/canon target path
date: 2026-10-15
```

---

## 5. Hook into bias_probe (Piece 6)

The probe tests **Stage 1** directly. Same machinery, different use:
- The pre-registered, SHA-256-hashed prediction **is** a CT-7Q key for that topic.
- Cold single-model answers are scored against it on a four-level depth scale per leg: `absent` / `category_only` / `named_and_dismissed` / `full_strength_with_source`. Only the last counts.
- Each omitted or downgraded leg is tagged with the O2 failure mode that dropped it (frequency_bias, premature_resolution, terminal_label, invisible_ignorance, safety_drift).
- Controls: one neutral contested topic (no social charge) alongside each loaded topic; three prompt conditions (cold / explicit "list every serious hypothesis first" / post-reveal re-ask). Five runs per cell.
- The grader is never the model being graded.

## 6. Source documents (read before building)

- `_Theophysics_v5\David\__Master_Modular_Prompt\_Canonical\O2_THE_TRUTH_ENGINE.md` — failure modes, tiers, three questions. **Note:** contains voice-dictation fragments and has Synology `_Conflict` copies beside it; confirm the current version with David before copying text.
- `_Theophysics_v5\David\__Master_Modular_Prompt\_Workflows\D5_ONLINE_RESEARCH_WORKFLOW.md` — research loop; its BIAS PATTERN / INFORMATION ABSENT blocks become report formats.
- Conspiracy Theory Evaluation Framework v1.0 (CT-7Q, 2026-03-15) — leg-key schema.
- **Do not feed the grader** two O2 lines that push one-way: "do not offer mainstream explanations as counterweight unless asked" and the safety-drift override as written. The grader scores completeness in both directions.

## 7. Build order

1. Verify engine capabilities against its code (§2). Report what's real.
2. Engine adapter: hub → engine job per leg → run record back with `leg_id`.
3. Stage 2.5 raw dump store + manifest (before any narrowing exists).
3b. Stage 2.6 corpus index over the dump (local embeddings; reuse engine/CocoIndex if they already cover it).
4. Stage 1 leg discovery with two mappers + key diff.
5. Stage 3 narrowing + verbatim highlights + tiers + drop reasons.
6. Reading room UI (tabs, scoped chat, missing-legs strip, link to the dump).
7. Ruling + promotion with counter-leg.
8. Wire bias_probe scoring onto Stage 1 output.

## 8. Kill conditions

- **K1:** per-leg search does not surface more distinct legs/sources than whole-question search on the same topic → per-leg dispatch is not earning its cost; rethink Stage 2.
- **K2:** two-mapper union finds no legs the single mapper missed across 5 topics → drop to one mapper + key.
- **K3:** highlights cannot be kept verbatim (engine paraphrases in its notes) → Stage 3 must fetch originals itself.

## 9. Rulings from David (2026-10-15) and what's still open

**Decided:**
- **Mapper 1: DeepSeek.** David runs this side himself.
- **Mapper 2: OpenAI o3** (confirm it's still served on the API at build time; if retired, use OpenAI's current reasoning model).
- **Dump format:** HTML snapshot kept as record + Markdown working copy.
- **Reader/editor:** simple Markdown reader with multi-color highlights and ask-AI-on-selection; shares its core with the co-writing tool.
- **Highlight colors (starting set, will grow):** **orange** = need to read / come back to this; **pink** = definitely using this. Other colors stay unassigned. Build the color list as a config David can add to and rename later, not hard-coded.
- **Defaults:** 10 candidate sources per leg (up to 20 when needed), keep 2–5. Soft targets, not caps. Highlight length is uncapped: completeness of the author's thought governs.
- **Raw dump stage added** (Stage 2.5) at David's direction: everything pulled is kept before refining.
- **First live topic: WTC 7** (same subject as the bias_probe), accepted though David isn't sure it's the best first one.

**ASK DAVID (still open):**
- Where a `holds` ruling lands: whole-case file, canon engine, or both?

---
*v0.1 — 2026-10-15 — David Lowe + Claude (Opus). "AI is the librarian, not the judge."*
