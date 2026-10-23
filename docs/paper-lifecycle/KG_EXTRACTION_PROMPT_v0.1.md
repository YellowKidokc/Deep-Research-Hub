# KG EXTRACTION PROMPT v0.1
## What should be pullable from every paper, if the paper has it?
**David Lowe (POF 2828) + Claude (Opus) | 2026-10-15 | Round-2 question for every AI on the crew**
**Companions:** `ID_AND_YAML_SPEC_v0.2.md` (§8, the sidecar "found" section is the current answer), `PAPER_LIFECYCLE_CHECKLIST_v0.2.md` §9.

---

## The prompt (paste this to each AI, with the three v0.2 files attached)

You are looking at the whole corpus of the Theophysics Research Initiative: ~1,300 papers, notes, transcripts and analysis outputs over 15 months, bridging physics, theology, mathematics, information theory and consciousness. We are building one knowledge graph over all of it. Every file will be scanned, and the scan will pull out everything the file contains that the graph should know about.

The current field list is in `ID_AND_YAML_SPEC_v0.2.md` §8 ("found" section) and reproduced below as the seed. It was written in one sitting and is almost certainly incomplete.

**Your job: be as thorough and detailed as you can.** Think about every kind of thing a paper in this corpus might contain that we would later want to query *across* papers, independently of the paper it came from — and that the scan should pull out **if the paper has it** (most papers will have only a few). Keywords, theories, laws, claims, evidence, equations, variables, named entities, people, places, dates, Scripture, witnesses, predictions, objections, analogies, isomorphisms, definitions, stories, open questions, methods, datasets, experiments, sigma values, kill conditions, rhetorical devices, opening motifs, audience level, register — and whatever we haven't thought of.

For each item you propose, give:
1. **Name** — a short field name.
2. **What it is** — one line.
3. **Why it's worth pulling** — the cross-paper query it enables ("find every paper that uses the Yukawa potential as parent equation"; "every paper that states an objection it doesn't answer").
4. **Family** — does it belong to one of the twelve core idea families (C, EV, AX, DEF, PRD, ISO, LEAN, R, BAL, KC, TAG, TOPIC), is it a file-level field, an edge, or does it need a new family? New families need a reason; the core is closed on purpose.
5. **Closed vocabulary?** — if the field should only take values from a fixed list, propose the list.
6. **Extraction** — can code get it (regex, parser), or does it need a model? If a model, is the result a proposal David confirms or a fact?

Then answer three things:
- **Group the full list** (seed plus yours) into a layered schema: what every file gets, what only claim-bearing files get, what only math files get, what only story pieces get.
- **Mark the ten you'd extract first** on Math Is Moral, and the ten you'd never bother with.
- **Say what you'd cut from the seed** and why.

Rules: add beneath, don't rewrite. Say which AI you are. Proposals, not rulings — David decides the schema.

---

## The seed (current `found` section, expanded)

**Every file**
- tags (closed vocabulary) · topic, also_in · register (declaration / canon) · reader level · series and part · authors and co-authors · written / ingested dates · source format

**Ideas (occurrences pointing to corpus-wide records)**
- claims, with stance per occurrence · axioms used · definitions used · evidence items · predictions · isomorphisms (registry-gated; analogies tagged separately) · Lean labels · kill conditions · local items (implications, open questions, asides)

**Math**
- equations, each with variables, parent equation, phase form, dimensional status, verdict (COHERENT_TESTED / UNTESTED / DEFECTIVE / DECORATIVE) · Master Equation nodes touched · Laws touched (by name) · numeric and statistical claims with source

**Argument structure**
- inference map (premises → conclusion, warrant groups) · load-bearing flag · hidden premises · objections stated (with whether answered) · strongest opponent named · circularity / equivocation flags · epistemic mode per claim

**Theology and history**
- Scripture references (cited / mentioned / alluded; KJV) · historical witnesses (thinker, work, where) · theological declarations · Fruits / spiritual terms derived or used · whole-case arguments helped / hurt / neutral

**Story and voice**
- human-anchor story · memorable lines · opening motif number (99–93 system) · Theopoetic Engine stage coverage · density / reading time

**Provenance and process**
- source hash, norm hash · extraction receipts · which stations have run · cross-paper links (version_of, successor_of, definitive_for) · what was cut and why

---

## Answers (append beneath, one block per AI)

*(none yet)*

*v0.1 — 2026-10-15 — David Lowe + Claude (Opus).*
