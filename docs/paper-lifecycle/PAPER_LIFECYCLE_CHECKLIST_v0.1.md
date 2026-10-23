# PAPER LIFECYCLE CHECKLIST v0.1
## Every bullet we can think of, by section — for the crew to extend
**David Lowe (POF 2828) + Claude (Opus) | 2026-10-15**
**Companion to:** `PAPER_LIFECYCLE_MAP_v0.1.md` (stages + what exists) and `ID_AND_YAML_SPEC_v0.1.md` (naming, classification, YAML). This file is the brainstorm: everything a paper might need to go through, whether or not anything exists for it yet.

**Instructions for reviewing AIs:** add bullets anywhere, mark any bullet you think is wrong or redundant with `[CUT?]` and a reason, and mark the five you think matter most with `[TOP]`. Don't rewrite existing bullets; add beneath them. Say which AI you are at the top of your additions.

---

## 0. Ground rules (apply to every section)
- Claims get canonized, not papers.
- Program is the clerk; David is the judge. No AI sets a ruling.
- Canon gate: address, grade, receipt, ruling, no unresolved conflict.
- Flags justified by TRUE / FALSE only, never "a critic would say."
- Every flag carries a blast radius: INERT / LOCAL / STRUCTURAL.
- Two registers: declaration (public, unhedged) and canon (graded, gated). The audit lives off-page.
- AI-generated content is labeled AI-proposed until a human reads it.
- Compiler facts and AI interpretations are never mixed (the lean-atom-extractor rule, applied everywhere).
- The original is never edited; every version points back to it.
- Nothing is deleted; replaced things move to an archive with a date.
- What got dropped is data: every cut gets a reason.
- Completeness in both directions: legs that cut against David's side get mapped too.
- Grades come from quoted checks computed in code, not a model's self-grade.
- Rating caps: API max +8, human review +9, Lean receipt only +10. Negatives are kept as negative controls.

## 1. Intake and identity
- One permanent paper UUID, minted once, carried everywhere.
- SHA-256 of the original at intake.
- Frozen untouched copy of the original.
- Duplicate check against the all-papers list (exact hash and near-duplicate).
- Version lineage: which earlier drafts or papers this one descends from.
- Standard title + `previous_names` history.
- Series membership (series code, part number).
- Author / co-author record, including which AI co-wrote it (authorship loyalty: audits go back to the authoring AI as an edit list).
- Date written vs. date ingested.
- Source format recorded (dictation, chat export, docx, HTML).
- Intake priority lane (priority / series / general).
- Dictation-artifact cleanup pass, logged, never silent.
- Register declared at intake: declaration piece or canon piece.
- Topic key(s) assigned (e.g. math-is-moral), so definitive-paper status can be tracked.

## 2. Decomposition (atoms / truth predicates)
- One claim per atom; atomicity rule enforced.
- Atom types: claim, evidence, proof, process, definition, equation, theological declaration, prediction, analogy.
- Each atom: own UUID, linked to paper UUID and exact location (character range) in the original.
- Epistemic mode per atom: definitional / mathematical / empirical / formal / framework assertion / theological declaration.
- Warrant class: what kind of support it would need.
- Load-bearing flag: does the paper's main conclusion depend on this atom?
- Inference map: which atoms are premises of which.
- Hidden premises surfaced: assumptions the argument needs but never states.
- Scripture references extracted in code first, then completed by model (cited / mentioned / alluded).
- Historical witnesses mentioned, extracted as separate references.
- Equations extracted with every variable listed.
- Analogies flagged as analogy, kept apart from claimed isomorphisms.
- Isomorphism claims gated: registry-gated, word-gate applied.
- Truth atoms: 50–100 short true statements per paper, ledger candidates.
- Coverage check: what fraction of the paper's sentences map to some atom.
- Which atom maker is authoritative (45 / 62 / atoms repo): ruling needed.

