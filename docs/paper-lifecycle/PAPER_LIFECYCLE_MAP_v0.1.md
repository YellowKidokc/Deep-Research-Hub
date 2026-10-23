# PAPER LIFECYCLE MAP v0.1
## One paper, beginning to end: raw draft → canonized claims → published page
**David Lowe (POF 2828) + Claude (Opus) | 2026-10-15 | For review by the whole crew**

---

## How to read this (for any AI reviewing it)

This maps the process every paper in David's corpus should go through, one for one. Each stage lists: what it does, what already exists (by repo and station number), status, and the gap. Status was set from a skim of the repos on 2026-10-15: folder listings, READMEs, and station.json descriptions. **Code was not read.** "HAVE" means a station claims to do it, not that it was verified.

Your job when reviewing: (1) add stages we missed, (2) challenge stage order, (3) say which gap you'd close first and why, (4) flag anything marked HAVE that you know doesn't actually work.

**Governing principle (David, Sep 23):** canon is a dependency declaration, not an honor. **Claims get canonized, not papers.** A paper is taken apart into claims, each claim is judged alone, and a new paper is built from what survived.

**Canon-worthiness gate (five conditions):** a claim enters canon only with an address, a grade, a receipt, a ruling by David, and no unresolved conflict. The program is the clerk; David is the judge.

**Test paper:** "Math Is Moral." Parts right, parts overstated, parts false. The goal is the definitive paper on that topic.

Repos skimmed: `pipeline-workflows` (API stations), `Faith-through-physics-atoms`, `Canonizationv1`, `nerve`, `cocoindex`, `deep-research-hub`, `deep-research`.

Status key: **HAVE** = station exists · **PARTIAL** = some of it exists · **MISSING** = nothing found · **SPECCED** = designed, not built.

---

## PHASE A — TAKE IT APART

**1. Intake and identity.** One permanent paper ID; frozen untouched original; duplicate check against an all-papers list.
- Have: `56_TITLE` (standard title, `previous_names` history), `47_NEW_PAPER` (per-paper working folder), sha256 matching in `31_EVIDENCE_MERGE_ORIGINALS`.
- Status: **PARTIAL.** Gap: no single paper UUID visibly carried across all three systems (pipeline stations, atoms repo, canon workbench). The UUID system doc David asked for on Sep 22 was not found.

**2. Decompose into atoms.** Claims, evidence, proofs, equations, definitions, theological declarations, each typed. These are the truth predicates.
- Have: `20_CKG`, `21_CKG_EXTRACT_CPE` (claims/proofs/evidence split), `45_CLAIM_ATOMS`, `62_ATOM_BUILDER`, `30_EVIDENCE_INTAKE`, `39_EVIDENCE_CHAIN_INTAKE_V2`; atoms repo `claim-atom-standard-1.0`.
- Status: **HAVE, with overlap.** Three stations make atoms (45, 62, atoms repo). Gap: decide which one is authoritative so atoms aren't minted three ways.

**3. Definitions.** Every term defined once, reused everywhere.
- Have: atoms repo **Canonical Definition Registry**.
- Status: **HAVE.** Gap: not visibly wired into the pipeline stations or the rendered page's glossary.

## PHASE B — TEST IT

**4. Math check.** Each equation judged coherent-tested / untested / defective / decorative; formalizable claims to Lean.
- Have: `05_LEAN` group: `55_LEAN_PAPERS`, `52` atom extractor, `66` sorry/axiom audit, `67` triage, `68_FORMALIZE_TARGETS` (claim in → proposed Lean statement out); `50`, `51` Lean pairing.
- Status: **PARTIAL.** Lean side is strong. Gap: the four-verdict equation check from template v0.3 isn't a station.
- Also: `D:\GitHub\lean-atom-extractor` (Sep 6). Scans a Lean corpus into SQLite with stable declaration IDs (`project:rel_path:fq_name`), runs compiler verification with SHA-256 receipts, audits sorry/admit/custom axioms, keeps AI interpretation quarantined from compiler facts, exports Atom JSON Schema 1.0, and has a web dashboard. `52_LEAN_ATOM_EXTRACTOR` appears to wrap it. **This is the receipt store: the only place a +10 grade can come from.** Gap: the three-way link **Lean declaration ID ↔ claim atom ID ↔ paper UUID** (part of spine S1). `55_LEAN_PAPERS`' theorem-to-claim reverse ledger is the start of it.

