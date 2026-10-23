# prompts

The API Layer's slot sets (screen 6). Every model call any screen makes is defined here, so a prompt changes in one place.

One JSON file per set: `<letter>_<name>.json`, ten numbered slots (`"1"` … `"10"`, `null` when empty). A slot names its provider and model, the API-key environment variable, and the prompt as an ordered list of parts. A part is either a file in this folder or the `input` template (`{text}`, `{title}`, `{video_id}`). Files beside a set live in a folder of the same name.

| Set | Slots |
|---|---|
| `Y_youtube.json` | 1 `baseline_summary`: the baseline CKG summary, appended to each transcript as `## Baseline Summary` |
| `W_rewrite.json` | 1 `shorter`, 2 `plainer`, 3 `as_the_skeptic`, 4 `unforgotten_sentence`, 5 `custom` (`{instruction}`): rewrite-by-selection for the Writer. Run by OpenWriter's drh plugin (`POST /api/drh/rewrite`), not `run_slot.py` — file parts become the system message, the input template the user message |
| `W_revise.json` | 1 `run_goals` (the Story tab's Run: picked checklist items as goals), 2 `chat` (the chat column beside the doc): whole-document revision returning `{ reply, edits }` as JSON; each edit lands in the doc as a pending rewrite, outlined and labelled with the model. Run by OpenWriter's drh plugin (`POST /api/drh/revise`), same assembly as `W_rewrite`, chat history between system and user message |
| `W_actions.json` | The Writer's preset API calls (left column "API calls", right rail "APIs" tab): 1 `rate` (scored report by part with rubric; each issue pinned as a comment on the quoted words), 2 `fix_from_rating` (acts on the last Rate report), 3 `tighten`, 4 `plainer`. Slots carry `output` (`notes` or `edits`) and `description`. The writer's own API calls live in `data/writer/actions.json`. Run by the drh plugin (`POST /api/drh/action`) |
| `S_synthesize.json` | 1 `stack_to_page`: a research record (checked notes, quotes, sources) in, one coherent 900–1,300 word article out; quotes verbatim, nothing invented. `python prompts/run_slot.py S 1 --file <record.md> --out data/writer/drafts/<name>.md`, then `POST` it to OpenWriter's `/api/documents` |
| `W_craft.json` | 1 `craft_opening`: craft three openings (research / story / YouTube-grounded) from the doc's current opening plus the hub's research, each graded against the story checklist; saved as a story file for the Story tab's variant cycler. Run by OpenWriter's drh plugin (`POST /api/drh/craft-opening`), same assembly as `W_rewrite` |

`run_slot.py` runs one slot. Standard library only, so any Python runs it:

```
python prompts/run_slot.py Y 1 --file "data/youtube/<Channel>/<Title>.md" --append
python prompts/run_slot.py Y 1 --dir data/youtube --since <unix-time> --append   # everything written since
python prompts/run_slot.py Y 1 --file x.md --dry-run                             # build the request, no call
```

Each call writes its exact request to `data/api/requests/` and one line to `data/api/log.jsonl` (slot, model, file, tokens in/out).

## Not slot sets

`R_web/` holds the prompts of the visible web pipeline (`drh_pipeline.py`, job_type `fork_map`), one file per stage: `premise`, `cast`, `triage`, `extract`, `forks`, `synthesize`. Each file is the system prompt for that stage; the stage's input is sent as JSON. The model comes from the job (`model:`) or `PROVIDERS.env`; triage uses the fast model, the rest the smart one.


`W_story_checklist.json` is the Writer's story checklist (OpenWriter, Story tab), not a slot set. Core items apply to every article; the other items are optional techniques ("extras in the loop"), grouped by the video that teaches them (`source` = video id in `sources`, `t` = seconds in). `outlines` are picked per document and their sections tick off like items. Edit the file to change the list; the tab reads it on load.
