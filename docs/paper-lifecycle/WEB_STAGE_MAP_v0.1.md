# WEB STAGE MAP v0.1
## Which existing program plugs into which page of the David-OS web app
**David Lowe (POF 2828) + Claude (Opus) | 2026-10-16**
Web app: `D:\GitHub\pipeline-workflows\CKG_SPLIT_DRAFT\serve_backside.py` → http://localhost:8771
Companion to: `PAPER_LIFECYCLE_MAP_v0.1.md`, `ID_AND_YAML_SPEC` (v0.2 now lives in the intake code)

---

## Where it stands (checked live, 2026-10-16)

| Page | Status |
|---|---|
| 1 Intake | **Built.** `intake.py` mints UUID + readable ID, freezes the original, writes the sidecar `<uuid>.meta.yaml` + `.norm.md`, keeps `registry.jsonl` and `topics.json` (ME tree + WC-01..18 seeded). 12 files ingested so far. |
| 2 Decompose | **Built (CKG run).** Folder → variants → parallel workers. V3.2 is ruled the real CKG; the live runner still sends the 3 KB template until switched. |
| 3 Verify · 4 Research · 5 Ruling · 6 Rebuild · 7 Publish · 8 Feedback · Settings | "Not Built Yet" placeholders. |

## The one idea that makes aggregation simple

