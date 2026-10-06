"""Export sync_server clips to a TSV index for the AI-HUB Clipboard tab."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

URL = "http://127.0.0.1:3456/api/clips?limit=200"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "Data" / "clips_index.tsv"


def clean(s: str, limit: int) -> str:
    text = (s or "").replace("\t", " ").replace("\r", " ").replace("\n", " ")
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def main() -> int:
    try:
        with urllib.request.urlopen(URL, timeout=4) as resp:
            clips = json.load(resp)
    except Exception as exc:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("", encoding="utf-8")
        print(f"export failed: {exc}", file=sys.stderr)
        return 1

    lines: list[str] = []
    for c in clips:
        if c.get("deleted"):
            continue
        cid = str(c.get("id") or "")
        slot = "" if c.get("slot") in (None, "") else str(c.get("slot"))
        when = str(c.get("updated_at") or c.get("created_at") or c.get("ts") or "")[:19]
        title = clean(str(c.get("title") or ""), 90)
        content = clean(str(c.get("content") or ""), 240)
        lines.append("\t".join([cid, slot, when, title, content]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {len(lines)} clips -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
