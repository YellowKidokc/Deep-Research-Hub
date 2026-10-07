# The Writer (screen 7) — design v0.1

**Date:** 2026-10-07 · **Owner:** David Lowe · **Status:** DRAFT. Built: the Story tab (right column) with checklist, paragraph stats and research cards (build step 1).
**Surface:** OpenWriter (`apps/openwriter`, MIT, unchanged upstream copy). It is the last app added to the hub.

The Writer is where everything gathered on one topic lands, gets sorted, and becomes a story. Research (screen 1 and 2), transcripts (screen 5) and classifications all feed into it. The person decides every word that stays.

---

## Layout

Obsidian-style, three columns:

| Left column | Centre | Right column |
|---|---|---|
| Documents and workspaces (OpenWriter's existing sidebar) | The document being written: the agent proposes, the person accepts or rejects (green insert, blue rewrite, red delete) | **What the system knows about this text**: proposed classifications, and the research cards that match them |

## What happens when a paper is pasted into a blank page

1. **Classify.** The text is classified with the circles from `docs/WEB_RESEARCH_v0.1.md` §4: domain slot, structural role and edges, position, tags. Proposals only, with a runner-up and confidence. Low confidence goes to the hold bucket, never force-fit.
2. **Pull the matching research** into the right column, by those classifications and by topic:
   - **Origin / first use**: who coined the term, where it was first used, the history of the word (etymology).
   - **Academic test**: has a study or experiment tested this, structurally? The essence paper, not the most-cited one.
   - **Precursor**: who predicted this long before its time.
   - **Forks**: the distinct arguments inside the topic, with positions and sources.
   - **Transcripts**: matching YouTube transcripts and their baseline summaries.

   Each card carries its receipt (dated quote, primary source). A card without a receipt shows as **unknown**, not as a fact.
3. **Interject.** A card can be dropped into the document at the cursor as a proposed insert, carrying its source with it.

## Rewrite by selection

Select text → right-click → rewrite: in a tone, shorter or longer, plainer, as the Skeptic, as the unforgotten sentence (several candidates, pick one). Every rewrite arrives as a pending change to accept or reject. The prompts for these live in `prompts/` (the API Layer, screen 6), never hard-coded.

## Aggregate → story pass

When all the research on a topic is in, one pass picks out: story mechanisms, weird facts, the best arguments, and the rest of the story list being designed separately (the Story API, an expected 20–40 pages of calls).

**Recommended shape:** do this in two steps, not literally one call. First, one call per source turns it into pills that each keep their source (claim, quote, receipt). Then the story pass runs over the pills. Reasons:
- A single call over everything hits the context limit on a big topic, and quietly drops whatever it couldn't fit.
- A weird fact that has lost its source can't be checked, and it's exactly the kind of fact that needs checking.
- The pills can be re-used by the next topic and the next video; one big answer can't.

## How it plugs into OpenWriter (without forking it)

OpenWriter plugins can add agent tools (MCP), server routes, right-click actions on a selection, and sidebar menu items. So:

- **A `drh` plugin** (new folder under `apps/openwriter/plugins/`, recorded in `UPSTREAM.md`):
  - routes that read `data/deep_research/`, `data/youtube/` and the classification records, and return cards for a document;
  - MCP tools so the agent can fetch cards, classify a document, and insert a card with its source;
  - right-click actions for the rewrite modes, each calling a slot in `prompts/`.
- **The right column is the one change to OpenWriter itself.** Its plugin API has no panel hook (`sidebarMenuItems` adds menu entries only), so the column needs a small UI addition in `packages/openwriter/src`, recorded in `apps/openwriter/UPSTREAM.md`. Everything else stays in the plugin.

## Not decided — ASK DAVID

- The Circle 1 slot list and the local schema per slot (classification Phase 0: ~25 hand-classified fixtures first).
- The tone list for rewrites.
- The Story API pages (being designed with another AI); they arrive as slot sets in `prompts/`.
- Whether the story / college / PhD versions from the original hub spec are still the three outputs.

## Build order (proposed)

1. **Built.** Right column (OpenWriter's Story tab) + `drh` plugin: story checklist from `prompts/W_story_checklist.json` (green when done, saved per doc), paragraph word/sentence counts against a band, research cards matched by topic. Classification not yet.
2. Rewrite-by-selection actions wired to `prompts/` slots.
3. Classification proposals (after Phase 0 fixtures exist).
4. Pills per source, then the story pass, once the Story API pages are ready.
