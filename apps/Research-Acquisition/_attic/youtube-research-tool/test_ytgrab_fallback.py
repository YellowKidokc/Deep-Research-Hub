"""Tests for the ytgrab hand-off bridge."""

import ytgrab_fallback as fb
from models import TranscriptSegment

SAMPLE_MD = """# Why Ships Float

**Video ID:** `dQw4w9WgXcQ`
**URL:** https://www.youtube.com/watch?v=dQw4w9WgXcQ
**Transcript Language:** English (auto-generated)
**Retrieved via:** webshare
**Captured:** 2026-09-23 00:40

---

## Transcript

[00:01] buoyancy is the whole story here
[00:06] displaced water pushes back
[01:00:10] and that is why they float
"""


def test_parse_markdown_pulls_metadata_and_text():
    data = fb.parse_markdown(SAMPLE_MD)
    assert data["title"] == "Why Ships Float"
    assert data["video_id"] == "dQw4w9WgXcQ"
    assert data["language"] == "English (auto-generated)"
    assert data["method"] == "webshare"
    assert data["text"].startswith("buoyancy is the whole story")
    assert "that is why they float" in data["text"]


def test_parse_markdown_handles_hour_long_stamps():
    data = fb.parse_markdown(SAMPLE_MD)
    starts = [start for start, _ in data["timed"]]
    assert starts == [1, 6, 3610]


def test_parse_markdown_falls_back_to_flat_prose():
    md = SAMPLE_MD.split("## Transcript")[0] + "## Transcript\n\njust plain prose here\n"
    data = fb.parse_markdown(md)
    assert data["text"] == "just plain prose here"
    assert data["timed"] == []


def test_segments_run_until_the_next_one_starts():
    data = fb.parse_markdown(SAMPLE_MD)
    segs = fb._build_segments(data["timed"], TranscriptSegment)
    assert [s.start for s in segs] == [1, 6, 3610]
    assert segs[0].end == 6
    assert segs[1].end == 3610
    assert segs[-1].end == 3614.0  # last segment gets a nominal tail


def test_disabled_without_env(monkeypatch):
    monkeypatch.delenv("YTGRAB_FALLBACK", raising=False)
    assert fb.is_enabled() is False


def test_disabled_when_downloader_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("YTGRAB_FALLBACK", "1")
    monkeypatch.setenv("YTGRAB_PATH", str(tmp_path / "nope.py"))
    monkeypatch.setenv("YTGRAB_PYTHON", str(tmp_path / "nope.exe"))
    assert fb.is_enabled() is False


def test_fetch_returns_none_when_disabled(monkeypatch):
    monkeypatch.delenv("YTGRAB_FALLBACK", raising=False)
    assert fb.fetch("https://youtu.be/x", TranscriptSegment, log=lambda m: None) is None
