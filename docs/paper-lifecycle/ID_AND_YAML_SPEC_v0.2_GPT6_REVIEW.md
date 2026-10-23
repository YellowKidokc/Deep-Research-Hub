# ID AND YAML SPEC v0.1
## How every item in the corpus is named, described, and connected
**David Lowe (POF 2828) + Claude (Opus) | 2026-10-15**
**Companion to:** `PAPER_LIFECYCLE_MAP_v0.1.md`, `PAPER_LIFECYCLE_CHECKLIST_v0.1.md`

---

## 1. Two IDs on everything

- **UUID** (hidden, permanent): what machines use. Never changes, never reused.
- **Readable ID** (visible): what David and the AIs use. You can tell roughly what something is by looking at it.
- If a readable ID ever has to change (filed under the wrong topic, topics merged), the old one is kept in `aliases`. Nothing that pointed to it breaks.

## 2. The one rule that decides the naming

**Things that are files get a home topic. Things that are ideas belong to the whole corpus.**

- A **file** (your paper, a web page, a book, a transcript, an analysis output) was ingested somewhere, so it gets a readable ID under the topic it came in through. Other topics point to it; it isn't duplicated.
- An **idea** (a claim, a definition, an axiom, a prediction, an isomorphism, a piece of evidence) exists independently of any one file and can belong to many topics at once. It gets a corpus-wide ID.

This is the fix for the structural defect found in the check: claims were named as children of papers, so one claim got a different ID in every paper. Now a paper *mentions* a claim; the claim itself is one record.

## 3. Topic registry

- One list: code, full name, parent (if any), date created, aliases, live counts.
- Codes are 2–4 letters (`MIM` = Math Is Moral). A new code is checked against the registry before it's issued.
- **Nesting is only for true part-of.** The Master Equation's laws are part of it, so they nest, by name, never by number (law ordering is still an open ruling): `ME.GRAV`, `ME.MOT`, `ME.EM`, `ME.STR`, `ME.THERM`, `ME.INFO`, `ME.QM`, `ME.REL`, `ME.WEAK`, `ME.COH`. Derived families go one level deeper: `ME.WEAK.ATONE`. Three levels maximum.
- Theories that *use* the Master Equation (Watcher, Grace, Math Is Moral) are their own topics and link to the nodes they touch.
- Counts live in the registry ("MIM: 4 house papers, 120 external, 31 claims"), never in IDs.

## 4. File IDs (topic-scoped)

Format: `TOPIC-ORIGIN-TYPE-NNNN`

