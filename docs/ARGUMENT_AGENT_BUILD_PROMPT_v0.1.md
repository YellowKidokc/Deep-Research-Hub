# ARGUMENT AGENT — Build Prompt v0.1
**Date:** 2026-10-22 | **Status:** Draft for David's approval before any build
**Builder:** unassigned (coder-ready; written to be handed to Claude Code or an online coder cold)
**Drafted by:** Claude (Fable), per David's direction to spec the continuously-running research agent

---

## What this is

A continuously running (or scheduled) research agent with ONE job:
keep the argument folders fed.

The argument tree is the target, not a suggestion:

```
\\192.168.2.50\h_hp\Desktop\Youtube API CKG\_API\_ARGUMENTS\
  01_S-EVIL_Evil_and_suffering\Q-EVIL-EVIDENTIAL\ ... (21 sections, ~100 Q-code folders)
  argument_ledger.csv / argument_ledger.json
  build_folders.py
  DEBATE_MAP.md
```

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
