# Acquisition Screen — Build Prompt v0.1 (DRAFT)
**Date:** 2026-10-06 · **Owner:** David Lowe · **Builder:** Claude Code (sole builder on this repo)
**Status:** DRAFT. Open items marked ASK DAVID.
**Siblings:** DEEP_RESEARCH_SCREEN_BUILD_PROMPT_v0.1.md, LAST30DAYS_SCREEN_BUILD_PROMPT_v0.1.md —
same queue folder, same job UUID, same two-tier screen, same receipts discipline.

## Purpose (read this before touching code)
Stated by David: "all of this is for the hard-to-find topics." Not page one of Google — the thing page
one doesn't have. Four verbs, chained: SEARCH (candidate URLs from many indexes) → LINKS (expand from
a good page: outlinks, citations, references) → CRAWL (bounded walk of a site that matters) → SCRAPE
(clean text + metadata). Output is ONE record shape that every other screen already eats
(GPTR `scraped_content` (url, raw_content); last30 `SourceItem`; CKG intake). Acquisition stops at
clean text. Judging is downstream (fork-finder, CKG). Everything acquired lands in the one `visited_urls`
ledger (Deep Research §5) so nothing is fetched twice across stations.

## Inventory (as found on disk, apps/Research-Acquisition unless noted)
- `link-research-engine/` — the closest thing to the station already: intake → discovery → classifier
  → dedupe → exporter, plus `role_engine.py`, `theophysics_seed.py`, a GUI, and a PROJECT_MAP that names
  the three phases (links → rip pages + outlinks + score → claims/entities/graph). Its search layer
  (`modules/search_providers.py`) is a DuckDuckGo HTML scrape plus an Exa "hint" that tells a human
  to go type the query. The Oct 3 "80 Arguments" run (`80 Arguments/search_report_20261003_032748.md`,
  Q-MORAL-OBJECTIVE) returned **0 results**. The DDG scrape is blocked. STRUCTURAL for this screen:
  the search layer that feeds everything else currently returns nothing.
- GPT Researcher retrievers (Deep Research §Engine) — 20 retrievers incl. tavily (keyed), exa, arxiv,
  openalex, semantic_scholar, pubmed_central, plus its scrapers and SSRF guard. This is the working
  search layer we already own; it is hidden inside the deep-research engine. Expose it.
- Serper key exists (last30days .env). Exa: `EXA_API_KEY` not set there; David uses Exa — ASK where.
- `trafilatura/` — vendored checkout. Best-in-class boilerplate removal for article text. Use it.
- `API_ALL/crawl4ai`, `API_ALL/Crawl4ai-rag`, `API_ALL/duke_axioms_crawl` — JS-capable crawler plus
  one specific crawl job. crawl4ai is the CRAWL verb; trafilatura is the SCRAPE verb; don't merge them.
- `theophysics-link-harvester/` — `harvester.py`, `math_scripture_harvester.py`, `math_scripture_queries.json`
  with an output folder: a working query-list → links harvester. Absorb its query-list format.
- `RECOVERED_CLOUDFLARE_DEEPCRAWL_2026-08-31/` — two HTML GUIs, no backend. UI reference only.
- `Rust-Search-/` (tpsearch) — LOCAL .md index + query (Phase 1). This is the Search Engine SCREEN,
  not an acquisition tool. Leave it there; acquisition writes into folders tpsearch indexes.
- `apps/MarginaliaSearch` — fresh clone, untouched. A full independent small-web search engine (Java,
  its own crawler + index). Self-hosting it is a project of its own. It also has a public API.
  ASK DAVID: self-host vs API key. The small web is exactly where hard-to-find lives, so it stays in
  the plan either way.
- `apps/Automated-AI-Web-Researcher-Ollama` — fresh clone, untouched. Overlaps GPTR. Evaluate once;
  probably retire.
