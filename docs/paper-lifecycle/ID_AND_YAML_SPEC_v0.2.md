# ID AND YAML SPEC v0.2
## How every item in the corpus is named, described, and connected
**David Lowe (POF 2828) + Claude (Opus) | v0.1 2026-10-15 · v0.2 consolidated 2026-10-15 from GPT-6, Gemini, Kimi**
**Companions:** `PAPER_LIFECYCLE_MAP_v0.2.md`, `PAPER_LIFECYCLE_CHECKLIST_v0.2.md`, `KG_EXTRACTION_PROMPT_v0.1.md`

**What changed from v0.1:** the header became a sidecar (the original file is never touched); the file-ID grammar is now exact and the hub example is fixed; edges carry `stance` and `warrant_group`; `undercuts` and `instantiates` join the relation list; dedup needs entailment, not similarity; the status block is a generated cache. Everything else is v0.1.

---

## 1. Two IDs on everything

- **UUID** (hidden, permanent): what machines use. Issued by one transactional registry (S1). Never changes, never reused. Moving or renaming a file does not change it.
- **Readable ID** (visible): what David and the AIs use. If it ever has to change (filed under the wrong topic, topics merged), the old one goes in `aliases`. Nothing that pointed to it breaks.

## 2. The one rule that decides the naming

**Things that are files get a home topic. Things that are ideas belong to the whole corpus.**

A **file** (a paper, web page, book, transcript, analysis output) was ingested somewhere, so it gets a readable ID under the topic it came in through. Other topics point to it. An **idea** (claim, definition, axiom, prediction, isomorphism, evidence item) exists independently of any one file and gets a corpus-wide ID. A paper *mentions* a claim; the claim is one record. This fixed the v0 defect where one claim had a different ID in every paper.

Two objects that look alike and aren't: an **occurrence** (this claim, at this span, in this file, with this stance) and the **idea** it points to. One file can hold many occurrences of one idea.

## 3. Topic registry

- One list: code, full name, parent (if any), date created, aliases, live counts.
- **Root codes** are 2–4 letters (`MIM` = Math Is Moral), checked against the registry before issue. Root-code aliases are immutable once issued.
- **Topic paths** nest only for true part-of, dotted, three levels max. Master Equation laws nest **by name, never number** (law ordering stays an open ruling): `ME.GRAV`, `ME.MOT`, `ME.EM`, `ME.STR`, `ME.THERM`, `ME.INFO`, `ME.QM`, `ME.REL`, `ME.WEAK`, `ME.COH`; derived families one deeper: `ME.WEAK.ATONE`.
- Theories that *use* the Master Equation (Watcher, Grace, MIM) are their own topics and link to the nodes they touch.
- Counts live in the registry, never in IDs.
- The 18 whole-case arguments are registry entries `WC-01`…`WC-18`.

## 4. File IDs (topic-scoped)

**Grammar (exact):** `TOPIC-ORIGIN-TYPE-NNNN` then an ordered suffix chain. Dashes separate the four root parts; dots separate suffixes; the topic may itself contain dots, so parsers split on `-` first.

```
^[A-Z]{2,4}(\.[A-Z]{2,6}){0,2}-[DAX]-[PNWBJYH]-\d{4}(\.v\d+)?(\.(m|q|L|x)\d+)?$
```

**Origin is a role, not an author:** **D** house work (David's papers and notes, including AI co-written; authors in metadata) · **A** machine analysis output (CKG runs, audits, deep passes) · **X** external (someone else's work).

**Type:** P paper · N note/draft · W web page · B book · J journal article · Y video/transcript · H hub research run.

**Suffixes, in order:**
- `.vN` — edit N of the same document. **The base ID is the frozen original; `.v1` is the first edit** (e.g. the dictation cleanup). An edit becomes a *successor* instead when it is rebuilt from ruled claims — then it gets a new base number and a `successor_of` edge.
- `.mNN` — occurrence (mention) NN inside this file, pointing to a corpus-wide idea. Chained after a version: `MIM-D-P-0004.v2.m07`.
- `.qN` — quote N from this source. `.LN` — leg N of a hub run. `.xNN` — local item NN (§7).

