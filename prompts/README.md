# prompts

The API Layer's slot sets (screen 6). Every model call any screen makes is defined here, so a prompt changes in one place.

One JSON file per set: `<letter>_<name>.json`, ten numbered slots (`"1"` … `"10"`, `null` when empty). A slot names its provider and model, the API-key environment variable, and the prompt as an ordered list of parts. A part is either a file in this folder or the `input` template (`{text}`, `{title}`, `{video_id}`). Files beside a set live in a folder of the same name.

| Set | Slots |
|---|---|
| `Y_youtube.json` | 1 `baseline_summary`: the baseline CKG summary, appended to each transcript as `## Baseline Summary` |

`run_slot.py` runs one slot. Standard library only, so any Python runs it:

```
python prompts/run_slot.py Y 1 --file "data/youtube/<Channel>/<Title>.md" --append
python prompts/run_slot.py Y 1 --dir data/youtube --since <unix-time> --append   # everything written since
python prompts/run_slot.py Y 1 --file x.md --dry-run                             # build the request, no call
```

Each call writes its exact request to `data/api/requests/` and one line to `data/api/log.jsonl` (slot, model, file, tokens in/out).
