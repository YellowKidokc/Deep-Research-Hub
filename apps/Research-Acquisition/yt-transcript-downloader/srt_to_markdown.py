#!/usr/bin/env python3
"""
srt_to_markdown.py

Convert YouTube-style SRT subtitle files into readable, Obsidian-friendly
markdown transcripts. Supports single-file and batch-folder modes.

Usage:
    python srt_to_markdown.py -i "video.srt" -o "video.md"
    python srt_to_markdown.py -i "subtitles_folder/" -o "markdown_folder/" --batch
    python srt_to_markdown.py -i "subtitles_folder/" --batch --in-place

The script groups consecutive subtitle lines into paragraphs based on:
  - time gap between cues (default > 1.5 s starts a new paragraph)
  - sentence boundaries
  - maximum paragraph length
"""

import argparse
import re
import sys
from datetime import timedelta
from pathlib import Path


def parse_timecode(tc: str) -> float:
    """Convert 'HH:MM:SS,mmm' or 'HH:MM:SS.mmm' to seconds."""
    tc = tc.strip().replace(",", ".")
    parts = tc.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    elif len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    else:
        return float(parts[0])


def format_timestamp(seconds: float, force_hours: bool = False) -> str:
    """Return [MM:SS] or [HH:MM:SS] depending on duration."""
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0 or force_hours:
        return f"[{hours:01d}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes:02d}:{secs:02d}]"


def clean_srt_text(text: str) -> str:
    """Clean up SRT text: remove tags, normalize whitespace, unwrap lines."""
    # Remove common SRT/HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove speaker identifiers like "- " at start of lines
    text = re.sub(r"^\s*-\s*", "", text, flags=re.MULTILINE)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_srt(path: Path) -> list[dict]:
    """Parse an SRT file into a list of cues: {start, end, text}."""
    content = path.read_text(encoding="utf-8-sig")
    # Normalize line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    # Split on double newlines (blank lines between entries)
    blocks = re.split(r"\n\s*\n", content.strip())
    cues = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        # First line is the cue number; second is the timecode
        timecode_line = lines[1].strip()
        match = re.match(r"(.+?)\s*-->\s*(.+)", timecode_line)
        if not match:
            continue
        start = parse_timecode(match.group(1))
        end = parse_timecode(match.group(2))
        text_lines = lines[2:]
        text = " ".join(line.strip() for line in text_lines if line.strip())
        text = clean_srt_text(text)
        if text:
            cues.append({"start": start, "end": end, "text": text})
    return cues


def find_break_point(text: str, max_chars: int) -> int:
    """
    Find a good place to split a long run-on text into two parts.
    Prefer sentence endings (with a small lookahead), then clause breaks,
    then simple word boundaries.
    """
    if len(text) <= max_chars:
        return -1

    # Look for sentence boundary before max_chars, with a small lookahead
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

    # Look for clause boundary
    for i in range(min(len(text), max_chars) - 1, -1, -1):
        if text[i] in ",;:" and text[i + 1] == " ":
            return i + 1

    # Fall back to last word boundary
    for i in range(min(len(text), max_chars) - 1, -1, -1):
        if text[i] == " ":
            return i

    return max_chars


