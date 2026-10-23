# PAPER LIFECYCLE CHECKLIST v0.2
## Every bullet we can think of, by section — for the crew to extend
**David Lowe (POF 2828) + Claude (Opus) | v0.1 2026-10-15 · v0.2 consolidated 2026-10-15 from GPT-6, Gemini, Kimi**
**Companions:** `PAPER_LIFECYCLE_MAP_v0.2.md` (stages, status, minimum path), `ID_AND_YAML_SPEC_v0.2.md` (naming, edges, sidecar), `KG_EXTRACTION_PROMPT_v0.1.md` (what to pull from every paper).

**How v0.2 differs:** accepted review bullets are merged in place, tagged `(GPT-6)`, `(Gemini)`, `(Kimi)` or `(Claude)` where they're new. Nothing of David's was cut; three v0.1 lines were reworded and are marked `[reworded]`. Rejected review items are listed at the end, not silently dropped. **★** marks bullets on the minimum path (see the map); everything unmarked is "later."

**Instructions for reviewing AIs (round 2):** add beneath, don't rewrite. `[CUT?]` plus a reason for anything you'd remove. `[TOP]` on your five. Say which AI you are at the top of your additions.

---

## 0. Ground rules (apply to every section)
- ★ Claims get canonized, not papers.
- ★ Program is the clerk; David is the judge. No AI sets a ruling; AI-entered rulings are drafts until ratified.
- ★ Canon gate: address, grade, receipt, ruling, no unresolved conflict.
- ★ Flags justified by DEMONSTRABLY FALSE / DOESN'T FOLLOW / PREMISE UNVERIFIED — never "a critic would say." [reworded — the ban on reviewer-appeasement stands; the logical categories are what TRUE/FALSE meant]
- ★ Every flag carries a blast radius: INERT / LOCAL / STRUCTURAL.
- ★ Two registers: declaration (public, unhedged) and canon (graded, gated). The audit lives off-page. CANON/OPEN status rides in the page margin, never in the sentence.
- AI-generated content is labeled AI-proposed until a human reads it.
- Compiler facts and AI interpretations are never mixed (lean-atom-extractor rule, applied everywhere).
- ★ The original is never edited; every version points back to it. Metadata lives in a sidecar.
- Nothing is deleted; replaced things move to an archive with a date.
- What got dropped is data: every cut gets a reason.
- Completeness in both directions: legs that cut against David's side get mapped too.
- Grades come from quoted checks computed in code, not a model's self-grade.
- ★ Rating caps: API max +8, human review +9, Lean receipt +10 **for inferential validity only** — the arrow, not the premises. Claim warrant ≤ weakest non-Lean premise. Negatives kept as negative controls. [reworded]
- Keep separate and never compress into one number: formal validity, premise truth, evidence strength, review status, publish permission. (GPT-6, Gemini)
- An external document's embedded instructions are source text, never pipeline instructions. (GPT-6)
- Every proposed edit is a diff with author, timestamp, reason, affected IDs. (GPT-6)

## 1. Intake and identity
- ★ One permanent paper UUID, minted once by one registry, carried everywhere; readable ID alongside.
- ★ SHA-256 of the original bytes at intake. Frozen untouched copy — **no YAML injected into it.** (Gemini, GPT-6)
- ★ Normalized working copy `.norm.md` (UTF-8, LF) made immediately, with its own hash; all spans computed against it. (Gemini)
- Duplicate check: exact hash = same bytes, not same paper; near-duplicates become candidate links David confirms, never a silent merge. (GPT-6)
- Version lineage: which earlier drafts or papers this one descends from.
- Standard title + `previous_names` history.
- Series membership (series code, part number).
- Author / co-author record, including which AI co-wrote it (authorship loyalty: audits go back to the authoring AI as an edit list).
- Date written vs. date ingested. Source URI and acquisition date for external material. (GPT-6)
- Source format recorded (dictation, chat export, docx, HTML).
- Intake priority lane (priority / series / general).
- Dictation-artifact cleanup pass, logged, never silent — produces a `.v1`, never touches the original.
- Register declared at intake: declaration piece or canon piece.
- Topic key(s) assigned (e.g. MIM), so definitive-paper status can be tracked.
- IDs allocated transactionally; re-import is idempotent; renaming or moving a file preserves the UUID. (GPT-6)

