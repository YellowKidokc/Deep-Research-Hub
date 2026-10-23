# TASK: extract evidence for a DEBATE_MAP question

The INPUT is a source essay. Pull out every empirical finding, named study, survey result, quotation, historical example, and citation it uses.

Output a Markdown file with this exact structure:

## Evidence
| Finding | Source in essay | Confidence | How it is used |
|---|---|---|---|
| [one-sentence finding] | [section or citation] | [high / medium / low] | [supports / undermines / illustrates] |
| ... | ... | ... | ... |

Rules:
- Do not invent studies, numbers, or names that do not appear in the essay.
- If a citation is vague (e.g., "studies show"), note `vague` in the source column.
- Keep findings in the essay's own words.
- Return only the table. No intro, no conclusion.