Examples: `MIM-D-P-0004` frozen original · `MIM-D-P-0004.v2` second edit · `MIM-D-P-0009` the rebuilt paper, `successor_of` 0004 · `MIM-X-B-0007.q3` quote 3 from external book 7 · `MIM-D-H-0002.L4` leg 4 of house hub run 2 *(v0.1 wrote `MIM-H-0002.L4`, which violated the grammar; any such ID is migrated with an alias, never silently rewritten)*.

Dropped hub sources still get numbers (what got cut is data); the registry counts kept and dropped separately.

## 5. Idea IDs (corpus-wide): the core families

| Family | What it is | Example | Notes |
|---|---|---|---|
| `C` | Claim (atomic, rulable) | `C-00412` | Carries ruling status. Papers mention it. Minted by one service (S3). |
| `EV` | Evidence item | `EV-00088` | Supports or opposes claims. Carries tier T1–T5 and a provenance chain. Open ruling: tier only, or ruling too? |
| `AX` | Axiom | `AX-T-042`, `AX-P-07` | Keeps existing numbering: 188 technical (T), 22 public (P). |
| `DEF` | Definition | `DEF-0123` | Canonical Definition Registry entries, versioned. |
| `PRD` | Prediction | `PRD-0007` | Pre-registration hash, observable, deadline, outcome. |
| `ISO` | Isomorphism | `ISO-002` | Keeps existing numbering. Two endpoints. Analogies don't get ISO numbers. |
| `LEAN` | Lean label | `LEAN-0031` | Pointer to lean-atom-extractor's own ID (`project:path:name`). Never a competing identity. |
| `R` | Ruling | `C-00412.r1` | Attached to the thing ruled on. Append-only. Signer, evidence snapshot, effective date, what it superseded. |
| `BAL` | Ballot | `BAL-0005` | Multi-AI votes spanning many claims. |
| `KC` | Kill condition | `C-00412.k1` | What would break the claim. |
| `TAG` | Tag (closed vocabulary) | `TAG-physics-thermo` | Open tags live in metadata only. |
| `TOPIC` | Topic codes | `MIM`, `ME.WEAK` | The registry in §3. |

Twelve families, closed. Anything else lives in the local block (§7) until it earns a family.

## 6. Connections: the edge vocabulary

Everything connects through **edges**: `from → relation → to`. The relation list is **closed** (the API picks from it, never invents one). Every relation has a domain and a range; the scanner may not propose `paper → proves → claim` (a paper can only *mention*; only a `LEAN` record or a formal chain can *prove*).

| Relation | Meaning | Domain → Range |
|---|---|---|
| `mentions` | file contains this idea, at this span, with this stance | occurrence → idea |
| `supports` | gives reason to believe | EV / C / occurrence → C |
| `opposes` | gives reason to doubt the claim itself (¬B) | EV / C / occurrence → C |
| `undercuts` | attacks the inference from premise to claim, not the claim (¬(A→B)) *(Gemini)* | EV / C → edge or warrant_group |
| `proves` | formal proof of an exact statement under checked assumptions | LEAN → C |
| `depends_on` | needs this to hold; never inferred from `mentions` or similarity | C → C / AX / DEF |
| `implies` | if this holds, that follows | C → C |
| `predicts` | the claim forecasts this | C → PRD |
| `tests` | evidence or outcome bears on a prediction | EV → PRD |
| `defines` | definition used | C → DEF |
| `maps_to` | an isomorphism endpoint | ISO → C / TOPIC |
| `instantiates` | a concrete case of an axiom or isomorphism *(Gemini)* | EV / C → AX / ISO |
| `touches` | links to a Master Equation node | C → ME.* |
| `witnesses` | a historical thinker reached it independently | occurrence (X source) → C |
| `version_of` | edit of the same document | file.vN → file |
| `successor_of` | rebuilt from | file → file |
| `helps` / `hurts` | bears on one of the whole-case arguments | C → WC-nn |

**Every edge record:**

```yaml
- id: E-00981
  from: MIM-D-P-0004.m07
  relation: mentions
  to: C-00412
  stance: asserts            # asserts | denies | quotes_opponent | questions | hypothetical  (mentions only)
  warrant_group: null        # id grouping conjoint premises (A AND B → C); null = independent  (depends_on / supports)
  proposed_by: claude-opus   # AI name or "david"
  status: proposed           # proposed | accepted | rejected
  date: 2026-10-15
  reason: "Thesis statement, §2 ¶3."
```

