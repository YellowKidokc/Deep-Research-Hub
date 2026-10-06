# Link Research Engine

Modular link-ingestion and source-research workspace.

This project is the clean orchestration layer around:

- `crawl4ai` for crawling and page extraction
- workbook exports for human review
- later: Postgres, embeddings, and graph enrichment

## Core idea

Build the system in separate, testable pieces first:

1. intake
2. discovery
3. link extraction
4. classification
5. scoring
6. export

Then wire the pieces together into a repeatable Docker-friendly pipeline.

## First-phase goal

Focus only on links coming in:

- case names in
- links out
- categorized
- deduped
- exported to Excel/CSV

## Module map

### `intake`
- Reads case lists and run settings.
- Defines target, scope, depth, output, and organization mode.

### `discovery`
- Finds candidate links from Wikipedia, trusted hubs, and later web-wide search.
- Supports provider layering: simple HTML search now, browser-driven providers later.

### `ripper`
- Pulls page content and outgoing links from selected sources.

### `classifier`
- Labels links by source type, domain class, and trust tier.
- Includes a role engine for deciding what to keep, review, or discard.

### `scoring`
- Ranks links for review and later page ripping.

### `exporter`
- Writes CSVs and workbook-friendly outputs.

## Relationship to `crawl4ai`

`crawl4ai` stays the crawling engine.

This repo becomes the research console and pipeline wrapper that:

- feeds case lists into crawlers
- decides what mode is running
- normalizes outputs
- exports review artifacts

## Suggested build order

1. Finish Wikipedia discovery mode
2. Add trusted-source enrichment mode
3. Add canonical URL normalization and dedupe pass
4. Add workbook export and merge rules
5. Add page-ripping mode
6. Add classification and scoring
7. Add Docker packaging

## Current utility scripts

- `scripts/run_nonwiki_enrichment_demo.py`: collect candidate links and score role fit.
- `scripts/run_nonwiki_dedupe.py`: canonicalize URLs, dedupe by case + canonical target, and output:
  - `data/output/nonwiki_enrichment_demo_deduped.csv`
  - `data/output/nonwiki_enrichment_demo_duplicates.csv`
  - `data/output/nonwiki_enrichment_demo_dedupe_summary.json`

## Six control questions

1. What is the target?
2. What do you want to do?
3. Where should it search?
4. How deep should it go?
5. What output do you want?
6. How should results be organized?
