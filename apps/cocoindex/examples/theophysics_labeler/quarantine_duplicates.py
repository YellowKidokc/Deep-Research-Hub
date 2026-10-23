"""Move the duplicate copies listed in state/reports/duplicates.csv into a quarantine folder.

Nothing is deleted. For each group, the row marked `keep` stays where it is; every row marked
`duplicate` is re-hashed together with its kept copy and moved only if both still exist and are
still byte-identical. Files go to <source>__DUPLICATES_QUARANTINE\\<same relative path>, which is
OUTSIDE the source folder so the labeler does not pick them up again.

    python quarantine_duplicates.py              # move them
    python quarantine_duplicates.py --dry-run    # show what would move
    python quarantine_duplicates.py --undo       # put everything back (uses the manifest)

The manifest (manifest.csv in the quarantine folder) records original path, quarantine path,
sha256 and the copy that was kept.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = Path(os.environ.get("LABELER_STATE", HERE / "state"))


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_of(path: str, sources: list[str]) -> str | None:
    low = path.lower()
    for s in sorted(sources, key=len, reverse=True):
        if low.startswith(s.lower().rstrip("\\/") + "\\") or low.startswith(s.lower().rstrip("\\/") + "/"):
            return s
    return None


def quarantine_root(source: str) -> str:
    return source.rstrip("\\/") + "__DUPLICATES_QUARANTINE"


def move(args) -> int:
    sources = json.loads((STATE / "sources.json").read_text(encoding="utf-8"))
    groups: dict[str, list[dict]] = defaultdict(list)
    with open(STATE / "reports" / "duplicates.csv", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            groups[r["group"]].append(r)
    moved = skipped = 0
    bytes_moved = 0
    manifests: dict[str, list[dict]] = defaultdict(list)
    problems: list[str] = []
    for g, rows in groups.items():
        keep = next((r for r in rows if r["suggest"] == "keep"), None)
        if not keep or not os.path.isfile(keep["path"]):
            problems.append(f"group {g}: kept copy missing, group left alone")
            skipped += sum(1 for r in rows if r["suggest"] == "duplicate")
            continue
        keep_hash = sha256(keep["path"])
        for r in rows:
            if r["suggest"] != "duplicate":
                continue
            src = r["path"]
            root = source_of(src, sources)
            if not root or not os.path.isfile(src):
                skipped += 1
                continue
            try:
                if sha256(src) != keep_hash:
                    problems.append(f"changed since scan, left alone: {src}")
                    skipped += 1
                    continue
            except OSError as exc:
                problems.append(f"could not read {src}: {exc}")
                skipped += 1
                continue
            rel = os.path.relpath(src, root)
            dest = os.path.join(quarantine_root(root), rel)
            if args.dry_run:
                print(f"would move  {src}")
                moved += 1
                continue
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                size = os.path.getsize(src)
                shutil.move(src, dest)
            except OSError as exc:
                problems.append(f"could not move {src}: {exc}")
                skipped += 1
                continue
            moved += 1
            bytes_moved += size
            manifests[root].append({"original": src, "quarantine": dest, "sha256": keep_hash,
                                    "kept_copy": keep["path"], "moved_at": datetime.now().isoformat(timespec="seconds")})
            if moved % 100 == 0:
                print(f"  ... {moved} moved", flush=True)
    for root, rows in manifests.items():
        qdir = quarantine_root(root)
        mpath = os.path.join(qdir, "manifest.csv")
        new = not os.path.exists(mpath)
        with open(mpath, "a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["original", "quarantine", "sha256", "kept_copy", "moved_at"])
            if new:
                w.writeheader()
            w.writerows(rows)
        Path(qdir, "README.txt").write_text(
            "Duplicate copies moved here by the Theophysics Labeler.\n"
            "Each one was byte-identical (sha256) to a copy that was KEPT in the original folder - see manifest.csv.\n"
            "Put everything back:  python quarantine_duplicates.py --undo\n"
            "When you are satisfied, you can delete this whole folder yourself.\n", encoding="utf-8")
    print(json.dumps({"moved": moved, "space_moved_mb": round(bytes_moved / 1048576, 1), "skipped": skipped,
                      "problems": len(problems), "dry_run": args.dry_run,
                      "quarantine": [quarantine_root(s) for s in manifests] or None}, indent=2))
    for p in problems[:20]:
        print("  !", p)
    return 0


def undo(_args) -> int:
    sources = json.loads((STATE / "sources.json").read_text(encoding="utf-8"))
    back = 0
    for s in sources:
        mpath = os.path.join(quarantine_root(s), "manifest.csv")
        if not os.path.exists(mpath):
            continue
        with open(mpath, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if os.path.isfile(r["quarantine"]) and not os.path.exists(r["original"]):
                    os.makedirs(os.path.dirname(r["original"]), exist_ok=True)
                    shutil.move(r["quarantine"], r["original"])
                    back += 1
    print(f"restored {back} files")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Move duplicate copies into a quarantine folder (never deletes).")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--undo", action="store_true")
    a = ap.parse_args()
    raise SystemExit(undo(a) if a.undo else move(a))
