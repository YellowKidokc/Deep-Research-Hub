#!/usr/bin/env python3
"""Build an additive Obsidian channel index from existing chapter analysis.

This script does not call an API and does not alter chapter notes. It reads the
analysis already appended to each note and writes two new files beside them:

* ``<Channel> - 000 Enriched Index.md``
* ``_entities_people_places_things.json``

The curated YouTube CKG fields are preferred over machine-extracted scorecard
entities. Missing analysis is marked as pending rather than guessed.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


CHAPTER_RE = re.compile(r"(?i)\bchapter\s+(\d+)\b")
FIELD_RE = re.compile(r"(?m)^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, re.S)
    return (match.group(1), text[match.end():]) if match else ("", text)


def front_value(front: str, key: str) -> str:
    for name, value in FIELD_RE.findall(front):
        if name == key:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                try:
                    return str(json.loads(value))
                except json.JSONDecodeError:
                    pass
            return value
    return ""


def yaml_list(front: str, key: str) -> list[str]:
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(.*)$", front)
    value = match.group(1).strip() if match else ""
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return [str(item) for item in parsed] if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def section(body: str, heading: str) -> str:
    match = re.search(rf"(?ms)^###\s+{re.escape(heading)}\s*\n(.*?)(?=^###\s+|\Z)", body)
    return match.group(1).strip() if match else ""


def clean_quote_prefix(text: str) -> str:
    return "\n".join(re.sub(r"^>\s?", "", line) for line in text.splitlines()).strip()


def extract_finding(body: str) -> str:
    match = re.search(r"(?m)^>\s*\*\*Finding:\*\*\s*(.+)$", body)
    return match.group(1).strip() if match else ""


def extract_overview(body: str) -> str:
    block = section(body, "Argument overview")
    if not block:
        return ""
    quoted_prose = []
    for line in block.splitlines():
        match = re.match(r"^>\s+(.+)$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if value and not value.startswith(("[!", "**", "- ")):
            quoted_prose.append(re.sub(r"\s+", " ", value))
    if quoted_prose:
        return max(quoted_prose, key=len)
    paragraphs = re.split(r"\n\s*\n", block)
    prose = []
    for paragraph in paragraphs:
        cleaned = clean_quote_prefix(paragraph)
        if not cleaned or cleaned.startswith("[!abstract]") or cleaned.startswith("**") or cleaned.startswith("-"):
            continue
        prose.append(re.sub(r"\s+", " ", cleaned))
    return prose[0] if prose else ""


def extract_ppt(body: str) -> dict[str, str]:
    block = section(body, "People, places, things")
    result = {}
    for label in ("People", "Places", "Things", "Scripture"):
        match = re.search(rf"(?ms)^\*\*{label}:\*\*\s*(.*?)(?=\n\s*\n\*\*|\Z)", block)
        result[label.lower()] = re.sub(r"\s+", " ", match.group(1)).strip() if match else ""
    return result


def plain_entity_names(value: str) -> list[str]:
    names = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", value)
    if names:
        return names
    return [part.strip() for part in value.split("·") if part.strip() and part.strip().lower() != "none"]


def chapter_number(path: Path, front: str) -> int:
    value = front_value(front, "chapter")
    if value.isdigit():
        return int(value)
    match = CHAPTER_RE.search(path.stem)
    return int(match.group(1)) if match else 999999


def load_notes(folder: Path) -> list[dict]:
    notes = []
    for path in folder.glob("*.md"):
        if "000 Index" in path.name or "000 Scorecard" in path.name:
            continue
        raw = path.read_text(encoding="utf-8-sig")
        front, body = split_frontmatter(raw)
        chapter = chapter_number(path, front)
        if chapter == 999999:
            continue
        ppt = extract_ppt(body)
        notes.append({
            "path": path,
            "chapter": chapter,
            "title": front_value(front, "title") or path.stem,
            "channel": front_value(front, "channel"),
            "url": front_value(front, "url"),
            "score": (re.search(r"(?m)^  score:\s*(.+)$", front) or [None, ""])[1].strip(),
            "grade": (re.search(r"(?m)^  grade:\s*(.+)$", front) or [None, ""])[1].strip().strip('"'),
            "finding": extract_finding(body),
            "summary": extract_overview(body),
            "people": ppt.get("people", ""),
            "places": ppt.get("places", ""),
            "things": ppt.get("things", ""),
            "scripture": ppt.get("scripture", ""),
            "scripture_fallback": yaml_list(front, "top_scripture"),
        })
    return sorted(notes, key=lambda item: (item["chapter"], item["path"].name.casefold()))


def build_index(folder: Path, notes: list[dict]) -> Path:
    channel = next((n["channel"] for n in notes if n["channel"]), folder.name)
    analyzed = sum(bool(n["finding"] or n["summary"]) for n in notes)
    lines = [
        f"# {channel} — Enriched Index", "",
        f"**Videos:** {len(notes)} · **API analyses available:** {analyzed} · **Pending:** {len(notes) - analyzed}",
        "",
        "> This index aggregates existing analysis; it makes no API calls. People, places, things, summaries, and Scripture are AI-extracted candidates until human review.",
        "",
    ]
    for note in notes:
        lines += [f"## {note['chapter']:03d}. [[{note['path'].stem}|{note['title']}]]", ""]
        metadata = []
        if note["score"]:
            metadata.append(f"score {note['score']}")
        if note["grade"]:
            metadata.append(f"grade {note['grade']}")
        if note["url"]:
            metadata.append(f"[YouTube]({note['url']})")
        if metadata:
            lines += [" · ".join(metadata), ""]
        if note["finding"] or note["summary"]:
            lines += [f"**One-sentence finding:** {note['finding'] or '_Not supplied by analysis._'}", "",
                      f"**Summary:** {note['summary'] or '_Not supplied by analysis._'}", ""]
            for label in ("people", "places", "things"):
                lines += [f"**{label.title()}:** {note[label] or '_None identified._'}", ""]
            scripture = note["scripture"] or " · ".join(note["scripture_fallback"])
            lines += [f"**Scripture:** {scripture or '_None identified._'}", ""]
        else:
            fallback = " · ".join(note["scripture_fallback"])
            lines += ["_API analysis pending; no summary or curated entities available._", ""]
            if fallback:
                lines += [f"**Machine-detected Scripture candidates:** {fallback}", ""]

    target = folder / f"{channel} - 000 Enriched Index.md"
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return target


def build_entities(folder: Path, notes: list[dict]) -> Path:
    totals = {key: Counter() for key in ("people", "places", "things")}
    videos = []
    for note in notes:
        record = {"chapter": note["chapter"], "title": note["title"], "file": note["path"].name,
                  "analysis_status": "available" if note["finding"] or note["summary"] else "pending"}
        for key in totals:
            names = plain_entity_names(note[key])
            record[key] = names
            totals[key].update(names)
        record["scripture"] = note["scripture"] or note["scripture_fallback"]
        videos.append(record)
    payload = {
        "note": "AI-extracted candidates; not human-reviewed. Curated CKG fields only; missing analyses remain pending.",
        "coverage": {"videos": len(notes), "analyzed": sum(v["analysis_status"] == "available" for v in videos)},
        "aggregate": {key: dict(counter.most_common()) for key, counter in totals.items()},
        "videos": videos,
    }
    target = folder / "_entities_people_places_things.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="One CHANNEL or PLAYLIST folder containing chapter Markdown notes")
    args = parser.parse_args()
    folder = args.folder.resolve()
    notes = load_notes(folder)
    if not notes:
        parser.error(f"No chapter notes found in {folder}")
    index = build_index(folder, notes)
    entities = build_entities(folder, notes)
    analyzed = sum(bool(n["finding"] or n["summary"]) for n in notes)
    print(f"notes={len(notes)} analyzed={analyzed} pending={len(notes) - analyzed}")
    print(index)
    print(entities)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