**AI-proposed edges stay proposals until David accepts** (Adversarial Review Gate). Edges live in **one ledger** (the source of truth, append-only). Each file's sidecar lists that file's own edges as a convenience copy, which a rebuild script checks against the ledger.

**Why stance:** Summa order means your papers state the objection at full strength before answering it. Without stance, "which papers assert C-00412?" returns the papers that refute it.

**Why warrant_group:** binary edges can't tell "C needs A and B together" from "A alone suffices, so does B." Dependency tracking (retire A, see what falls) is impossible without it.

**Correlation walks fall out of the edges:** from a prediction → claims that predict it → evidence that tests it → papers that mention them. From a claim → every paper, every piece of evidence for and against, its axioms, its proof, its rulings. From an axiom → every claim that depends on it.

## 7. The local block: unlimited, per paper or per topic

The twelve families are closed so the corpus stays searchable; the local block is where a paper keeps what matters to *it* and doesn't fit a family yet. Free-form `kind`, optional proposed links into the core.

```yaml
local:
  - id: MIM-D-P-0004.x01
    kind: implication
    text: "Any physical origin event presupposes mathematical order already in place."
    bears_on: [WC-03]
    note: "Track; may become a claim."
```

**Promotion rule:** a local item becomes a core idea when David promotes it (`.x01` → `C-00520`, then ruled). A local *kind* that recurs across many topics is a candidate new family. The core grows deliberately, never by the API inventing categories. Unknown fields survive schema migration by landing here.

## 8. The sidecar: what a corpus scan produces for every file

