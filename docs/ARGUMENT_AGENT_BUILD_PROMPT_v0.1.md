# ARGUMENT AGENT — Build Prompt v0.1
**Date:** 2026-10-22 | **Status:** Draft for David's approval before any build
**Builder:** unassigned (coder-ready; written to be handed to Claude Code or an online coder cold)
**Drafted by:** Claude (Fable), per David's direction to spec the continuously-running research agent

---

## What this is

A continuously running (or scheduled) research agent with ONE job:
keep the argument folders fed.

The argument tree is the target, not a suggestion.
**CORRECTED 2026-10-23 (David ruled): the home is the Canon DEBATE_MAP, not the NAS copy.**

```
C:\Users\David\Documents\faiththruphysics.com\Canon\DEBATE_MAP\
  P00_GROUND_RULES ... P10_PEOPLE   (11 parts, 112 Q-folders in case order; restacked Oct 19)
  00_INDEX.md, CASE_STACK.md, DEBATE_MAP.md, MIRROR_QUESTIONS.md, RESTACK_LOG.md
  restack.py, build_folders.py
```

Every question carries a domain tag: SHARED / SCI / THEO / PASTORAL (see CASE_STACK.md).
The older topic-layout copy at `\\192.168.2.50\h_hp\Desktop\Youtube API CKG\_API\_ARGUMENTS\`
(21 S-sections, Oct 17) is SUPERSEDED. Do not write to it. Its `argument_ledger.csv` must be
migrated or rebuilt against the Canon tree before milestone 1. The 00_PREP gate
(`docs/superpowers/specs/2026-10-20-api-prep-gate-design.md`) is DESIGNED to produce
`debate_map_matches` per item but is NOT BUILT yet (checked 2026-10-23: no `00_prep.py`, no
`debate_map` key in `paths.json`). When it lands, Lane B's stub writer consumes those matches
and does not redo the matching. Until then Lane B must do its own Tier-0 matching.

Two lanes, same agent:

- **Lane A — OUTWARD (new material):** research runs that pull new material from the
  web/forums/YouTube pipeline for a given Q-code and file it.
- **Lane B — INWARD (corpus match):** walk David's existing corpus and match existing
  papers/notes/transcripts to Q-codes. David: "one going through my past corpus to match
  existing work to questions." This lane produces no new research — only stubs + ledger rows.

David's words for the whole thing: "a full-time job."

---

## Standing rules (inherited — do not re-decide these)

1. **Nothing is dropped — status, not deletion.** The agent returns ALL arguments found,
   including settled/"stupid" ones. It never pre-filters to the live legs and never assumes
   David's thesis. (Hub-wide rule, already written into the hub.)
2. **Simple case default.** One input (a Q-code, or "sweep"), defaults everywhere; a second
   expanding interface for depth. Same look as the other screens.
3. **Working originals stay separate.** The agent copies/borrows from D:\GitHub and the NAS;
   it never edits source repos.
4. **One canonical home per document; argument folders hold STUBS, not copies.**
   (Ruled 2026-10-22, this session.) A stub is a small .md containing: doc UUID, canonical
   path, source lane, date, and one line on WHY this doc serves THIS argument. A doc serving
   five arguments = one body, five stubs. The ledger is the registry: UUID → Q-codes → stub paths.
5. **New Q-codes require a ledger row** stating which existing code the new one is distinct
   FROM and why the distinction matters. Folders are created only through build_folders.py,
   never by hand. Sections (the 21) change rarely; Q-codes grow freely under this one-line rule.
6. **Source lane is metadata, not address.** Origin (habermas-channel, godlogic, tiktok-recon,
   forums, web) is a ledger column. Arguments are the only folder axis.
7. **Dedup before filing.** Content hash checked against the ledger. Same content arriving
   from two sources = one canonical doc, two source-lane entries, stubs unchanged.

---

## Lane A — Outward research runs

**Input:** a Q-code (e.g. Q-BEGIN-NOTHING), or a queue of Q-codes, or "thinnest-first"
(agent reads the ledger, ranks Q-folders by stub count, works the thinnest).

**Per run:**
1. Read the Q-folder's existing stubs + DEBATE_MAP.md entry → build the "already have" set.
2. Research pass through the existing hub engines (GPT Researcher engine / last30days
   forums lane / Acquisition screen — reuse, do not rebuild). Planner may propose sub-queries;
   ALL results are kept per Rule 1.
3. Output per source found:
   - raw pull → canonical home under the Q-folder's `_intake/` (new material has no other home yet)
   - ledger row: UUID, content hash, source lane, URL, date, Q-code(s), status=NEW
   - stub in each matched Q-folder
4. Run receipt (YAML) in the Q-folder: what was searched, what was found, what was filed,
   what failed. Receipts are append-only.

**Status vocabulary (ledger `status` column):** NEW → REVIEWED → USED | PARKED | RETIRED.
RETIRED means "settled/known-bad argument, kept on purpose" — never deleted (Rule 1).

## Lane B — Inward corpus matching

**Scope v1 (expand later):** the obsidian_indexed transcripts, EVIDENCE OUTBOX lanes,
and one corpus root David names at runtime. NOT the whole NAS in v1.

**Per file:** cheap classification first (Tier 0: keyword signatures per Q-code, derivable
from DEBATE_MAP.md + folder names), escalate ambiguous files to a model pass (DeepSeek —
David runs it — through the hub's existing OpenRouter path). Output = stubs + ledger rows
only. The file itself is never moved: its canonical home is where it already lives (Rule 3).

**Confidence is three-valued** (matches the canon-stamp design): MATCHED (auto-stub),
CANDIDATE (stub flagged for David's review), NO-MATCH (logged, not stubbed). Tier 0 may
never write MATCHED on its own for subtle Q-codes; keyword-obvious ones (explicit
"Euthyphro", "Kalam", "fine-tuning") may.

---

## What the agent must NOT do

- Must not delete, merge, or rewrite any document.
- Must not create Q-code folders by hand (build_folders.py only, with the ledger row).
- Must not summarize-and-discard: the raw pull is always kept.
- Must not rank arguments by its own judgment of quality. It may record counts and dates;
  judgment is David's and the review screens'.
- Must not run the 21-call deep chain (48/057) by default — by rule or by hand only
  (standing YouTube pipeline rule, applies here too).

---

## Where it runs (open — David decides)

Options David named: local / Ollama / Claude / Cloudflare. v1 recommendation: local,
scheduled (Rust Idle Runner already exists for exactly this — run when idle), because
Lane B is filesystem-heavy and the NAS paths are LAN. Continuous daemon can come later;
the run-receipt design makes scheduled and continuous equivalent from the ledger's view.

## Build order

1. Ledger schema extension (status, source-lane, hash, Q-codes[], stub-paths[]) +
   migration of the existing argument_ledger.csv.
2. Stub writer + dedup check (shared by both lanes).
3. Lane B Tier-0 classifier over obsidian_indexed (smallest corpus, fastest feedback).
4. Lane B model escalation.
5. Lane A single-Q-code run end-to-end through the existing engine.
6. Thinnest-first queue + receipts + the simple screen (one input box, one "advanced" fold).

Milestone 1 = steps 1–3. Demand a read receipt from the builder before any code:
they restate this doc's rules in their own words; wrong restatement = stop.

## Open questions for David (answer before milestone 2)

- Q-code keyword signatures: generate draft signatures from DEBATE_MAP.md automatically,
  or does David want to seed/edit them by hand first?
- Lane B corpus root #1 after obsidian_indexed: which folder?
- Does Lane A _intake/ material later migrate to a pipeline lane, or is _intake/ its
  permanent canonical home?
- Review screen: fold into the Search Engine screen, or its own seventh-screen tab?

---
*Blast radius of this whole spec: LOCAL. It writes stubs, ledger rows, and _intake files.
Nothing in canon, no source repo, and no existing pipeline is modified.*


---

## Dry-run findings (2026-10-23) — READ BEFORE BUILDING LANE B

A read-only prototype exists at `scripts/argument_match_dryrun.py` (Python, no writes into the vault
or DEBATE_MAP; reports go to `D:\FIS_REPORTS\argument-match-dryrun-2026-10-23\`). It scored the seven
vault roots under `C:\Users\David\Documents\faiththruphysics.com\10_VAULTS\_ Theophysics_Case_for_Christ\`.
Treat it as a sketch to learn from, not code to extend.

**Corpus reality (832 files in the 7 roots, only 69 are scorable prose):**
- `_first_principles_to_god` (31 md): a 26-question public Q&A "story spine" (Q00-Q25). It is a THIRD
  question set; it needs a crosswalk table (Q00-Q25 -> debate-map Q-IDs) that David approves row by row.
- `01-Historical-Jesus` (19): mostly unnamed "Clipboard Text (N).txt" dumps. Match on content, not names.
- `00_CORE_ARGUMENTS` (740 files, 508 MB): almost all Lean build output (.lean/.olean/.hash), 66 PDFs,
  spreadsheets and scripts. Prose lives in `06_TikTok_Core_Ideas` (18 md/txt, incl. a 559-topic URL list).
  PDFs need text extraction. Lean build artifacts must be excluded outright.
- `01_Tik Tok`, `00_CANONICAL`, `02_PHILOSOPHY_AND_WORLDVIEWS`, `01_Proofs-and-Arguments`: skeletons
  (.fisnote files, a few spreadsheets/scripts). Nothing to match yet.
- The vault root has ~20 more folders in two numbering styles (hyphen and underscore). Likely where
  more prose lives. Not yet scanned. Ask David before including them.

**Traps found (the build must handle each):**
1. Framework vocabulary poisons keyword matching: "coherence" appears everywhere in David's writing,
   so six Q-series files all landed on Q-GOD-COHERENCE. Keep a framework-term stoplist and confirm with
   the model before anything counts as MATCHED.
2. Multi-topic list files (e.g. `bulk_urls_559_topics_*.txt`) match one question at 1.00. Match at
   chunk/line level for list-like files, never whole-document.
3. Generic filenames ("Clipboard Text", "Untitled", "index", "README") must not contribute tokens.
4. Single-token questions saturate scores. Require 2+ distinct matched terms for any score above ~0.5.
5. 20 of 112 questions have no question text in DEBATE_MAP.md (the restack-added ones); their
   `QUESTION.md` files are blank too. Flag them; do not guess text for them.

**Where stubs land:** every question folder already has `00_FINAL, 01_CLAIMS, 02_EVIDENCE, 03_REVIEWS,
04_SOURCES, 05_SCRIPTS, 06_SHORTS, 07_REBUTTALS, EVIDENCE` plus QUESTION/MIRROR/OUR_ANSWER/README/VERDICT.
Source stubs go in `04_SOURCES`. Claim/evidence stubs are a later pass.

**Safety:** the vault is a git repo AND under Syncthing (`.stfolder`, `.stversions`). Anything written
there syncs and versions. Dry-run first, show David the report, write stubs only after his go, in small
batches, and never touch `.fisnote` or `.fis_meta.json`.

**Pipeline per file (matches the 00_PREP design):** Tier-0 keyword shortlist -> model confirmation through
Forge (never direct) returning 0-5 matches with score + one-line reason -> David approves (or a threshold
he sets) -> stub + ledger row. Everything below MATCHED is a CANDIDATE shown for review, not filed.

### Run 2 (2026-10-23): "Tick tock" + loose TikTok docs

- `Tick tock\` is the real TikTok arsenal: 91 files in 11 subfolders (00_COMBAT_DOCTRINE, 01_ATTACK_VECTORS,
  02_APOLOGETIC = APO-01..APO-20 argument cards, 03_THEOLOGICAL_WEAPONS, 04_BERNAYS_AND_PERSUASION,
  05_DRAFTS_AND_FRAGMENTS, 06_CONVERSATION_TRANSCRIPTS, 07_RESEARCH_BACKING, 08_REFERENCE_DATA,
  09_FRAMEWORK_SEPARATED, 999Z_ARCHIVE). Four more TikTok docs sit loose at the vault root
  (TIKTOK_ARGUMENT_STRUCTURE, TIKTOK_COMBAT_DOCTRINE, TIKTOK_DEBATE_ARSENAL, TikTok_Arguments_Master).
- `Theophysics_Case_for_Christ\` (inner) and `V2Theophysics_Case_for_Christ\` are EMPTY skeletons. Skip.
- Single-topic cards match well (about 12 of 20 APO top picks right by eye): Moral Law, Consciousness,
  Unity of Laws, Historical Jesus, Why Anything, Cumulative Case, Fine-Tuning. Misses: Justice, Purpose and
  Experience all landed on Q-BEGIN-NOTHING (a generic-word magnet); Coherence landed on Q-MIND-PHYSICAL.
  Down-weight generic stems ("noth", "someth", "mean") and rely on the model confirmation step.
- EXCLUDE: `999Z_ARCHIVE` (editor backups / duplicates) and `09_FRAMEWORK_SEPARATED` (25 framework-layer
  rewrites, mean best score 0.43: they are not question-matched documents).
- Multi-topic files again need chunk-level matching: SHORTFORM_SCRIPT_PACK_10_ARGUMENTS,
  SHORTFORM_ARGUMENT_PACK_10_HOOKS, TOP_20_ATTACK_VECTORS_DATABASE, TikTok_Arguments_Master.
- Candidate for David's "the 30": the 20 APO cards + the 10-argument shortform pack. UNCONFIRMED.
