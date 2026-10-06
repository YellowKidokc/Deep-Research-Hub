"""Direct transcript fetch via youtube-transcript-api.

This sits between yt-dlp and the ytgrab hand-off. It hits a different
endpoint than yt-dlp does, so it often succeeds when yt-dlp is blocked -
and unlike the ytgrab fallback it runs in-process, with no subprocess, no
temp directory, and no Markdown round-trip.

ytgrab still earns its place as the last resort: its value is the
orchestration (direct pass, then rotating Webshare with retries, then the
optional free-proxy swarm), not the library, which is this same one.

Webshare credentials come from the environment, exactly as the downloader
reads them, so there is one place to set them and no copy in the repo.
"""

from __future__ import annotations

import os

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.proxies import WebshareProxyConfig
    AVAILABLE = True
except ImportError:  # pragma: no cover - depends on the environment
    YouTubeTranscriptApi = None  # type: ignore[assignment]
    WebshareProxyConfig = None  # type: ignore[assignment]
    AVAILABLE = False

# Webshare rotates server-side, so retries are what actually gets a fresh IP.
WEBSHARE_RETRIES = int(os.environ.get("TRANSCRIPT_API_RETRIES", "5"))

PREFERRED_LANGS = ("en", "en-US", "en-GB")


def is_enabled() -> bool:
    """Off unless explicitly turned on, so existing behaviour is unchanged."""
    if not AVAILABLE:
        return False
    flag = os.environ.get("TRANSCRIPT_API_DIRECT", "").strip().lower()
    return flag in ("1", "true", "yes", "on")


def webshare_config():
    """A Webshare config from the environment, or None if unset."""
    user = os.environ.get("WEBSHARE_USER", "").strip()
    password = os.environ.get("WEBSHARE_PASS", "").strip()
    if not user or not password or WebshareProxyConfig is None:
        return None
    # The library appends the -rotate suffix itself; passing it in duplicates it.
    if user.endswith("-rotate"):
        user = user[: -len("-rotate")]
    return WebshareProxyConfig(
        proxy_username=user,
        proxy_password=password,
        retries_when_blocked=WEBSHARE_RETRIES,
    )


def pick_transcript(transcript_list):
    """English if there is one, then an English translation, then anything."""
    try:
        t = transcript_list.find_transcript(list(PREFERRED_LANGS))
        return t, f"English ({'auto-generated' if t.is_generated else 'manual'})"
    except Exception:
        pass
    for t in transcript_list:
        if getattr(t, "is_translatable", False):
            try:
                return t.translate("en"), f"{t.language} -> English"
            except Exception:
                continue
    for t in transcript_list:
        return t, getattr(t, "language", "unknown")
    return None, ""


def to_segments(fetched, segment_cls) -> list:
    """Library snippets -> this tool's TranscriptSegment objects."""
    segments = []
    for snip in fetched:
        start = float(getattr(snip, "start", 0.0) or 0.0)
        duration = float(getattr(snip, "duration", 0.0) or 0.0)
        text = (getattr(snip, "text", "") or "").strip()
        if text:
            segments.append(segment_cls(text=text, start=start, end=start + duration))
    return segments


def fetch(video_id: str, segment_cls, use_webshare: bool = True, log=None) -> dict | None:
    """One transcript, or None if this path cannot get it.

    `segment_cls` is passed in rather than imported so this module does not
    import yt_scrape back.
    """
    def say(msg: str) -> None:
        if log:
            log(msg)

    if not is_enabled() or YouTubeTranscriptApi is None:
        return None

    config = webshare_config() if use_webshare else None
    try:
        api = YouTubeTranscriptApi(proxy_config=config) if config else YouTubeTranscriptApi()
        listing = api.list(video_id)
    except Exception as exc:
        say(f"  transcript-api listing failed: {type(exc).__name__}")
        return None

    transcript, lang = pick_transcript(listing)
    if transcript is None:
        say("  transcript-api found no usable track.")
        return None

    try:
        fetched = transcript.fetch()
    except Exception as exc:
        say(f"  transcript-api fetch failed: {type(exc).__name__}")
        return None

    segments = to_segments(fetched, segment_cls)
    text = " ".join(s.text for s in segments).strip()
    if len(text) < 50:
        say("  transcript-api returned an empty transcript.")
        return None

    say(f"  transcript-api recovered {len(text):,} chars"
        f"{' via Webshare' if config else ' direct'}.")
    return {
        "text": text,
        "segments": segments,
        "language": lang,
        "method": "transcript-api" + ("-webshare" if config else "-direct"),
    }
