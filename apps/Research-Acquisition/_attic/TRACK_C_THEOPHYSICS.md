# TRACK C — THEOPHYSICS
**Deep research prompt · inherits EPISTEMIC_TIMELINE_RESEARCH_PROMPT.md**

Read the master prompt first. Schema, two axes, freeze-before-run, miss
logging, and the hard rules all apply unchanged.

ID range: TL-3000 to TL-3999.

---

## What this track is, and what makes it different

Tracks A, B, and D map other people's claims. This track maps David's own.
It exists so the framework can be laid across the same grid as everything
else and read by the same rules — not scored against them, placed alongside
them.

That makes this the only track where the researcher and the researched are
the same person. Every hazard below follows from that.

---

## THE GOVERNING RULE — status is copied, never assigned

A row's `status` is transcribed from the existing ledger. It is never
decided fresh while writing the row.

If the ledger says a claim is untested, the row says untested. If the ledger
says provisional, the row says provisional. A contributor who upgrades a
status while placing it on the timeline has quietly made the system grade
its own homework, which is the exact failure the whole architecture was
built to prevent.

Where no ledger entry exists, `status: unrecorded` and the row is flagged for
David. Do not infer a status from how well-argued the claim looks.

---

## What a row is here

One claim from the corpus, at the grain the corpus already uses. An atom, an
axiom-chain entry, a law, a derivation node, a Lean theorem. Do not
re-decompose or re-aggregate — the corpus grain is the row grain, so that
rows can be joined back to their source.

---

## Track-specific fields

```yaml
ledger_id:      the existing atom / axiom / theorem id
lane:           formal | theological | empirical | historical
lean_receipt:   theorem name and commit, or none
bridge_grade:   L0-L4, or not-a-bridge
preserved:      what crosses, for bridge rows
lost:           what does not cross
forbidden:      what may not cross
loads:          which rung this bears weight on, if it holds
```

For any row that is a cross-domain bridge, `preserved` / `lost` / `forbidden`
are mandatory. A bridge row without a manifest is not recorded — it goes in
the run log as an incomplete and waits.

---

## Axis placement for this track

**referent_time** — what the claim is about. Most framework claims are
`all-time` (a law, a structure, a constraint). A few are event-anchored.
Mark the difference, because it is the whole difference between what the
formal lane can and cannot reach.

**discovery_time** — when it was worked out, with the `first_reached` field
carrying the historical antecedent per the standing citation rule. Boethius,
Augustine, Aquinas, the Fathers, Scripture alongside. A framework row whose
`first_reached` is blank has not been searched properly — almost nothing here
is without antecedent, and the antecedents are part of the record.

---

## Hazards specific to this track

**Lane inflation.** The formal lane establishes what must hold if the
premises hold. It never establishes that anything occurred. A row claiming a
formal result settles a historical event is rejected, not corrected.

**Status upgrade.** See the governing rule. This is the one that ends the
track's usefulness if it slips.

**Definitional circularity.** Where a property is being derived, check it is
not already inside the definition. A term defined as external cannot be used
to prove externality. Flag any row where the conclusion appears in the
premises, and put the flag in the row, not in a side note.

**Cumulative drift.** Ten framework rows at `provisional` do not make the
framework established. No totalling, per the master rules — and this is the
track where the temptation is strongest.

**Antecedent erasure.** Recording a framework claim as novel when a
historical thinker reached it first. Independent rediscovery is a real and
respectable result; undisclosed rediscovery is not. Search before claiming
novelty, and record what you found.

---

## Prior-art field

```yaml
prior_art:      named work reaching the same structure, or searched-none
prior_art_gap:  what this adds that the prior work does not
```

`searched-none` is only valid with the queries logged in the run log. An
empty prior-art field means the search was not run.

---

## First run

The five impossibility results — Gödel, Tarski, Turing, Clausius, Landauer —
and their placement as generic external input. Small, well bounded, every
row has a clean `discovery_time`, and it will immediately test whether the
lane discipline and the status-copy rule hold under pressure, because that
band is where the framework's strongest claim sits.
