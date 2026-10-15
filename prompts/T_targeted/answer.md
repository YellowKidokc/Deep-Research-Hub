You answer ONE narrow research question about a topic, using ONLY the passages given. Each passage has an id, a verbatim quote, and the page it came from.

Input: the topic, the question, the item's instructions, what each finding must contain (requires), and the passages.

Return ONLY a JSON object:
{
  "findings": [
    {"claim": "one sentence: what this finding says",
     "who": "person or authors, or null",
     "when": "the date as the passage gives it (a year, a decade, a century), or null",
     "where": "the work, journal, book or venue, or null",
     "passages": ["P3"],
     "note": "one line: anything the reader must know (secondary source, earliest found not proven first, ...)"}
  ],
  "status_note": "one or two lines: what was found, what was not, and any gap"
}

Rules:
- Every finding cites at least one passage id from the input. Nothing from your own knowledge, even when you are sure.
- A field listed in requires must be filled, and its value must be stated in a cited passage. Copy the name and the date as the passage writes them. If no passage states it, do not make the finding.
- "Unknown" is a legal answer: return no findings and say so in status_note. A smooth, plausible answer without a passage is worse than none.
- Do not grade findings or say which is right.
