# Screen 5 — YouTube

Paste a video or channel URL. The hub runs `apps/Research-Acquisition/yt-transcript-downloader/ytgrab.py <url> --out data/youtube`, then slot `Y/1` (`prompts/Y_youtube.json`, baseline CKG summary) appends `## Baseline Summary` to every transcript that run wrote. One file per video: `data/youtube/<Channel>/<Title>.md`.

- **Intake**: URL, optional per-run limit, the runs and their live log.
- **Library**: channels, videos (ok / failed / no transcript, summarized or not), the file itself.

The browser prompt ("download this?") is the watch plugin in `apps/Research-Acquisition/youtube-transcript-ytdlp/watch_downloader/`; it writes to the same folder through the same two steps.

TODO (screen 4): index `data/youtube/` with cocoindex for vector search.
