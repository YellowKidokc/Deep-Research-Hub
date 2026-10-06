# Next Tasks

## Highest-value next tasks

1. Build a canonical URL and dedupe module.
2. Add a page-ripping module that accepts kept links from the role engine.
3. Export non-Wiki enrichment into a polished workbook.
4. Add link-list mode for user-provided URLs.
5. Add Excel-driven run configuration.

## Best bounded prompt for another AI

Build the next module for `link-research-engine`:

- Input: candidate links from `run_nonwiki_enrichment_demo.py`
- Process:
  - normalize URLs
  - dedupe by canonical target
  - group by domain
  - preserve source role and score
- Output:
  - cleaned CSV
  - workbook tab or workbook file

Keep the implementation modular and compatible with the existing `src/link_research_engine/modules` layout.
