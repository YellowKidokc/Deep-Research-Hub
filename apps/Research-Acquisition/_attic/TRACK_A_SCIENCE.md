# TRACK A — SCIENCE
**Deep research prompt · inherits EPISTEMIC_TIMELINE_RESEARCH_PROMPT.md**

Read the master prompt first. Schema, two axes, freeze-before-run, miss
logging, and the hard rules all apply unchanged. This file adds only what is
specific to the science track.

ID range: TL-1000 to TL-1999.

---

## What a row is here

One named result, law, theorem, or empirical finding. Not a field, not a
research programme, not a scientist. "The second law of thermodynamics" is a
row. "Thermodynamics" is not. "Carnot" is not.

If a result has a formal statement, the row carries the statement, not a
gloss of what it means.

---

## Bands on axis R (referent time) — one per run

1. First instant / Planck era
2. Inflation and the earliest structure
3. Nucleosynthesis
4. Recombination and the background radiation
5. First stars and galaxies
6. Solar system and Earth formation
7. Origin of life
8. Complex life and its diversification
9. Human emergence
10. Present-day operating regularities (no distinct referent era)
11. Far future — heat death, information limits

Band 10 will be the largest. Most physics describes a regularity that holds
at all times rather than an event at one time. Those rows get
`referent_time: all-time` and their interest lies entirely on axis D.

---

## Sweep on axis D (discovery time)

Do not start at 1600. Each band gets swept across the whole record:

- Ancient: Aristotle, Archimedes, Ptolemy, Lucretius
- Patristic and medieval: Augustine on time, Philoponus on impetus,
  Grosseteste, Buridan, Oresme
- Early modern: Copernicus, Kepler, Galileo, Newton, Leibniz
- Nineteenth century: Carnot, Clausius, Kelvin, Maxwell, Boltzmann, Gibbs,
  Darwin, Mendel
- Twentieth: Planck, Einstein, Noether, Hubble, Gödel, Tarski, Turing,
  Shannon, Landauer, Penzias and Wilson, Bekenstein, Hawking, Guth
- Present: whatever is current, marked as current

A band whose rows all sit after 1850 has been swept lazily. Go back and look
for the antecedent.

---

## Track-specific fields

```yaml
formal_statement:   the equation or theorem statement, if it has one
regime:             where it holds and where it breaks
consensus:          settled | contested | fringe | superseded
replication:        strong | limited | single-result | not-applicable
```

`consensus` is about the scientific community's current position. It is a
report, not an endorsement, and it never becomes a truth value.

---

## Hazards specific to this track

**Presentism.** Do not record an ancient thinker as having anticipated a
modern result. Buridan's impetus is not Newton's first law. Record what he
actually said and let the distance show.

**Whig history.** The record is not a march toward the present. Superseded
results were often better supported in their day than their replacements
were at first. Record the supersession, not a verdict on the people.

**Popularization dating.** Date the result to its publication, not to when
it became famous. These differ by decades for several major results.

**Consensus as certainty.** `consensus: settled` means the field agrees. It
does not mean established, and it never licenses an upgrade in `status`.

**Interpretation smuggled into statement.** Record the result. The
interpretation of what it means about reality is a separate row, in a
different lane, usually `formal` or `theological`, with its own warrant.

---

## First run

Band 3, nucleosynthesis. Narrower than the first instant, well documented,
clean dates, and it will expose whether the schema handles a band where the
referent is a process rather than an instant. Do band 1 second, once the
grain is set.