## 2. Decomposition (candidate atoms)
- ★ One claim per atom; atomicity rule enforced.
- Atom types: claim, evidence, proof, process, definition, equation, theological declaration, prediction, analogy.
- ★ Each occurrence: own ID (`.m07`), linked to the corpus-wide idea and to its span in `.norm.md` (plus extraction version). The occurrence and the idea are different objects. (GPT-6)
- ★ **Stance on every occurrence:** asserts / denies / quotes_opponent / questions / hypothetical. Summa order means objections appear at full strength; without stance the scanner records David asserting them. (Gemini)
- ★ Premises grouped by `warrant_group`: "A and B together" vs. "A or B alone." Dependency tracking can't compute without it. (Gemini)
- Epistemic mode per atom: definitional / mathematical / empirical / formal / framework assertion / theological declaration.
- Warrant class: what kind of support it would need; quantifiers, scope, premises, inferential step stated explicitly. (GPT-6)
- Load-bearing flag: does the paper's main conclusion depend on this atom?
- Inference map: which atoms are premises of which.
- Hidden premises surfaced: assumptions the argument needs but never states.
- Scripture references extracted in code first, then completed by model (cited / mentioned / alluded).
- Historical witnesses extracted as separate references.
- Equations extracted with every variable listed.
- Analogies flagged as analogy, kept apart from claimed isomorphisms.
- Isomorphism claims gated: registry-gated, word-gate applied.
- Candidate atomic statements: 50–100 short declarative statements per paper, ledger candidates — **not "true" until ruled.** [reworded; Kimi flagged "truth atoms" as minting truth before judgment]
- Coverage check: what fraction of the paper's sentences map to some atom; sampled human review for false negatives. (GPT-6)
- ★ One mint (S3): 45, 62 and the atoms repo submit candidates; one service issues canonical C-IDs. (GPT-6, Kimi)

## 3. Definitions and vocabulary
- Every technical term defined once in the Canonical Definition Registry; definition carries a version and a sense. (GPT-6)
- Term first-use detection: the definition appears where the reader first meets the word.
- Plain-language definition and technical definition, both.
- Collision check: same word, two meanings across the corpus; homonyms and deliberate polysemy distinguished from contradictory definitions. (GPT-6)
- Drift check: has the term's meaning shifted since it was canonized? A definition change triggers dependent-claim checks. (GPT-6)
- Physics terms used in theological sense flagged and defined for that use.
- Glossary generated per paper from the registry.
- Closed vocabularies for domain, reader, type, so the API can't invent labels.

## 4. Contradiction engine (moved before triage in v0.2)
- ★ Internal: paper vs. itself, atom-pair comparison, not one prompt over the whole paper. (Gemini)
- ★ Against canon: every new atom vs. the canon ledger.
- ★ Against retired claims: is the paper reviving something already retired?
- Against open claims: conflicts with things still pending, flagged softer.
- Against David's stated positions (whole-case arguments).
- Against Scripture as David reads it.
- Against established physics/math, with the conflict named, not auto-resolved.
- Conflict type: direct contradiction / tension / scope conflict / terminology collision / changed time frame / genuine paradox (protected). (GPT-6)
- ★ Dedup: embeddings only propose candidate pairs; SAME / DISTINCT / CONFLICT decided by bidirectional entailment plus a negation-and-quantifier-flip detector. (Gemini, GPT-6)
- Store the exact two statements and their context for every alleged conflict. (GPT-6)
- Conflicts never resolved by machine; each becomes a ruling item. Opposing canon records create a blocking reconciliation task.
- Contradiction history: every conflict ever found and how it was ruled.

## 5. Prior art and originality (fast pass here; deep legs in §8)
- ★ Per claim: ORIGINAL / HISTORICAL WITNESS / MODERN PARALLEL / BORROWED / UNVERIFIED — provisional until a documented literature search. (GPT-6)
- ★ Nearest-neighbor paper: the single closest existing work, named and engaged.
- ★ Strongest opponent: the best existing work against the thesis.
- External literature search (not just model memory): PhilPapers, SEP, arXiv, CCEL, JSTOR where reachable — hostile and supportive both.
- Historical witnesses sought deliberately (Fathers, Augustine, Boethius, Aquinas…), cited as independent convergence, never as debt.
- Modern parallels: who is working on this now.
- Bridge originality: at each domain seam, what's the original move vs. the borrowed parts.
- Date-of-first-statement: when David first wrote this idea, from the corpus timeline (priority record).
- Contact list: modern authors whose work overlaps.

