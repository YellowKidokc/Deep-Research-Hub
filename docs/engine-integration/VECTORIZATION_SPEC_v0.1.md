# VECTORIZATION SPEC v0.1
## What vectors are, what they buy us, and the NAS library plan
**Author:** David Lowe (POF 2828) + Claude (Opus) | **Date:** 2026-10-15 | **Builder:** Kimi
**Companion to:** `ENGINE_INTEGRATION_SPEC_v0.1.md` (Stage 2.6)

---

## 1. Decision

We are vectorizing. Not just the per-question research dumps, but a growing library across all of David's work. It lives on a new dedicated drive/share on the NAS.

## 2. What a vector is (and isn't)

- An embedding model turns a chunk of text (a paragraph or section) into a list of numbers, typically a few hundred to ~2,000. Chunks about similar things get similar numbers.
- **The AI never reads vectors.** They live in a search index. A question is embedded the same way, the index finds the closest chunks, and the AI is handed **the original text** of those chunks. The AI only ever reads words.
- **Lossy.** The original text can't be rebuilt from a vector. It keeps "what this is about," not the argument itself. The text must always be stored alongside.
- **Not smaller.** A ~500-word page is ~3 KB of text; a 768-number vector is also ~3 KB. Compression ratio is about 1:1, worse counting the text we must keep. Vectorization is for **finding**, not for shrinking.
- **No memorization.** Nothing enters model weights. Retrieved text is placed into context fresh each conversation and is gone after.
- Analogy: a card catalog for a library, not a summary of the books.

## 3. The context-window math

- ~650 tokens per page, so a 1M-token window ≈ **1,500 pages**.
- **Without vectors:** a model can read up to ~1,500 pages, all of it, once per conversation.
- **With vectors:** the library can be any size (10k pages, 1M pages). The window still holds ~1,500 pages, but they are the most relevant ones, pulled from the whole library on demand.
- **What vectors buy is reach, not capacity:** a fixed window searching an unlimited library.
- **Long-context caveat:** recall of the middle of a very long context is weaker than the start and end. ~100 pages is comfortable; near the window limit it starts to matter.

## 4. The operating rule: read whole when it fits, retrieve when it doesn't

| Scale | Size (approx.) | Method |
|---|---|---|
| One leg | 20–100 pages ≈ 15k–65k tokens | **Read whole.** Load the leg's full Markdown into context. |
| One question (e.g. WTC 7, 7 legs) | up to ~700 pages ≈ 450k tokens | **Read whole** on a 1M-window model; retrieve if the model's window is smaller. |
| Cross-question / whole library (18 whole-case arguments, every run ever) | grows without limit | **Retrieve** from the index. |

**Why read whole when possible:** retrieval only returns chunks that *look like* the query. Whole reading catches connections between things that don't look related, which is exactly the kind of noticing this project runs on. Retrieval is a fallback for scale, not an upgrade.

## 5. Bias guard (carried from the integration spec)

Similarity search returns what resembles the question. A leg phrased in consensus language retrieves consensus passages: the same bias, entering through the search box.
- Filter searches by `leg_id` / `side` metadata, not similarity alone.
- When answering about one leg, also pull top hits from the opposing leg(s).
- Always show which chunks an answer came from.

## 6. NAS library plan

- **New dedicated drive/share on the NAS** for the vector library (path: ASK DAVID).
- Layout:
```
<NAS_VECTOR_ROOT>/
  corpus/        # source of record: HTML snapshots + Markdown working copies
  index/         # vector DB files (rebuildable from corpus/ at any time)
  manifests/     # what was ingested, when, from where, with which model
  models.yaml    # embedding model name + version used for each index
```
- **corpus/ is the truth; index/ is disposable.** Backups protect `corpus/` and `manifests/`. The index can always be rebuilt.
- **Pin the embedding model.** Vectors from different models are not comparable. Record the model + version in `models.yaml`; changing models means a full re-index, logged.
- **Free / local stack:** local embedding model via Ollama or sentence-transformers; store in SQLite + sqlite-vec or LanceDB. No paid API.
- **Reuse before build:** check the engine's built-in semantic search and the existing CocoIndex feeder first.

## 7. Chunk metadata (minimum)

```yaml
chunk_id: ""
source_path: ""          # corpus/ Markdown file
char_range: [0, 0]       # exact location in the source
html_path: ""            # original snapshot
url: ""
question_id: ""          # null for non-research corpus (vault, papers)
leg_id: ""
side: official | dissent | neutral
tier: T1 | T2 | T3 | T4 | T5
kept: true | false       # survived Stage 3 narrowing?
highlight: orange | pink | null
corpus_type: research_dump | vault | paper | transcript
ingested: 2026-10-15
embed_model: ""          # must match models.yaml
```

## 8. Build order

1. David creates the NAS share; record the path here.
2. Verify engine semantic search + CocoIndex; decide reuse vs. new.
3. Pick and pin one local embedding model; write `models.yaml`.
4. Ingest the first WTC 7 dump; test search with leg filters + the opposing-leg pull.
5. Then widen ingestion (vault, papers, transcripts) in batches, each logged in `manifests/`.

## 9. Kill conditions

- **V1:** leg-filtered retrieval on WTC 7 misses passages David marked pink in a whole read → retrieval is unreliable at this chunk size; re-chunk or rely on whole reading.
- **V2:** index rebuild from `corpus/` does not reproduce search results → something outside the corpus is being treated as truth; fix before scaling.

## 10. Rulings from David (2026-10-15)

- **NAS location:** a new **V: drive** dedicated to vectorization. `<NAS_VECTOR_ROOT>` = `V:\` (confirm exact share path when created).
- **Ingestion order:** delegated to the builders. Proposed order (smallest and most controlled first, so problems surface early):
  1. **WTC 7 research dump.** First test; small, fully known, checkable against David's pink highlights (V1).
  2. **Canonical documents** (canon folders, Master Equation set, Truth Engine blocks). Small, high-value, the core everything else is checked against.
  3. **Papers** (the ~1,300 research papers, in batches).
  4. **Wider vault** (working notes, session logs).
  5. **Transcripts** (YouTube/TikTok pipeline output). Largest and noisiest, so last.
- Tag each batch with `corpus_type` so canon is never mixed with working notes in search results unless asked.

---
*v0.1 — 2026-10-15 — David Lowe + Claude (Opus). "The corpus is the truth; the index is disposable."*
