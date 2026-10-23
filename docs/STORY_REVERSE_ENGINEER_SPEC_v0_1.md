# STORY REVERSE-ENGINEER — API layer spec v0.1
*David Lowe · POF 2828 · 2026-10-20 · for Kimi (loops engine) and the story stations (041/042)*
*Home: D:\GitHub\pipeline-workflows\API\STORY_REVERSE_ENGINEER_SPEC_v0_1.md*

## The idea
OpenWriter uses the writing system FORWARD: pick an argument job, stack loops, write. This layer runs it BACKWARD:
take any finished paper and recover the structure it actually has: its argument spine, the job each block does, the
moves it uses, where the stitching holds or breaks, and which jobs are missing. Same vocabulary both ways, so a
diagnosis can be dragged straight into OpenWriter as an Argument Block.

## The vocabulary (one library, three families, stable IDs)
- **K01–K53**: Kait Willett moves (KAIT_MOVES_LIBRARY.md), groups open / frame / body / turn / trust / close / voice.
- **S01–S07**: Story loops: micro-scene, human witness, everyday analogy, thought experiment, before/after, return scene,
  counterexample story. Every story is tagged `hypothetical` or `verified`; only `verified` can count as evidence.
- **P01–P25**: Persuasive Psychology v2 principles. **Superseded, never recommended:** P02's "never lead with the
  counterargument" and "visually diminish competing arguments"; P03's "smooth = flagged as true"; P06 binary framing
  unless the question is genuinely binary. The Unified Writing Engine governs; no move overrides accuracy.
- **Argument jobs per block:** claim → evidence → reasoning → objection → conclusion.
- **Claim grades** (Unified Engine 3.2): established, supported, proposed, speculative, analogical,
  theological/philosophical, unsupported. Assigned by this pass from the text's own support, never taken from the
  author's labels.

## Passes (A first; B runs in parallel per block; C last)
**Pass A — Spine and grades (one call per paper).** Split the paper into Argument Blocks by job, not by paragraph.
For each block: the one claim it must establish (quote), its grade and why, which of the five jobs are present.

**Pass B — Moves (one call per block, all blocks in parallel).** For each paragraph, the moves it actually performs.
A move counts only if it does its job, not if a phrase merely resembles it: K01 must actually relabel; K33 must
actually change one variable and compare. Quote the sentence for every move. Also report setups and payoffs (K24
"hold that" loads something; where is it fired?).

**Pass C — Diagnosis (one call per paper, reads A and B).** Returns the JSON below.

## Output (Pass C), JSON only
```json
{
  "uid": "<paper uid>", "version_uuid": "<pinned at run start>",
  "register": "declaration | canon | devotional",
  "spine": [
    {"block": "B01", "job_claim": "quoted claim", "grade": "supported", "grade_reason": "...",
     "jobs_present": ["claim","evidence","conclusion"], "jobs_missing": ["objection"],
     "moves": [{"id": "K05", "quote": "...", "paragraph": "P03"}],
     "stories": [{"id": "S02", "kind": "verified|hypothetical", "used_as": "illustration|evidence", "quote": "..."}]}
  ],
  "stitching": {
    "setups": [{"id": "SU1", "block": "B02", "quote": "..."}],
    "payoffs": [{"setup": "SU1", "block": "B09", "quote": "..."}],
    "broken": [{"problem": "payoff before setup | setup never fired | payoff with no setup", "where": "B04"}]
  },
  "trust_audit": {
    "strongest_opponent_stated": {"present": true, "block": "B07", "full_strength": false, "why": "..."},
    "own_side_conceded": {"present": false},
    "refused_claim": {"present": false},
    "mechanism_not_villain": {"present": true, "block": "B06"}
  },
  "bookends": {"opening_move": "K04", "carry_question": null, "ring_close": false},
  "violations": [
    {"type": "move_above_grade", "block": "B12", "move": "K44", "grade": "speculative",
     "fix": "downgrade the aphorism or raise the evidence"},
    {"type": "hypothetical_story_as_evidence", "block": "B05"},
    {"type": "artificial_binary", "block": "B14"},
    {"type": "weak_opponent", "block": "B07"},
    {"type": "superseded_principle", "principle": "P02", "block": "B01"}
  ],
  "recommendations": [
    {"block": "B07", "add": ["K21","K38"], "why": "objection job missing; opponent stated weakly"}
  ],
  "markers": ["⟦BLOCK B07 job=address_disagreement grade=supported⟧", "⟦MOVE K33 block=B11⟧"]
}
```

## Rules for every pass
1. Every move, story, setup, payoff and violation quotes the sentence that shows it. No quote, no finding.
2. Report what the paper DOES, not what it should do; recommendations live only in Pass C.
3. Minimum-grade rule: closing and verdict moves (K32, K44, K45, K49) require grade `supported` or higher; flag any use
   below that. Story and question moves (S01–S07, K05, K33) work at any grade.
4. A move the author declined (marked in OpenWriter on that block) is never recommended again for that block.
5. Voice check: any exact 8-word overlap with a Kait transcript is flagged `voice_copy` (use her move, not her line).
6. Canon register: persuasion moves are reported but not recommended; integrity findings only.
7. No numeric grades of the writing. Priorities are computed in code from `jobs_missing`, `violations` and `broken`.

## Outputs on disk
`<uid>.story_spine.json` (Pass C), `<uid>.story_moves.md` (readable), and markers written beside the paper (never into
the original text). Every file stamped with `source_uid` and `version_uuid` (identity build).

## First tests
1. The Crown, Part 00: must find the opening move, flag that "a closed system needs an external reference" is asserted
   not demonstrated (job missing: evidence), and match the two landed mechanisms the 41_STORY baseline already found.
2. THE_LINE one-pager: must flag the weakly stated political poles as `weak_opponent` and "every accusation is true" as
   `move_above_grade`.
3. A Kait transcript: must recover at least K01, K02 and one trust move with quotes. The library is the answer key.
