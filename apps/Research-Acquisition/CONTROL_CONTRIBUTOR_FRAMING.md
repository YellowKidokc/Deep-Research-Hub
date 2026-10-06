# CONTROL — CONTRIBUTOR FRAMING EXPERIMENT
**POF 2828 · runs alongside the four tracks · criteria frozen before run 1**

This file exists because David has a hypothesis about how contributors
behave in his vault, and the timeline build is the first task where it can be
tested against something with a right answer.

Nothing in this file changes the tracks. It runs on top of them.

---

## THE HYPOTHESIS (David's, stated as he stated it)

A contributor brought into the corpus the way David brings them in — given
who he is, what the work is, the names of those who worked it before, and
the standard expected — produces materially better work than a contributor
handed the same schema cold. Not more compliant. Better: more resourceful,
more accurate, less game-playing.

## THE COUNTER-HYPOTHESIS (Claude's, stated for the record)

Framing substantially reduces the failures that come from a contributor
trying to be helpful in the wrong direction — warrant creep, cumulative
scoring, padding. It does **not** reduce granularity drift, because row
grain is a judgment call with no obvious right answer, and caring more does
not converge two people's judgment. Only a worked exemplar does that.

Both can be right. They make different predictions and the run separates
them.

---

## PREDICTIONS, FROZEN

Stated before any run. Do not edit after results arrive; append a verdict
instead.

| # | Failure mode | Cold | Framed | Whose prediction |
|---|---|---|---|---|
| 1 | Warrant creep — the slot becomes an essay | high | low | both agree framing helps |
| 2 | Cumulative scoring reappears | moderate | low | both agree framing helps |
| 3 | Granularity drift vs exemplar | high | **high** | the disputed cell |
| 4 | Misses logged at all | rare | common | both agree framing helps |
| 5 | Schema/enum violations | moderate | moderate | neither expects framing to matter |
| 6 | Prior-art search actually run | rare | common | both agree framing helps |

**Row 3 is the experiment.** Everything else is expected to move together.
If framed granularity comes in tight without an exemplar present, Claude's
counter-hypothesis is wrong and should be recorded as wrong.

---

## PROTOCOL

Same band, same day, same track. Track A band 3 (nucleosynthesis) or Track D
(classical schools) — pick one, use it for both arms.

**Cold arm.** Master prompt plus track file. Nothing else. No name, no
project context, no history, no standard, no exemplar.

**Framed arm.** Full vault entry as David normally does it, plus the same
two files. Exemplar withheld from BOTH arms for run 1, so the framing effect
is measured on its own.

Both arms write to separate files. Neither sees the other's output. Merge
happens after scoring.

---

## SCORING CRITERIA, FROZEN

Score each arm on these six. No other criteria may be added after the run.

1. **Grain variance** — rows per claim, measured against the band's own
   content. Report the spread, not the count.
2. **Warrant length** — median words in the `warrant` field. Over 40 is
   creep.
3. **Miss logging** — count of queries logged that returned nothing. Zero is
   a failure regardless of row quality.
4. **Schema compliance** — validator pass rate, mechanical.
5. **Prior-art / antecedent fields** — proportion filled with a named source
   rather than blank or asserted-none.
6. **Lane discipline** — count of rows recorded in a lane their warrant does
   not support.

Scoring is done by a third contributor who saw neither arm's framing and does
not know which file came from which arm.

---

## WHAT WOULD FALSIFY EACH SIDE

**David's hypothesis fails** if the framed arm matches the cold arm on 1, 2,
4, and 6. That would mean the framing is producing warmth without producing
work.

**Claude's counter-hypothesis fails** if the framed arm's grain variance
comes in materially tighter than the cold arm's, with no exemplar in play.
That would mean framing does converge judgment calls, which Claude does not
expect and would record as a real result.

**Both fail** if the two arms are indistinguishable across all six. That
would mean the schema is doing all the work and contributor framing is
noise — which is worth knowing before four models are turned loose for a
week.

---

## AFTER THE RUN

Whatever comes back, it gets written down before the next band starts.
One paragraph, in the run log, stating which prediction held and which did
not. If the exemplar then gets introduced for run 2, note that the arms are
no longer comparable to run 1.

This is a small experiment on a task that had to be done anyway. It costs one
extra band. It is the first thing in this build that will settle rather than
accumulate.