**5. Triage (the lawyer's audit).** Per claim: held / overstated / false / missing, with the defensible version of each overstatement and a blast radius.
- Have: `36_EVIDENCE_THREE_DIALS` (claimed vs. earned strength, which is overstatement detection), `58_ARGUMENT_GRADE`, `59_CHI_EVALUATOR`, `43_PAPER_GRADER` (includes self-contradiction), `63_PAPER_AUDIT` chain.
- Status: **PARTIAL.** Gap: no output in the four-column format with defensible versions, and no separate private audit file.

**6. Internal contradiction.** Does the paper contradict itself?
- Have: `43_PAPER_GRADER` self-contradiction metric.
- Status: **HAVE.**

**7. Contradiction against canon.** Does any new atom conflict with what's already canon?
- Have: atoms repo **Adversarial Review Gate** blocks opposed node wires; the truth-atom ledger was planned Sep 14.
- Status: **PARTIAL / MISSING.** Gap: no corpus-wide check of a new paper's atoms against the canon ledger.

## PHASE C — PLACE IT IN THE WORLD

**8. Prior art and originality.** For each claim: who already holds it? Tag ORIGINAL / HISTORICAL WITNESS / MODERN PARALLEL / BORROWED. Expect originality to concentrate in the bridges between domains.
- Have: `49_GAP_MAP` ("who said it first," with citations), `33_EVIDENCE_BUILD_ONE_ARGUMENT` (lineage, originality), `58_ARGUMENT_GRADE` (originality 0–8).
- Status: **PARTIAL.** Gap: these draw on David's own corpus plus model knowledge. Nothing searches the outside literature and verifies it. That is the deep research hub's job (stage 9). Example for Math Is Moral: Clarke-Doane, *Morality and Mathematics* (OUP 2020) must be found and faced.

**9. External research (the legs).** Each contested claim becomes a hub question: legs (both sides) → per-leg search → raw dump → reading room → ruling.
- Have: `deep-research-hub` + `deep-research` engine; specs in `docs/engine-integration/`.
- Status: **SPECCED.**

**10. Cross-argument impact.** Which of David's other arguments does this claim help, which does it hurt, and why? Record the hurts.
- Have: `48_TOPIC_SYNTHESIS` (best arguments across all papers), `49_GAP_MAP` (expand / contract / holes), atoms repo node graph.
- Status: **PARTIAL.** Gap: no helps/hurts registry linking claims to the 18 whole-case arguments.

**11. Knowledge graph and tags.** Keywords, defined terms, links to other papers.
- Have: `44_TAGGER` (20 tags), `65_PAPER_INTELLIGENCE` (includes knowledge graph), `taxonomy.json`, CocoIndex.
- Status: **HAVE.**

## PHASE D — RULE ON IT

**12. Ruling and canon.** David rules per claim: canon / open / retired. Big claims go to a cold multi-AI ballot. Every canon claim carries its strongest objection.
- Have: `Canonizationv1` workbench (FastAPI + React + Postgres, verified running Sep 22; claims start as CANDIDATE_DRAFT — NOT ADMITTED); ballot process (Numbers in God); atoms repo `canon_guard`, `canon/`, `_canon/`, `canon-store/`, `canon_store/`; vault `02_CANONIZATION`.
- Status: **HAVE, but scattered. Most important open question:** which one is the canon of record? Canon appears to live in several places, and the atom types don't match (workbench six types vs. vault/CKG four). Not verified whether these conflict; needs a ruling before scale.

**13. Dependency tracking.** Which published papers rest on which canon claims, so retiring a claim shows what it pulls down.
- Status: **MISSING.**

**14. Predictions and kill conditions.** What would break each claim; dated predictions logged.
- Have: CKG claim cards carry a kill condition.
- Status: **PARTIAL.** Gap: no dated prediction register.

## PHASE E — BUILD IT BACK

**15. Rebuild.** Write a new paper from canon and open claims only. Declaration register, David's voice, unhedged. Objections stated at full strength before the answer (Summa order). Historical witnesses and Scripture cited as you go. Title decided here, from what the ruled claims support.
- Have: `34_EVIDENCE_SERIES_SYNTHESIS` (master paper for a series, from companions, not from ruled claims); `47_NEW_PAPER` makes a folder only; co-writing tool planned.
- Status: **MISSING. Confirmed the biggest gap.** Everything built runs *toward* canon; nothing runs back *out* of canon into a paper.

**16. Story.** The human anchor carrying the argument, as its own pass.
- Have: `14_STORY` (story material cards), `41_STORY` (hook / sequence / coherence, memorable lines).
- Status: **HAVE.**

**17. Reader layer.** Definitions at first use; complexity ramp (start plain, build); plain-language translation of the math.
- Have: atoms repo "truth descends as far as people require" plus proposed plain-language math translation nodes; `55_LEAN_PAPERS` writes a reader paper per Lean file.
- Status: **PARTIAL.** Gap: no ramp pass on a full paper.

**18. Citation check.** Every cited source verified to say what we claim; AI-added attributions start UNVERIFIED.
- Status: **MISSING.**

**19. Private audit file.** What held / broke / overstated / defensible version. Never published.
- Have: `46_REPORT_COMBINE` (all station results into one report).
- Status: **PARTIAL.** Gap: the lawyer-format file itself.

## PHASE F — SHIP IT AND FEED IT BACK

**20. Render and publish.** HTML to faiththruphysics.com; Word (.docx) for Zenodo.
- Have: `64_SITE_PACKAGE` (house per series, page per part, Markdown + HTML), workflows `SubstackPublish`, `GTQArticlePublicRefinery`, `MasterHTMLComponentPipeline`.
- Status: **PARTIAL.** Gap: 64 publishes *audit results*, not the rebuilt paper; no Zenodo .docx export seen.

**21. Product tiers.** Free public page; paid deep tier = atom ledger, legs, reading room, deep API passes.
- Have: `57_API_DEEP`, `40_ANALYTICAL_ARMS`.
- Status: **PARTIAL.** The deep content exists; packaging it as a tier doesn't.

**22. Feed back.** Published paper + claims into the vector library (V:); becomes the definitive paper for its topic key; future papers checked against it.
- Have: `37_EVIDENCE_SQLITE_SYNC`, `38_EVIDENCE_SIDECARS`, CocoIndex, vectorization spec.
- Status: **SPECCED.**

---

## THE SHAPE OF IT

The parts mostly exist. ~55 stations in `pipeline-workflows\API` alone cover most stages. What's missing is mostly the **spine** that makes one paper flow through all of them as one object.

**The spine (connect what exists):**
- **S1. One paper ID** across pipeline, atoms repo, canon workbench, hub, vector library.
- **S2. One canon of record.** Pick it; the others read from it. Resolve the six-type vs. four-type mismatch.
- **S3. One atom maker.** 45, 62 and the atoms repo collapse to one, or one feeds the others.

**True gaps (build new):**
- **G1. Rebuild** (stage 15): ruled claims → new paper. Biggest gap; where the co-writing tool lives.
- **G2. Contradiction against canon** (stage 7).
- **G3. Dependency tracking** (stage 13): retire a claim, see what falls.
- **G4. External prior art + legs** (stages 8–9): the hub.
- **G5. Citation check** (stage 18).
- **G6. Lawyer-format audit file** (stage 19) and the four-column triage (stage 5).
- **G7. Helps/hurts registry** (stage 10) and **dated prediction register** (stage 14).

**Repo housekeeping (LOCAL, nothing downstream moves):**
- `D:\GitHub\Canonization-upstream`: README only.
- `D:\GitHub\Canonization vers`: empty.
- `D:\GitHub\_Canonizationv1_vendored_cocoindex_backup`: a full copy of cocoindex.
- `Canonizationv1` contains its own nested `pipeline-workflows` folder, while the Oct 7 ruling made `D:\GitHub\pipeline-workflows\API` the one canonical API.
- Its README is GitHub boilerplate; the real status is in `CANONIZATION_STATUS.md`.
Candidates to retire after a check that nothing references them.

## QUESTIONS FOR THE CREW

1. What stage is missing from this list?
2. Is the order right? (Especially: should prior art come before triage?)
3. Which of S1–S3 first? Our read: S2, because rulings have nowhere certain to land until it's settled.
4. Which gap after the spine? Our read: G1 rebuild, because it's the first thing that produces a better paper rather than better analysis.
5. Anything marked HAVE that you know doesn't run?

---
*v0.1 — 2026-10-15 — David Lowe + Claude (Opus). Status from a skim of folders and station descriptions, not code; verify before building on any HAVE.*