## 6. Triage (the lawyer's audit)
- ★ Four buckets per claim: HELD / OVERSTATED / FALSE / MISSING — not exclusive; a claim that's partly held and partly overstated is split into new atoms. (GPT-6, Gemini)
- ★ HELD carries equal weight in the report; it's not a footnote.
- ★ Defensible version written for every overstatement — **as a new C-record with anchors recomputed against the rewrite text;** the original keeps its draft spans. (Kimi T-11)
- ★ Blast radius per flag.
- Claimed strength vs. earned strength (three dials).
- Strongest counterexample and the unresolved assumption recorded per flag; note whether the repair changes the thesis. (GPT-6)
- Hedge audit: too many hedges in declaration pieces is also a failure.
- Overclaim language detection ("proves," "necessarily," "all," "only").
- Scope check: claim stated for all cases when evidence covers some.
- Retrodiction vs. prediction labeled.
- Circularity check; equivocation check; category check (theological claim judged by empirical standard or vice versa).
- Paradox vs. contradiction distinguished; held paradoxes protected.
- Protected intuition zone: material David holds but hasn't submitted for canon isn't flagged.
- Second pass to catch errors the auditor's own rewrite introduced. (GPT-6)
- Audit goes to the authoring AI as an edit list when another AI wrote the paper.

## 7. Mathematical verification (on surviving claims)
- Each equation: COHERENT_TESTED / UNTESTED / DEFECTIVE / DECORATIVE.
- Dimensional / units check; variables defined operationally or marked not yet operational.
- Three-layer explanation per equation: equation, term-by-term plain English, what happens when you turn each term.
- Limiting cases; sign and boundary checks.
- Consistency with the canonical Master Equation and the Ten Laws as currently ruled.
- Formalization candidates sent to Lean (`68_FORMALIZE_TARGETS`) **from the defensible rewrite**, always labeled PROPOSED. (Gemini)
- ★ Lean receipt grades the arrow only; warrant ≤ weakest non-Lean premise; bridge fidelity (Lean defs ↔ prose defs) human-reviewed. (Gemini, GPT-6)
- Custom `structure` / `def` declarations audited alongside `sorry` / `admit` / `axiom`; a theorem about a toy structure fails the statement-gap check. (Gemini)
- Receipt: Lean version, dependency lock, exact statement, source hash, allowed axioms, sorry audit. (GPT-6)
- Three-way link: Lean declaration ID ↔ C-ID ↔ paper UUID.
- Theorem-to-claim reverse ledger: what each proof proves vs. what the paper says it proves.
- Numeric claims recomputed in code with inputs, units and uncertainty; sigma values traced to source and conditions.

## 8. External research (the hub)
- Contested claims become hub questions.
- Leg discovery by two models from different labs, unioned; treat same-lab or same-prompt models as correlated. (GPT-6)
- Premise flag: does the question assume something?
- Per-leg search, 10–20 candidates, keep 2–5; soft targets.
- Raw dump kept (HTML record + Markdown working copy), immutable. Drop reason for every cut source.
- Verbatim highlights, no length cap **in the private reading room**; fair-use gate at publish (§18). (Gemini)
- Tier per source (T1–T5) with reason; provenance chain (primary / intermediary / copied citation); dependent repetitions are not independent confirmations. (GPT-6)
- Reading room: tab per leg, scoped chat, missing-legs strip; highlight colors configurable.
- Bias probe on the research itself: pre-registered prediction, hashed.
- Opposing-leg pull whenever chatting about one leg.

## 9. Cross-argument impact and knowledge graph
- Which whole-case arguments (WC-01..18) this claim helps, hurts, is neutral to; why, one line each. Record the hurts.
- Which Laws / Master Equation nodes it touches; which tridirectional-root properties it instantiates.
- Links to other papers on the same topic key; definitive-paper status for the key: this one, another, or PENDING.
- Tags from closed vocabulary + open tags in metadata only.
- Edges typed with domain/range; `depends_on` is never inferred from `mentions` or from similarity. (GPT-6, Gemini)
- Graph edges proposed by AI stay proposals until David accepts (Adversarial Review Gate).
- Orphan check: atoms that connect to nothing else in the corpus.
- *What else the graph should hold per paper: see `KG_EXTRACTION_PROMPT_v0.1.md` (round 2 question).*

## 10. Ruling and canon
- ★ One canon of record (S2 ruling).
- ★ Atom-type mapping resolved by the S3 mint (six vs. four types).
- ★ Per claim: CANON / OPEN / RETIRED, plus HOLD where a pending run will decide.
- Strongest objection attached to every CANON claim.
- Big claims go to a cold multi-AI ballot; votes recorded with reasons.
- ★ Ruling receipt: who ruled, when, on what evidence snapshot, what it replaced, effective date. (GPT-6)
- ★ Rulings append-only; a reversal is a new ruling, never an edit; the current ruling is a view.
- AI-drafted ruling proposals marked and kept provisional until David ratifies. [reworded from "delegated rulings"]
- Canon version number; any past canon state reconstructable.
- Ruling queue view: what's waiting for David, sorted by blast radius.
- ★ **Paper disposition after ruling: REBUILD / MERGE / RETIRE.** Survivors always stay in the ledger; MERGE folds them into another topic's definitive paper; RETIRE gives the paper no successor. (Claude)

