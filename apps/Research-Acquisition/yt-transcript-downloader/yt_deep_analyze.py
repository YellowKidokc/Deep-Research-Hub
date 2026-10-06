#!/usr/bin/env python3
"""
yt_deep_analyze.py — Turn polished YouTube transcripts into deep-analysis markdown.

Reads raw or V1-polished .md transcripts, produces readable paragraphs, and prepends
a structured but human-centric analysis block designed for anomaly detection,
question extraction, and cross-video synthesis.

Usage:
    python yt_deep_analyze.py --in transcripts_inbox --out analyzed_transcripts
    python yt_deep_analyze.py --in "subtitles/Gary Habermas" --out analyzed
    python yt_deep_analyze.py --file "subtitles/Andrei Jikh/Trump.md" --out analyzed

Output naming convention:
    {Channel} - {Sequence} - {Title}__analyzed.md
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Timestamp / paragraph helpers (minimal copy so this script is self-contained)
# ---------------------------------------------------------------------------

TS_LINE_MD = re.compile(r"^\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s*(.*)$")
MD_META = re.compile(r"^\*\*(.+?):\*\*\s*(.+?)\s*$", re.M)
WORDISH = re.compile(r"[A-Za-z0-9À-ÿ]")

GAP_SECONDS = 2.0
MAX_PARA_CHARS = 520
SENTENCE_BREAK_CHARS = 240


def parse_md_body(body):
    segs = []
    for line in body.splitlines():
        m = TS_LINE_MD.match(line.strip())
        if m:
            h, mnt, s, text = m.groups()
            start = (int(h) * 3600 + int(mnt) * 60 + int(s)) if s else (int(h) * 60 + int(mnt))
            if text.strip():
                segs.append({"start": float(start), "end": None, "text": text.strip()})
        elif line.strip():
            for chunk in re.split(r"(?<=[.!?])\s+", line.strip()):
                if chunk:
                    segs.append({"start": None, "end": None, "text": chunk})
    return segs


def parse_single_md(raw):
    title_m = re.search(r"^#\s+(.+)$", raw, re.M)
    meta = dict(MD_META.findall(raw))
    # Try to find a "Transcript" section; otherwise take everything after the metadata block.
    tmatch = re.search(r"(?:^|\n)##?\s*Transcript\s*\n+(.+)\s*$", raw, re.S | re.M)
    if not tmatch:
        tmatch = re.search(r"(?:^|\n)##\s+.*\n+(.+)\s*$", raw, re.S | re.M)
    if not tmatch:
        # fallback: skip first #title line and any **Key:** value metadata lines
        lines = raw.splitlines()
        body_lines = []
        in_meta = True
        for line in lines:
            if line.startswith("# "):
                continue
            if in_meta and re.match(r"^\*\*.*:\*\*", line):
                continue
            if in_meta and line.strip() == "":
                continue
            in_meta = False
            body_lines.append(line)
        body = "\n".join(body_lines).strip()
    else:
        body = tmatch.group(1).strip()
    return {
        "title": title_m.group(1).strip() if title_m else "untitled",
        "video_id": meta.get("Video ID", "").strip("` "),
        "url": meta.get("URL", ""),
        "language": meta.get("Transcript Language", ""),
        "channel": meta.get("channel", ""),
        "date": meta.get("Captured", ""),
        "body": body,
    }


def parse_chapter_md(raw):
    """Parse the Gary Habermas chapter format with YAML frontmatter."""
    import yaml
    try:
        # split YAML frontmatter
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                front = yaml.safe_load(parts[1])
                rest = parts[2]
                title = front.get("title", "")
                channel = front.get("channel", "")
                video_id = front.get("video_id", "")
                url = front.get("url", "")
                language = front.get("transcript_language", "")
                chapter = front.get("chapter", "")
                # Explicitly grab the "## Transcript" section if present.
                tmatch = re.search(r"(?:^|\n)##?\s*Transcript\s*\n+(.+)\s*$", rest, re.S | re.M)
                body = tmatch.group(1).strip() if tmatch else rest
                return {
                    "title": f"Chapter {chapter} — {title}" if chapter else title,
                    "video_id": video_id,
                    "url": url,
                    "language": language,
                    "channel": channel,
                    "date": "",
                    "body": body,
                }
    except Exception:
        pass
    return None


def clean_text(text, keep_markers=False):
    t = re.sub(r"\s+", " ", text).strip()
    if not keep_markers:
        t = re.sub(r"^>>\s*", "", t)
    return t


def build_paragraphs(segments):
    paras, cur, cur_start, cur_end = [], [], None, None
    for seg in segments:
        text = seg["text"]
        gap = (seg["start"] - cur_end) if (cur and seg["start"] is not None and cur_end is not None) else 0.0
        hard_break = (
            cur
            and (text.lstrip().startswith(">>")
                 or gap > GAP_SECONDS
                 or len(" ".join(cur)) >= MAX_PARA_CHARS
                 or (len(" ".join(cur)) >= SENTENCE_BREAK_CHARS and cur[-1].rstrip().endswith((".", "!", "?"))))
        )
        if hard_break:
            paras.append({"start": cur_start, "text": " ".join(cur)})
            cur, cur_start = [], None
        cleaned = clean_text(text, keep_markers=False)
        if cleaned:
            cur.append(cleaned)
            if cur_start is None and seg["start"] is not None:
                cur_start = seg["start"]
            if seg["end"] is not None:
                cur_end = seg["end"]
    if cur:
        paras.append({"start": cur_start, "text": " ".join(cur)})
    return paras


def fmt_stamp(seconds):
    if seconds is None:
        return "--:--"
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def count_words(text):
    tokens = [t for t in text.split() if WORDISH.search(t)]
    tokens = [t for t in tokens if not re.fullmatch(r"\[\d{1,2}:\d{2}(?::\d{2})?\]|\[?--:--\]?|\[Music\]", t)]
    return len(tokens)


def safe_name(title):
    name = re.sub(r'[<>:"/\\|?*]', "_", title).strip(" .")
    return name[:120] or "untitled"


def extract_first_timestamp(body):
    m = TS_LINE_MD.search(body)
    if m:
        h, mnt, s, _ = m.groups()
        return (int(h) * 3600 + int(mnt) * 60 + int(s)) if s else (int(h) * 60 + int(mnt))
    return None


def build_analysis_header(video, seq, source_name, word_count):
    title = video.get("title") or "untitled"
    channel = video.get("channel") or "Unknown Channel"
    date = video.get("date") or ""
    video_id = video.get("video_id") or ""
    url = video.get("url") or ""
    language = video.get("language") or ""

    lines = [
        "---",
        f'type: youtube_deep_analysis_v1',
        f'channel: "{channel}"',
        f'video_sequence: {seq}',
    ]
    if date:
        lines.append(f'date: "{date}"')
    lines += [
        f'original_title: "{title}"',
        f'video_id: "{video_id}"',
        f'url: "{url}"',
    ]
    if language:
        lines.append(f'transcript_language: "{language}"')
    lines += [
        f'classification: []',
        f'keywords: []',
        f'anomalies_detected: []',
        f'synthesis_hooks: []',
        f'claim_atoms: []',
        f'cross_video_themes: []',
        f'source_file: "{source_name}"',
        f'word_count: {word_count}',
        f'analyzed_at: "{datetime.now().isoformat(timespec="seconds")}"',
        "---",
        "",
        f"# {channel} — {title}",
        "",
    ]
    if url:
        lines.append(f"[Watch on YouTube]({url})")
        lines.append("")
    lines += [
        "> **Deep analysis scaffold** — fill in the sections below. The YAML frontmatter is designed so a future synthesis API can ingest N of these files and output cross-video reports.",
        "",
        "---",
        "",
        "## 1. Channel & Context",
        "",
        "_Who is this channel? What is their overall project? Where does this video sit in their arc? What audience are they speaking to, and what do they assume the audience already believes?_",
        "",
        "## 2. The Core Claim",
        "",
        "_State the video's underlying thesis in one or two sentences. This should be the claim everything else is scaffolding for._",
        "",
        "## 3. What They Actually Mean",
        "",
        "_What is the latent frame? What worldview, fear, hope, or moral order is being reinforced? What question is the video really answering even if it never asks it directly?_",
        "",
        "## 4. Anomalies & Weird Details",
        "",
        "_Things that don't fit, unusually precise claims, contradictions, rhetorical tics, moments where the speaker slips out of character, facts that feel too convenient, or evidence that is stronger/weaker than the conclusion requires. These are the highest-value extraction targets._",
        "",
        "- **Anomaly 1:** _description + timestamp_",
        "- **Anomaly 2:** _description + timestamp_",
        "",
        "## 5. Effects & Implications",
        "",
        "_If the core claim is true, what follows? If it is false or only partly true, what follows? Who gains and loses power, money, attention, or meaning under each scenario?_",
        "",
        "## 6. Q&A Extraction",
        "",
        "_Questions the video raises and the answers it supplies. Include timestamps._",
        "",
        "| Question | Answer Given | Timestamp |",
        "|---|---|---|",
        "| _Question?_ | _Answer_ | `[mm:ss]` |",
        "",
        "## 7. Connections & Synthesis Hooks",
        "",
        "_Themes, claims, or anxieties that could link to other videos. Name the hook and suggest what kind of video would complete or contradict it._",
        "",
        "- **Hook:** _description_",
        "",
        "## 8. Source Reliability & Rhetorical Notes",
        "",
        "_Credibility signals: cited sources, credentials, sponsorships, emotional pressure tactics, certainty calibration, what is admitted vs. hidden._",
        "",
        "## 9. Polished Transcript",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def process_file(path, out_dir, seq, in_dir=None):
    path = Path(path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    in_dir = Path(in_dir) if in_dir else None

    raw = path.read_text(encoding="utf-8-sig", errors="replace")

    # Try chapter format first, then single-video format
    video = parse_chapter_md(raw)
    if video is None:
        video = parse_single_md(raw)

    segments = parse_md_body(video["body"])
    if not segments:
        return None, "SKIP (no transcript segments found)"

    paras = build_paragraphs(segments)
    transcript_body = "\n\n".join(
        f"[{fmt_stamp(p['start'])}] {p['text']}" for p in paras
    )
    word_count = count_words(transcript_body)

    # Infer channel from folder structure only if it looks like a channel subfolder.
    if not video.get("channel"):
        if in_dir and path.parent != in_dir and path.parent.parent == in_dir:
            video["channel"] = path.parent.name
        elif in_dir and path.parent == in_dir:
            video["channel"] = "Unknown Channel"
        else:
            video["channel"] = path.parent.name

    header = build_analysis_header(video, seq, path.name, word_count)
    out_text = header + transcript_body + "\n"

    channel = video.get("channel") or "Unknown"
    title = video.get("title") or path.stem
    out_name = f"{safe_name(channel)} - {seq:03d} - {safe_name(title)}__analyzed.md"
    out_path = out_dir / out_name
    out_path.write_text(out_text, encoding="utf-8")
    return out_path, f"OK -> {out_path.name}"


def main():
    p = argparse.ArgumentParser(description="Deep-analyze YouTube transcripts.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--in", dest="in_dir", help="folder containing transcript .md files")
    g.add_argument("--file", dest="single_file", help="single transcript .md file")
    p.add_argument("--out", dest="out_dir", default=str(SCRIPT_DIR / "analyzed_transcripts"), help="output folder")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.single_file:
        inputs = [Path(args.single_file)]
    else:
        in_dir = Path(args.in_dir)
        inputs = sorted([f for f in in_dir.iterdir() if f.suffix.lower() == ".md" and f.is_file()])
        # also recurse one level for channel folders
        for sub in sorted(in_dir.iterdir()):
            if sub.is_dir():
                inputs += sorted([f for f in sub.iterdir() if f.suffix.lower() == ".md" and f.is_file()])

    if not inputs:
        print(f"No .md transcript files found in: {args.in_dir or args.single_file}")
        return

    print(f"Analyzing {len(inputs)} file(s) -> {out_dir}\n")
    ok = 0
    for idx, path in enumerate(inputs, 1):
        try:
            out_path, msg = process_file(path, out_dir, idx, in_dir=args.in_dir)
            print(f"  {path.name}: {msg}")
            if out_path:
                ok += 1
        except Exception as e:
            print(f"  {path.name}: ERROR {e}")
    print(f"\nDone. {ok}/{len(inputs)} analyzed.")


if __name__ == "__main__":
    main()
