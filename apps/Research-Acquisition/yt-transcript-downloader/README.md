# yt-transcript-downloader

Bulk YouTube transcript capture, cleaning and indexing. Windows-first, local Python.

## Main entry points

| Launcher | What it does |
|---|---|
| `RUN_WITH_WEBSHARE.bat` | Paste a video, playlist or channel URL. Direct first, Webshare rotating residential when blocked. Re-runs skip anything already saved. |
| `retry_failed.bat` | Re-fetch every failure placeholder, for one channel folder or the whole library. |
| `GRAB_CHANNEL.bat` / `GRAB_BIG_CHANNEL.bat` | Size-aware channel downloads in resumable batches. |
| `WATCH_SUBTITLES.bat` | Watches `subtitles/` and cleans each channel once downloads go quiet. |
| `SET_WEBSHARE_CREDENTIALS.bat` | Stores `WEBSHARE_USER` / `WEBSHARE_PASS` as user environment variables. Nothing is written to disk. |

## Library layout

```
subtitles/<Channel>/
    <Title>.md          raw transcript, one per video (written the moment it is captured)
    Clean MD/           readable prose: normal paragraphs, sparse five-minute timestamp headings
    Channel Summary/    reserved
    Prompts/            reserved
```

`ytgrab.py` indexes the library by video id, so a channel re-run only fetches
videos that are missing or have a failure placeholder. When a run ends it
converts every channel it touched directly into readable prose in `Clean MD/`
(`--no-clean` to skip). It does not create the older timestamp-per-paragraph
layer first. Conversion is local: rule-based cleanup plus the optional
`punctuators` ONNX model.

## Not in this repo

Transcripts and every derived folder are gitignored and stay local.
`pipeline-workflows/` is its own repository.

## Setup

```
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\pip install punctuators   # optional, for punctuated Clean MD notes
SET_WEBSHARE_CREDENTIALS.bat
```
