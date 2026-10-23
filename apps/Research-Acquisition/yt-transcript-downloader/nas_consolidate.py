#!/usr/bin/env python3
"""
nas_consolidate.py

Pull the content out of the four scattered pipeline archive trees on the NAS,
deduplicate by content hash, and copy what is unique into
Youtube API CKG\\_ARCHIVE\\<source-tree>\\<original relative path>.

Never deletes or moves anything in the source trees.

Skips:
  - Lean/build artifacts: .hash .olean .ilean .c .trace .ltar .ir .private
    .server .pyc .o .d .olean.hash
  - dependency/build dirs: .git node_modules __pycache__ .lake .elan venv
    .venv target dist
  - shortcuts and executables: .lnk .exe .dll .pyd .so
  - zero-byte files (logged)

Dedup rule: sha256 of file content. First occurrence (shortest source path
wins) is copied; later identical files are logged in _DEDUP_REPORT.csv.
"""

import csv
import hashlib
import pathlib
import sys
import time

sys.dont_write_bytecode = True

BASE = pathlib.Path("//192.168.2.50/h_hp/Desktop/Folders")
TREES = ["_____pipeline-workflows-main", "__API", "___Pipeline_Done_New",
         "____NEW_SUPER_FOLDER"]  # smallest/most-content-dense first
DST = pathlib.Path("//192.168.2.50/h_hp/Desktop/Youtube API CKG/_ARCHIVE")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".lake", ".elan",
             "venv", ".venv", "target", "dist", ".idea", ".vscode"}
SKIP_EXTS = {".hash", ".olean", ".ilean", ".c", ".trace", ".ltar", ".ir",
             ".private", ".server", ".pyc", ".o", ".d", ".lnk", ".exe",
             ".dll", ".pyd", ".so", ".tmp"}


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    report_path = DST / "_DEDUP_REPORT.csv"
    copied = dupes = skipped_junk = errors = zero_byte = 0
    t0 = time.time()

    with open(report_path, "w", newline="", encoding="utf-8") as csvf:
        w = csv.writer(csvvf := csvf)
        w.writerow(["action", "src", "kept_copy_or_reason"])
        by_hash: dict[str, str] = {}

        for tree in TREES:
            root = BASE / tree
            stack = [root]
            while stack:
                d = stack.pop()
                try:
                    children = list(d.iterdir())
                except OSError as e:
                    w.writerow(["error", str(d), repr(e)])
                    errors += 1
                    continue
                for e in children:
                    try:
                        if e.is_dir():
                            if e.name.lower() not in SKIP_DIRS:
                                stack.append(e)
                            continue
                        if not e.is_file():
                            continue
                    except OSError:
                        continue
                    ext = e.suffix.lower()
                    if ext in SKIP_EXTS:
                        skipped_junk += 1
                        continue
                    try:
                        size = e.stat().st_size
                    except OSError:
                        errors += 1
                        continue
                    if size == 0:
                        zero_byte += 1
                        continue
                    try:
                        digest = sha256(e)
                    except OSError as ex:
                        w.writerow(["error", str(e), repr(ex)])
                        errors += 1
                        continue
                    if digest in by_hash:
                        dupes += 1
                        w.writerow(["dupe", str(e), by_hash[digest]])
                        continue
                    rel = e.relative_to(root)
                    dst = DST / tree / rel
                    try:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        with open(e, "rb") as fin, open(dst, "wb") as fout:
                            for chunk in iter(lambda: fin.read(1 << 20), b""):
                                fout.write(chunk)
                    except OSError as ex:
                        w.writerow(["error", str(e), repr(ex)])
                        errors += 1
                        continue
                    by_hash[digest] = str(dst)
                    copied += 1
                    w.writerow(["copied", str(e), str(dst)])
                    if copied % 500 == 0:
                        el = time.time() - t0
                        print(f"{copied} copied, {dupes} dupes, {errors} err, "
                              f"{el/60:.0f} min, now: {tree}/{rel.parent}",
                              flush=True)

        w.writerow(["summary", f"copied={copied} dupes={dupes} "
                    f"junk={skipped_junk} zero_byte={zero_byte} errors={errors}", ""])
    print(f"DONE copied={copied} dupes={dupes} junk={skipped_junk} "
          f"zero={zero_byte} errors={errors} in {(time.time()-t0)/60:.0f} min")


if __name__ == "__main__":
    main()
