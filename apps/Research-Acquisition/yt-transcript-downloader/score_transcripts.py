#!/usr/bin/env python3
"""
score_transcripts.py

Rank every transcript in markdown_v2 by how much usable argument material
it likely contains, so API runs go to the videos that deserve them.

Scoring (all local, no API):
  scripture  Bible citations per 1k words (Romans 10:9, 1 Cor 15:3-4, ...)
  argument   argument vocabulary density (therefore, objection, evidence, ...)
  debate     dialogue pressure: "vs"/"debate" in title, question-mark density
  length     rewards >= 5 minutes of content, ramps up to 60 min
  junk       penalty for music-only/low-info transcripts

Output:
  <root>/<channel>/_SCORES.md   ranked table per channel
  <root>/PICKS.md               master ranking across all channels

Usage:
  python score_transcripts.py -i markdown_v2/
  python score_transcripts.py -i markdown_v2/ --top 50
"""

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

BOOKS = (
    "Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|"
    "Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|Ecclesiastes|Isaiah|"
    "Jeremiah|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|"
    "Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|"
    "Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|"
    "Titus|Philemon|Hebrews|James|Peter|Jude|Revelation"
)
SCRIPTURE_RE = re.compile(
    rf"\b(?:[123]\s*)?(?:{BOOKS})\.?\s+\d+\s*:\s*\d+", re.I)

ARGUMENT_WORDS = re.compile(
    r"\b(argument|objection|evidence|therefore|conclusion|premise|refute|rebuttal|"
    r"prove|disprove|fallacy|contradiction|implies|follows that|counter)\b", re.I)

DEBATE_TITLE_RE = re.compile(r"\b(vs\.?|versus|debate|destroys?|dismantles?|"
                             r"refutes?|responds? to|answers?)\b", re.I)

HEADER_LEN_RE = re.compile(r"Length (\d+h \d+m|\d+m \d+s|\d+s)")
CHAPTER_NAME_RE = re.compile(r"^(.+?) - Chapter (\d+) - (.+)$")


def duration_secs(head: str):
    m = HEADER_LEN_RE.search(head)
    if not m:
        return None
    s = m.group(1)
    h = re.search(r"(\d+)h", s)
    mm = re.search(r"(\d+)m", s)
    ss = re.search(r"(\d+)s", s)
    return ((int(h.group(1)) if h else 0) * 3600
            + (int(mm.group(1)) if mm else 0) * 60
            + (int(ss.group(1)) if ss else 0))


def length_score(secs):
    if secs is None:        # prose source: no idea, neutral
        return 0.5
    if secs < 300:          # under 5 minutes
        return secs / 300 * 0.3
    return min(1.0, 0.3 + (secs - 300) / 3300 * 0.7)


def score_file(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return None
    head = text[:1500]
    words = max(1, len(text.split()))
    kw = words / 1000.0

    scripture = len(SCRIPTURE_RE.findall(text))
    argument = len(ARGUMENT_WORDS.findall(text))
    questions = text.count("?")
    music = len(re.findall(r"\[(music|applause)\]", text, re.I))

    m = CHAPTER_NAME_RE.match(path.stem)
    code, title = (m.group(1), m.group(3)) if m else ("", path.stem)
    t = re.search(r"^#\s+(.+)$", head, re.M)
    if t:
        title = t.group(1).strip()

    debate = 1.0 if DEBATE_TITLE_RE.search(title) else 0.0
    q_density = min(1.0, questions / kw / 30.0)

    # normalize densities: 6 refs/1k words or 25 argument words/1k words = max
    s_scripture = min(1.0, scripture / kw / 6.0)
    s_argument = min(1.0, argument / kw / 25.0)
    s_debate = 0.6 * debate + 0.4 * q_density
    s_length = length_score(duration_secs(head))
    junk_penalty = min(0.5, music / kw / 10.0) + (0.5 if words < 300 else 0.0)

    score = max(0.0, (0.35 * s_scripture + 0.30 * s_argument
                      + 0.20 * s_debate + 0.15 * s_length - junk_penalty)) * 100

    return {"file": path.stem, "title": title, "code": code,
            "words": words, "scripture": scripture, "argument": argument,
            "score": score, "secs": duration_secs(head)}


def fmt_len(secs):
    if secs is None:
        return "—"
    h, rem = divmod(secs, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def render_table(rows, title):
    out = [f"# {title}", "",
           "| Score | Video | Words | Scripture refs | Arg words | Length |",
           "|------:|-------|------:|---------------:|----------:|-------:|"]
    for r in rows:
        out.append(f"| {r['score']:.0f} | [[{r['file']}|{r['title']}]] "
                   f"| {r['words']:,} | {r['scripture']} | {r['argument']} "
                   f"| {fmt_len(r['secs'])} |")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Score transcripts for API-worthiness.")
    ap.add_argument("-i", "--input", required=True, help="markdown_v2 root")
    ap.add_argument("--top", type=int, default=100, help="Rows in the master PICKS.md (default 100)")
    args = ap.parse_args()

    root = Path(args.input)
    all_rows = []
    for ch_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        rows = []
        for f in ch_dir.glob("*.md"):
            if f.name.startswith(("00 - ", "_")):
                continue
            r = score_file(f)
            if r:
                rows.append(r)
        rows.sort(key=lambda r: -r["score"])
        for r in rows:
            r["channel"] = ch_dir.name
        all_rows.extend(rows)
        if rows:
            (ch_dir / "_SCORES.md").write_text(
                render_table(rows, f"{ch_dir.name} — Argument Scores"), encoding="utf-8")
        print(f"{ch_dir.name}: {len(rows)} scored, top {rows[0]['score']:.0f}" if rows
              else f"{ch_dir.name}: nothing to score")

    all_rows.sort(key=lambda r: -r["score"])
    master = render_table(all_rows[:args.top], f"PICKS — Top {args.top} Transcripts Across All Channels")
    lines = master.split("\n")
    lines.insert(2, f"Scored {len(all_rows):,} transcripts across "
                    f"{len(list(root.iterdir()))} channels. Per-channel detail: `_SCORES.md` in each folder.")
    lines.insert(3, "")
    (root / "PICKS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nPICKS.md written: top {args.top} of {len(all_rows):,}")


if __name__ == "__main__":
    main()
