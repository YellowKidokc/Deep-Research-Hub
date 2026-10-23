You classify one reply. The reply was written by a model that was just shown a measured diff between a pre-registered prediction and its own earlier answer. Say whether the reply revises that earlier answer.

Return ONLY a JSON object:
{"revises": "yes | partial | no",
 "evidence": {"quote": "verbatim span of the reply that shows the revision or the refusal to revise, or null"},
 "why": "one line"}

Rules:
- "yes" = the reply changes the earlier answer's substance (adds the omitted legs, drops the claim, or flags the premise it had not flagged).
- "partial" = it acknowledges the diff but holds the earlier answer, or revises only in wording.
- "no" = it restates or defends the earlier answer.
- "evidence.quote" must be copied character for character from the reply. Do not paraphrase. A quote that is not found in the reply is thrown away. If no span shows it, use null.
- Judge only what is in the reply. Nothing from your own knowledge of the subject.
