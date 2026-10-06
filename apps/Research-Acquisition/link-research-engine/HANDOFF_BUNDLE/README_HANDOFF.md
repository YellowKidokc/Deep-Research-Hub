# Link Research Engine Handoff

## Purpose

Package the current ingestion system so another AI or GitHub collaborator can continue the build without re-discovering the architecture.

## What this project is

This repo is a modular research-ingestion engine focused on:

- link discovery
- source enrichment
- workbook-quality review outputs
- later page ripping and graph extraction

It is designed to sit beside `crawl4ai`, not replace it.

## Current build status

### Working now
- intake question model
- modular repo skeleton
- Theophysics seed ingestion from deployed metadata
- non-Wikipedia enrichment demo
- workbook export

### Not fully wired yet
- Excel-to-engine one-click execution
- full non-Wiki ripper pass
- stronger dedupe/canonicalization
- final scoring/ranking workflow
- unified GUI shell

## Key files

- `README.md`
- `PROJECT_MAP.md`
- `config/run_profile.example.json`
- `config/source_role_rules.example.json`
- `scripts/build_theophysics_intake_workbook.py`
- `scripts/run_nonwiki_enrichment_demo.py`
- `src/link_research_engine/modules/role_engine.py`
- `src/link_research_engine/modules/search_providers.py`
- `src/link_research_engine/modules/theophysics_seed.py`

## Sample outputs

- `data/workbooks/theophysics_link_intake.xlsx`
- `data/output/nonwiki_enrichment_demo.csv`
- `data/output/nonwiki_enrichment_demo_summary.json`

## Immediate next task

Build the first real non-Wikipedia enrichment pass that:

1. searches multiple providers
2. applies the role engine
3. keeps the top candidate links
4. hands the kept links to a page-ripping module
5. exports a high-quality workbook

## Constraints

- Workbook quality matters and is part of the product.
- The system should stay modular and Docker-friendly.
- Search providers should be pluggable.
- A role engine should decide what links survive.

## Relationship to Excel

Excel is the first GUI.
The intake workbook is already the process model.
The Python engine should read config-like inputs and write polished workbook outputs.
