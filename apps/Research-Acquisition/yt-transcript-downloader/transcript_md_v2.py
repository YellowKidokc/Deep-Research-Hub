#!/usr/bin/env python3
"""
transcript_md_v2.py

One standard Obsidian-ready markdown format for every YouTube transcript,
from either source:

  - .srt subtitle files (Simon Dixon grab, future NAS grabs)
  - old-format .md transcripts (cue-per-line "[MM:SS] text" under "## Transcript")

Output, per channel folder:

  <Channel>/00 - Channel Summary.md          (stats + chapter list, sorts to top)
  <Channel>/<CODE> - Chapter 001 - <Title>.md
  <Channel>/<CODE> - Chapter 002 - <Title>.md
  ...

Each video file:

  # <Title>
  **Channel:** [[<Channel>]] (`CODE`) · Chapter N of M · Length MM:SS
  <metadata lines preserved from the old header, if any>
  ---
  ## Contents        (clickable outline, one entry per section)
  ---
  ## Part 1 · 00:00  (a section every --section minutes, default 10)
  [00:00] paragraph  (sentence-aware paragraphs, timestamp at each start)

Channel codes come from channel_codes.json next to this script (edit it to
taste); channels missing from the file get auto initials and are added.

Usage:
  python transcript_md_v2.py -i "video.srt" -o "video.md"
  python transcript_md_v2.py -i "subtitles/" -o "markdown_v2/" --batch
  python transcript_md_v2.py -i "subtitles/" -o "markdown_v2/" --batch --section 5
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

# ---------- timecode helpers ----------

def parse_timecode(tc: str) -> float:
    tc = tc.strip().replace(",", ".")
    parts = tc.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(parts[0])


def fmt_ts(seconds: float, force_hours: bool = False) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0 or force_hours:
        return f"[{h:01d}:{m:02d}:{s:02d}]"
    return f"[{m:02d}:{s:02d}]"


def bare_ts(seconds: float, force_hours: bool = False) -> str:
    return fmt_ts(seconds, force_hours).strip("[]")


def fmt_duration(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


# ---------- input parsers -> list of cues {start, end, text} ----------

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\s*-\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_srt(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8-sig", errors="replace")
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        m = re.match(r"(.+?)\s*-->\s*(.+)", lines[1].strip())
        if not m:
            continue
        text = clean_text(" ".join(l.strip() for l in lines[2:] if l.strip()))
        if text:
            cues.append({"start": parse_timecode(m.group(1)),
                         "end": parse_timecode(m.group(2)),
                         "text": text})
    return cues


OLD_META_RE = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")
OLD_CUE_RE = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$")


def parse_old_md(path: Path) -> tuple[list[dict], list[str], str]:
    """Parse the old cue-per-line markdown. Returns (cues, header_lines, title)."""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")

    title = path.stem
    header_lines: list[str] = []
    cues: list[dict] = []
    in_transcript = False

    for line in lines:
        s = line.rstrip()
        if not in_transcript:
            if s.startswith("# ") and title == path.stem:
                title = s[2:].strip()
            elif re.match(r"^##\s*Transcript", s):
                in_transcript = True
            elif OLD_META_RE.match(s):
                header_lines.append(s)
            continue
        m = OLD_CUE_RE.match(s)
        if m:
            text = clean_text(m.group(2))
            if text:
                cues.append({"start": parse_timecode(m.group(1)),
                             "end": 0.0, "text": text})

    # Old format has no cue end times; approximate from the next cue start.
    for i, cue in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else cue["start"] + 2.0
        cue["end"] = max(nxt, cue["start"] + 0.1)
    return cues, header_lines, title


# ---------- paragraph grouping ----------

def find_break_point(text: str, max_chars: int) -> int:
    if len(text) <= max_chars:
        return -1
    search_end = min(len(text), max_chars + 80)
    best_sentence = -1
    for i in range(search_end - 1, -1, -1):
        if text[i] in ".!?" and i + 1 < len(text) and text[i + 1] == " ":
            if i + 1 <= max_chars or best_sentence == -1:
                best_sentence = i + 1
            if i + 1 <= max_chars:
                break
    if best_sentence != -1:
        return best_sentence
    for i in range(min(len(text), max_chars) - 1, -1, -1):
        if text[i] in ",;:" and text[i + 1] == " ":
            return i + 1
    for i in range(min(len(text), max_chars) - 1, -1, -1):
        if text[i] == " ":
            return i
    return max_chars


def group_paragraphs(cues, gap_threshold=1.5, max_chars=600, max_duration=45.0):
    if not cues:
        return []
    paragraphs = []
    current_start = cues[0]["start"]
    current_text = cues[0]["text"]
    last_end = cues[0]["end"]

    for cue in cues[1:]:
        gap = cue["start"] - last_end
        candidate = current_text + " " + cue["text"]
        duration = cue["start"] - current_start
        sentence_ended = current_text.rstrip().endswith((".", "!", "?"))
        clause_break = current_text.rstrip().endswith((",", ";", ":"))

        if gap > gap_threshold:
            paragraphs.append((current_start, current_text.strip()))
            current_start, current_text = cue["start"], cue["text"]
        elif len(candidate) > max_chars:
            split_at = find_break_point(candidate, max_chars)
            if 0 < split_at < len(candidate):
                paragraphs.append((current_start, candidate[:split_at].strip()))
                current_start, current_text = cue["start"], candidate[split_at:].strip()
            else:
                paragraphs.append((current_start, current_text.strip()))
                current_start, current_text = cue["start"], cue["text"]
        elif duration >= max_duration and (sentence_ended or clause_break):
            paragraphs.append((current_start, current_text.strip()))
            current_start, current_text = cue["start"], cue["text"]
        else:
            current_text = candidate
        last_end = cue["end"]

    paragraphs.append((current_start, current_text.strip()))
    return paragraphs


# ---------- naming ----------

def load_channel_codes(script_dir: Path) -> dict:
    path = script_dir / "channel_codes.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_channel_codes(script_dir: Path, codes: dict) -> None:
    path = script_dir / "channel_codes.json"
    path.write_text(json.dumps(codes, indent=2, ensure_ascii=False, sort_keys=True),
                    encoding="utf-8")


def auto_code(channel: str, taken: set) -> str:
    words = re.findall(r"[A-Za-z0-9]+", channel)
    base = "".join(w[0] for w in words).upper() or "XX"
    code, n = base, 2
    while code in taken:
        code = f"{base}{n}"
        n += 1
    return code


BAD_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|#@$%\^&]')


def safe_filename(text: str, max_len: int = 120) -> str:
    text = BAD_FILENAME_CHARS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip().strip(".")
    return text[:max_len].rstrip()


def clean_title(title: str, channel: str) -> str:
    # Drop a trailing " - <Channel>" (the old files repeat the channel name).
    t = re.sub(r"\s+-\s+" + re.escape(channel) + r"\s*$", "", title)
    return t.strip()


# ---------- rendering ----------


def render_video(title: str, channel: str, code: str, chapter: int, total: int,
                 header_lines: list[str], paragraphs, section_minutes: float,
                 duration: float) -> str:
    force_hours = duration >= 3600
    section_secs = section_minutes * 60.0

    sections: list[list[tuple[float, str]]] = [[]]
    section_starts: list[float] = [paragraphs[0][0] if paragraphs else 0.0]
    for start, text in paragraphs:
        if sections[-1] and start - section_starts[-1] >= section_secs:
            sections.append([])
            section_starts.append(start)
        sections[-1].append((start, text))

    out = [f"# {title.lstrip('#').strip()}", ""]
    out.append(f"**Channel:** [[{channel}]] (`{code}`) · "
               f"Chapter {chapter} of {total} · Length {fmt_duration(duration)} · "
               f"[[00 - Channel Summary]]")
    for hl in header_lines:
        if hl.startswith("**Channel:**"):
            continue
        out.append(hl)
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Contents")
    out.append("")
    for i, st in enumerate(section_starts, 1):
        label = f"Part {i} · {bare_ts(st, force_hours)}"
        out.append(f"- [[#{label}|{label}]]")
    out.append("")
    out.append("---")
    out.append("")

    for i, (st, paras) in enumerate(zip(section_starts, sections), 1):
        out.append(f"## Part {i} · {bare_ts(st, force_hours)}")
        out.append("")
        for start, text in paras:
            out.append(f"{fmt_ts(start, force_hours)} {text}")
            out.append("")
    return "\n".join(out)


def render_channel_summary(channel: str, code: str, entries: list[dict]) -> str:
    timed = [e for e in entries if e.get("duration") is not None]
    prose = [e for e in entries if e.get("duration") is None]
    total_dur = sum(e["duration"] for e in timed)
    n = len(entries)
    avg = total_dur / len(timed) if timed else 0
    longest = max(timed, key=lambda e: e["duration"]) if timed else None

    out = [f"# {channel} — Channel Summary", ""]
    out.append(f"**Code:** `{code}`")
    out.append(f"**Videos:** {n}")
    if prose:
        out.append(f"**With timestamps:** {len(timed)} · **Prose only:** {len(prose)}")
    if timed:
        out.append(f"**Total transcript length:** {fmt_duration(total_dur)}")
        out.append(f"**Average video length:** {fmt_duration(avg)}")
    if longest:
        out.append(f"**Longest video:** [[{longest['file']}|{longest['title']}]] "
                   f"({fmt_duration(longest['duration'])})")
    out.append("")
    out.append("> Chapter numbers follow the order the videos were captured; "
               "upload dates were not available, so order may not match YouTube.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Chapters")
    out.append("")
    out.append("| # | Video | Length |")
    out.append("|---|-------|--------|")
    for e in entries:
        dur = fmt_duration(e["duration"]) if e.get("duration") is not None else "—"
        out.append(f"| {e['chapter']} | [[{e['file']}|{e['title']}]] | {dur} |")
    out.append("")
    return "\n".join(out)


# ---------- driver ----------

def read_source(src: Path):
    """Returns (cues, header_lines, title)."""
    if src.suffix.lower() == ".srt":
        return parse_srt(src), [], src.stem
    return parse_old_md(src)


def convert_one(src: Path, dst: Path, section_minutes: float,
                channel: str = "", code: str = "", chapter: int = 0, total: int = 0) -> dict:
    cues, header_lines, title = read_source(src)
    if not cues:
        return {"status": "EMPTY"}
    paragraphs = group_paragraphs(cues)
    duration = max(c["end"] for c in cues)
    title = clean_title(title, channel) if channel else title
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render_video(title, channel, code, chapter, total,
                                header_lines, paragraphs, section_minutes, duration),
                   encoding="utf-8")
    return {"status": "OK", "duration": duration, "title": title}


def is_old_transcript_md(path: Path) -> bool:
    if path.name.startswith(("channel_", "00 - ")):
        return False
    try:
        head = path.read_text(encoding="utf-8-sig", errors="replace")[:4000]
    except Exception:
        return False
    if "## Transcript" not in head:
        return False
    # Must actually contain cue lines; cleaned-prose files also say "## Transcript".
    return any(OLD_CUE_RE.match(l) for l in head.split("\n"))


def run_batch(src_root: Path, out_root: Path, section_minutes: float,
              srt_only: bool, md_only: bool) -> None:
    script_dir = Path(__file__).resolve().parent
    codes = load_channel_codes(script_dir)
    codes_changed = False

    patterns = []
    if not md_only:
        patterns.append("**/*.srt")
    if not srt_only:
        patterns.append("**/*.md")
    files = sorted({f for pat in patterns for f in src_root.glob(pat)})
    files = [f for f in files if out_root not in f.parents]

    # Group by channel (first path part under the root)
    by_channel: dict[str, list[Path]] = {}
    for f in files:
        rel = f.relative_to(src_root)
        channel = rel.parts[0] if len(rel.parts) > 1 else src_root.name
        if f.suffix.lower() == ".md" and not is_old_transcript_md(f):
            continue
        by_channel.setdefault(channel, []).append(f)

    ok = empty = fail = 0
    for channel in sorted(by_channel):
        # Phase 1: parse everything; only channels with real transcripts get a code.
        parsed = []
        for f in sorted(by_channel[channel], key=lambda p: p.stem.lower()):
            try:
                cues, header_lines, title = read_source(f)
            except Exception as e:
                print(f"FAIL {f}: {e}", file=sys.stderr)
                fail += 1
                continue
            if not cues:
                empty += 1
                continue
            parsed.append((f, cues, header_lines, title, max(c["end"] for c in cues)))
        if not parsed:
            continue

        if channel not in codes:
            codes[channel] = auto_code(channel, set(codes.values()))
            codes_changed = True
        code = codes[channel]
        total = len(parsed)

        # Phase 2: number, render, write.
        entries = []
        for i, (f, cues, header_lines, title, duration) in enumerate(parsed, 1):
            title = clean_title(title, channel)
            name = safe_filename(f"{code} - Chapter {i:03d} - {title}") + ".md"
            dst = out_root / channel / name
            paragraphs = group_paragraphs(cues)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(render_video(title, channel, code, i, total,
                                        header_lines, paragraphs,
                                        section_minutes, duration),
                           encoding="utf-8")
            ok += 1
            entries.append({"chapter": i, "title": title,
                            "file": dst.stem, "duration": duration})
        summary = out_root / channel / "00 - Channel Summary.md"
        summary.write_text(render_channel_summary(channel, code, entries),
                           encoding="utf-8")
        print(f"{channel}: {len(entries)} videos ({code})")

    if codes_changed:
        save_channel_codes(script_dir, codes)
    print(f"done: {ok} converted, {empty} empty, {fail} failed -> {out_root}")


# ---------- prose import (videos that exist only as cleaned prose) ----------

PROSE_PLACEHOLDER_RE = re.compile(r"no transcript available", re.I)
CHAPTER_NAME_RE = re.compile(r"^.+? - Chapter \d+ - (.+?)(?:\s+-\s+.+?)?$")
SKIP_NAME_RE = re.compile(r"^(channel_|playlist_|00 - )| - 000 Index$", re.I)
YAML_FIELD_RE = re.compile(r'^(\w+):\s*"?(.+?)"?\s*$', re.M)


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", t.lower())


def read_prose(path: Path, channel: str):
    """Read a cleaned-prose transcript. Returns dict or None if not usable."""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    head = raw[:6000]
    if "## Transcript" not in head:
        return None
    if any(OLD_CUE_RE.match(l) for l in head.split("\n")):
        return None  # raw cue format, handled by the normal converter
    if PROSE_PLACEHOLDER_RE.search(head):
        return None

    # Body = everything after the first "## Transcript" heading.
    body = raw.split("## Transcript", 1)[1].strip()
    if len(body) < 200:
        return None

    # Title: YAML title field, else first H1, else filename.
    title = None
    m = re.search(r'^title:\s*"(.+?)"\s*$', raw[:2000], re.M)
    if m:
        title = m.group(1)
    else:
        m = re.search(r"^#\s+(.+)$", raw, re.M)
        if m:
            title = m.group(1).strip()
    if not title:
        title = path.stem
    m = CHAPTER_NAME_RE.match(title)
    if m:
        title = m.group(1)
    title = re.sub(r"^Chapter \d+\s*[—-]\s*", "", title)
    title = clean_title(title, channel).strip()

    meta = []
    for field, label in (("video_id", "Video ID"), ("url", "URL")):
        m = re.search(rf'^{field}:\s*"?(.+?)"?\s*$', raw[:2000], re.M)
        if m:
            val = m.group(1)
            meta.append(f"**{label}:** `{val}`" if field == "video_id" else f"**{label}:** {val}")
    return {"title": title, "body": body, "meta": meta}


def render_prose_video(title: str, channel: str, code: str, chapter: int,
                       total: int, meta: list[str], body: str) -> str:
    out = [f"# {title.lstrip('#').strip()}", ""]
    out.append(f"**Channel:** [[{channel}]] (`{code}`) · "
               f"Chapter {chapter} of {total} · Length — (prose source, no timestamps) · "
               f"[[00 - Channel Summary]]")
    out.extend(meta)
    out.append("")
    out.append("---")
    out.append("")
    out.append(body)
    out.append("")
    return "\n".join(out)


def scan_output_channel(out_ch: Path):
    """Entries for every converted video file, parsed back from filenames/headers."""
    entries = {}
    if not out_ch.is_dir():
        return entries
    for f in out_ch.glob("*.md"):
        m = re.match(r"^.+? - Chapter (\d+) - (.+)$", f.stem)
        if not m:
            continue
        chapter = int(m.group(1))
        try:
            head = f.read_text(encoding="utf-8-sig", errors="replace")[:1500]
        except Exception:
            continue
        t = re.search(r"^#\s+(.+)$", head, re.M)
        title = t.group(1).strip() if t else m.group(2)
        dur = None
        d = re.search(r"Length (\d+h \d+m|\d+m \d+s|\d+s)", head)
        if d:
            s = d.group(1)
            hh = re.search(r"(\d+)h", s)
            mm = re.search(r"(\d+)m", s)
            ss = re.search(r"(\d+)s", s)
            dur = ((int(hh.group(1)) if hh else 0) * 3600
                   + (int(mm.group(1)) if mm else 0) * 60
                   + (int(ss.group(1)) if ss else 0))
        entries[f.stem] = {"chapter": chapter, "title": title,
                           "file": f.stem, "duration": dur}
    return entries


def fix_chapter_totals(out_ch: Path, total: int) -> None:
    for f in out_ch.glob("* - Chapter *.md"):
        text = f.read_text(encoding="utf-8", errors="replace")
        new = re.sub(r"Chapter (\d+) of \d+",
                     lambda m: f"Chapter {m.group(1)} of {total}", text, count=1)
        if new != text:
            f.write_text(new, encoding="utf-8")


def run_prose_import(src_root: Path, out_root: Path) -> None:
    script_dir = Path(__file__).resolve().parent
    codes = load_channel_codes(script_dir)
    codes_changed = False

    imported = skipped_dupe = 0
    for ch_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
        channel = ch_dir.name
        out_ch = out_root / channel
        entries = scan_output_channel(out_ch)
        have_titles = {norm_title(e["title"]) for e in entries.values()}
        channel_has_output = bool(entries)

        # Candidate prose files: anything under a Clean MD folder, chapter-named
        # files, or — for channels with no output at all — every top-level md.
        candidates = []
        for f in ch_dir.rglob("*.md"):
            if SKIP_NAME_RE.search(f.stem):
                continue
            rel_parts = f.relative_to(ch_dir).parts
            if "Clean MD" in rel_parts[:-1]:
                candidates.append(f)
            elif CHAPTER_NAME_RE.match(f.stem):
                candidates.append(f)
            elif not channel_has_output and len(rel_parts) == 1:
                candidates.append(f)
        if not candidates:
            continue

        new_items = []
        for f in sorted(candidates, key=lambda p: p.stem.lower()):
            try:
                p = read_prose(f, channel)
            except Exception as e:
                print(f"FAIL {f}: {e}", file=sys.stderr)
                continue
            if not p or not p["title"]:
                continue
            if norm_title(p["title"]) in have_titles:
                skipped_dupe += 1
                continue
            new_items.append(p)
            have_titles.add(norm_title(p["title"]))
        if not new_items and channel_has_output:
            continue

        if channel not in codes:
            codes[channel] = auto_code(channel, set(codes.values()))
            codes_changed = True
        code = codes[channel]

        next_chapter = max((e["chapter"] for e in entries.values()), default=0) + 1
        total = len(entries) + len(new_items)
        out_ch.mkdir(parents=True, exist_ok=True)
        for p in new_items:
            name = safe_filename(f"{code} - Chapter {next_chapter:03d} - {p['title']}") + ".md"
            dst = out_ch / name
            dst.write_text(render_prose_video(p["title"], channel, code,
                                              next_chapter, total, p["meta"], p["body"]),
                           encoding="utf-8")
            entries[dst.stem] = {"chapter": next_chapter, "title": p["title"],
                                 "file": dst.stem, "duration": None}
            next_chapter += 1
            imported += 1

        ordered = sorted(entries.values(), key=lambda e: e["chapter"])
        (out_ch / "00 - Channel Summary.md").write_text(
            render_channel_summary(channel, code, ordered), encoding="utf-8")
        fix_chapter_totals(out_ch, total)
        print(f"{channel}: +{len(new_items)} prose chapters ({code})")

    if codes_changed:
        save_channel_codes(script_dir, codes)
    print(f"done: {imported} prose chapters imported, {skipped_dupe} duplicates skipped")


def main():
    ap = argparse.ArgumentParser(description="Unified transcript -> Obsidian markdown (v2).")
    ap.add_argument("-i", "--input", required=True, help="Input .srt/.md file or folder.")
    ap.add_argument("-o", "--output", help="Output .md file or folder.")
    ap.add_argument("--batch", action="store_true", help="Process a whole folder tree.")
    ap.add_argument("--section", type=float, default=10.0,
                    help="Minutes per section (default: 10; use 5 for shorter sections).")
    ap.add_argument("--srt-only", action="store_true", help="Batch: convert only .srt files.")
    ap.add_argument("--md-only", action="store_true", help="Batch: convert only old-format .md files.")
    ap.add_argument("--prose-import", action="store_true",
                    help="Import videos that exist only as cleaned prose (no timestamps).")
    args = ap.parse_args()

    src = Path(args.input)
    if args.prose_import:
        out_root = Path(args.output) if args.output else src.parent / (src.name + "_v2")
        run_prose_import(src, out_root)
        return
    if args.batch or src.is_dir():
        if not src.is_dir():
            ap.error("Batch mode requires an input folder.")
        out_root = Path(args.output) if args.output else src.parent / (src.name + "_v2")
        run_batch(src, out_root, args.section, args.srt_only, args.md_only)
    else:
        if not src.is_file():
            ap.error(f"Input file not found: {src}")
        dst = Path(args.output) if args.output else src.with_suffix(".v2.md")
        r = convert_one(src, dst, args.section)
        print(f"{r['status']}: {dst}")


if __name__ == "__main__":
    main()
