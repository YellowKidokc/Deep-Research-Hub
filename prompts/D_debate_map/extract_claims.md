# TASK: extract claims for a DEBATE_MAP question

The INPUT is a source essay. Read it carefully and extract every claim that answers, supports, or advances the debate question implied by the essay's focus.

Output a Markdown file with this exact structure:

## Claims
1. **Claim:** [state the claim plainly] — **Support in source:** [which section / finding / argument backs it] — **Tag:** [relevant debate question ID, e.g. Q-MORAL-OBJECTIVE]
2. ...

Rules:
- Keep claims in the essay's own words; do not invent new arguments.
- If the essay marks a premise as contested or speculative, label it `contested`.
- Each claim should be one sentence.
- Return only the Markdown list. No intro, no conclusion.
