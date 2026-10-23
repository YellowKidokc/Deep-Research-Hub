# Deep Research Hub

One local application, seven screens, that takes a question or a folder of files and produces a research record: the forks inside the argument, the origin of the idea, the sources, the data, and the written piece. A workbench with a walk-through, not a chatbot.

| # | Screen | What it does | Status |
|---|--------|--------------|--------|
| 1 | Deep Research | Job queue over GPT Researcher: folder per job, read receipt, run ledger; `fork_map` jobs: premise audit → neutral cast → triage → verbatim passages → fork map | **steps 1, 2, 4 built** |
| 2 | Targeted Research | Fixed battery (etymology, first statement, first study, last 30 days, apologetics) → `facts.json` | milestone 6 |
| 3 | Acquisition | Scrape / Links / Crawl over a local Deepcrawl worker; Search = Marginalia result links → files | **built** |
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

### Tray (Windows)

On Windows the hub is a tray app: the same command opens the hub window and puts an amber "D" in the taskbar tray.

- Left-click the tray icon: open or raise the window. Right-click: Open Hub, each screen, Forge state, Restart, Quit.
- Closing the window hides it to the tray. Only Quit exits; Quit stops every app the hub started. The hub runs inside a Windows job object, so its apps die with it even if it is killed or crashes.
- A second launch raises the running hub instead of starting another.
- `--tray` starts hidden. `--headless` serves the page with no window or tray (what CI uses; the only mode on Linux/macOS).

Start on login (per-user Run key, no admin needed; uses the `.exe` you run it from, so build release first):

```
cargo build --release --manifest-path hub/Cargo.toml
hub\target\release\drh-hub.exe --autostart on     REM off to remove
```

The release build has no console window. The `.exe` finds the repo from its own location, so the login start needs no `DRH_ROOT`.

### Forge (every AI call)

The hub holds no model keys and no provider SDKs. Every AI call goes to Forge (repo Rust_AI_API) on its local port: the page calls `/api/forge/<path>` (`forge()` in `web/src/api.js`) and the hub passes it to `FORGE_URL/<path>` unchanged. `FORGE_URL` defaults to `http://127.0.0.1:8790`. The hub checks Forge every 5 s; the tray menu, tray icon (red corner) and page header show `Forge: DOWN` when it is unreachable, and AI calls then fail with a 503 that says so. Nothing falls back to a direct call. Retry policy (in `hub/src/forge_client.rs` only): a refused connection is retried after 0.25 s and 1 s; a call that reached Forge is never repeated.

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

## Screen 3, Acquisition

Scrape, Links and Crawl run `apps/deepcrawl/drh_crawl.py` against Deepcrawl's API worker, run locally with
`apps/deepcrawl/apps/workers/v0/wrangler.local.jsonc` (no auth, local KV/D1, nothing on deepcrawl.dev). Start it from
the screen ("Start worker") or Home ("Deepcrawl API worker", 127.0.0.1:8080). First time only:
`cd apps/deepcrawl && pnpm install --filter "deepcrawl-worker-v0..."`, then
`cd apps/workers/v0 && pnpm exec wrangler d1 migrations apply DB_V0 --local -c wrangler.local.jsonc`.

- Scrape: one page → `data/crawl/<host>/<stamp>/pages/001_*.md` (front matter: url, title, description, fetched).
- Links: every link on a page, internal and external (its citations) → `data/links/<host>/<stamp>/links.txt`, `links.json`, `tree.json`.
- Crawl: same-host breadth-first walk, `pages` and `depth` limits → markdown per page, `links.json`, `index.md`, `crawl.json`.
- Search: `apps/MarginaliaSearch/drh_search.py` takes result links from Marginalia's official API → `data/search/<query>/<stamp>/results.json`,
  `links.txt`, `results.md`; `read N` also pulls the top N to markdown through Deepcrawl. The shared `public` key runs out
  (per minute and per day); put a personal key in `MARGINALIA_API_KEY` (free for non-commercial use: kontakt@marginalia.nu) and restart the hub.

Launch params `web_url` (http/https, no spaces) and `query` (1-300 chars, never starting with `-`) are checked by the hub.

## Screen 5, YouTube

Paste a video or channel URL on the Intake tab. The hub runs `ytgrab.py <url> --out data/youtube`, then slot `Y/1` appends `## Baseline Summary` to each transcript that run wrote. The summary calls DeepSeek, so `DEEPSEEK_API_KEY` must be set in the environment the hub (or the watch plugin) starts from; without it the run ends `failed` and the transcripts are kept without a summary. Re-running the slot later fills in what is missing: `python prompts/run_slot.py Y 1 --dir data/youtube --append`.

The browser prompt is the watch plugin: `apps/Research-Acquisition/youtube-transcript-ytdlp/watch_downloader/start_server.bat`, then load `extension/` unpacked in Chrome. It writes to the same `data/youtube/`.

Old `.srt`/`.txt` transcripts from the retired downloaders: `python scripts/archive_pre_ytgrab.py` zips them to `data/youtube/_archive/<date>_pre-ytgrab.zip` with an index (`--dry-run` to see the list first, `--src` for folders outside the repo).

`apps/Research-Acquisition/` carries only what ytgrab.py, the watch plugin and GPT Researcher need; the rest of Research-Acquisition stays in `D:\GitHub\Research-Acquisition` and is git-ignored here (`_attic/`). `git config --global core.longpaths true` is still a good idea on Windows.

## Screen 7, The Writer

OpenWriter is the writing surface: build it once (`cd apps/openwriter && npm install && npx turbo run build`), start it from the Home launch list (or `node packages/openwriter/dist/bin/pad.js`), enable **Deep Research Hub** in its Plugins tab, and restart it. The **Story** tab in its right rail shows the story checklist (`prompts/W_story_checklist.json`; ticks saved in `data/writer/checklists/`), paragraph lengths against the band, and research cards from `data/deep_research/` and `data/youtube/` that match the document's heading.

## Independence test

Kill the hub, `cd` into any `apps/` folder, run the app by hand. If it works, the wrapper is a wrapper.
