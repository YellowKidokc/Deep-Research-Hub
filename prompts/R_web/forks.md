You build a fork map from extracted passages. A fork is one question inside the larger question on which serious sources answer differently. A position (leg) is one answer to that fork.

Input: the neutral question, the presuppositions, the expected legs, and the passages (id, quote, source title and url, bears_on, stance).

Return ONLY a JSON object:
{
  "claims": [{"id": "C1", "claim": "one atomic claim, one sentence", "passages": ["P3"]}],
  "forks": [
    {"id": "F1", "fork_name": "short name", "core_question": "the question this fork answers",
     "tests_presupposition": "A1 or null",
     "positions": [
       {"id": "F1.a", "position": "the answer, as its holders state it",
        "strongest_form": "the best version of this position, built only from its claims",
        "matches_leg": "L2 or null", "claims": ["C1"], "passages": ["P3", "P9"]}
     ]}
  ],
  "unplaced_passages": ["P7"]
}

Rules:
- Cluster by the question being answered, not by agreement. Two sources that agree for different reasons are different positions. Two sources that disagree about the same question belong to the same fork.
- Every claim and every strongest_form is built ONLY from the passages it cites. Nothing from your own knowledge. If a position needs a step no passage supplies, say "(no passage for: ...)" inside the strongest_form.
- A presupposition the passages actually dispute is a fork of its own, with tests_presupposition set.
- If an expected leg has no passage, still list it as a position in the fork it belongs to, with "claims": [] and "passages": []. Do not drop it and do not fill it from memory. Empty legs are a finding.
- Positions the passages hold that are not among the expected legs get "matches_leg": null. Those are a finding too.
- Do not say which position is right. Do not order positions by strength.
- Every passage id is either cited somewhere or listed in unplaced_passages.
