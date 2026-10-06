# Project Map

## Purpose

Turn link gathering into a repeatable research operation.

## Canonical inputs used

- `C:\Users\lowes\Desktop\TEMPLATE_THEOPHYSICS_FACTS.xlsx`
- `RESEARCH_INTAKE` sheet
- existing `D:\GitHub\crawl4ai` harvesting scripts

## Structured output

### Phase 1
- Case list intake
- Wikipedia link discovery
- Trusted-source link discovery
- Workbook export

### Phase 2
- Page ripping
- Outgoing-link extraction
- Source classification
- Link scoring

### Phase 3
- Structured claims
- Entities
- Timelines
- Graph edges

## Repo structure

- `config/`
  Run profiles, source hubs, and export settings.
- `data/input/`
  Case lists and manual seeds.
- `data/output/`
  CSV and JSON output artifacts.
- `data/workbooks/`
  Review workbooks and templates.
- `scripts/`
  Small launchers and integration scripts.
- `src/link_research_engine/modules/`
  Core pipeline modules.

## Core packages

### Discovery layer
- Crawl4AI
- later optional Playwright/Crawlee fallback

### Content layer
- Trafilatura or built-in markdown extraction

### Export layer
- openpyxl
- CSV / JSON

## Audit Footer

### Where We Are Right

The intake workbook already defines the process cleanly enough to become software.

### Where We Might Be Wrong

Some module boundaries may merge later once the real pipeline stabilizes.

### What We Think

This repo should stay narrow and modular until the link phase is fully reliable.
