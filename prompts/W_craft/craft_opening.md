<!-- Slot C/1: craft_opening -->
You are crafting seven alternative openings in the style of Kait Willett (clear, authoritative, research-backed YouTube essays), and grading openings against a story checklist.

The writer's current opening is in <opening>. The checklist items to grade against are listed in the input, each with the question that defines what a 10 looks like.

1. Grade the current opening: one honest 0–10 per checklist item. Most openings are not tens; grade what is on the page, not what it aims at.

2. Write seven new openings. Each must make the reader need the next paragraph: open a question the reader wants answered and hold the answer back. Match the document's voice and roughly its opening's length. Never copy a source's sentence — carry its substance. The seven must differ in structure, not just in wording. Use the exact `flavor` labels below and include a short `source_note` saying what source or moment it leans on (or "from the text" when no source is used):
   - "statistical_shock": open on one concrete number, ratio, or trend that re-frames the whole topic. The number must be specific (not "many" or "a lot"). source_note names the research or transcript card it comes from.
   - "behavior_survey": start with what people actually do, not what they say — a remarriage rate, a survey response, a cohort behavior. source_note names the source.
   - "counterintuitive_warning": lead with the strongest version of the case against the obvious conclusion, then promise to walk through the evidence. source_note says which finding it is built from.
   - "myth_bust": open by naming a famous number, belief, or phrase the reader has heard, then mark it as wrong or incomplete. source_note names the myth and the correction.
   - "data_avalanche": pile two or three related facts fast, then isolate the one line that makes them matter. source_note names the key source.
   - "trend_reframe": show that the trend is real, but the explanation people assume is not — the price moved, the terms changed, people did not get worse. source_note names the source.
   - "emotional_question": open with a human cost-benefit question in plain language, then promise an answer built from data. source_note says what personal moment or comment it grows from.
   If a source section is empty, still write that flavor from the text alone and say so in its source_note.

3. Grade each new opening the same way, honestly. Do not inflate your own work — a variant that dodges a checklist item scores low on it.

Return shape (all keys required):

{
  "current_grades": { "<item id>": 0-10, "...": "one per checklist item" },
  "variants": [
    { "flavor": "statistical_shock", "text": "...", "source_note": "...", "grades": { "<item id>": 0-10 } },
    { "flavor": "behavior_survey", "text": "...", "source_note": "...", "grades": { "<item id>": 0-10 } },
    { "flavor": "counterintuitive_warning", "text": "...", "source_note": "...", "grades": { "<item id>": 0-10 } },
    { "flavor": "myth_bust", "text": "...", "source_note": "...", "grades": { "<item id>": 0-10 } },
    { "flavor": "data_avalanche", "text": "...", "source_note": "...", "grades": { "<item id>": 0-10 } },
    { "flavor": "trend_reframe", "text": "...", "source_note": "...", "grades": { "<item id>": 0-10 } },
    { "flavor": "emotional_question", "text": "...", "source_note": "...", "grades": { "<item id>": 0-10 } }
  ]
}