def group_cues_into_paragraphs(
    cues: list[dict],
    gap_threshold: float = 1.5,
    max_chars: int = 600,
    max_duration: float = 45.0,
) -> list[tuple[float, str]]:
    """Group SRT cues into readable paragraphs."""
    if not cues:
        return []

    paragraphs = []
    current_start = cues[0]["start"]
    current_text = cues[0]["text"]
    last_end = cues[0]["end"]

    def finalize(start: float, text: str):
        paragraphs.append((start, text.strip()))

    for cue in cues[1:]:
        gap = cue["start"] - last_end
        candidate = current_text + " " + cue["text"]
        duration = cue["start"] - current_start

        # Hard conditions that always start a new paragraph
        hard_break = gap > gap_threshold

        # Soft conditions: paragraph is getting long; break at a boundary
        sentence_ended = current_text.rstrip().endswith((".", "!", "?"))
        clause_break = current_text.rstrip().endswith((",", ";", ":"))
        duration_expired = duration >= max_duration
        over_long = len(candidate) > max_chars

        if hard_break:
            finalize(current_start, current_text)
            current_start = cue["start"]
            current_text = cue["text"]
        elif over_long:
            # Force a split inside the candidate text at the best boundary
            split_at = find_break_point(candidate, max_chars)
            if split_at > 0 and split_at < len(candidate):
                finalize(current_start, candidate[:split_at])
                remainder = candidate[split_at:].strip()
                current_start = cue["start"]  # timestamp the new paragraph at the latest cue
                current_text = remainder
            else:
                finalize(current_start, current_text)
                current_start = cue["start"]
                current_text = cue["text"]
        elif duration_expired and (sentence_ended or clause_break):
            finalize(current_start, current_text)
            current_start = cue["start"]
            current_text = cue["text"]
        else:
            current_text = candidate

        last_end = cue["end"]

    finalize(current_start, current_text)
    return paragraphs


def srt_to_markdown(
    input_path: Path,
    output_path: Path,
    gap_threshold: float = 1.5,
    max_chars: int = 600,
    max_duration: float = 45.0,
) -> None:
    cues = parse_srt(input_path)
    if not cues:
        print(f"Warning: no cues found in {input_path}", file=sys.stderr)
        return

    title = input_path.stem
    duration = cues[-1]["end"]
    force_hours = duration >= 3600

    paragraphs = group_cues_into_paragraphs(cues, gap_threshold, max_chars, max_duration)

    lines = [f"# {title}", ""]
    for start, text in paragraphs:
        ts = format_timestamp(start, force_hours=force_hours)
        lines.append(f"{ts} {text}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(paragraphs)} paragraphs to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert SRT subtitle files to readable Markdown transcripts."
    )
    parser.add_argument(
        "-i", "--input", required=True,
        help="Input SRT file or folder containing SRT files."
    )
    parser.add_argument(
        "-o", "--output",
        help="Output Markdown file or folder. Defaults to same name/folder as input."
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Process all .srt files in the input folder."
    )
    parser.add_argument(
        "--in-place", action="store_true",
        help="When batch processing, write .md files next to the source .srt files."
    )
    parser.add_argument(
        "--gap", type=float, default=1.5,
        help="Time gap (seconds) that triggers a new paragraph (default: 1.5)."
    )
    parser.add_argument(
        "--max-chars", type=int, default=600,
        help="Maximum paragraph length in characters (default: 600)."
    )
    parser.add_argument(
        "--max-duration", type=float, default=45.0,
        help="Maximum paragraph duration in seconds (default: 45)."
    )

    args = parser.parse_args()
    input_path = Path(args.input)

    if args.batch or input_path.is_dir():
        if not input_path.is_dir():
            parser.error("Batch mode requires an input folder.")
        srt_files = sorted(input_path.glob("**/*.srt"))
        if not srt_files:
            print(f"No .srt files found in {input_path}", file=sys.stderr)
            sys.exit(1)

        if args.output:
            output_dir = Path(args.output)
        elif args.in_place:
            output_dir = None
        else:
            output_dir = input_path.parent / (input_path.name + "_markdown")

        for srt_file in srt_files:
            if args.in_place:
                out = srt_file.with_suffix(".md")
            else:
                rel = srt_file.relative_to(input_path)
                out = output_dir / rel.with_suffix(".md")
            srt_to_markdown(srt_file, out, args.gap, args.max_chars, args.max_duration)
    else:
        if not input_path.is_file():
            parser.error(f"Input file not found: {input_path}")
        output_path = Path(args.output) if args.output else input_path.with_suffix(".md")
        srt_to_markdown(input_path, output_path, args.gap, args.max_chars, args.max_duration)


if __name__ == "__main__":
    main()
