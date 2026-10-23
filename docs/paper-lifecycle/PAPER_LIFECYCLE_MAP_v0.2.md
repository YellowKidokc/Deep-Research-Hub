# PAPER LIFECYCLE MAP v0.2
## One paper, beginning to end: raw draft → ruled claims → published page
**David Lowe (POF 2828) + Claude (Opus) | v0.1 2026-10-15 · v0.2 consolidated 2026-10-15**
**Consolidates reviews by:** GPT-6, Gemini, Kimi (all 2026-10-15). v0.1 and the three reviews stay in this folder untouched; the change log at the bottom says what was applied, what was rejected, and why.

---

## How to read this

Every stage lists what it does, what already exists (repo and station number), status, and the gap. Status was set from a skim of folder listings, READMEs and station.json on 2026-10-15. **Code was not read.** So **CLAIMED** means a station says it does this, not that anyone has proved it. Nothing marked CLAIMED counts until a fixture runs through it.

**Governing principle (David, Sep 23):** canon is a dependency declaration, not an honor. **Claims get canonized, not papers.** A paper is taken apart into claims, each claim is judged alone, and a new paper is built from what survived.

**Canon gate (five conditions):** a claim enters canon only with an address, a grade, a receipt, a ruling by David, and no unresolved conflict. The program is the clerk; David is the judge.

**Test paper:** "Math Is Moral." Parts right, parts overstated, parts false. Goal: the definitive paper on that topic.