**Origin is a role, not an author:**
- **D** = house work (David's papers and notes, including ones an AI co-wrote; authorship goes in metadata)
- **A** = machine analysis output (CKG runs, audits, API deep passes)
- **X** = external (someone else's work)

**Type:** P paper · N note/draft · W web page · B book · J journal article · Y video/transcript · H hub research run

**Children of a file use a dot:**
- `.v1`, `.v2` = edits of the same document (the base ID is the frozen original)
- `.m07` = mention #7 inside this file, pointing to a corpus-wide item (a claim, definition, axiom…)
- `.q3` = quote #3 from this source
- `.L2` = leg #2 of a hub run
- `.x01` = local item #1 (see §7)

Examples:
- `MIM-D-P-0004`: Math Is Moral, house paper #4 (frozen original)
- `MIM-D-P-0004.v2`: its second edit
- `MIM-D-P-0009`: the rebuilt paper, a new number, linked `successor_of` to 0004 and anything else it drew from
- `MIM-X-B-0007.q3`: quote 3 from external book 7
- `MIM-H-0002.L4`: leg 4 of hub run 2
- Dropped hub sources still get numbers (what got cut is data); the registry counts kept and dropped separately.

## 5. Idea IDs (corpus-wide): the core families

| Family | What it is | Example | Notes |
|---|---|---|---|
| `C` | Claim (atomic, rulable) | `C-00412` | Carries canon status. Papers mention it. |
| `EV` | Evidence item (a fact, a measurement, a document) | `EV-00088` | e.g. NIST's 2.25 s free-fall concession. Supports or opposes claims. |
| `AX` | Axiom | `AX-T-042`, `AX-P-07` | Keeps existing numbering: 188 technical (T), 22 public (P). |
| `DEF` | Definition | `DEF-0123` | The Canonical Definition Registry entries. |
| `PRD` | Prediction | `PRD-0007` | Carries its pre-registration hash and outcome. |
| `ISO` | Isomorphism | `ISO-002` | Keeps existing numbering. Records two endpoints. Analogies don't get ISO numbers. |
| `LEAN` | Lean label | `LEAN-0031` | A readable pointer to lean-atom-extractor's own ID (`project:path:name`). Never a competing identity. |
| `R` | Ruling | `C-00412.r1` | Attached to the thing ruled on. Append-only. |
| `BAL` | Ballot | `BAL-0005` | Multi-AI votes spanning many claims and topics. |
| `KC` | Kill condition | `C-00412.k1` | What would break the claim. |
| `TAG` | Tag (closed vocabulary) | `TAG-physics-thermo` | Open tags live in metadata only, never as IDs. |
| `TOPIC` | The topic codes themselves | `MIM`, `ME.WEAK` | The registry in §3. |

That's the core: twelve families, closed. Anything else lives in the local block (§7) until it earns a family.

## 6. Connections: the edge vocabulary

Everything connects through **edges**: `from → relation → to`. The relation list is **closed** (the API picks from it, never invents one), so every connection in the corpus can be queried the same way.

| Relation | Meaning | Typical use |
|---|---|---|
| `mentions` | file contains this idea | `MIM-D-P-0004.m07 → C-00412` |
| `supports` | gives reason to believe | `EV-00088 → C-00412` |
| `opposes` | gives reason to doubt | `MIM-X-B-0007.q3 → C-00412` |
| `proves` | formal proof | `LEAN-0031 → C-00412` |
| `depends_on` | needs this to hold | `C-00412 → AX-T-042` |
| `implies` | if this holds, that follows | `C-00412 → C-00519` |
| `predicts` | the claim forecasts this | `C-00412 → PRD-0007` |
| `tests` | evidence/outcome bears on a prediction | `EV-00140 → PRD-0007` |
| `defines` | definition used | `C-00412 → DEF-0123` |
| `maps_to` | an isomorphism endpoint | `ISO-002 → ME.WEAK`, `ISO-002 → C-00301` |
| `touches` | links to a Master Equation node | `C-00412 → ME.INFO` |
| `witnesses` | historical thinker reached it independently | `MIM-X-B-0011.q1 → C-00412` |
| `version_of` | edit of the same document | `MIM-D-P-0004.v2 → MIM-D-P-0004` |
| `successor_of` | rebuilt from | `MIM-D-P-0009 → MIM-D-P-0004` |
| `helps` / `hurts` | bears on one of the whole-case arguments | `C-00412 → WC-07` |

Every edge carries: who proposed it (AI or David), status (`proposed` / `accepted` / `rejected`), date, and a one-line reason. **AI-proposed edges stay proposals until David accepts them** (the Adversarial Review Gate rule).

**The correlation you asked for falls out of this.** Starting from any one thing, follow the edges:
- **From a prediction:** which claims predict it → what evidence tests it → which papers mention those claims.
- **From a claim:** every paper that mentions it, every piece of evidence for and against, its axioms, its Lean proof, its predictions, its ruling.
- **From a paper:** every claim it makes, and for each one, how strong it stands across the whole corpus, not just in that paper.
- **From an axiom:** every claim that depends on it. That's dependency tracking: retire the axiom, see what falls.

Edges live in **one ledger** (the source of truth). Each file's YAML lists that file's own edges as a convenience copy, which a rebuild script checks against the ledger.

(`WC-01`…`WC-18` are the 18 whole-case arguments, kept as entries in the topic registry.)

## 7. The local block: unlimited, per paper or per topic

The twelve core families are closed so the whole corpus stays searchable. But a paper will always have things that matter to *it* and don't fit a family yet. Those go in the **local block**: free-form, no limit, owned by that file or topic.

Example from Math Is Moral: an implication you want to carry, like "the Big Bang, if it happened, presupposes mathematics that was already there." That's not a ruled claim yet, it's a consequence you're tracking for this paper. It goes local:

```yaml
local:
  - id: MIM-D-P-0004.x01
    kind: implication          # free text: implication, open question, example, image, aside...
    text: "Any physical origin event presupposes mathematical order already in place."
    bears_on: [WC-03]          # optional links into the core, proposed until accepted
    note: "Track; may become a claim."
```

**Promotion rule:** a local item becomes a core idea when David promotes it (e.g. the implication above becomes `C-00520` and gets ruled on). A local *kind* that keeps showing up across many topics is a candidate for a new core family. That's how the core grows, deliberately, instead of the API inventing categories.

## 8. The YAML header: what a corpus scan identifies in every file

This is the header a knowledge-bank scan fills in for every file in the corpus. Top section is the core (closed fields, same on every file); the bottom is the local block.

```yaml
# ---- identity ----
id: MIM-D-P-0004
uuid: 7f3c2a9e-...                  # permanent, machine use
aliases: []                         # old readable IDs, if any
title: "Math Is Moral"
standard_title: "DLowe 2025-11-02 · Math Is Moral · necessity, moral realism · Thesis"
topic: MIM                          # home topic
also_in: [NIG, ME.INFO]             # other topics that point here
origin: D                           # D house · A analysis · X external
type: P
authors: [David Lowe]
co_authors: [Gemini]                # authorship loyalty: audits go back to them
register: declaration               # declaration | canon
sha256: "..."
where: ["V:\\corpus\\MIM\\...", "O:\\_Theophysics_v5\\..."]
written: 2025-11-02
ingested: 2026-10-15
version_of: null
successor_of: []

# ---- what the scan found in it ----
tags: [TAG-math-foundations, TAG-moral-realism]
claims: [C-00412, C-00413, C-00519]        # via .m mentions
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

# ---- status ----
canon_fraction: 0.42                # share of its claims ruled canon
open_claims: 5
retired_claims: 2
definitive_for: null                # set to MIM when this is the definitive paper
last_scan: 2026-10-15
scan_receipt: "..."                 # model, prompt version, hash

# ---- local (unlimited) ----
local:
  - id: MIM-D-P-0004.x01
    kind: implication
    text: "Any physical origin event presupposes mathematical order already in place."
```

**Rule:** the scan only *proposes* the "what the scan found" section. IDs that already exist are linked; anything new comes back as a candidate for David to accept, so the scan never mints canon on its own.

*(Values in the example above are illustrative, including the date, co-author and counts. The real header gets filled from the actual paper.)*

## 9. The ten intake questions → the header

| # | Question | Fills |
|---|---|---|
| 1 | Which topic? | `topic`, first part of `id` |
| 2 | House, analysis, or external? | `origin` |
| 3 | What type? | `type` |
| 4 | A version of something already in? | `version_of` or `.vN` |
| 5 | A duplicate? | stop, or link to existing |
| 6 | Does it make claims? | → atom extraction → `claims` |
| 7 | Does it contain math? | → math check → `equations`, `lean` |
| 8 | Does it touch the Master Equation? | `me_nodes` |
| 9 | Does it state or use an isomorphism? | `isomorphisms` → ISO registry |
| 10 | Declaration or canon? | `register` |

Questions 1–5 build the ID. Questions 6–10 route the file to stations.

## 10. Build order

1. Topic registry (codes, parents, aliases), including the Master Equation tree and `WC-01..18`.
2. Map existing numbering in: the 188 technical axioms, 22 public axioms, ISO numbers, lean-atom-extractor IDs.
3. Edge ledger with the closed relation list.
4. Intake form: the ten questions, minting IDs.
5. Corpus scan that proposes the "what it found" section for every file.
6. Claim dedup: mentions across papers collapsed onto single `C` records (embedding clustering, David confirms merges).
7. Query views: from a prediction, a claim, a paper, an axiom.

## 11. Open rulings for David

- Which canon store holds the `C` records and rulings (workbench / atoms repo / vault)? Same question as the lifecycle map's S2; this spec needs the answer.
- Existing atoms (from stations 45, 62 and the atoms repo): re-ID them into `C`, or map old IDs as aliases?
- Do `EV` items need their own canon status, or do they only carry tiers (T1–T5)?
- Two-letter vs. four-letter topic codes: any length rule beyond "unique"?

---
*v0.1 — 2026-10-15 — David Lowe + Claude (Opus). "Files get a home topic. Ideas belong to the whole corpus."*

---

# GPT-6 ID / YAML SPEC REVIEW ADDENDUM — 2026-10-15

**Reviewer:** OpenAI GPT-6 | **Reviewed:** 2026-10-15 17:20 UTC | **Review mode:** friendly adversarial, document-level (no repo execution)

## Confirmed inconsistencies in v0.1 text

- **File-ID grammar:** `TOPIC-ORIGIN-TYPE-NNNN` conflicts with `MIM-H-0002.L4` in §4. Suggested example: `MIM-D-H-0002.L4` if house-created; if an external hub run, `MIM-X-H-0002.L4`.
- **Example YAML:** `uuid: 7f3c2a9e-...` is intentionally illustrative, not a valid UUID. Implementations must validate a full UUID.
- **Version semantics:** `.v2` edits a document while a rebuilt successor receives a new base ID. Specify exactly when an edit becomes a successor and whether `.v1` denotes the frozen original or first revision.
- **Canonical bytes vs embedded YAML:** a frozen source's SHA-256 cannot stay the same after injecting frontmatter. Keep `source_sha256`, `extracted_text_sha256`, and `artifact_sha256` separately; attach generated YAML in a sidecar unless working on an explicitly editable derivative.
- **Evidence example:** the purported NIST free-fall item in §5 is illustrative and not source-verified in this review. Do not seed it as a factual evidence record without a primary-source receipt.

## Proposed normative rules

1. **ID uniqueness:** UUID allocated by one transactional registry; readable IDs allocated by topic/type/origin sequence with a unique constraint. Re-ingestion must be idempotent; aliases are unique and resolvable.
2. **Separate entities:** SOURCE (provenance), DOCUMENT (intellectual work), VERSION (text state), ARTIFACT (bytes/file), OCCURRENCE (exact span), IDEA (corpus-wide concept/claim), RECEIPT (check), RULING (human decision), RELEASE (published build). One file can contain many occurrences of the same idea.
3. **Never merge claims solely by embedding similarity:** candidate merges preserve original IDs as aliases only after review; non-equivalent or contradictory claims must remain distinct. Split/merge history is reversible.
4. **Explicit edge typing and validation:** define domain/range for every edge, direction, transitivity rules and whether it is evidential or merely navigational. `proves` must reference an exact Lean statement and checked assumptions. `depends_on` must not be inferred from `mentions`.
5. **Rulings are append-only events:** the latest effective ruling is a materialized view, not a mutable truth field. Store signer, scope, evidence version, effective date and supersession.
6. **Metadata is not the source of truth:** YAML is a generated view of authoritative registries. Include `schema_version`, `generated_at`, `generated_by`, `source_sha256`, `manifest_id`, and `registry_snapshot` so stale metadata is detectable.
7. **Privacy and provenance:** add rights/license, confidentiality, source URI, acquisition timestamp, extraction method/version and permitted processing destinations.
8. **State separation:** use `workflow_state` (candidate/review/blocked/etc.), `ruling_status` (CANON/OPEN/RETIRED when ruled), `evidence_status` (verified/unverified/disputed), and `publication_status` separately. Do not conflate these with `register: declaration|canon`.
9. **Topic code grammar:** define the root code rule and dotted hierarchy separately. `ME.WEAK.ATONE` is a topic path, not a 2–4-letter root code. Reserve immutable code aliases and enforce depth ≤3.
10. **Schema migration:** preserve unknown fields in `local`, maintain versioned JSON Schema, add backward-compatible readers, and test round-trip export/import without dropping metadata.

## Proposed minimal YAML sidecar example (not a retroactive change to v0.1)

```yaml
schema_version: '0.2-proposed'
id: MIM-D-P-0004
uuid: '00000000-0000-4000-8000-000000000004' # illustrative only
topic: MIM
source_sha256: '<sha256 of untouched intake bytes>'
artifact_sha256: '<sha256 of this derivative, if applicable>'
registry_snapshot: '<immutable snapshot id>'
workflow_state: REVIEW_PENDING
ruling_status: null
evidence_status: UNVERIFIED
publication_status: NOT_RELEASED
occurrences:
  - occurrence_id: MIM-D-P-0004.m07
    claim_id: C-00412
    source_anchor: {page: 2, start: 145, end: 212, extraction_version: 'extractor-1'}
    link_status: PROPOSED
review_receipt: '<immutable receipt id>'
```

**Note:** This example is a *sidecar* or derivative metadata file; the original frozen document is not edited. The placeholder SHA values must fail production validation until replaced.

## Migration and validation tests

- Existing `MIM-H-0002.L4` is rejected or migrated with an explicit alias, never silently rewritten.
- Concurrent allocation cannot produce duplicate readable IDs.
- Renaming/moving a file preserves UUID and references.
- Source hash change invalidates derived receipt freshness.
- Schema round-trip retains unknown local fields and edge status.
- Retiring `C-00412` triggers dependency alerts without deleting earlier releases.
- Every YAML edge matches a versioned authoritative edge-ledger record.

**Review status:** Proposed amendment only. Requires David's decision on canon store, ID allocator, atom maker, and evidence status policy.

