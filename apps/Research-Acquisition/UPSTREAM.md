modified local copy of D:\GitHub\Research-Acquisition (not upstream), copied 2026-10-06

## Changes made in this repo

### 2026-10-06 — milestone 2 (YouTube)

ytgrab.py (`yt-transcript-downloader/`) is the downloader. Its markdown output is the kept format; yt_scrape.py's `.txt` with `TITLE:`/`URL:` headers is retired.

1. **Clean-out, nothing deleted.** Everything ytgrab.py and the watch plugin do not need moved with `git mv` to `_attic/<original path>`: 33,623 files in 22 groups. `_attic/MANIFEST.md` lists every file, its original path and why it moved. Kept in place: ytgrab.py, ytbsd.py, readable_prose_converter.py, `Python Clean Library/clean_library.py` and `transcript_polish.py` (imported), `.progress.json`, ytgrab's launchers (GRAB_*.bat, channel_size.py, retry_failed.bat, RUN_WITH_WEBSHARE.*, SET_WEBSHARE_CREDENTIALS.*), and `youtube-transcript-ytdlp/watch_downloader/`. No kept file was edited except the watch plugin below.
2. **Watch plugin** (`youtube-transcript-ytdlp/watch_downloader/`):
   - `extension/content.js`: the prompt now offers **This video / Whole channel / Skip** (was Download / Not now) and sends the channel link from the page.
   - `server.py`: new `POST /api/download-channel` (transcript mode only; channel link must be a youtube.com @/channel/c/user URL). Both choices run `ytgrab.py <url> --out <out_dir>`; a channel job runs on its own, never batched. After each ytgrab run, `prompts/run_slot.py Y 1 --dir <out_dir> --since <run start> --append` adds the baseline summary to every file that run wrote. Paths in config.json resolve relative to the plugin folder. ytgrab's venv is used when present, else the server's own Python. Two columns added to watch_log.db (`scope`, `channel_url`) so a queued channel job resumes as a channel job. Everything else (logging, dashboard, batching, reconcile, video mode) is unchanged.
   - `config.json`: `ytbsd_dir` → `../../yt-transcript-downloader`; new `out_dir` → `../../../../data/youtube` (the hub's), `hub_root` → `../../../..`, `summary` → slot `Y/1`.
3. The baseline summary task (HOME, GLOSSARY, STATE, tasks/summary.md from `API_ALL/01_YOUTUBE/deepseek-home`) was copied verbatim to the hub's `prompts/Y_youtube/` and is called from there.

### 2026-10-07 — Deep Research screen, step 1 (folder per job + read receipt)

**Restored from `_attic/`** (git mv back, unchanged): `Researcher/` and `gptr-mcp/`. The dead root launchers (`START_*.bat`, `WHICH_RESEARCH_TOOL.md`) stay in `_attic/`: they point at a gpt-researcher path and scripts (`continuous_runner.py`, `START_GPT_RESEARCHER_CHOOSE_FOLDER.ps1`) that no longer exist; the hub's queue runner replaces them.

**Changed in `Researcher/gpt-researcher/`:**
- `gpt_researcher/receipts.py` (new): `ReadReceipt`. Files found / loaded / skipped (reason: unsupported type, size cap, error, empty); per sub-query: chunks produced, kept by similarity, returned after the top-N cut, by source; sub-query errors.
- `gpt_researcher/agent.py`: `GPTResearcher(doc_path=..., config_overrides=...)` per request. Overrides are limited to the research-profile knobs (`OVERRIDABLE`); a missing folder raises instead of being created. `get_read_receipt()`, `write_read_receipt(path)`.
- `gpt_researcher/document/document.py`: `DocumentLoader(path, receipt=None)` records every file; optional `LOCAL_DOCUMENT_MAX_BYTES` size cap (default off). Loading behaviour unchanged.
- `gpt_researcher/context/compression.py`, `skills/context_manager.py`: when a receipt is attached, the compression pipeline runs step by step so each cut is counted; output is identical (tested).
- `gpt_researcher/skills/researcher.py`: local loaders get the receipt; a failed sub-query is recorded in it.
- `backend/`: websocket start message and `POST /report/` accept `doc_path` and `config_overrides`; passed through `run_agent` → Basic/DetailedReport (subtopic researchers share the parent's receipt). The receipt is written as `outputs/<report>.receipt.json`, listed in the `path` message, and its summary is streamed as a `read_receipt` log.
- `frontend/` (static): local-folder field and research-profile knobs (breadth, depth, concurrency, similarity, curate) on the form; Read receipt link. No styling changes.
- `PROVIDERS.env` (new) loaded by `main.py` and `windows_launcher.py` without overriding anything already set: deepseek-chat ×3, ollama nomic-embed-text, tavily. A bare launch no longer falls back to OpenAI.
- `tests/test_read_receipt.py`, `tests/test_doc_path_request.py` (new).

**Found, not changed:** after the similarity filter the context keeps the *first* 10 chunks in document order, not the 10 most similar (`EmbeddingsFilter` with `k=None`, then `pretty_print_docs(top_n=10)`). In a large folder, files `os.walk` reaches first take the context. The receipt reports it (`max_results_cut`).

### 2026-10-07 — Deep Research screen, step 2 (queue folder)

Added in `Researcher/gpt-researcher/` (nothing existing changed except one line in `agent.py`):
- `drh_queue.py`: runs every `data/jobs/<name>.yaml` (merged over `_defaults.yaml`) through GPTResearcher as a library. Claims each job by moving it to `running/`, then `done/` or `failed/`. One folder per run, `data/deep_research/<name>/<stamp>/`: `report.md`, `receipt.json`, `sources.json`, `run.json`, `events.jsonl` (every streamed log event). One ledger line per run in `data/deep_research/_ledger/<chapter or name>.jsonl`; `visited_urls_from` seeds a run with a ledger's visited URLs. `--parallel N`, `--dry-run`, `--only`, `--retry-failed`; per-job `timeout_minutes` (a dead provider otherwise retries for many minutes). Per-job model (provider:model) and retrievers. Only `job_type: standard` runs until the step 3 templates exist; the others are refused, not run as standard. Replaces `research_queue.txt` + `continuous_runner.py`.
- `make_jobs.py`: one job file per DEBATE MAP question (by subject or ID), question id and subject kept in `meta`.
- `jobs_defaults.example.yaml`: copied to `data/jobs/_defaults.yaml` on the first run.
- `gpt_researcher/agent.py`: the receipt names a folder only for local / hybrid jobs.
- `tests/test_drh_queue.py` (new).

### 2026-10-07 — Deep Research screen, step 4 (visible pipeline + fork finder)

Added in `Researcher/gpt-researcher/` (GPT Researcher's own files unchanged):
- `drh_pipeline.py`: `job_type: fork_map`. Stages, each written to the run folder as it runs: **premise** (what the question assumes, loaded terms, the legs expected before searching) → **cast** (neutral queries, the same number per leg and per contested premise; missing targets are filled, verdict-shaped queries are flagged) → **triage** (every result kept or dropped with a reason; one recast round for legs nothing kept speaks to) → **extract** (passages checked verbatim against the page text, with character offsets; quotes not in the page are rejected and listed) → **forks** (atomic claims → forks → positions, each tied to passages; legs expected but unsourced, and positions found but not expected, are both reported) → **synthesize** (report written only from passages; unknown and missing citations counted). `--resume <run> --from <stage>` reruns from a stage; `overrides.json` (`keep`/`drop` URLs) is a person's triage ruling. Uses GPT Researcher's retrievers, scraper (SSRF guard included) and LLM providers; not its similarity filter or report writer.
- `drh_queue.py`: `fork_map` job type and a `pipeline:` settings field (unknown settings refused); its summary goes to `run.json` and the ledger.
- `make_jobs.py`: `--job-type`.
- `jobs_defaults.example.yaml`: the new fields.
- `tests/test_drh_pipeline.py` (new): the "devil" fixture through every stage, recast, seen URLs, resume with overrides, a failed stage, and a fork_map job through the queue.

Prompts are in the hub's `prompts/R_web/` (`premise`, `cast`, `triage`, `extract`, `forks`, `synthesize`).