**The original file is never edited.** Metadata lives beside it in `<ID>.meta.yaml`. (v0.1 put this in the file's own header; injecting it changes the bytes and kills the intake hash. Every v0.1 phrase "the scan fills in the header" now means "the scan writes the sidecar," and the rebuild-script check compares sidecar to ledger.)

Three sections: **identity** (fixed at intake), **found** (proposed by the scan, accepted by David), **status** (a generated cache — never hand-edited, regenerated from the ledgers on build, so forty sidecars don't go stale every time a ruling lands).

```yaml
schema_version: "0.2"
# ---- identity (fixed at intake) ----
id: MIM-D-P-0004
uuid: "<full RFC-4122 UUID; placeholder fails validation>"
aliases: []
title: "Math Is Moral"
standard_title: "DLowe 2025-11-02 · Math Is Moral · necessity, moral realism · Thesis"
topic: MIM
also_in: [NIG, ME.INFO]
origin: D
type: P
authors: [David Lowe]
co_authors: [Gemini]            # authorship loyalty: audits go back to them
register: declaration           # declaration | canon
source_sha256: "<untouched intake bytes>"
norm_sha256: "<the .norm.md working copy all spans point into>"
source_uri: null                # external material: where it came from
acquired: 2026-10-15
where: ["V:\\corpus\\MIM\\...", "O:\\_Theophysics_v5\\..."]
written: 2025-11-02
ingested: 2026-10-15
version_of: null
successor_of: []
disposition: null               # after ruling: REBUILD | MERGE | RETIRE

# ---- found (proposed by the scan; accepted by David) ----
tags: [TAG-math-foundations, TAG-moral-realism]
occurrences:
  - id: MIM-D-P-0004.m07
    idea: C-00412
    stance: asserts
    span: {start: 145, end: 212, against: norm_sha256, extractor: "ckg-21 v3.2"}
    status: proposed
claims: [C-00412, C-00413, C-00519]   # rolled up from occurrences
axioms: [AX-T-042, AX-P-07]
definitions: [DEF-0123, DEF-0130]
evidence: [EV-00088]
predictions: [PRD-0007]
isomorphisms: [ISO-002]
lean: [LEAN-0031]
me_nodes: [ME.INFO, ME.COH]
scripture: ["Psalm 19:1", "John 1:1"]
witnesses: ["Augustine, De libero arbitrio II"]
equations: 3
whole_case: {helps: [WC-03], hurts: [], neutral: [WC-11]}
edges: []                        # convenience copy; the ledger is the truth

# ---- status (generated cache; regenerate, never edit) ----
workflow_state: REVIEW_PENDING   # EXTRACTED | REVIEW_PENDING | DISPUTED | RULED | RELEASED
canon_fraction: 0.42
open_claims: 5
retired_claims: 2
definitive_for: null             # set to MIM when this is the definitive paper
last_scan: 2026-10-15
scan_receipt: "<model, prompt version, hash>"
generated_at: 2026-10-15T17:00:00Z
registry_snapshot: "<immutable snapshot id>"

# ---- local (unlimited) ----
local:
  - id: MIM-D-P-0004.x01
    kind: implication
    text: "Any physical origin event presupposes mathematical order already in place."
```

**Rules:** the scan only *proposes* the found section; existing IDs are linked, new ones come back as candidates. `workflow_state` (where the file is in the pipeline) is separate from a claim's `ruling_status` (CANON / OPEN / RETIRED) and separate from `register`; none of them stands in for another. The NIST free-fall `EV-00088` example from v0.1 was illustrative — no evidence record is seeded without a primary-source receipt. *(All values above are illustrative.)*

## 9. The ten intake questions → the sidecar

| # | Question | Fills |
|---|---|---|
| 1 | Which topic? | `topic`, first part of `id` |
| 2 | House, analysis, or external? | `origin` |
| 3 | What type? | `type` |
| 4 | A version of something already in? | `version_of` or `.vN` |
| 5 | A duplicate? | exact hash: stop; near: candidate link for David |
| 6 | Does it make claims? | → atom extraction → `occurrences`, `claims` |
| 7 | Does it contain math? | → math check → `equations`, `lean` |
| 8 | Does it touch the Master Equation? | `me_nodes` |
| 9 | Does it state or use an isomorphism? | `isomorphisms` → ISO registry |
| 10 | Declaration or canon? | `register` |

Questions 1–5 build the ID. Questions 6–10 route the file to stations.

## 10. Claim dedup (how mentions collapse onto one `C`)

Embedding similarity only produces a **candidate cluster**. Before any merge is proposed to David, a bidirectional entailment check (A ⊢ B and B ⊢ A) and a negation/quantifier/modal-flip detector run. Outcomes: SAME (propose merge; old IDs become aliases), DISTINCT, or CONFLICT (becomes a ruling item). Merges and splits are reversible and keep history. "Mathematics is prior to physical law" and "physical law is prior to mathematics" embed nearly identically; they must never merge.

## 11. Build order

1. Topic registry (root codes, paths, aliases), including the Master Equation tree and `WC-01..18`.
2. Map existing numbering in: 188 technical axioms, 22 public axioms, ISO numbers, lean-atom-extractor IDs.
3. Edge ledger with the closed relation list, stance, warrant_group, proposal status.
4. Intake form: the ten questions, minting IDs, writing the sidecar, producing `.norm.md`.
5. Corpus scan that proposes the found section for every file.
6. Claim dedup per §10; David confirms merges.
7. Query views: from a prediction, a claim, a paper, an axiom.
8. Status-cache regeneration on build.

## 12. Validation tests for the spec

- Regex rejects `MIM-H-0002.L4`; migration assigns `MIM-D-H-0002.L4` with the old form as alias.
- Hash of the intake file is identical before and after intake + scan (sidecar holds the metadata).
- Concurrent mints yield distinct IDs; re-ingesting identical bytes under a new path yields one source identity with two locations.
- Renaming or moving a file preserves UUID and every edge.
- Five adversarial pairs (negation, ∀/∃ flip, direction reversal, can/must) never become MERGE candidates.
- Retiring one conjoint premise marks the claim BROKEN; retiring one of two independent supports leaves it SUPPORTED.
- Every sidecar edge matches a ledger record; a stale status cache is detectable by `registry_snapshot`.
- Unknown local fields survive a schema round-trip.

## 13. Open rulings for David

- **S1 / S2 / S3** (one session): ID registry; canon store of record; atom mint.
- Existing atoms (stations 45, 62, atoms repo): re-ID into `C`, or map old IDs as aliases?
- Do `EV` items get rulings, or only tiers (T1–T5)?
- Any topic-code length rule beyond "unique"?
- Law ordering (ME nodes nest by name, so this can stay open without blocking).

*v0.2 — 2026-10-15 — David Lowe + Claude (Opus), consolidating GPT-6, Gemini, Kimi. "Files get a home topic. Ideas belong to the whole corpus."*
