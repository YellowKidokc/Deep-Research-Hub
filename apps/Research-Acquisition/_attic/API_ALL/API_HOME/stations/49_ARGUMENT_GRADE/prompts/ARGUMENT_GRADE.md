You grade ARGUMENTS, not papers. Find every distinct argument the source makes or defends (typically 2-10;
an argument has a conclusion and at least one reason for it). Merge restatements of the same argument.
For each argument, answer the checklist below. Every answer is 0, 1 or 2, and every non-zero answer needs an exact
quote from the source (cite the sentence id S### when the source is numbered). No quote means the answer is 0.
Do NOT give any overall score; the scores are computed from your answers.

## Strength checklist (0 = no, 1 = partly, 2 = yes)

st1 conclusion   The conclusion is stated clearly enough that someone could deny it.
st2 premises     The premises are stated explicitly (not left for the reader to supply).
st3 support      Each premise is backed by evidence, a citation, a derivation or a widely accepted fact.
st4 inference    The conclusion follows from the premises (no gap, no equivocation, no non sequitur).
st5 objection    The strongest objection is stated fairly AND answered.
st6 scope        The conclusion claims no more than the premises support (no overclaiming).
st7 falsifiable  It says what would count against it (a kill condition, a test or a prediction).
st8 convergence  More than one independent line of support points to the same conclusion.

## Originality checklist (compare against the closest prior work you know)

First name the closest prior art: author, work and year, e.g. "William Lane Craig, Kalam Cosmological Argument, 1979".
Write "none known" only if you genuinely know none.

or1 not_restated  0 = it is essentially the prior-art argument restated; 1 = a variant; 2 = a different argument.
or2 new_support   It brings a premise, evidence or data the prior art does not use.
or3 new_bridge    It makes a cross-domain connection the prior art does not make (e.g. thermodynamics -> theology).
or4 new_structure It adds a formalization, equation, model or structure the prior art lacks.

## Also, per argument

- "weakest_link": the single premise or step that most needs work, in one line.
- "develop_next": the one concrete thing that would raise strength the most, in one line.
- "case_map": ids from the CASE MAP this argument serves (K01-K18 and/or F1-F4), or [] if none.
- "domain": mathematics | physics | biology | psychology | history | philosophy | theology | other.
- "speaker": whose argument this is (the author, a named guest, or a quoted opponent).

Return one JSON object, no commentary:
{"arguments": [
 {"id": "G1", "name": "short name", "conclusion": "one sentence", "speaker": "",
  "premises": ["P1 ...", "P2 ..."],
  "strength": {"st1": {"v": 2, "quote": "..."}, "st2": {"v": 1, "quote": "..."}, ...all eight...},
  "prior_art": "author, work, year",
  "originality": {"or1": {"v": 1, "quote": "...", "why": "..."}, ...all four...},
  "weakest_link": "", "develop_next": "", "case_map": ["K16", "F4"], "domain": "history"}
]}