## 11. Dependency tracking
- Every published paper lists the canon claims it rests on.
- Retire a claim → list of papers, pages and claims that fall — computed over `warrant_group`s, so one lost conjoint premise breaks a claim and one lost independent support doesn't. (Gemini)
- Upgrade a claim (new receipt) → list of papers that can now speak more strongly.
- Alerts on the published site when an underlying claim changes status.

## 12. Predictions and kill conditions
- Kill condition per load-bearing claim.
- Dated prediction register: observable, measurement method, threshold, deadline, competing predictions, scoring rule — all set before the outcome is known. (GPT-6)
- Pre-registration hash for each prediction.
- Outcome tracking: confirmed / failed / pending, with dates; failed predictions kept as negative controls.

## 13. Rebuild (writing the new paper)
- ★ Built from CANON + OPEN claims only; RETIRED never re-enters.
- ★ OPEN claims stated plainly in declaration register; their status carried by the page's margin badge, not by hedge words. (Gemini, over GPT-6)
- Structure: Human Anchor → Principle Revealed → Jesus Story → Core Insight → Truth Bomb (Theopoetic Engine) for public pieces.
- Objections at full strength before the answer (Summa order).
- Historical witnesses and Scripture cited as you go, not as footnotes.
- Title decided from what the ruled claims support.
- ★ David's voice, unhedged in declaration register; honesty stated once in the frame.
- Complexity ramp: open plain (college level), build to technical. Density control: one idea per paragraph in story pieces.
- Definitions at first use, pulled from the registry.
- Every sentence traceable to an atom, a witness, or marked as connective prose.
- Co-writing tool: select-text-and-refine, read mode vs. write mode.
- ★ The rebuilt paper gets its own ID, linked `successor_of` to every parent.
- Diff view: original vs. rebuilt, so David sees what moved and why.
- ★ **Post-rebuild claim diff:** re-atomize the rebuilt paper, diff against the ruled set; any new consequential claim blocks publish until ruled or cut. (Gemini, GPT-6, Kimi)

## 14. Story layer
- Human anchor story for the opening; story bank per paper.
- Story spine checked against the argument spine: does the story carry the actual claim?
- Memorable lines gated (no lines that overstate the canon).
- Generated stories and analogies never presented as historical evidence. (GPT-6)
- Reuse tracking: the same story not used in five papers.

## 15. Reader layer
- Reader levels: public / college / technical / formal (Lean).
- Plain-language translation of each equation.
- "Six-year-old test" / Playground Protocol for core terms.
- Reading time and difficulty score; alt text; readable on phone.

## 16. Citation verification
- Every external citation fetched: exists, passage located, says what we say, support strength noted. (GPT-6)
- AI-added attributions start UNVERIFIED.
- Quotes checked word-for-word; Scripture against the King James text.
- Dead links checked at publish and periodically after.
- Unverified load-bearing citations block publish.

## 17. Private audit file
- What held / what broke / what's overstated / defensible version, with blast radius each.
- What was cut from the original and why.
- Open risks: where a hostile reader hits first, stated as TRUE/FALSE issues.
- Model disagreements and dissenting rationale recorded, with David's final disposition. (GPT-6)
- Never published; stored beside the paper.

## 18. Render and publish
- ★ HTML page for faiththruphysics.com (series house, page per part); Markdown master as the source.
- Word (.docx) for Zenodo; DOI recorded back on the paper. (Zenodo metadata and license validated separately — GPT-6)
- Substack version (shorter, story-forward).
- Metadata on the page: canon status of key claims (margin badge / drawer), version, date, topic key.
- ★ At publish, pin: source hash, claim and ruling versions, citation and Lean receipts, renderer version. (GPT-6, trimmed)
- ★ Fair-use quote gate applied here, not at ingestion. (Gemini)
- Changelog and errata history on the page; a withdrawn claim shows as withdrawn; prior releases stay recoverable. (GPT-6)
- Mobile check before publish.
- ★ Publish is a human button press; nothing auto-publishes. Blocked by unverified load-bearing citations or a failed post-rebuild diff.

## 19. Product tiers
- Free: the public paper.
- Paid deep tier: atom ledger, legs, reading room, API-deep passes, Lean receipts.
- College / academic package: formal paper + Lean + claims ledger.
- Audio version (TTS station exists); video / YouTube script version.
- Per-paper "go deeper" links from free page into the paid layer.

