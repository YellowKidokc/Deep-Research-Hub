# Deep Research Hub

One local application, seven screens, that takes a question or a folder of files and produces a research record: the forks inside the argument, the origin of the idea, the sources, the data, and the written piece. A workbench with a walk-through, not a chatbot.

| # | Screen | What it does | Status |
|---|--------|--------------|--------|
| 1 | Deep Research | Job queue over GPT Researcher: folder per job, read receipt, run ledger; `fork_map` jobs: premise audit → neutral cast → triage → verbatim passages → fork map | **steps 1, 2, 4 built** |
| 2 | Targeted Research | Fixed battery (origin and first use, first statement, first study, apologetics; essence paper and last 30 days to come) → `facts.json`, every finding tied to a verbatim quote | **built** |
| 3 | Acquisition | Scrape / Links / Crawl / Search → files | milestone 3 |
| 4 | Search Engine | cocoindex + MarginaliaSearch over `data/` | milestone 4 |
| 5 | YouTube | Video or channel → ytgrab.py markdown in `data/youtube/<Channel>/`, baseline summary appended | **built** |
| 6 | API Layer | Prompt bench: system prompt, ten slots, swappable slot sets | milestone 5 |
| 7 | The Writer | OpenWriter (`apps/openwriter`) as the surface: research and classifications in the side columns, rewrite by selection, Story API calls | app added; design in `docs/WRITER_v0.1.md` |

Suggested order 1 → 2 → 3/4/5 → 6 → 7. Nothing enforces it; every screen runs on its own.

## Layout

```
hub/        Rust wrapper: spawns apps/, serves web/dist, keeps state in data/
  launch.json   the only commands the page can start (no raw command lines over HTTP)
web/        JSX front end (react + vite, same as Top-of-Mind)
apps/       the eleven apps (ten originals + openwriter), each with UPSTREAM.md recording any change made here
prompts/    the API Layer's slot sets; every model call is defined here (run_slot.py runs one)
scripts/    one-off maintenance (archive_pre_ytgrab.py)
data/       everything produced (git-ignored): procs/ (each run's record and log), youtube/, api/
```

## Run it

```
cd web && npm install && npm run build && cd ..
cargo run --manifest-path hub/Cargo.toml
```

Open http://127.0.0.1:2828. `DRH_PORT` changes the port; `DRH_ROOT` points at the repo if you run the hub from elsewhere. The hub only listens on 127.0.0.1.

For front-end work, `cd web && npm run dev` serves on vite's port and proxies `/api` to the hub.

## How the hub runs an app

Each entry in `hub/launch.json` names an `apps/` folder, a working directory inside it, a program, and arguments. `"program": "python"` means the app's own interpreter: the first `.venv` or `venv` found between the working directory and the app root (`Scripts\python.exe` on Windows, `bin/python` elsewhere), else the system Python. Apps never share an environment.

Output (stdout and stderr) goes to `data/procs/<id>.log`; the record goes to `data/procs/<id>.json`. A page reload, or a hub restart, shows the same list. Anything that was running when the hub died is marked `lost`.

## Screen 1, Deep Research

One job file per question in `data/jobs/` (merged over `data/jobs/_defaults.yaml`); the Queue tab runs them, N at a time, through GPT Researcher (`apps/Research-Acquisition/Researcher/gpt-researcher/drh_queue.py`). Each run gets `data/deep_research/<job>/<stamp>/` with the report, its read receipt (files and chunks read, kept, dropped), sources, run record and event log, plus a line in the chapter's ledger. Field reference: `jobs_defaults.example.yaml` in that folder.

`job_type: fork_map` runs the visible pipeline instead (`drh_pipeline.py`, prompts in `prompts/R_web/`). Before any search it lists what the question assumes and every leg (distinct position) a serious person holds, then searches each leg equally in neutral words, keeps only passages found verbatim in the pages, and maps forks → positions → passages. The run folder adds `premise.json`, `net.json`, `triage.json`, `passages.json`, `forks.json`, `forks.md` and `pipeline.json`; the Runs tab shows how many expected legs found a source, which found none, and which positions turned up that nobody expected. To overrule triage, write `overrides.json` (`{"keep": [urls], "drop": [urls]}`) in the run folder and run `drh_pipeline.py --resume <run folder> --from extract`.

Make jobs from the DEBATE MAP:

```
cd apps/Research-Acquisition/Researcher/gpt-researcher
.venv\Scripts\python make_jobs.py path\to\DEBATE_MAP.md --jobs ..\..\..\..\data\jobs --subjects S-CHURCH S-PERSONAL
.venv\Scripts\python make_jobs.py path\to\DEBATE_MAP.md --jobs ..\..\..\..\data\jobs --subjects S-EVIL --job-type fork_map
```

GPT Researcher needs its own venv in that folder (`python -m venv .venv`, then `pip install -r requirements.txt`), `DEEPSEEK_API_KEY` and `TAVILY_API_KEY` in the environment, and Ollama running for embeddings (`PROVIDERS.env`).

## Screen 2, Targeted Research

Type a topic, pick battery items, Run. Each item is a narrow lookup with its own searches (`prompts/T_targeted/battery.json`; edit it to change the battery): **origin and first use**, **first statement / precursor**, **first study**, **apologetics**. Every finding cites passages copied verbatim from the pages read, and the date and name a finding gives must be written in those passages, or it is rejected (and listed with the reason). "unknown" is a legal answer. The Facts tab shows each item's findings with their quotes and links, what was rejected and why, and how much was searched and read. Output: `data/targeted/<topic>/<stamp>/facts.json` and `facts.md`.

Several topics in one go: `python drh_targeted.py --topics-file topics.txt --out ..\..\..\..\data\targeted` (in `apps/Research-Acquisition/Researcher/gpt-researcher`).

## Screen 5, YouTube

Paste a video or channel URL on the Intake tab. The hub runs `ytgrab.py <url> --out data/youtube`, then slot `Y/1` appends `## Baseline Summary` to each transcript that run wrote. The summary calls DeepSeek, so `DEEPSEEK_API_KEY` must be set in the environment the hub (or the watch plugin) starts from; without it the run ends `failed` and the transcripts are kept without a summary. Re-running the slot later fills in what is missing: `python prompts/run_slot.py Y 1 --dir data/youtube --append`.

The browser prompt is the watch plugin: `apps/Research-Acquisition/youtube-transcript-ytdlp/watch_downloader/start_server.bat`, then load `extension/` unpacked in Chrome. It writes to the same `data/youtube/`.

Old `.srt`/`.txt` transcripts from the retired downloaders: `python scripts/archive_pre_ytgrab.py` zips them to `data/youtube/_archive/<date>_pre-ytgrab.zip` with an index (`--dry-run` to see the list first, `--src` for folders outside the repo).

`apps/Research-Acquisition/` carries only what ytgrab.py, the watch plugin and GPT Researcher need; the rest of Research-Acquisition stays in `D:\GitHub\Research-Acquisition` and is git-ignored here (`_attic/`). `git config --global core.longpaths true` is still a good idea on Windows.

## Screen 7, The Writer

OpenWriter is the writing surface: build it once (`cd apps/openwriter && npm install && npx turbo run build`), start it from the Home launch list (or `node packages/openwriter/dist/bin/pad.js`), enable **Deep Research Hub** in its Plugins tab, and restart it. The **Story** tab in its right rail shows the story checklist (`prompts/W_story_checklist.json`; ticks saved in `data/writer/checklists/`), paragraph lengths against the band, and research cards from `data/deep_research/` and `data/youtube/` that match the document's heading.

**Dossier tab** (also in the right rail): one folder per topic in `data/writer/dossiers/<name>/`. Dump into it the open document, pasted text, or links to research already in the hub, then **Sort**: every source is broken into pills, each tied to its own words, and each pill is placed in a section of the saved workflow (`prompts/D_dossier/workflows/default.json`: core claims, origin, who said what, evidence, numbers, arguments for, objections, stories, weird facts, terms, open questions) or cut with a reason. It sorts; it never writes the paper. `dossier.md` is the sorted dossier, `cuts.md` what was cut and why, `ledger.json` where every pill went. Sorting again reads only what is new. An agent connected to OpenWriter's MCP server can do the same with the `drh_dossier_*` tools. Needs `DEEPSEEK_API_KEY` in the environment OpenWriter starts from; from a terminal: `python scripts/dossier.py new|add|run|list`.

## Independence test

Kill the hub, `cd` into any `apps/` folder, run the app by hand. If it works, the wrapper is a wrapper.