**Three rulings David makes before anything is built (one session; they're entangled):**
- **S1** — who mints IDs (one transactional registry; UUID + readable ID; aliases).
- **S2** — which store is the canon of record for C-records and rulings (workbench / atoms repo / vault). The others become read-only mirrors.
- **S3** — one atom *mint*. Stations 45, 62 and the atoms repo may all keep extracting as candidate lanes; only one service issues a canonical C-ID. (Not "one atom maker" — one mint.)

Status key: **CLAIMED** = station exists per its description, unverified · **PARTIAL** · **MISSING** · **SPECCED** = designed, not built.

---

## THE MINIMUM PATH (new in v0.2)

Run this first, on Math Is Moral, before building anything new. Stages marked **★** are on the path; everything else in this map is "later." If a ★ stage has no working station, that's the build queue, in this order.

★1 Intake → ★2 Atoms → ★4 Contradiction → ★5 Fast prior art → ★6 Triage → ★10 Ruling → ★11 Paper disposition → ★14 Rebuild → ★15 Post-rebuild diff → ★20 Publish.

**Definition of done for the path: the MIM-SLICE-01 fixture passes.** Five items from Math Is Moral enter as `MIM-D-P-0004` and come out the other side with zero manual file edits:
1. A HELD definitional/formal claim (Gödel I) → linked to a Lean receipt, ruled CANON.
2. A HELD historical-witness claim (Augustine, *De libero arbitrio* II) → linked by `witnesses`, ruled CANON.
3. An OVERSTATED claim ("moral realism is mathematically proven") → triage flags DOESN'T-FOLLOW, writes the defensible version as a **new** C-record with its own anchors, routes it to a hub leg against Clarke-Doane 2020.
4. A FALSE claim ("every consistent axiom system is physically realized") → DEMONSTRABLY FALSE, ruled RETIRED, blocked from the rebuild.
5. A local implication (`.x01`, "any physical origin presupposes mathematical order") → stays in the sidecar's local block.
Pass: the rebuilt `MIM-D-P-0009` contains 1, 2 and the rewrite of 3; never 4; the sidecar and edge ledger are produced by the pipeline, not by hand.

---

## PHASE A — TAKE IT APART

**★1. Intake and identity.** One permanent paper UUID plus readable ID (`MIM-D-P-0004`); frozen original **bytes untouched** on disk; metadata in a sidecar `<ID>.meta.yaml`, never injected into the original; a normalized working copy (`.norm.md`, UTF-8, LF) with its own hash, which all later spans are computed against; source URI and acquisition date recorded; dedup by exact hash first, near-duplicate only as a candidate link David confirms. Instructions embedded in an external document are source text, never pipeline instructions.
- Have: `56_TITLE`, `47_NEW_PAPER`, sha256 in `31_EVIDENCE_MERGE_ORIGINALS`.
- Status: **PARTIAL.** Gap: no single paper ID carried across pipeline, atoms repo, workbench, hub (S1). Sidecar and `.norm.md` don't exist.

**★2. Decompose into candidate atoms.** Claims, evidence, proofs, equations, definitions, theological declarations, predictions, analogies — each typed, each a *candidate* until minted. Every occurrence (`.m07`) carries a **stance**: asserts / denies / quotes_opponent / questions / hypothetical — because Summa order means the paper states the objection at full strength, and without stance the scanner records you asserting it. Premises grouped by `warrant_group` so "A and B together" is distinguishable from "A or B alone."
- Have: `20_CKG`, `21_CKG_EXTRACT_CPE`, `45_CLAIM_ATOMS`, `62_ATOM_BUILDER`, `30`, `39`; atoms repo `claim-atom-standard-1.0`.
- Status: **CLAIMED, three ways.** Gap: S3 — one mint. Stance and warrant_group don't exist anywhere yet.

**3. Definitions.** Every term defined once, reused everywhere; glossary per paper from the registry.
- Have: atoms repo Canonical Definition Registry.
- Status: **CLAIMED.** Gap: not wired into the stations or the rendered page.

## PHASE B — FAST KILL (cheap filters before anything expensive)

**★4. Contradiction.** Internal (paper vs. itself) and against the canon ledger — including **retired** claims, so a paper can't quietly revive one. Embeddings only propose candidate pairs; a pair is called SAME, DISTINCT or CONFLICT only after a bidirectional-entailment check, because a negation, a quantifier flip, or "can" → "must" leaves the vectors nearly identical. Conflicts are never resolved by machine; each becomes a ruling item.
- Have: `43_PAPER_GRADER` self-contradiction metric; atoms repo Adversarial Review Gate.
- Status: **PARTIAL.** Gap: no corpus-wide check against the ledger; no entailment step.

**★5. Fast prior art.** Cheap pass from model knowledge and the corpus: for each load-bearing claim, the **nearest-neighbor work** and the **strongest opponent**, named (Math Is Moral: Clarke-Doane, *Morality and Mathematics*, OUP 2020). Tag ORIGINAL / HISTORICAL WITNESS / MODERN PARALLEL / BORROWED / UNVERIFIED — all provisional until stage 8's literature search. Moved up from v0.1's stage 8 so no one formalizes or researches a claim a known text already demolishes as phrased.
- Have: `49_GAP_MAP`, `33_EVIDENCE_BUILD_ONE_ARGUMENT`, `58_ARGUMENT_GRADE`.
- Status: **PARTIAL.**

**★6. Triage (the lawyer's audit).** Per claim, four **buckets** (not exclusive — one claim can be partly held and partly overstated, split it): HELD / OVERSTATED / FALSE / MISSING, with the defensible version of every overstatement and a blast radius. **A rewrite is a new C-record** with anchors recomputed against the rewrite text; the original atom keeps its spans against the draft. Flags are justified only by DEMONSTRABLY FALSE, DOESN'T FOLLOW, or PREMISE UNVERIFIED — never "a critic would say." HELD carries equal weight in the report.
- Have: `36_EVIDENCE_THREE_DIALS`, `58`, `59_CHI_EVALUATOR`, `43`, `63_PAPER_AUDIT`.
- Status: **PARTIAL.** Gap: no four-bucket output with defensible versions; no separate private audit file.

## PHASE C — HEAVY VERIFICATION (surviving and rewritten claims only)

**7. Math check and Lean.** Each equation COHERENT_TESTED / UNTESTED / DEFECTIVE / DECORATIVE; formalizable claims to Lean — **on the defensible rewrite, never the draft sentence.** A Lean receipt certifies the **arrow** (premises ⊢ conclusion). It does not certify the premises, and it does not certify that the Lean definitions mean what the English means. So: +10 for inferential validity only; the claim's warrant grade can't exceed its weakest non-Lean premise; a human-reviewed bridge-fidelity check (Lean defs ↔ prose defs) is required; custom `structure`/`def` declarations are audited alongside `sorry`/`admit`/`axiom`, because a theorem about a one-field toy structure compiles clean and proves nothing. Receipt records exact statement, toolchain, source hash, axiom policy.
- Have: `05_LEAN` group (`55`, `52`, `66`, `67`, `68`, `50`, `51`); `D:\GitHub\lean-atom-extractor` (the receipt store).
- Status: **PARTIAL.** Gap: three-way link Lean ID ↔ C-ID ↔ paper ID; the validity/warrant split doesn't exist in any grader.

**8. External research (the legs).** Contested claims become hub questions: legs both ways → per-leg search → raw dump → reading room → ruling. Verbatim highlights **uncapped** in the private reading room; the fair-use gate is at stage 20, not here. Originality tags from stage 5 become final only after this.
- Have: `deep-research-hub` + `deep-research` engine; `docs/engine-integration/`.
- Status: **SPECCED.**

**9. Cross-argument impact and knowledge graph.** Which whole-case arguments (WC-01..18) a claim helps, hurts, or is neutral to, one line why; Laws and Master Equation nodes touched; links to other papers on the topic key. *(What the graph should hold per paper is the subject of `KG_EXTRACTION_PROMPT_v0.1.md`, next round.)*
- Have: `48_TOPIC_SYNTHESIS`, `49_GAP_MAP`, `44_TAGGER`, `65_PAPER_INTELLIGENCE`, CocoIndex, atoms repo node graph.
- Status: **PARTIAL.** Gap: helps/hurts registry; none of the taggers emit the closed edge vocabulary.

## PHASE D — RULE ON IT

**★10. Ruling and canon.** David rules per claim: CANON / OPEN / RETIRED (plus HOLD when a pending run will decide). Rulings are append-only events (`C-00412.r1`, `.r2`…); the current ruling is a view, never an edited field. AI-entered rulings are **drafted proposals** until David ratifies. Big claims go to a cold multi-AI ballot. Every CANON claim carries its strongest objection.
- Have: `Canonizationv1` workbench (claims enter as CANDIDATE_DRAFT, not admitted); ballot process; atoms repo `canon_guard` and several `canon*/` folders; vault `02_CANONIZATION`.
- Status: **CLAIMED, scattered.** Gap: S2. Six-type vs. four-type atom mismatch resolved by S3.

**★11. Paper disposition (new in v0.2).** After the claims are ruled, the *paper* gets a verdict: **REBUILD** (enough load-bearing claims survived to carry a successor), **MERGE** (survivors fold into another topic's definitive paper; this paper gets no successor), or **RETIRE** (survivors live in the ledger; no successor). The ledger keeps every claim either way. This is the abort rule applied to the paper object — the v0.1 map assumed every paper comes out the far end rebuilt.
- Status: **MISSING** (one field on the paper record plus a ruling).

**12. Dependency tracking.** Which published papers rest on which canon claims; retire a claim → list what falls; upgrade a claim → list what can speak more strongly. Computable only because stage 2 grouped premises by `warrant_group`: retiring one of two conjoint premises breaks the claim, retiring one of two independent supports doesn't.
- Status: **MISSING.**

**13. Predictions and kill conditions.** Kill condition per load-bearing claim; dated prediction register with observable, method, threshold, deadline and pre-registration hash set *before* the outcome is known; failed predictions kept as negative controls.
- Have: CKG claim cards carry a kill condition.
- Status: **PARTIAL.**

## PHASE E — BUILD IT BACK

**★14. Rebuild.** New paper from CANON + OPEN claims only; RETIRED never re-enters. Declaration register, David's voice, **unhedged** — the honesty frame once at the top, and the CANON/OPEN status of each claim carried by the page's margin badge or drawer, never by hedge words inside the sentence. Objections at full strength before the answer (Summa order). Witnesses and Scripture cited as you go. Title decided here, from what the ruled claims support. Successor gets a new number, `successor_of` every parent.
- Have: `34_EVIDENCE_SERIES_SYNTHESIS`, `47_NEW_PAPER` (folder only); co-writing tool planned.
- Status: **MISSING. Biggest true gap.** Everything built runs toward canon; nothing runs back out of it into a paper.

**★15. Post-rebuild claim diff (new in v0.2).** Re-atomize the rebuilt paper and diff it against the ruled set. Any consequential new claim the writing introduced — a Truth Bomb, a connective sentence that overreaches, an OPEN claim stated as settled — blocks publication until it's either linked to a ruled atom, ruled itself, or cut. Without this stage the lifecycle can't prove its own output says only what survived.
- Status: **MISSING.**

**16. Story.** The human anchor carrying the argument, as its own pass; story spine checked against the argument spine; generated stories never presented as historical evidence.
- Have: `14_STORY`, `41_STORY`. Status: **CLAIMED.**

**17. Reader layer.** Definitions at first use; complexity ramp (college level in, technical out); plain-language translation of every equation.
- Have: `55_LEAN_PAPERS` reader paper; atoms repo plain-language nodes. Status: **PARTIAL.**

**18. Citation check.** Every external citation fetched: exists, says what we say, quote word-for-word, Scripture against the KJV. AI-added attributions start UNVERIFIED. Unverified load-bearing citations block publish.
- Status: **MISSING.**

**19. Private audit file.** Held / broke / overstated / defensible version, with blast radius; what was cut and why; where a hostile reader hits first (as TRUE/FALSE issues); model disagreements recorded. Never published.
- Have: `46_REPORT_COMBINE`. Status: **PARTIAL.**

## PHASE F — SHIP IT AND FEED IT BACK

**★20. Render and publish.** HTML to faiththruphysics.com; Word (.docx) for Zenodo (DOI recorded back). Publish is a human button. At publish, pin: source hash, claim and ruling versions, citation and Lean receipts, renderer version. Fair-use quote gate applied here. Errata / correction history kept on the page; a withdrawn claim shows as withdrawn, prior releases stay recoverable.
- Have: `64_SITE_PACKAGE`, `SubstackPublish`, `GTQArticlePublicRefinery`, `MasterHTMLComponentPipeline`.
- Status: **PARTIAL.** Gap: 64 publishes audit results, not the rebuilt paper; no Zenodo export; no pin or errata.

**21. Product tiers.** Free page; paid deep tier (atom ledger, legs, reading room, deep passes, Lean receipts).
- Have: `57_API_DEEP`, `40_ANALYTICAL_ARMS`. Status: **PARTIAL.**

**22. Feed back.** Published paper and atoms into the vector library; topic key marked definitive; contradiction engine re-run against the corpus; writing queue regenerated.
- Have: `37`, `38`, CocoIndex, vectorization spec. Status: **SPECCED.**

---

## THE SHAPE OF IT

The parts mostly exist as CLAIMED stations. What's missing is the **spine** (one paper as one object through all of them) and six true gaps.

**Spine:** S1 one ID · S2 one canon of record · S3 one mint.
**True gaps, in build order after the spine:** G1 rebuild (14) · G2 post-rebuild diff (15) · G3 contradiction against the ledger with entailment (4) · G4 triage output in lawyer format + private file (6, 19) · G5 dependency tracking on warrant groups (12) · G6 citation check (18). External legs (8) are the hub's own roadmap.

**Repo housekeeping (LOCAL):** `Canonization-upstream` (README only), `Canonization vers` (empty), `_Canonizationv1_vendored_cocoindex_backup` (full cocoindex copy), and the nested `pipeline-workflows` inside `Canonizationv1` (Oct 7 ruling made `D:\GitHub\pipeline-workflows\API` the one API). Retire after a reference check.

## QUESTIONS FOR THE CREW (round 2)

1. Is the minimum path the right ten stages? What would you drop from it or add to it?
2. Does the MIM-SLICE-01 fixture test the spine, or does it leave a seam untested?
3. Paper disposition: REBUILD / MERGE / RETIRE — missing an outcome?
4. Anything applied in the change log below that you'd reverse, with a reason?
5. See `KG_EXTRACTION_PROMPT_v0.1.md`: what should be pullable from every paper?

---

## CHANGE LOG v0.1 → v0.2

**Applied (and who raised it):**
- Sidecar metadata, frozen bytes untouched, `.norm.md` with separate hash — GPT-6, Gemini (B-03/F-02, F-03), Kimi (consistency tail). STRUCTURAL to hashing, LOCAL to the text.
- Lean receipt = validity only; warrant capped at weakest premise; bridge fidelity; `structure`/`def` audit — GPT-6, Gemini (B-04/F-05), Kimi. STRUCTURAL.
- Post-rebuild claim diff (15) — GPT-6 (E0), Gemini (B-05/F-08), Kimi. STRUCTURAL.
- Reorder: contradiction and fast prior art before triage; Lean and legs only on survivors — Gemini (NB-04), GPT-6 (B2), Kimi.
- Rewrite = new C-record with recomputed anchors — Kimi (T-11).
- Stance on occurrences; `warrant_group` on premises; `undercuts` edge — Gemini (B-07, NB-02), Kimi.
- Dedup by entailment, never embedding alone — GPT-6, Gemini (B-06).
- Flag justifications: FALSE / DOESN'T FOLLOW / PREMISE UNVERIFIED — Gemini §5.3 (clarifies David's rule; the ban on "a critic would say" stands).
- "One mint, many candidate lanes" instead of "one atom maker" — GPT-6 (R3), Kimi.
- Rulings append-only, AI rulings are drafts — GPT-6 (D0).
- Pin versions at publish; errata history; fair-use gate at publish only — GPT-6 (F0/F1) trimmed to the useful part; Gemini on placement.
- Minimum path + fixture — Gemini §6 slice, GPT-6 implementation order, Claude.
- Paper disposition (11) — Claude.
- HAVE → CLAIMED — all three reviewers.

**Rejected:**
- Hedging OPEN claims inside declaration prose (GPT-6 E0). Violates the two-register rule; badge in the margin instead. Gemini and Kimi concur.
- Length cap on private reading-room highlights (GPT-6 R4). Gate belongs at publish. Gemini and Kimi concur.
- Nine-entity data model and full release-manifest machinery (GPT-6 R3/F0). Right distinctions, wrong scale for one man; kept the two hashes, the occurrence record, and the publish pin.
- "Never send private manuscripts to external models by default" (GPT-6 A0). Not how this crew works. Kept only: an external document's embedded instructions are data.

**Still David's to rule:** S1, S2, S3 (one session). Then: do existing atoms re-ID into `C` or keep old IDs as aliases; do `EV` items get rulings or only tiers; law ordering (ME nodes nest by name so it can stay open).

*v0.2 — 2026-10-15 — David Lowe + Claude (Opus), consolidating GPT-6, Gemini, Kimi.*
