# Evidence Chain Plan

## Purpose

Define the next layer after ingestion:

- links come in
- pages get mapped
- evidence gets sorted
- useful research objects come out

This is the conceptual bridge between link intake and full research automation.

## Phase 1 — Link Intake

Input:
- case name
- website
- topic
- manual link list

Output:
- raw links
- deduped links
- source domains
- preliminary scores

## Phase 2 — Page Mapping

Each kept link should be mapped into a page object.

Minimum fields:
- `url`
- `canonical_url`
- `title`
- `domain`
- `source_type`
- `provider`
- `snippet`
- `discovery_reason`
- `keep_reason`

If ripped:
- `clean_text`
- `outgoing_links`
- `date_candidates`
- `author_candidates`
- `downloadables_present`
- `pdf_links_present`
- `reference_section_present`

## Phase 3 — Research Object

After mapping, each page should become a research object.

Target object:
- `page_summary`
- `main_claims`
- `evidence_snippets`
- `entities`
- `timeline_candidates`
- `trust_notes`
- `contradiction_notes`
- `why_keep`

## Evidence Sorting Model

The engine should sort evidence by:

1. source strength
2. independence
3. document quality
4. relevance to the case
5. specificity of claims
6. presence of primary artifacts

## Evidence Tiers

### Tier 1
- primary documents
- government records
- court material
- direct transcripts
- original datasets

### Tier 2
- reputable analysis citing primary material
- archives
- serious reference pages

### Tier 3
- commentary
- secondary summaries
- blog interpretation

### Tier 4
- weak speculation
- low-context reposts
- unsourced compilation pages

## Suggested Research Flow

1. ingest links
2. dedupe and score
3. keep top links
4. rip top links
5. extract metadata and entities
6. summarize only the strongest pages
7. build workbook / notebook output

## Model Strategy

### Cheap / local first
- metadata extraction
- date extraction
- entity extraction
- duplicate detection

### Strong model second
Only on top pages:
- summarize page
- identify claims
- extract evidence snippets
- explain why it matters
- mark contradictions or caveats

## Near-Term Build

The next concrete module set should be:

- `ripper.py`
- `page_mapper.py`
- `page_research.py`
- `evidence_sorter.py`

## What We Think

The next big gain is not more raw links. It is turning the best links into structured evidence objects that can be reviewed, exported, and later graphed.