- RECON (Playwright/BrowserOS + SBERT + DeBERTa NLI + Neo4j, per David's prompt) — not in this repo.
  ASK DAVID: where it lives. It is the LINKS/JS-page layer if it runs.
- Dead: `START_*.bat` at the root, `WHICH_RESEARCH_TOOL.md` (points at archived local-deep-research),
  link-research-engine's intake path `C:\Users\lowes\Desktop\TEMPLATE_THEOPHYSICS_FACTS.xlsx`
  (different user profile; stale).

## What we keep, and what we do NOT inherit
KEEP: link-research-engine's pipeline shape and classifier/dedupe/role modules; GPTR retrievers + SSRF
guard; trafilatura; crawl4ai; the harvester's query-list JSON; tpsearch as the index that acquisition
feeds; Marginalia as the small-web index; the forums registry (`data/forums.yaml`, last30 §1) as a
search provider in its own right.
DO NOT INHERIT: the DDG HTML scrape (dead, never reliable); the Exa "hint" (a human in the loop is not
a provider); the Excel intake path; the Cloudflare GUIs as anything but a sketch; the dead launchers.

## The record (one shape, every verb emits it)
`{job_uuid, url, canonical_url, title, text, published_at, fetched_at, provider, stage(search|links|crawl|scrape),
 parent_url, depth, outlinks[], content_hash, extractor, status, bytes, notes}`
- `canonical_url` + `content_hash` are the dedupe key and the `visited_urls` ledger entry.
- `parent_url` + `depth` are the provenance chain: how we got here. Hard-to-find pages are found by
  chains, not by queries; the chain is the receipt.
- Every verb writes a RECEIPT beside its output: URLs attempted, fetched, skipped (and why: robots,
  4xx/5xx, size cap, SSRF guard, dedupe hit), text length, extractor used. Same discipline as the
  Deep Research read receipt.

## Build order (proposed)
### 1. SEARCH station   ← first, because today it returns zero
- One `search` CLI, provider-pluggable, fan-out, merged + deduped. Providers in tiers:
  - Paid, keyed, reliable: tavily (have), serper (have), exa (ASK). These replace DDG, period.
  - Academic, free: openalex, semantic_scholar, arxiv, pubmed_central (all already in GPTR).
    These are the "hard to find" tier for physics/theology — turn them ON by default in our class.
  - Small web: Marginalia (API or self-host, ASK). Also hard-to-find tier.
  - Forums: query the enabled forums registry directly (Discourse/SE search endpoints).
- Input = the harvester's query-list JSON (one file per argument, many queries each), or one query.
- Output = search records + receipt (provider, query, hits, errors). A provider returning 0 is a line
  in the receipt, not a silent nothing.
### 2. LINKS station
- Take a record (or any URL), rip the page, extract outlinks, classify them (link-research-engine
  `classifier.py` / `role_engine.py` — reuse), score, emit child records at depth+1.
- Citation chasing is the whole point: references sections, footnotes, "see also", author pages.
  Academic pages: follow DOI/OpenAlex "cited by" / "references" via API rather than scraping.
- Bounded by depth and by domain allowlist/denylist from the job YAML.
### 3. SCRAPE station
- trafilatura first (fast, clean). crawl4ai (headless) when trafilatura returns under N chars or the
  page is JS-rendered. Playwright/BrowserOS only for login walls — flagged in the receipt, never silent.
- Honor robots. SSRF guard from GPTR.
### 4. CRAWL station
- crawl4ai bounded site walk: seed URL, max depth, max pages, same-domain, include/exclude patterns.
  Emits records through SCRAPE. This is for "this whole site matters" (a journal, a forum archive,
  a seminary's paper repository), not for the open web.
### 5. Ledger + handoff
- All records append to the one `visited_urls` ledger (shared with Deep Research). Dedupe before fetch.
- Clean-text records drop into a folder tpsearch indexes and CKG intake watches. No second database.

## Job YAML (same queue folder)
`job_type: acquire`; `verbs: [search, links, scrape]` (crawl opt-in); `queries_file` or `query`;
`providers[]`; `depth`; `max_pages`; `domains_allow[]`; `domains_deny[]`; `extractor`; `out_dir`; `chapter`.

## Screen — two tiers, same shell
- TIER 1: one text box. Query in → search (all enabled providers) → links depth 1 → scrape → records
  shown as pills with the provenance chain, receipt beside. Defaults everywhere.
- TIER 2 (expand): providers, tiers on/off, depth, crawl bounds, extractor, allow/deny, output folder,
  queries-file picker. Run log streams the receipts.

## ASK DAVID before touching
- Where RECON lives, and whether it is alive.
- Exa: key, and where it is.
- Marginalia: self-host (big) or public API (fast).
- Kill list confirmation: DDG scraper, Automated-AI-Web-Researcher-Ollama, dead launchers, WHICH_RESEARCH_TOOL.md.
- Frontend tech (hub-wide, still open).
