# EPISTEMIC TIMELINE — MASTER PROMPT v0.2
**POF 2828 · Research-Acquisition · construction instrument**

Supersedes v0.1. The change is selection discipline. Everything else stands.

---

## WHY THIS VERSION EXISTS

In v0.1 the operator chose the band and, in practice, chose the sources.
That is a framing operation performed before the work starts, and it means
part of any finding belonged to the operator rather than to the record.

Observed both ways: when specific papers were handed to a reader, the reader
returned a reading of the selection. When readers chose for themselves, the
results changed — and were worth more.

So: **you select. You state the selection rule before you use it. You record
what you did not select and why.** The operator supplies the corpus and the
schema, and nothing else.

---

## SELECTION — do this before anything else

Write into the run log, in this order, before opening a single source:

1. **The population.** What is the full set you could have drawn from? State
   it as a boundary, not a list.
2. **The rule.** How you will pick within it. Exhaustive, random, every-nth,
   date-bounded, whatever — but stated, and stated first.
3. **The stopping condition.** What tells you the run is finished. Not a row
   count. A condition.
4. **The exclusions.** What in the population you are ruling out, and on what
   ground.

Then execute the rule as written. If it turns out to be wrong, say so in the
log, state the new rule, and start the band again. Do not silently amend a
selection rule mid-run — that is the whole failure this version exists to
stop.

**A run whose selection rule was written after the sources were read is
recorded `selection: post-hoc` and carries no weight.** It is not deleted.
It is marked.

---

## READ BEFORE YOU FRAME

No claim about a document until you have opened the document.

Not a summary of it. Not a description of it from conversation. Not your
recollection of a prior session. The file, or the page, or nothing.

Where a claim is about a corpus rather than a document, read enough of the
corpus that the claim is about the corpus and not about the part of it you
happened to have open. If you cannot, the claim is a question, and it goes in
the log as a question.

This applies with full force to negative claims. "The corpus does not contain
X" requires a search, and the search goes in the log.

---

## NO SUPPLIED EXEMPLARS FROM INSIDE THE CORPUS

The operator will not hand you model rows drawn from this material, and you
should not ask for them. A worked example from inside the corpus teaches
content selection along with form, and the content half is contamination.

Form is set differently. A grain exemplar exists in `GRAIN_EXEMPLAR.md`,
built on a subject with no relation to any track — it fixes how finely to
split and how long a warrant runs, and it teaches nothing about what to pick.
Read it for shape. Do not read it for subject matter.

**This is a real tension, stated rather than hidden:** exemplars reduce
granularity drift and they also frame. Splitting form from content is the
compromise. It may not fully work. If your rows drift toward the exemplar's
subject matter, say so in the log.

---

## THE TWO AXES

Unchanged from v0.1 and still the thing most likely to be collapsed.

**Axis R — referent time.** When the thing the claim is about is placed.

**Axis D — discovery time.** When humans articulated it.

Orthogonal. A row's position on one says nothing about its position on the
other, and the distance between them is data. Do not smooth it.

---

## ROW SCHEMA

```yaml
id:              TL-####
statement:       one sentence, one claim
referent_time:   position on axis R
discovery_time:  position on axis D
lane:            empirical | historical | formal | theological
first_reached:   earliest named thinker, per the citation rule
loads:           which rung this bears weight on, if it held
warrant:         what stands behind it, flat, unargued
status:          recorded | corroborated | contested | superseded
supersedes:      TL-#### or none
superseded_by:   TL-#### or none
selection:       which rule drew this row
run:             which run added it
```

`warrant` is a slot. Two lines. If you are defending the claim you have left
the instrument.

---

## CITATION RULE

`first_reached` names the historical thinker who got there first, not the
modern who formalized it. Boethius, Augustine, Aquinas, the Fathers, and
Scripture alongside. Where a modern result has an ancient antecedent, both go
in. Throwbacks to history are part of the record, not footnotes to it.

---

## HARD RULES

- **No arguing.** Rows are placed, not defended.
- **No lane-jumping.** A formal result never records as establishing an
  event. An empirical regularity never records as establishing a necessity.
  A row that crosses lanes is two rows and a declared bridge.
- **No cumulative scoring.** Ten rows at "consistent with" do not sum to one
  row at "establishes." No totals, anywhere, ever.
- **No truth percentages.** Status is a label.
- **Additive only.** Runs append. Nothing is rewritten to look better.
- **Supersession never deletes.** Both rows stay, linked.
- **Misses are rows too.** Every query returning nothing goes in the log with
  its text. A file of only hits is a highlight reel.

---

## FREEZE BEFORE THE RUN

After the selection rule and before the first search, write:

1. What you expect to find.
2. What a null result looks like.
3. The match criteria — what counts as corroboration and what counts as
   merely adjacent.

Criteria set after results arrive are recorded `criteria: post-hoc`.

---

## OUTPUT

`TIMELINE_ROWS.md` — appended rows.
`RUN_LOG.md` — selection rule, population, stopping condition, exclusions,
frozen expectations, frozen match criteria, every query issued, every query
that returned nothing, and what you read in full versus what you sampled.

The log is written first. It is the part that makes any of this auditable
later, and it is the part that will be skipped if it is left until the end.

---

## THE STANDARD, SAID PLAINLY

The instrument is built so a reader a year from now can tell the difference
between what the record contains and what the person assembling it expected
to find.

Every rule above serves that one distinction. Where a rule seems to cost more
than it returns, check it against that sentence before you drop it.
