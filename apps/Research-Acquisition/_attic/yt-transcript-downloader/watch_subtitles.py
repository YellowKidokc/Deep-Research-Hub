"""
watch_subtitles.py
------------------
One watcher for the whole subtitles/ library.

Every --poll seconds it takes a cheap snapshot of each channel folder (file
count + newest modified time). When a folder changes, that channel is marked
"busy". Once a channel has had no new or changed transcripts for --quiet
minutes, the download is treated as finished and the channel is cleaned into
Obsidian notes by "Python Clean Library/clean_library.py" (local Python only,
punctuation model switched on automatically if installed).

Loose files dropped straight into subtitles/ are first sorted into channel
folders by sort_by_channel.py, then cleaned.

Polling instead of OS file events: no extra dependencies, works on network
drives, and cannot miss events during a burst of hundreds of files.

Usage:
    python watch_subtitles.py                  # watch forever, 10 min quiet window
    python watch_subtitles.py --quiet 5        # 5 min quiet window
    python watch_subtitles.py --catch-up       # clean anything not yet cleaned, then watch
    python watch_subtitles.py --dry-run        # log what would run
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
SUBS = REPO / "subtitles"
NOTES = REPO / "obsidian_transcripts"
CLEAN_DIR = REPO / "Python Clean Library"
CLEAN_SCRIPT = CLEAN_DIR / "clean_library.py"
SORT_SCRIPT = CLEAN_DIR / "sort_by_channel.py"
LOG_FILE = REPO / "watch_subtitles.log"

EXTS = (".md", ".srt", ".vtt")
LOOSE = ""  # key for files sitting directly in subtitles/


def log(msg: str) -> None:
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode(), flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def is_transcript(name: str) -> bool:
    return name.lower().endswith(EXTS) and not name.endswith("000 Index.md")


def snapshot() -> dict[str, tuple[int, float]]:
    """{channel: (transcript_count, newest_mtime)}; LOOSE for files in the root."""
    snap: dict[str, tuple[int, float]] = {}
    loose_n, loose_t = 0, 0.0
    with os.scandir(SUBS) as it:
        for entry in it:
            if entry.is_dir():
                if entry.name.startswith((".", "_")):
                    continue
                n, newest = 0, 0.0
                try:
                    with os.scandir(entry.path) as sub:
                        for f in sub:
                            if f.is_file() and is_transcript(f.name):
                                n += 1
                                newest = max(newest, f.stat().st_mtime)
                except OSError:
                    continue
                snap[entry.name] = (n, newest)
            elif entry.is_file() and is_transcript(entry.name):
                loose_n += 1
                loose_t = max(loose_t, entry.stat().st_mtime)
    if loose_n:
        snap[LOOSE] = (loose_n, loose_t)
    return snap


def python_exe() -> str:
    venv = REPO / "venv" / "Scripts" / "python.exe"
    return str(venv) if venv.exists() else sys.executable


def has_punctuators(py: str) -> bool:
    r = subprocess.run([py, "-c", "import punctuators"], capture_output=True)
    return r.returncode == 0


def run(cmd: list[str], dry_run: bool) -> int:
    log("run: " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    if dry_run:
        return 0
    r = subprocess.run(cmd, cwd=CLEAN_DIR, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tail = (r.stdout or "").strip().splitlines()[-3:]
    for line in tail:
        log(f"    {line}")
    if r.returncode != 0:
        err = (r.stderr or "").strip().splitlines()[-1:] or ["(no stderr)"]
        log(f"    exit {r.returncode}: {err[0]}")
    return r.returncode


IN_PLACE = True  # notes go to subtitles/<Channel>/Clean MD/ (set False for obsidian_transcripts/)


def clean(channel: str | None, py: str, punct: bool, dry_run: bool) -> None:
    cmd = [py, str(CLEAN_SCRIPT), "--src", str(SUBS)]
    cmd += ["--in-place"] if IN_PLACE else ["--out", str(NOTES)]
    if channel:
        cmd += ["--channel", channel]
    if punct:
        cmd.append("--punctuate")
    run(cmd, dry_run)


def sort_loose(py: str, dry_run: bool) -> None:
    run([py, str(SORT_SCRIPT), "--dir", str(SUBS), "--apply"], dry_run)


def main() -> int:
    ap = argparse.ArgumentParser(description="Clean each channel into Obsidian notes once its downloads go quiet.")
    ap.add_argument("--quiet", type=float, default=10, help="minutes with no new transcripts before cleaning (default 10)")
    ap.add_argument("--poll", type=float, default=30, help="seconds between folder checks (default 30)")
    ap.add_argument("--catch-up", action="store_true", help="clean everything not yet cleaned on startup")
    ap.add_argument("--no-punctuate", action="store_true", help="skip the local punctuation model")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SUBS.is_dir():
        log(f"error: subtitles folder not found: {SUBS}")
        return 1

    py = python_exe()
    punct = not args.no_punctuate and has_punctuators(py)
    quiet_s = args.quiet * 60

    log(f"watching : {SUBS}")
    log(f"notes -> : {'subtitles/<Channel>/Clean MD/' if IN_PLACE else NOTES}")
    log(f"quiet    : {args.quiet:g} min   poll: {args.poll:g} s   punctuation: {'on' if punct else 'off'}")

    if args.catch_up:
        log("catch-up: cleaning anything new since the last run")
        clean(None, py, punct, args.dry_run)

    last = snapshot()
    busy: dict[str, float] = {}  # channel -> time of last seen change

    try:
        while True:
            time.sleep(args.poll)
            try:
                now_snap = snapshot()
            except OSError as e:
                log(f"scan failed: {e}")
                continue
            now = time.monotonic()

            for ch, sig in now_snap.items():
                if last.get(ch) != sig:
                    if ch not in busy:
                        label = ch or "(loose files)"
                        was = last.get(ch, (0, 0))[0]
                        log(f"activity: {label}  ({was} -> {sig[0]} files) - waiting for it to go quiet")
                    busy[ch] = now
            last = now_snap

            for ch, t in list(busy.items()):
                if now - t < quiet_s:
                    continue
                del busy[ch]
                label = ch or "(loose files)"
                log(f"quiet for {args.quiet:g} min: {label} - cleaning")
                if ch == LOOSE:
                    sort_loose(py, args.dry_run)
                    clean(None, py, punct, args.dry_run)
                    last = snapshot()  # sorting moved files; don't treat that as new activity
                else:
                    clean(ch, py, punct, args.dry_run)
                log(f"done: {label}")
    except KeyboardInterrupt:
        log("stopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())
