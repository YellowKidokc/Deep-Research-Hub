# 48_API_DEEP

One chain, one run per paper: **Fruits → Axioms → Atoms → Lean → Stories → Master Equation → Coherence**
(David, 2026-09-26: "There's no way that I don't run one and not run them all").

Drop papers (.md) into `API_HOME\INBOX8_API_DEEP\` and run `ONE_MENU.bat 48` with no item: that folder is the default input.

```bat
ONE_MENU.bat 48 --item "path\to\paper.md"            :: or a paper folder, or a folder of .md files
ONE_MENU.bat D  --item "path\to\folder" --limit 3     :: routine D = this chain
python stations\48_API_DEEP\48_api_deep.py paper.md --copy          :: NO API: prompts to files + ALL_IN_ONE on clipboard
python stations\48_API_DEEP\48_api_deep.py paper.md --copy fruits   :: copy just one station's prompt
```

## Prompts are copies, not rewrites

`prompts/` holds the original station prompts copied verbatim from `05_API_DEEP_STATIONS` and `08_NEW_STATION_SPECS`;
`lib/` holds the tested prompt builders (`atom_prompt.py`, `axiom_prompt.py`) and the Fruits grader `fruits_grade.py`
(its rubric, schema, validator, score recompute and renderer are reused as-is). Edit a prompt file to change the call.

Two prompts were written new, because nothing on disk existed for them:
- `FRUITS_SYSTEM_v0.3.0.md` — the grader's config names `fruits_system_v0.3.0.txt`, which was never copied anywhere.
- `FRUITS_SENTENCES.md` — Stage 2 of ANALYTICAL_ARMS_V1 (every sentence, 9 fruits, −2..+2).

## Calls

Every call is JSON mode with max_tokens 8192 (DeepSeek's default is 4k, which truncates), the whole paper numbered
`[P01]`/`S001` locally so every station cites the same ids. A truncated or invalid reply is retried once with the problem
stated; Fruits verdicts are validated against the rubric and sent back once if they fail.

- phase 1, parallel: atoms · Fruits sentence ranges (70 sentences each) · master equation Part A ×2 (temperature 0.7)
- phase 2, parallel, with the atom list (A01..) and the sentence summary: Fruits verdict · axiom nodes · Lean 4 · stories · coherence · ME Part B (only when the paper has math)

## Output (`RUNS/48_API_DEEP/<paper>/<stamp>/`, or `<paper>/02_RUNS/48_API_DEEP/` for paper folders)

`API_DEEP.html` (the page, matrix house style: Love × Truth plot, fruit lollipops, sentence heat strip, every section,
searchable sentence table) · `API_DEEP.md` · `API_DEEP.json` · one `<station>.json` each · `love_truth.json` ·
`fruits_sentences.xlsx` (Sentences colour-coded with Truth Engine trigger words · Profile · Paragraphs) · `API_DEEP.run.json` (tokens, errors, prompt-file hashes) · `calls/` (raw replies).
A rerun reuses every successful call whose prompt is unchanged, so fixing one prompt only pays for that station.
Exit code is 1 if any call failed.

## Not done yet

- Lean corpus is not searched; Lean output is formalization targets only.
- Axiom registry = AXIOMS_PART1 (191 nodes), pending David's canonical-registry decision.
- HTML page template for station 46.
