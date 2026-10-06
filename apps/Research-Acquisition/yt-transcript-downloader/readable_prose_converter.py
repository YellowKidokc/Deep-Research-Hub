#!/usr/bin/env python3
"""Convert the transcript library into long-form, Obsidian-readable prose.

This converter deliberately does *not* put a timestamp on every paragraph.
It emits one timestamped section heading per time interval (five minutes by
default), then writes ordinary multi-sentence paragraphs beneath it.

Speaker information is conservative:
  * an explicit ``Name:`` prefix is retained as a speaker label;
  * YouTube's ``>>`` marker starts a new turn with an em dash;
  * no speaker names are invented.

Sources are never edited, moved, or deleted. Output is written to a separate
directory and an incremental state file makes reruns safe.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parent
CLEAN_LIB = REPO / "Python Clean Library"
sys.path.insert(0, str(CLEAN_LIB))

import clean_library as base  # noqa: E402


STATE_NAME = ".readable_prose_state.json"
MODE = "readable-prose-v1"
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
EXPLICIT_SPEAKER = re.compile(
    r"^([A-Z][A-Za-z0-9 .’'_-]{1,38}):\s+(?=\S)"
)


def section_start(seconds: float | None, interval_seconds: int) -> int:
    if seconds is None:
        return 0
    return int(seconds // interval_seconds) * interval_seconds


def split_paragraphs(text: str, target_chars: int, max_chars: int) -> list[str]:
    """Split punctuated prose into substantial, sentence-aligned paragraphs."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    sentences = [s.strip() for s in SENTENCE_END.split(text) if s.strip()]
    if len(sentences) == 1:
        # Unpunctuated fallback: long readable blocks at a word boundary.
        words = text.split()
        out, cur = [], []
        for word in words:
            if cur and len(" ".join(cur + [word])) > max_chars:
                out.append(" ".join(cur))
                cur = []
            cur.append(word)
        if cur:
            out.append(" ".join(cur))
        return out

    out, cur = [], []
    for sentence in sentences:
        candidate = " ".join(cur + [sentence])
        if cur and len(candidate) > max_chars:
            out.append(" ".join(cur))
            cur = [sentence]
            continue
        cur.append(sentence)
        # Aim for sustained prose, normally about 5-10 sentences.
        if len(" ".join(cur)) >= target_chars and len(cur) >= 4:
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def normalize_model_tokens(text: str) -> str:
    """Resolve punctuation-model <unk> tokens without inventing words."""
    # Common model emissions: co<unk>founder, long,<unk>term, 90<unk>, 5<unk>20.
    text = re.sub(r"(?i)([A-Za-z]),?\s*<unk>\s*([A-Za-z])", r"\1-\2", text)
    text = re.sub(r"(?i)(\d)\s*<unk>\s*(\d)", r"\1:\2", text)
    text = re.sub(r"(?i)(\d)\s*<unk>(?=\s|$)", r"\1%", text)
    text = re.sub(r"(?i)\s*<unk>\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def collect_blocks(segments: list[dict], interval_seconds: int) -> list[dict]:
    """Group caption fragments by time section and reliable speaker boundary."""
    blocks: list[dict] = []
    current: dict | None = None

    for seg in segments:
        raw = re.sub(r"\s+", " ", seg.get("text", "")).strip()
        if not raw:
            continue

        changed = raw.startswith(">>")
        if changed:
            raw = re.sub(r"^>>\s*", "", raw).strip()

        speaker = ""
        match = EXPLICIT_SPEAKER.match(raw)
        if match:
            speaker = match.group(1).strip()
            raw = raw[match.end():].strip()

        cleaned = base.rule_clean(raw)
        if not cleaned:
            continue

        bucket = section_start(seg.get("start"), interval_seconds)
        needs_new = (
            current is None
            or current["bucket"] != bucket
            or changed
            or (speaker and speaker != current.get("speaker"))
        )
        if needs_new:
            current = {
                "bucket": bucket,
                "start": seg.get("start"),
                "speaker": speaker,
                "speaker_change": changed and not speaker,
                "parts": [],
            }
            blocks.append(current)
        current["parts"].append(cleaned)

    return blocks


def prepare_blocks(
    segments: list[dict],
    interval_seconds: int,
    use_model: bool,
    target_chars: int,
    max_chars: int,
) -> tuple[list[dict], int]:
    blocks = collect_blocks(segments, interval_seconds)
    texts = [base.capitalise(" ".join(block.pop("parts"))) for block in blocks]
    model_words = 0
    model_indices = [i for i, text in enumerate(texts) if use_model and base.is_unpunctuated(text)]
    if model_indices:
        restored = base.punctuate([texts[i] for i in model_indices])
        for i, text in zip(model_indices, restored):
            texts[i] = normalize_model_tokens(text)
            model_words += base.count_words(texts[i])
    for block, text in zip(blocks, texts):
        block["paragraphs"] = split_paragraphs(text, target_chars, max_chars)
    return blocks, model_words


def timestamp_heading(seconds: int, url: str) -> str:
    label = base.fmt_stamp(seconds)
    if url:
        joiner = "&" if "?" in url else "?"
        return f"### [{label}]({url}{joiner}t={seconds}s)"
    return f"### {label}"


def render_note(video: dict, channel: str, rel_src: str, blocks: list[dict], interval_minutes: int) -> str:
    url = video.get("url") or (
        f"https://www.youtube.com/watch?v={video['video_id']}"
        if video.get("video_id") else ""
    )
    quote = lambda value: json.dumps(value or "", ensure_ascii=False)
    word_count = base.count_words(
        " ".join(p for block in blocks for p in block["paragraphs"])
    )
    lines = [
        "---",
        f"title: {quote(video.get('title'))}",
        f"channel: {quote(channel)}",
        f"video_id: {quote(video.get('video_id'))}",
        f"url: {quote(url)}",
        f"transcript_language: {quote(video.get('language'))}",
        f"source_file: {quote(rel_src)}",
        f"converted: {MODE}",
        f"converted_on: {datetime.now():%Y-%m-%d}",
        f"timestamp_interval_minutes: {interval_minutes}",
        f"words: {word_count}",
        "tags: [youtube, transcript, readable-prose]",
        "---",
        "",
        f"# {video.get('title') or 'Untitled transcript'}",
        "",
        f"**Channel:** [[{channel}]]" + (f" · [Watch on YouTube]({url})" if url else ""),
        "",
        "## Transcript",
        "",
    ]

    last_bucket = None
    for block in blocks:
        if block["bucket"] != last_bucket:
            lines.extend([timestamp_heading(block["bucket"], url), ""])
            last_bucket = block["bucket"]

        if block.get("speaker"):
            lines.extend([f"**{block['speaker']}:**", ""])
        for paragraph_index, paragraph in enumerate(block["paragraphs"]):
            if block.get("speaker_change") and paragraph_index == 0:
                paragraph = "— " + paragraph
            lines.extend([paragraph, ""])

    return "\n".join(lines).rstrip() + "\n"


def load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", required=True, help="subtitles library root")
    parser.add_argument("--out", help="separate output root")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="write into subtitles/<Channel>/Clean MD while preserving raw transcripts",
    )
    parser.add_argument("--channel", help="convert only one channel folder")
    parser.add_argument("--source", help="convert only this exact source-relative path")
    parser.add_argument("--timestamp-minutes", type=int, default=5)
    parser.add_argument("--target-chars", type=int, default=900)
    parser.add_argument("--max-chars", type=int, default=1400)
    parser.add_argument("--punctuate", action="store_true", help="use the local ONNX punctuation model")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.timestamp_minutes < 1:
        parser.error("--timestamp-minutes must be at least 1")
    if args.target_chars < 200 or args.max_chars < args.target_chars:
        parser.error("paragraph sizes must satisfy 200 <= target <= max")

    src_root = Path(args.src).resolve()
    if args.in_place and args.out:
        parser.error("choose either --in-place or --out, not both")
    if not args.in_place and not args.out:
        parser.error("--out is required unless --in-place is used")
    out_root = src_root if args.in_place else Path(args.out).resolve()
    if not args.in_place and (src_root == out_root or src_root in out_root.parents):
        parser.error("output must be separate from the source library")

    if args.punctuate and not args.dry_run:
        try:
            import punctuators  # noqa: F401
        except ImportError:
            parser.error("--punctuate requires the local punctuators package")

    state_path = out_root / STATE_NAME
    state = load_state(state_path)
    sources = list(base.list_sources(str(src_root), args.channel))
    if args.source:
        wanted = args.source.replace("\\", "/").casefold()
        sources = [item for item in sources if item[2].replace("\\", "/").casefold() == wanted]
        if not sources:
            parser.error(f"source not found in library: {args.source}")
    todo = []
    placeholders = 0
    for channel, path, rel in sources:
        if base.is_placeholder(path):
            placeholders += 1
            continue
        stat = os.stat(path)
        previous = state.get(rel)
        if (
            not args.force
            and previous
            and previous.get("mode") == MODE
            and previous.get("size") == stat.st_size
            and abs(previous.get("mtime", 0) - stat.st_mtime) < 1
            and all((out_root / item).exists() for item in previous.get("outputs", []))
        ):
            continue
        todo.append((channel, path, rel, stat))

    # Individual transcripts establish video IDs before combined dumps are read.
    todo.sort(key=lambda item: os.path.basename(item[1]).startswith(("channel_", "playlist_")))
    if args.limit:
        todo = todo[:args.limit]
    redo = {rel for _, _, rel, _ in todo}
    seen_ids = {
        video_id
        for rel, record in state.items() if rel not in redo
        for video_id in record.get("video_ids", [])
    }
    claimed_outputs = {
        output.replace("\\", "/").casefold()
        for rel, record in state.items() if rel not in redo
        for output in record.get("outputs", [])
    }

    print(
        f"{len(sources)} source files: {placeholders} placeholders, "
        f"{len(todo)} to convert as readable prose."
    )
    interval_seconds = args.timestamp_minutes * 60
    stats = {"notes": 0, "duplicates": 0, "empty": 0, "model_words": 0}

    for index, (channel, path, rel, stat) in enumerate(todo, 1):
        videos = base.read_videos(path)
        combined = len(videos) > 1 or os.path.basename(path).startswith(("channel_", "playlist_"))
        outputs, video_ids = [], []
        for video in videos:
            video_id = video.get("video_id", "")
            if combined and video_id and video_id in seen_ids:
                stats["duplicates"] += 1
                continue
            if not video.get("segments"):
                stats["empty"] += 1
                continue

            blocks, model_words = prepare_blocks(
                video["segments"], interval_seconds, args.punctuate and not args.dry_run,
                args.target_chars, args.max_chars,
            )
            if not any(block["paragraphs"] for block in blocks):
                stats["empty"] += 1
                continue
            stats["model_words"] += model_words

            name = base.safe_name(video.get("title", "")) if combined else base.safe_name(Path(path).stem)
            note_dir = Path(channel) / base.CLEAN_SUBDIR if args.in_place else Path(channel)
            out_rel = note_dir / f"{name}.md"
            suffix = 2
            while out_rel.as_posix().casefold() in claimed_outputs:
                out_rel = Path(channel) / f"{name} ({video_id or suffix}).md"
                suffix += 1
            outputs.append(out_rel.as_posix())
            claimed_outputs.add(out_rel.as_posix().casefold())
            if video_id:
                seen_ids.add(video_id)
                video_ids.append(video_id)

            if not args.dry_run:
                destination = out_root / out_rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                if args.in_place:
                    base.ensure_channel_layout(src_root / channel)
                destination.write_text(
                    render_note(video, channel, rel, blocks, args.timestamp_minutes),
                    encoding="utf-8",
                )
            stats["notes"] += 1

        if not args.dry_run:
            state[rel] = {
                "mode": MODE,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "outputs": outputs,
                "video_ids": video_ids,
            }
            if index % 25 == 0 or index == len(todo):
                save_state(state_path, state)
                print(f"  {index}/{len(todo)} source files")

    if not args.dry_run:
        save_state(state_path, state)
    verb = "would be written" if args.dry_run else "written"
    print(f"\n{stats['notes']} readable-prose notes {verb} to {out_root}")
    print(f"{stats['duplicates']} duplicate combined-dump videos skipped")
    print(f"{stats['empty']} empty transcript sections skipped")
    print(f"{stats['model_words']:,} words processed by the local punctuation model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
