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