## 3. Definitions and vocabulary
- Every technical term defined once in the Canonical Definition Registry.
- Term first-use detection: the definition appears where the reader first meets the word.
- Plain-language definition and technical definition, both.
- Collision check: same word used with two meanings across the corpus.
- Drift check: has the term's meaning shifted since it was canonized?
- Physics terms used in theological sense flagged and defined for that use.
- Glossary generated per paper from the registry.
- Closed vocabularies for domain, reader, type, so the API can't invent labels.

## 4. Mathematical verification
- Each equation: COHERENT_TESTED / UNTESTED / DEFECTIVE / DECORATIVE.
- Dimensional / units check where physical quantities appear.
- Variables defined operationally (how you'd measure it), or marked as not yet operational.
- Three-layer explanation per equation: equation, term-by-term plain English, what happens when you turn each term.
- Limiting cases: does the equation reduce to known physics in the right limit?
- Sign and boundary checks.
- Consistency with the canonical Master Equation and the Ten Laws as currently ruled.
- Formalization candidates sent to Lean (`68_FORMALIZE_TARGETS`), always labeled PROPOSED.
- Lean receipts recorded in lean-atom-extractor; sorry / admit / custom axiom count per theorem.
- Assumptions file per Lean module reviewed before running.
- Three-way link: Lean declaration ID ↔ claim atom ID ↔ paper UUID.
- Theorem-to-claim reverse ledger: what each proof actually proves vs. what the paper says it proves.
- Statement-gap check: the Lean theorem proves something narrower than the prose claims? Flag it.
- Numeric claims recomputed in code, not trusted from text.
- Statistical claims (sigma values) traced to their original source and conditions.

## 5. Triage (the lawyer's audit)
- Four columns per claim: HELD / OVERSTATED / FALSE / MISSING.
- HELD carries equal weight in the report; it's not a footnote.
- Defensible version written for every overstatement.
- Blast radius per flag.
- Claimed strength vs. earned strength (three dials).
- Hedge audit: too many hedges in declaration pieces is also a failure.
- Overclaim language detection ("proves," "necessarily," "all," "only").
- Scope check: claim stated for all cases when evidence covers some.
- Retrodiction vs. prediction labeled.
- Circularity check: does a premise assume the conclusion?
- Equivocation check: same word, two meanings, inside one argument.
- Category check: is a theological claim being judged by empirical standards or vice versa?
- Paradox vs. contradiction distinguished; held paradoxes protected, not flagged as errors.
- Protected intuition zone: material David holds but hasn't submitted for canon isn't flagged.
- Audit goes to the authoring AI as an edit list when another AI wrote the paper.

## 6. Contradiction engine
- Internal: paper vs. itself.
- Against canon: every new atom vs. the canon ledger.
- Against open claims: conflicts with things still pending, flagged softer.
- Against retired claims: is the paper reviving something already retired?
- Against David's stated positions (whole-case arguments).
- Against Scripture as David reads it.
- Against established physics/math, with the conflict named, not auto-resolved.
- Conflict type: direct contradiction / tension / scope conflict / terminology collision.
- Conflicts never resolved by machine; each becomes a ruling item.
- Semantic dedup (embedding clustering) so the same claim phrased two ways is recognized.
- Contradiction history: every conflict ever found and how it was ruled.

## 7. Prior art and originality
- Per claim: ORIGINAL / HISTORICAL WITNESS / MODERN PARALLEL / BORROWED / UNVERIFIED.
- External literature search (not just model memory): PhilPapers, Stanford Encyclopedia, arXiv, CCEL, JSTOR where reachable.
- Historical witnesses sought deliberately (Fathers, Augustine, Boethius, Aquinas, etc.).
- Modern parallels: who is working on this now.
- Nearest-neighbor paper: the single closest existing work, named and engaged.
- Strongest opponent: the best existing work against the thesis.
- Bridge originality: at each domain seam, what's the original move vs. the borrowed parts.
- Date-of-first-statement: when did David first write this idea, from the corpus timeline (priority record).
- Credit language rule: witnesses cited as independent convergence, never implying David took from them.
- Contact list: modern authors whose work overlaps, for possible correspondence.

## 8. External research (the hub)
- Contested claims become hub questions.
- Leg discovery by two models from different labs (DeepSeek + OpenAI), unioned.
- Premise flag: does the question assume something?
- Per-leg search, 10–20 candidates, keep 2–5; soft targets.
- Raw dump kept (HTML record + Markdown working copy), immutable.
- Drop reason for every cut source.
- Verbatim highlights, no length cap.
- Tier per source (T1–T5) with reason.
- Reading room: tab per leg, scoped chat, missing-legs strip.
- Highlight colors (orange = come back, pink = using it), configurable.
- Bias probe on the research itself: pre-registered prediction, hashed.
- Opposing-leg pull whenever chatting about one leg.

## 9. Cross-argument impact and knowledge graph
- Which whole-case arguments (the 18) this claim helps.
- Which it hurts; record the hurts.
- Which it is neutral to.
- Why, one line each.
- Which Laws / Master Equation variables it touches.
- Which tridirectional-root properties it instantiates.
- Links to other papers on the same topic key.
- Definitive-paper status for the topic key: this one, another, or PENDING.
- Tags from closed vocabulary + open tags in metadata only.
- Graph edges proposed by AI stay proposals until David accepts (Adversarial Review Gate).
- Orphan check: atoms that connect to nothing else in the corpus.

## 10. Ruling and canon
- One canon of record (ruling needed: workbench / atoms repo / vault).
- Atom-type mapping resolved (six vs. four types).
- Per claim: CANON / OPEN / RETIRED, plus HOLD where a pending run will decide.
- Strongest objection attached to every CANON claim.
- Big claims go to a cold multi-AI ballot; votes recorded with reasons.
- Ruling receipt: who ruled, when, on what evidence, what it replaced.
- Rulings append-only; a reversal is a new ruling, never an edit.
- Delegated rulings (AI-entered) marked and kept provisional until ratified.
- Canon version number; any past canon state reconstructable.
- Ruling queue view: what's waiting for David, sorted by blast radius.

## 11. Dependency tracking
- Every published paper lists the canon claims it rests on.
- Retire a claim → list of papers, pages and other claims that fall.
- Upgrade a claim (new receipt) → list of papers that can now speak more strongly.
- Alerts on the published site when an underlying claim changes status.

## 12. Predictions and kill conditions
- Kill condition per load-bearing claim.
- Dated prediction register: what the framework predicts before it's known.
- Pre-registration hash for each prediction.
- Outcome tracking: confirmed / failed / pending, with dates.
- Failed predictions kept as negative controls, never deleted.

## 13. Rebuild (writing the new paper)
- Built from CANON + OPEN claims only; RETIRED claims never re-enter.
- OPEN claims marked as open in the canon register, stated plainly in declaration register.
- Structure: Human Anchor → Principle Revealed → Jesus Story → Core Insight → Truth Bomb (Theopoetic Engine) for public pieces.
- Objections at full strength before the answer (Summa order).
- Historical witnesses and Scripture cited as you go, not as footnotes.
- Title decided from what the ruled claims support.
- David's voice, unhedged in declaration register; honesty stated once in the frame.
- Complexity ramp: open plain (college level), build to technical.
- Density control: one idea per paragraph in story pieces, room to breathe.
- Definitions at first use, pulled from the registry.
- Every sentence traceable to an atom, a witness, or marked as connective prose.
- Co-writing tool: select-text-and-refine, read mode vs. write mode.
- The rebuilt paper gets its own UUID, linked to the original as its successor.
- Diff view: original vs. rebuilt, so David sees what moved and why.

## 14. Story layer
- Human anchor story for the opening.
- Story bank per paper (facts, human moments, memorable lines).
- Story spine checked against the argument spine: does the story carry the actual claim?
- Memorable lines gated (no lines that overstate the canon).
- Reuse tracking: the same story not used in five papers.

## 15. Reader layer
- Reader levels: public / college / technical / formal (Lean).
- Plain-language translation of each equation.
- "Six-year-old test" / Playground Protocol for core terms.
- Reading time and difficulty score.
- Accessibility: alt text for figures, readable on phone.

## 16. Citation verification
- Every external citation fetched and checked: does it say what we say it says?
- AI-added attributions start UNVERIFIED.
- Quotes checked word-for-word against source.
- Scripture references checked against the King James text.
- Dead links checked at publish and periodically after.

## 17. Private audit file
- What held / what broke / what's overstated / defensible version.
- Every flag's blast radius.
- What was cut from the original and why.
- Open risks: what a hostile reader would hit first (stated as TRUE/FALSE issues, not reviewer-appeasement).
- Never published; stored beside the paper.

## 18. Render and publish
- HTML page for faiththruphysics.com (series house, page per part).
- Word (.docx) for Zenodo; DOI recorded back on the paper.
- Markdown master kept as the source for both.
- Substack version (shorter, story-forward).
- Metadata on the page: canon status of key claims, version, date, topic key.
- Changelog on the page: what changed between versions.
- Mobile check before publish.
- Publish is a human button press; nothing auto-publishes.

## 19. Product tiers
- Free: the public paper.
- Paid deep tier: atom ledger, legs, reading room, API-deep passes, Lean receipts.
- College / academic package: formal paper + Lean + claims ledger.
- Audio version (TTS station exists).
- Video / YouTube script version.
- Per-paper "go deeper" links from free page into the paid layer.

## 20. Feedback into the corpus
- Published paper + atoms ingested into the vector library (V:).
- Canon ledger updated; truth-atom ledger updated.
- Topic-key index updated: this is now the definitive paper.
- Other papers on the topic re-pointed to it instead of re-arguing.
- Contradiction engine re-run against the corpus with the new canon.
- Writing queue regenerated from topic keys still PENDING.

## 21. Metrics and quality over time
- Per-paper scorecard (grades, coverage, originality, canon fraction).
- Corpus statistics: how many claims canon / open / retired.
- Change since last version.
- Which stations catch the most real errors (station effectiveness).
- AI-collaborator track record: whose flags held up under ruling.
- Bias probe results over time, per model.

## 22. System and operations
- One paper flows through all stations as one object (the spine).
- Every station: INBOX / OUTBOX / BACKSIDE pattern, walk-up paths, never hard-coded.
- Every run writes a receipt: source hash, model, prompt version, tokens, time, errors.
- Finish each item before the next; reruns skip what's done.
- Cost tracking per paper and per station.
- Model pinning per station; changes logged.
- Station-to-stage map kept current (this document's companion).
- Health check across all repos; retired repos marked clearly.
- Backups: originals, canon, rulings, receipts. Indexes are rebuildable and don't need backup.
- Public-repo rule: no INBOX / OUTBOX / keys committed.

## 23. People and roles
- David: judge, voice, final publish.
- Each AI: named lane (builder, auditor, mapper, voter), recorded per paper.
- Cold readers: AIs who haven't seen the work, used for ballots and bias checks.
- Human outside readers (future): who, at what stage.

## 24. Naming, classification and YAML
*(Full detail: `ID_AND_YAML_SPEC_v0.1.md` in this folder.)*

**The governing rule**
- Files get a home topic. Ideas belong to the whole corpus.
- Every item has two IDs: a hidden permanent UUID (machines) and a readable ID (people). Old readable IDs are kept as aliases, never broken.
- Counts never go in an ID; the topic registry keeps live counts.

**Topic registry**
- 2–4 letter codes (e.g. `MIM` = Math Is Moral), checked against the registry before issue.
- Nesting only for true part-of: Master Equation laws nest **by name, never number** (`ME.GRAV`, `ME.MOT`, `ME.EM`, `ME.STR`, `ME.THERM`, `ME.INFO`, `ME.QM`, `ME.REL`, `ME.WEAK`, `ME.COH`); derived families one level deeper (`ME.WEAK.ATONE`); three levels max.
- Theories that use the Master Equation (Watcher, Grace, MIM) are their own topics and link to the nodes they touch.
- The 18 whole-case arguments are registry entries `WC-01`…`WC-18`.

**File IDs (topic-scoped):** `TOPIC-ORIGIN-TYPE-NNNN`
- Origin is a role, not an author: **D** house work (incl. AI co-written; authors in metadata), **A** machine analysis output, **X** external.
- Type: P paper · N note/draft · W web page · B book · J journal article · Y video/transcript · H hub run.
- Children: `.v2` edit of same document (base ID = frozen original) · `.m07` mention of a corpus-wide idea · `.q3` quote · `.L2` hub leg · `.x01` local item.
- A rebuilt paper gets a new number, linked `successor_of` to every parent.
- Dropped hub sources still get numbers; registry counts kept vs. dropped separately.

**Idea IDs (corpus-wide): twelve core families, closed**
- `C` claim (carries canon status; papers mention it) · `EV` evidence item · `AX` axiom (keeps existing numbering: `AX-T-001..188`, `AX-P-01..22`) · `DEF` definition · `PRD` prediction (with pre-registration hash) · `ISO` isomorphism (keeps existing numbering; two endpoints; analogies get none) · `LEAN` label pointing to lean-atom-extractor's own ID · `R` ruling (`C-00412.r1`, append-only) · `BAL` ballot · `KC` kill condition (`C-00412.k1`) · `TAG` closed-vocabulary tag · `TOPIC` codes.

**Edges (closed relation list)**
- mentions · supports · opposes · proves · depends_on · implies · predicts · tests · defines · maps_to · touches · witnesses · version_of · successor_of · helps / hurts.
- Every edge: proposer (AI or David), status (proposed / accepted / rejected), date, one-line reason. AI edges stay proposals until David accepts.
- One edge ledger is the source of truth; each file's YAML carries a checked copy of its own edges.
- Correlation walks: prediction → claims → evidence → papers; claim → everything for and against it; axiom → every claim that depends on it (dependency tracking).

**Local block (unlimited)**
- Anything specific to one paper or topic that doesn't fit a core family yet (e.g. an implication MIM wants to carry).
- Free-form `kind`, optional proposed links into the core.
- Promotion: David promotes a local item into a core idea; a local *kind* recurring across many topics becomes a candidate new family.

**YAML header (what a corpus scan identifies in every file)**
- Identity: id, uuid, aliases, title, standard_title, topic, also_in, origin, type, authors, co_authors, register, sha256, where, written, ingested, version_of, successor_of.
- Found in it: tags, claims, axioms, definitions, evidence, predictions, isomorphisms, lean, me_nodes, scripture, witnesses, equations, whole_case (helps / hurts / neutral).
- Status: canon_fraction, open_claims, retired_claims, definitive_for, last_scan, scan_receipt.
- Local: unlimited items.
- The scan only proposes; existing IDs get linked, new ones come back as candidates for David.

**The ten intake questions (build the ID, then route)**
1. Which topic? 2. House, analysis, or external? 3. What type? 4. A version of something already in? 5. A duplicate?
6. Does it make claims? 7. Does it contain math? 8. Does it touch the Master Equation? 9. Does it state or use an isomorphism? 10. Declaration or canon?
- 1–5 build the ID; 6–10 route the file to stations.

**Open rulings**
- Which canon store holds `C` records and rulings.
- Existing atoms: re-ID into `C`, or keep old IDs as aliases.
- Do `EV` items get canon status or only tiers (T1–T5)?
- Any topic-code length rule beyond "unique."

## 25. Open questions for the crew
- What section is missing entirely?
- Which bullets are redundant with each other?
- Which five matter most?
- What order should a single paper actually move through these sections?
- What's the smallest version of this that would produce one finished definitive paper (Math Is Moral) end to end?

---
*v0.1 — 2026-10-15 — David Lowe + Claude (Opus). Add beneath, don't overwrite.*