## 20. Feedback into the corpus
- Published paper + atoms ingested into the vector library.
- Canon ledger updated; topic-key index updated: this is now the definitive paper.
- Other papers on the topic re-pointed to it instead of re-arguing.
- Contradiction engine re-run against the corpus with the new canon.
- Writing queue regenerated from topic keys still PENDING.

## 21. Metrics and quality over time
- Per-paper scorecard (grades, coverage, originality, canon fraction).
- Corpus statistics: claims canon / open / retired; change since last version.
- Station effectiveness: which stations catch real errors — measured as false-positive / false-negative rates on a reviewed sample, not flag counts. (GPT-6)
- AI-collaborator track record: whose flags held up under ruling.
- Bias probe results over time, per model.

## 22. System and operations
- ★ One paper flows through all stations as one object (the spine).
- Every station: INBOX / OUTBOX / BACKSIDE pattern, walk-up paths, never hard-coded.
- ★ Every run writes a receipt: source hash, model, prompt version, tokens, time, errors.
- Finish each item before the next; reruns skip what's done; idempotency keys; partial-failure states. (GPT-6)
- Cost tracking per paper and per station; model pinning per station.
- Station-to-stage map kept current.
- Health check across all repos; retired repos marked clearly.
- Backups: originals, canon, rulings, receipts — and a tested restore. Indexes are rebuildable.
- Public-repo rule: no INBOX / OUTBOX / keys committed.

## 23. People and roles
- David: judge, voice, final publish.
- Each AI: named lane (builder, auditor, mapper, voter), recorded per paper; model family and shared context recorded so correlated reviewers aren't counted as independent. (GPT-6)
- Cold readers: AIs who haven't seen the work, used for ballots and bias checks.
- Human outside readers (future): who, at what stage.

## 24. Naming, classification and YAML
*(Full detail: `ID_AND_YAML_SPEC_v0.2.md`. Summary only here.)*
- Files get a home topic. Ideas belong to the whole corpus.
- Two IDs on everything: hidden UUID (machines), readable ID (people); old readable IDs kept as aliases.
- File IDs `TOPIC-ORIGIN-TYPE-NNNN` with ordered dot-suffixes; idea IDs in twelve closed families; closed edge list with stance and warrant_group.
- Metadata in a sidecar; dynamic counts (canon_fraction etc.) are a generated cache, never hand-edited.
- Ten intake questions: 1–5 build the ID, 6–10 route the file.

## 25. Open questions for the crew (round 2)
- Is the ★ minimum path the right set? What's missing from it, what's on it that shouldn't be?
- Which five bullets matter most now that the reviews are merged?
- Anything in the "applied" list you'd reverse?
- What's the smallest version that produces one finished Math Is Moral — does the MIM-SLICE-01 fixture in the map cover it?
- Answer `KG_EXTRACTION_PROMPT_v0.1.md`.

---

## REJECTED REVIEW ITEMS (with reason)
- Hedging OPEN claims inside declaration prose (GPT-6 E0 / §13–17) — violates the two-register rule; badge carries the status.
- Length cap on private reading-room highlights (GPT-6 §7–8) — gate at publish.
- Full nine-entity data model and release-manifest system (GPT-6) — right distinctions, wrong scale; kept the hashes, occurrence record, and publish pin.
- "Never send private manuscripts to external models by default" (GPT-6 A0) — not how this crew works.

## PROPOSED TESTS carried from the reviews (acceptance tests for the spine and slice)
- Sidecar hash invariance: hash before and after intake + scan is identical (Gemini T-01).
- Adversarial pairs (negation, quantifier flip, direction reversal) never become MERGE candidates (Gemini T-02).
- `theorem math_is_moral : True := trivial` grades validity +10, warrant ≤ +5, STATEMENT_GAP flagged (Gemini T-03).
- Retire one conjoint premise → claim BROKEN; retire one of two independent supports → still SUPPORTED (Gemini T-04).
- Inject an unapproved universal claim into the rebuild → publish blocked until linked or stripped (Gemini T-05).
- Triage rewrite enters as a new C-record with recomputed anchors; the original's spans still resolve against the draft (Kimi T-11).
- Stance polarity: a quoted objection is not indexed as an assertion (Kimi T-12).
- GPT-6 R5 tests 1–10 (re-ingest, near-duplicate, extra axiom, fake citation, retire load-bearing claim, injected instruction, concurrent mint, source change, failed journal write, rebuild from CANON+OPEN).

*v0.2 — 2026-10-15 — David Lowe + Claude (Opus), consolidating GPT-6, Gemini, Kimi. Add beneath, don't overwrite.*
