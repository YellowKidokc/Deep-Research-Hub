# Deep Research Screen — Build Prompt v0.1
**Date:** 2026-10-06 · **Owner:** David Lowe · **Builder:** Claude Code (sole builder on this repo)
**Status:** LOCKED by David. Open items marked ASK DAVID — do not decide them yourself.

## Purpose (read this before touching code)
This screen exists to run a 40-job matrix: 20 THE_STORY chapters (AX_GI_01..20) × 2 job types
(cold-derivation, prior-art sweep). The engine must be built for that matrix, not for one-off queries.
Secondary purpose: a giveaway class of the same tool (queue deep research from inside your own Obsidian).

## Engine (as found, verified running 2026-10-06)
- GPT Researcher checkout: `D:\GitHub\Research-Acquisition\Researcher\gpt-researcher`
  (mirrored under `apps/Research-Acquisition/Researcher/gpt-researcher` — treat the D:\GitHub one as source).
- LLM: `deepseek:deepseek-chat` for FAST/SMART/STRATEGIC. Embeddings: `ollama:nomic-embed-text`. Retriever: `tavily`.
- Keys live in Windows USER env (DEEPSEEK_API_KEY, TAVILY_API_KEY). The LLM/EMBEDDING/RETRIEVER lines are NOT
  in gpt-researcher/.env — they are in `Research-Acquisition\gptr-mcp\.env`. A bare launch silently falls back
  to OpenAI. Fix: copy those lines into gpt-researcher/.env (no keys).
- Working launcher: `gpt-researcher\windows_launcher.py` (uvicorn 127.0.0.1:8000, applies RESEARCH_PROFILE.env).
- Root launchers in Research-Acquisition (`START_*.bat`) are DEAD: they point at `%ROOT%gpt-researcher\`
  (moved under Researcher\) and call `continuous_runner.py` / `START_GPT_RESEARCHER_CHOOSE_FOLDER.ps1` which
  don't exist in the live checkout. Repair or delete; `WHICH_RESEARCH_TOOL.md` is stale too.

## What we keep from GPTR, and what we do NOT inherit
KEEP: retrievers (20, incl. arxiv/openalex/semantic_scholar/pubmed_central/exa), scrapers, visited_urls dedup,
SSRF guard, the websocket log stream (every stage emits named events — that is our receipts stream), gptr-mcp.
DO NOT INHERIT: `skills/deep_research.py` recursion (thesis-deepener, auto-answers its own clarifying
questions with "Automatically proceeding"), the curator (one LLM opinion, no receipt), the 0.35 similarity
filter as the only path to context. GPTR is the ACQUISITION engine: search → scrape → chunk. We stop it there.

## Build order (LOCKED)
### 1. Folder-per-job + read receipt   ← first, everything depends on it
- `doc_path` becomes a per-request field (backend already accepts `document_urls` per request; extend to a
  local folder path). Server must NOT need a restart to change folders.
- Every job writes a READ RECEIPT: files found, files loaded, files skipped (and why: size cap, type, error),
  chunks produced, chunks kept vs dropped by similarity, per sub-query. JSON next to the output.
  Rationale (David, verified): GPTR reads a fraction of the folder, keeps a fraction of that, reports nothing.
- Surface the RESEARCH_PROFILE knobs (breadth, depth, concurrency, curate, results/query) on the form.

### 2. Queue folder
- `data/jobs/<job>.yaml` one per job; `data/jobs/_defaults.yaml` inherited by all.
  Fields: query, chapter (AX_GI_nn), job_type (cold_derive | prior_art | hybrid_rule | standard), report_source
  (web | local | hybrid), doc_path, retrievers[], model, custom_prompt, depth/breadth overrides, visited_urls_from.
- Runner walks the folder, runs each, writes output + read receipt + run ledger, moves yaml to `data/jobs/done/`.
- This replaces the dead `research_queue.txt` + `continuous_runner.py`.

### 3. Job templates
- **cold_derive**: input = root statement + ONE chapter claim, NO framework vocabulary in the prompt. Ask: what
  does this root entail, how do you reach the conclusion, where does it fail. This is a test, not research.
- **prior_art**: fork-finder on the chapter claim: who said this, in what words, when. Receipts required
  (dated quote, primary source). No receipt → "unknown" is the legal answer. Never smooth a weird origin.
- **hybrid_rule**: local folder = the article(s); web = everything else; custom_prompt = rule on / rewrite /
  add / cut / make coherent, show diffs. ("Already wrote the article — give it another look.")

### 4. Fork-finder skill
- New file `gpt_researcher/skills/fork_finder.py`, sits BETWEEN scrape and compression, consumes raw
  `scraped_content` (url, raw_content) per sub-query BEFORE the similarity filter narrows toward the query.
- Output = pills, not prose. Fork pill fields: ASK DAVID (proposed: fork_name, core_question, positions[],
  sources_per_position[], receipts[]).
- Not a patch to deep_research.py.

### 5. Run ledger (the only "memory")
- Per topic: what was asked, URLs visited, learnings, receipts. Feed last run's visited_urls into the next run
  on the same chapter (GPTR already accepts `visited_urls` on construction) → cumulative, goes wider each time.
- Canon JSON / pills remain THE memory. Do not build a second memory inside this tool.

## Classes
1. Giveaway: web + local docs, job-level folder picker, queue folder, Obsidian plugin shell. No framework vocabulary anywhere.
2. Ours: same engine + academic retrievers ON + vault as local source + pills out + fork-finder.
3. Locked preset of (1) with David's prompts baked in — only if the class needs it.

## ASK DAVID before touching
- Which frontend gets the in-house theme: static vanilla (`/`) or Next.js, or does the hub shell replace both.
- Fork pill schema (above).
- Exact academic retriever set for class 2.

## Noise / INERT
- `.runtime/server.log` shows `ahk-main` polling `/bridge/jobs` on :8000 (404s) — AI-HUB.ahk expects a
  job-bridge endpoint this server doesn't have. Harmless. Either give it the endpoint in the queue runner or point it elsewhere.

## Next screen after this one: last30days (`apps/last30days-skill`).
