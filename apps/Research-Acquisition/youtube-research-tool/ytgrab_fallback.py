"""Fallback transcript acquisition via the yt-transcript-downloader.

yt-dlp is the research tool's primary fetcher, but it gives up quickly when
YouTube blocks it. ytgrab.py in the downloader repo is far more stubborn: it
runs a direct pass, then a Webshare rotating-residential pass with retries,
then an optional free-proxy swarm. When yt-dlp comes back empty we shell out
to ytgrab and convert its Markdown into the segments the rest of this tool
already knows how to handle.

Acquisition is the only thing that crosses the repo boundary. Cleaning,
claim extraction, and every other research stage stay here.

Off unless YTGRAB_FALLBACK is truthy, so the test suite and plain runs are
unaffected. Paths are overridable with YTGRAB_PATH / YTGRAB_PYTHON.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_REPO = Path(r"D:\GitHub\Research-Acquisition\yt-transcript-downloader")

# ytgrab hands back "[MM:SS] text" or "[HH:MM:SS] text" per line.
_STAMPED = re.compile(r"^\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s*(.*)$")
_META = re.compile(r"^\*\*(?P<key>[^:*]+):\*\*\s*(?P<value>.*?)\s*$")

# ytgrab's own passes already take minutes on a blocked video; don't cut them off early.
TIMEOUT_SEC = int(os.environ.get("YTGRAB_TIMEOUT", "1800"))


def is_enabled() -> bool:
    """Opt-in only, and only if the downloader is actually installed."""
    if os.environ.get("YTGRAB_FALLBACK", "").strip().lower() not in ("1", "true", "yes", "on"):
        return False
    return script_path().exists() and python_path().exists()


def script_path() -> Path:
    override = os.environ.get("YTGRAB_PATH", "").strip()
    return Path(override) if override else DEFAULT_REPO / "ytgrab.py"


def python_path() -> Path:
    override = os.environ.get("YTGRAB_PYTHON", "").strip()
    if override:
        return Path(override)
    return script_path().parent / "venv" / "Scripts" / "python.exe"


def _stamp_to_seconds(h: str | None, m: str, s: str | None) -> float:
    # ytgrab omits the hours field under an hour, so the groups shift.
    if s is None:
        return int(h) * 60 + int(m)
    return int(h) * 3600 + int(m) * 60 + int(s)


def parse_markdown(md: str) -> dict:
    """Pull title, metadata, plain text, and timed segments out of ytgrab's .md."""
    meta: dict[str, str] = {}
    title = ""
    lines_out: list[tuple[float, str]] = []
    flat: list[str] = []
    in_body = False

    for line in md.splitlines():
        stripped = line.strip()
        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        if stripped == "## Transcript":
            in_body = True
            continue
        if not in_body:
            m = _META.match(stripped)
            if m:
                meta[m.group("key").strip().lower()] = m.group("value").strip().strip("`")
            continue
        if not stripped or stripped == "---":
            continue
        m = _STAMPED.match(stripped)
        if m:
            g1, g2, g3, text = m.groups()
            if text:
                lines_out.append((_stamp_to_seconds(g1, g2, g3), text))
        else:
            flat.append(stripped)

    if lines_out:
        text = " ".join(t for _, t in lines_out)
    else:
        text = " ".join(flat)

    return {
        "title": title or meta.get("video id", ""),
        "video_id": meta.get("video id", ""),
        "language": meta.get("transcript language", ""),
        "method": meta.get("retrieved via", ""),
        "text": text.strip(),
        "timed": lines_out,
    }


def _build_segments(timed: list[tuple[float, str]], segment_cls):
    """A segment runs until the next one starts; the last gets a nominal 4s."""
    segments = []
    for i, (start, text) in enumerate(timed):
        end = timed[i + 1][0] if i + 1 < len(timed) else start + 4.0
        segments.append(segment_cls(text=text, start=start, end=end))
    return segments


def fetch(url: str, segment_cls, log=None) -> dict | None:
    """Run ytgrab for one URL. Returns parsed transcript data, or None.

    `segment_cls` is passed in (rather than imported) to keep this module
    free of a circular import back into yt_scrape.
    """
    def say(msg: str) -> None:
        (log or (lambda m: print(m, file=sys.stderr)))(msg)

    if not is_enabled():
        return None

    with tempfile.TemporaryDirectory(prefix="ytgrab_fallback_") as tmp:
        cmd = [
            str(python_path()), str(script_path()), url,
            "--out", tmp,
        ]
        # Deliberately NOT --skip-direct: ytgrab's direct pass uses
        # youtube-transcript-api, a different code path from yt-dlp, so it
        # often succeeds on its own before any proxy attempt is spent.
        say(f"  Handing off to ytgrab (Webshare passes) — this can take a while...")
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=TIMEOUT_SEC, cwd=str(script_path().parent),
            )
        except subprocess.TimeoutExpired:
            say(f"  ytgrab timed out after {TIMEOUT_SEC}s.")
            return None
        except OSError as exc:
            say(f"  Could not start ytgrab: {exc}")
            return None

        md_files = sorted(Path(tmp).glob("*.md"))
        if not md_files:
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()
            say("  ytgrab produced no transcript." + (f" {tail[-1]}" if tail else ""))
            return None

        data = parse_markdown(md_files[0].read_text(encoding="utf-8", errors="replace"))

    if not data["text"] or len(data["text"]) < 50:
        say("  ytgrab returned an empty transcript.")
        return None

    data["segments"] = _build_segments(data["timed"], segment_cls)
    data["method"] = f"ytgrab-{data.get('method') or 'unknown'}"
    say(f"  ytgrab recovered {len(data['text']):,} chars via {data['method'] or 'unknown'}.")
    return data
