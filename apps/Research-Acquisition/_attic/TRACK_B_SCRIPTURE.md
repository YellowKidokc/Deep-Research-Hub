# TRACK B — SCRIPTURE
**Deep research prompt · inherits EPISTEMIC_TIMELINE_RESEARCH_PROMPT.md**

Read the master prompt first. Schema, two axes, freeze-before-run, miss
logging, and the hard rules all apply unchanged.

ID range: TL-2000 to TL-2999.

---

## What a row is here

One event, or one claim the text makes about an event. Not a book, not a
chapter, not a person. "The Exodus from Egypt" is a row. "Exodus" is not.

Where the text makes a claim ABOUT an event rather than narrating it
(prophecy, retrospective interpretation, epistolary reference), that is its
own row with its own two dates.

---

## THE TWO DATES ARE MANDATORY HERE

This track is the reason the grid has two axes, so neither date may be
omitted or merged.

```yaml
referent_time:        when the event is placed
composition_trad:     traditional dating of the text recording it
composition_crit:     critical dating of the same text
dating_dispute:       none | minor | major
dating_source_trad:   who
dating_source_crit:   who
```

Both composition dates go in. Always. Where they agree, say so. Where they
differ by centuries, record both figures and mark the dispute major.

**Do not adjudicate.** Recording both is the whole job. A row that carries
only one composition date has baked in a position, and every count derived
from the finished grid inherits that position invisibly. This is the single
most damaging thing that can go wrong in this track.

---

## Bands on axis R — one per run

1. Creation
2. The Fall
3. Antediluvian and the Flood
4. Patriarchs
5. Egypt, Exodus, Sinai
6. Conquest and Judges
7. United monarchy
8. Divided monarchy
9. Exile
10. Return and Second Temple
11. Intertestamental
12. Incarnation and infancy
13. Ministry
14. Cross and Resurrection
15. Pentecost and apostolic period
16. Consummation (referent in the future)

Band 16 is the one that breaks naive timelines: the referent has not
occurred, the composition date is fixed in the first century. Record it
anyway. The grid should be able to hold it.

---

## Seed data — use it, do not retype it

- **Viz.Bible events table** — dates, duration, predecessors, participants,
  location, verse references, grouped into periods. CSV, JSON, Airtable, or
  Neo4j. Old Testament records are complete; New Testament is still being
  compiled, so bands 12-16 are hand-built.
- **STEPBible-Data (Tyndale House), CC BY 4.0** — TIPNR gives every proper
  name with all references. This is the join key linking an event row to its
  people.
- **OpenBible.info geocoding, CC BY 4.0** — the place dimension.

None of these carry composition dates. That field is built by hand, both
values, every row.

---

## Track-specific fields

```yaml
genre:        narrative | law | poetry | prophecy | wisdom | epistle | apocalyptic
reference:    book chapter:verse
claim_type:   event | interpretation | prediction | command
```

`genre` is load-bearing. A chronology built by reading poetry and apocalyptic
the same way as chronicle will produce dates the text never asserted. Record
the genre and let the reader weigh it.

---

## Hazards specific to this track

**Harmonization.** Where two accounts differ, record both as separate rows
and mark them. Smoothing a discrepancy destroys exactly the data a later
reader needs.

**Single-tradition dating.** See above. Both values, always.

**Genre flattening.** A day in Genesis 1, a day in a psalm, and a day in
Revelation are not the same kind of claim. Genre first, then dating.

**Retrojected precision.** Where the text gives no date, the row says so.
`referent_time: not dated by text` is a valid and common entry. Do not
import a chronologist's calculation into the referent field without naming
the chronologist in `dating_source_trad`.

---

## First run

Band 5, Egypt through Sinai. It has the richest external cross-referencing,
a live and well-documented dating dispute (early vs late Exodus), and enough
genre variety to test the schema. Band 1 last, once the grain is set — it is
the hardest and it deserves a practiced hand.
