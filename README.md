# Deep Research Hub

One local application, seven screens, that takes a question or a folder of files and produces a research record: the forks inside the argument, the origin of the idea, the sources, the data, and the written piece. A workbench with a walk-through, not a chatbot.

| # | Screen | What it does | Status |
|---|--------|--------------|--------|
| 1 | Deep Research | Fork finder: every position on a question, in its authors' words, with provenance | milestone 7 |
| 2 | Targeted Research | Fixed battery (etymology, first statement, first study, last 30 days, apologetics) → `facts.json` | milestone 6 |
| 3 | Acquisition | Scrape / Links / Crawl / Search → files | milestone 3 |
| 4 | Search Engine | cocoindex + MarginaliaSearch over `data/` | milestone 4 |
| 5 | YouTube | Video or channel → ytgrab.py markdown in `data/youtube/<Channel>/`, baseline summary appended | **built** |
| 6 | API Layer | Prompt bench: system prompt, ten slots, swappable slot sets | milestone 5 |
| 7 | The Writer | Story API variance engine → story / college / PhD markdown | milestone 8 |

Suggested order 1 → 2 → 3/4/5 → 6 → 7. Nothing enforces it; every screen runs on its own.

## Layout

```
hub/        Rust wrapper: spawns apps/, serves web/dist, keeps state in data/
  launch.json   the only commands the page can start (no raw command lines over HTTP)
web/        JSX front end (react + vite, same as Top-of-Mind)
apps/       the twelve existing repos, each with UPSTREAM.md recording any change made here
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

## Screen 5, YouTube

Paste a video or channel URL on the Intake tab. The hub runs `ytgrab.py <url> --out data/youtube`, then slot `Y/1` appends `## Baseline Summary` to each transcript that run wrote. The summary calls DeepSeek, so `DEEPSEEK_API_KEY` must be set in the environment the hub (or the watch plugin) starts from; without it the run ends `failed` and the transcripts are kept without a summary. Re-running the slot later fills in what is missing: `python prompts/run_slot.py Y 1 --dir data/youtube --append`.

The browser prompt is the watch plugin: `apps/Research-Acquisition/youtube-transcript-ytdlp/watch_downloader/start_server.bat`, then load `extension/` unpacked in Chrome. It writes to the same `data/youtube/`.

Old `.srt`/`.txt` transcripts from the retired downloaders: `python scripts/archive_pre_ytgrab.py` zips them to `data/youtube/_archive/<date>_pre-ytgrab.zip` with an index (`--dry-run` to see the list first, `--src` for folders outside the repo).

Cloning on Windows needs `git config --global core.longpaths true`: a few paths under `apps/Research-Acquisition/_attic/` are over 260 characters.

## Independence test

Kill the hub, `cd` into any `apps/` folder, run the app by hand. If it works, the wrapper is a wrapper.
