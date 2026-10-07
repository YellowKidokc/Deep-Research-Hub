# Web Research & Results — spec v0.1 (parcelled)

**Date:** 2026-10-07 · **Owner:** David Lowe · **Source:** David ↔ Kimi conversation, sorted into buildable parts by Claude Code.
**Status:** DRAFT. Nothing here is built yet unless marked. Items marked **ASK DAVID** are not decided.

This is the "next version" of the Deep Research screen: the web search and results version. The conversation mixed five different systems. They are separated below, each assigned to where it lives in the hub, so nothing is built twice and nothing drifts.

---

## 0. The one rule that runs through all of it

**Discovery before construction.** Every research tool on the market starts with a direction and shops for evidence (prosecution). This one maps the question space first (investigation): which distinct arguments exist inside a question, who holds them, in whose words, with what receipts. Picking a side is a later step, done by a person.

**Receipts at every stage, written as the stage runs.** Not reconstructed afterwards. If a stage left no record, the stage did not happen.

**Pills, not prose.** Research output is structured records with sources attached. Prose is a rendering of pills, made later, and never the only copy.

---

## 1. The visible pipeline (screen 1, next version)

The same four stages every AI research tool runs internally, each one exposed and stored.

| Stage | Does | Stored (per sub-query) | Human can |
|---|---|---|---|
| 1. Cast the net | Several searches with *neutral* framings (not "is X real", which is already a thesis). 40–60 results. | every result: title, URL, snippet, which search found it, rank | see all of them |
| 2. Triage | Reads snippets, picks which to fetch | kept + dropped, each with a one-line reason | override kept/dropped |
| 3. Extract | Fetches the kept pages, pulls the passages that matter | the passages themselves (verbatim, with source URL and position), not summaries | see the lines, strike or add |
| 4. Synthesize | Writes only from the extracted passages | every claim points at passage IDs | trace any claim to a line |

**Where this sits in the code we have:** GPT Researcher already does 1 (retrievers), fetch (scrapers), and a weak 3 (the similarity filter). Step 1 of the Deep Research build made 3 observable (the read receipt) and found that its cut is positional, not by relevance. The visible pipeline replaces GPTR's "similarity filter → write" with "triage → extract → synthesize-from-passages", keeping GPTR as the acquisition engine (search, scrape, dedupe, SSRF guard). This is step 4 of the locked Deep Research build order.

**Hard part:** stage 3. Choosing what to highlight is where the judgment lives and where errors hide. It needs its own critic lane on a *different model* from the extractor.

---

## 2. The fork map (screen 1, the stage after extraction)

Input: a topic ("the devil"). Output: N forks.

1. **Wide cast** with neutral framings (see stage 1).
2. **Atomic claims**: each extracted passage reduced to single claims ("ha-satan is a job title in Hebrew"), each tagged with its source and passage.
3. **Cluster by argument type, not by agreement.** Two sources that agree for different reasons are in different clusters; two sources that disagree about the same question are in the same cluster. This is the hard engineering problem: structural difference vs surface difference.
4. **Fork pill**: `fork_name`, `core_question`, `positions[]`, `sources_per_position[]`, `receipts[]` (dated quote + primary source).
5. **Human picks** which forks go forward, and how much each gets.

Worked example from the conversation: "the devil" produced 12 forks (ontological status, origin / privatio boni, OT ha-satan vs NT Satan, scope of power, theodicy, serpent identification, possession vs mental illness, dualism, mechanism of sin, secular dismissal, atheistic Satanism, entropy-as-adversary). Use it as the first fixture.

**ASK DAVID:** the fork pill fields above are the proposal; confirm or change before it is built.

---

## 3. Specialist research agents (one per question type)

David's call, and structurally right: one agent per question type, because each has a different cast pattern, success test and kill condition. In the hub these are **job types in the queue** (`data/jobs/*.yaml`, `job_type:`), sharing the queue, receipt and ledger already built.

| Agent (job_type) | Asks | Success | Kill / legal "no" |
|---|---|---|---|
| `fork_map` | What distinct arguments exist in this question? | N forks, each with positions and receipts | — |
| `origin_trace` | Where did this concept / phrase first appear, and how did it travel? | a chain of hops, each with a dated primary-source quote (first attestation) | a hop with no receipt ends the chain: **"unknown" is a legal answer**. Never smooth a weird origin into a clean one. |
| `essence_paper` | Which study, experiment or paper captures the core of this? | the paper whose central claim matches the load-bearing claim of the question (rubric-scored, never citation rank) | runs only after a fork map exists, because the fork map says what the question's structure is |
| `precursor` | Who predicted this long before its time? | a person + a dated quote from that person | a precursor without a dated quote is a rumour, not a finding |
| `prior_art` | Who said this, in what words, when? | dated quote, primary source | as origin_trace |
| `cold_derive` | Root + one claim, no framework vocabulary: what follows, where does it fail? | a derivation with its failure points | a test, not research |
| `hybrid_rule` | Local article + web: rule on, rewrite, add, cut; show diffs | diffs | — |