**The sidecar is the spine.** Every file now has a home: `INTAKE\files\<uuid>\`, with the frozen original, a normalized working copy, and a sidecar whose "found" fields (`claims`, `occurrences`, `axioms`, `definitions`, `evidence`, `predictions`, `isomorphisms`, `lean`, `me_nodes`, `scripture`, `witnesses`, `tags`) start empty.

So aggregating doesn't mean merging programs. It means **each existing program becomes the thing that fills certain sidecar fields.** The programs stay where they are and keep working on their own. Each one gets a thin adapter:

1. **In:** a UUID → read `files\<uuid>\<uuid>.norm.md` (+ the sidecar for context).
2. **Run:** hand it to the program the way it already works (drop into its INBOX and press its button, or import its function). The program itself is untouched.
3. **Out:** copy the program's output to `files\<uuid>\<stage>\<program>\` with its run receipt.
4. **Propose:** write the fields it found into the sidecar as `proposed`, and append one event to `registry.jsonl`.
5. **Accept:** David accepts or rejects on the page. Nothing becomes `accepted` without him.

Every page in the web app is then the same screen: pick files, pick which programs run, watch progress, review what they proposed. That's the "run" page you already have, generalized.

---

## Page by page: what plugs in

Station numbers are folders in `D:\GitHub\pipeline-workflows\API`. Status from station descriptions and READMEs, not from running each one.

### 1 Intake — BUILT
- Already doing it: `intake.py` (hash, dedup, ID, freeze, sidecar, registry, topics).
- Could plug in: `56_TITLE` (standard title + previous names) to fill `standard_title`; `lean_to_md.py` (`Lean 4 Files\_LEAN_TO_MARKDOWN`) to give `.lean` files a readable working copy.
- Retire: `47_NEW_PAPER` (per-paper folder) is replaced by `files\<uuid>\`. `31_EVIDENCE_MERGE_ORIGINALS` hash matching overlaps intake's dedup.
- Open: `topic` and `register` are null on the ingested files; intake needs the ten questions on the page so those get answered at intake.

### 2 Decompose — BUILT (CKG)
- Already doing it: CKG run (`CKG_SPLIT_DRAFT\calls\`, 39 calls, V3.2).
- Plugs in → fills:
  - `21_CKG_EXTRACT_CPE` → claims / proofs / evidence split → `claims`, `evidence`
  - `45_CLAIM_ATOMS`, `62_ATOM_BUILDER`, atoms repo `claim-atom-standard-1.0` → `claims`, `occurrences`
  - atoms repo **Canonical Definition Registry** → `definitions`
  - `39_EVIDENCE_CHAIN_INTAKE_V2` → `evidence`, truth atoms
  - `44_TAGGER` → `tags`
  - `65_PAPER_INTELLIGENCE` → knowledge-graph edges (proposed)
  - Scripture / witness extraction (in CKG today) → `scripture`, `witnesses`
- **Ruling needed first:** one atom maker (45 / 62 / atoms repo). Three makers will mint the same claim three times.
- Switch: point the live runner at V3.2.

### 3 Verify — NOT BUILT
- Plugs in:
  - `43_PAPER_GRADER` → grades, self-contradiction
  - `36_EVIDENCE_THREE_DIALS` → claimed vs. earned strength (the overstatement column)
  - `58_ARGUMENT_GRADE`, `59_CHI_EVALUATOR`, `42` statistics wall
  - Lean group: `68_FORMALIZE_TARGETS` (claim → proposed Lean), `50`/`51` pairing, `52` + `D:\GitHub\lean-atom-extractor` (compiler receipts), `66` sorry/axiom audit, `67` triage, `55_LEAN_PAPERS` (theorem-to-claim ledger) → `lean`
  - `63_PAPER_AUDIT` already chains 43 → 65 → 57 → 58 → 59 → 42 → 46 → 64; it can be the page's "run all" button.
- Missing: the four-verdict equation check; the four-column audit output (held / overstated / false / missing + defensible version).

### 4 Research — NOT BUILT
- Plugs in:
  - `D:\GitHub\deep-research-hub` + `D:\GitHub\deep-research` engine (specced in `docs\engine-integration\`) → legs, raw dump, reading room → `evidence`, `witnesses`
  - `49_GAP_MAP` ("who said it first") and `33_EVIDENCE_BUILD_ONE_ARGUMENT` (lineage, originality) → prior-art tags
  - `48_TOPIC_SYNTHESIS` → best arguments across all papers on the topic
  - `57_API_DEEP`, `40_ANALYTICAL_ARMS` → deep passes
  - Scouts: CrossVideoSynthesis, TikTok recon, Topic Engine → outside material for a topic
- Fills: `evidence`, `witnesses`, whole-case helps / hurts.

### 5 Ruling — NOT BUILT (but the engine exists)
- Plugs in: `D:\GitHub\Canonizationv1` workbench (FastAPI + React + Postgres; claims start CANDIDATE_DRAFT), the ballot process, atoms repo `canon_guard` + Adversarial Review Gate.
- This page is where every `proposed` field from pages 2–4 gets accepted or rejected, and where claims get CANON / OPEN / RETIRED.
- **Blocker:** which store is the canon of record (workbench / atoms repo / vault). Until that's ruled, this page has nowhere to write.

### 6 Rebuild — NOT BUILT (and nothing to plug in yet)
- Closest existing: `34_EVIDENCE_SERIES_SYNTHESIS` (builds a master paper from station outputs), `14_STORY` + `41_STORY` (story material), the planned co-writing tool, the voice skills.
- Missing: the step that takes ruled claims and writes a new paper from them. Biggest gap in the whole map.

### 7 Publish — NOT BUILT
- Plugs in: `64_SITE_PACKAGE` (HTML per series and part), workflows `SubstackPublish`, `GTQArticlePublicRefinery`, `MasterHTMLComponentPipeline`; a Word (.docx) export for Zenodo; `46_REPORT_COMBINE` for the private audit file.
- Note: 64 publishes audit results today, not a rebuilt paper.

### 8 Feedback — NOT BUILT
- Plugs in: `37_EVIDENCE_SQLITE_SYNC`, `38_EVIDENCE_SIDECARS`, `D:\GitHub\cocoindex`, the vector library on V: (`docs\engine-integration\VECTORIZATION_SPEC_v0.1.md`).
- Job: published paper + accepted fields go into the library; topic marked definitive; contradiction check re-run against the corpus.

### Settings — NOT BUILT
- Model per program (pinned), API keys, which programs are on/off per page, worker counts. `ckg.json` already has this shape for CKG; generalize it to one file per page.

---

## Order to plug them in

Aim: one paper, Math Is Moral, all the way through. Plug in only what that one paper needs; everything else waits.

1. **Intake:** add the ten questions to the intake page so `topic` and `register` get filled. Ingest the MIM paper(s).
2. **Decompose:** switch CKG to V3.2; rule on the one atom maker; wire it to fill `claims` / `occurrences`.
3. **Verify:** one button that runs `63_PAPER_AUDIT` on a UUID, plus `68_FORMALIZE_TARGETS` for the math claims.
4. **Ruling:** rule the canon of record, then connect the Canonizationv1 workbench as the accept/reject screen.
5. **Research:** one hub question on MIM's most contested claim (e.g. against Clarke-Doane).
6. **Rebuild:** by hand the first time, with the co-writing tool if it's ready. Build the automated step from what doing it by hand teaches.
7. **Publish:** `64_SITE_PACKAGE` + a .docx export.
8. **Feedback:** last; it only matters once something has been published.

Research comes after ruling in this order on purpose: the first pass rules on what the paper already claims, and research then goes after only the claims that came out OPEN.

## Rulings this map needs from David

1. **One atom maker** (45 / 62 / atoms repo). Blocks page 2.
2. **Canon of record** (workbench / atoms repo / vault). Blocks page 5.
3. **Adapter style:** drop-in-INBOX-and-press-button (programs untouched, slower) or import-the-function (faster, touches code). Recommend INBOX first: it works today for every station.

---
*v0.1 — 2026-10-16 — David Lowe + Claude (Opus). Aggregate first; combine later.*
