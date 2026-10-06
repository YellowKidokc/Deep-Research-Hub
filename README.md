# Deep Research Hub

One local application, seven screens, that takes a question or a folder of files and produces a research record: the forks inside the argument, the origin of the idea, the sources, the data, and the written piece. A workbench with a walk-through, not a chatbot.

| # | Screen | What it does | Status |
|---|--------|--------------|--------|
| 1 | Deep Research | Fork finder: every position on a question, in its authors' words, with provenance | milestone 7 |
| 2 | Targeted Research | Fixed battery (etymology, first statement, first study, last 30 days, apologetics) → `facts.json` | milestone 6 |
| 3 | Acquisition | Scrape / Links / Crawl / Search → files | milestone 3 |
| 4 | Search Engine | cocoindex + MarginaliaSearch over `data/` | milestone 4 |
| 5 | YouTube | Video or channel → transcripts as markdown in `data/youtube/<channel>/` | milestone 2 |
| 6 | API Layer | Prompt bench: system prompt, ten slots, swappable slot sets | milestone 5 |
| 7 | The Writer | Story API variance engine → story / college / PhD markdown | milestone 8 |

Suggested order 1 → 2 → 3/4/5 → 6 → 7. Nothing enforces it; every screen runs on its own.

## Layout

```
hub/        Rust wrapper: spawns apps/, serves web/dist, keeps state in data/
  launch.json   the only commands the page can start (no raw command lines over HTTP)
web/        JSX front end (react + vite, same as Top-of-Mind)
apps/       the twelve existing repos, untouched, each with UPSTREAM.md
data/       everything produced (git-ignored); data/procs/ holds each run's .json record and .log
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

## Independence test

Kill the hub, `cd` into any `apps/` folder, run the app by hand. If it works, the wrapper is a wrapper.