These three (origin, essence, precursor) are the same battery the original hub spec put on **screen 2, Targeted Research** (etymology and first use, first person to state it, first study, who predicted it a century out). One definition, used by both screens.

**Why origin is the dangerous one:** search ranks by relevance and recency, which is the opposite of first attestation. A model asked for an origin will produce a plausible, smooth, wrong family tree. The receipts rule above is the guard.

---

## 4. Classification system (corpus side, not the research agent)

From the first half of the conversation. It classifies *David's own papers* into the canon; it is not part of web research, but research output (pills) lands in the same canon, so the pill format must match.

- **Circle 1, domain slot** (what it IS): small, exclusive, David's list (Master Equation, Axioms, Bible studies, Series, One-pagers, 4Q/apologetics, Christ_Arguments, …). Each slot has an include rule, an exclude rule and 2–3 examples (one in, two near-misses).
- **Circle 2, structural role** (what it DOES): genre (argument, survey, empirical, formal system, interpretation, testimony, proposal) plus **edges**: `extends`, `attacks`, `confirms`, `presupposes` → canon node IDs.
- **Circle 3, position** (where it STANDS): agrees with / contradicts / testimony about / provenance for.
- **Circle 4, tags**: search surface only, never routing. A tag that starts to route means a slot is missing.
- **Local schema per Circle 1 slot**: starts with 3–4 fields, grows only when rulings demand it.
- **Hold bucket**: under ~80% confidence or a close runner-up → never force-fit; keeps its edges. Clusters in the hold bucket with a *shared failure signature* produce a proposal for a new slot. A person rules (two doors: detection proposes, declaration commands).
- **Learning loop**: every ruling + one line of "why" becomes an example and sharpens the slot definitions. Agreement is tracked **per slot**, so the system can say which slots are trustworthy.
- **Phase 0 gate**: freeze the pill schema, hand-classify ~25 fixtures (including deliberate anomalies), and run a diff harness before the classifier touches the real corpus.

Where it goes: a corpus/canon tool beside screen 4 (Search Engine). **ASK DAVID:** own screen, or part of screen 4.

---

## 5. The Writer program (screen 7) and renderers

Not research. Listed so it doesn't get folded into the research agent.

- **Ruling points per paragraph:** a highlight box with 2–3 sentences and ~5 options, each with a predicted weight; forward-only.
- **Choice ledger:** the system predicts the pick, the person picks, the difference is logged. The ledger is the training data (contextual bandit). Build the ledger first; prediction without logged choices is guessing.
- **Evidence badges:** research pills (predictor, study, statistic, origin) shown at the point of writing, with their receipts and standing.
- **Boosters:** optional paid API features, shown in a sidebar when the statistics say they apply.
- **Unforgotten sentence:** per paragraph, generate candidates for the most memorable line and let the person pick. One slot in the API Layer (screen 6).
- **Renderers on one contract:** YouTube script, two-host dialogue (Explainer + Skeptic, where the Skeptic voices the kill conditions), YouTube Short (the highest-tension pill, not the best summary). Each one takes a canon subgraph and formats it; none of them is a source of truth.

v1 of the Writer is the smallest loop: present options → pick → log → adjust → next.

---

## 6. Build order proposed for the research side

1. **Visible pipeline on one question** (§1): stages 1–4 stored as JSON beside the report; synthesize-from-passages with claim → passage links. Reuses GPTR acquisition and the existing queue/receipt/ledger.
2. **Fork map** (§2) on the stored passages; first fixture "the devil".
3. **Specialist job types** (§3): `origin_trace`, `precursor`, `essence_paper`, with the receipts rules as hard validation (a hop or precursor without a dated quote is rejected, not softened).
4. Classification (§4) and the Writer (§5) are separate builds.

---

## 7. Corrections and open points from the conversation

- **"The cupcake lady."** Kimi's guess was Jessica Utts (a statistician known for auditing parapsychology data). The description (children, one vs two, knowing the arithmetic is wrong before any formal system) fits developmental work on infant number sense better, e.g. Karen Wynn, *Addition and subtraction by human infants*, Nature, 1992. Both are unverified guesses. This is a good first job for the `precursor` / `origin_trace` agents. Don't put either name in a script until it has a receipt.
- **The word lost in dictation** ("traced back to a torched"): unknown. If one destination keeps showing up when origins are traced, it is a standing hypothesis to test with receipts, not a finding.
- **Literature quotes in the conversation** (the "Evidence Tracing and Execution Provenance" survey and the audit-trail quotes) were given by another AI without links. Verify before citing.
- **"Nobody has built origin / essence / precursor search"** is a strong claim; treat it as unverified until the precursor agent itself has checked it.
- **Academic retrievers for class 2:** undecided.
