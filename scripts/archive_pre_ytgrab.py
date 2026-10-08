"""Zip every pre-ytgrab .srt / .txt transcript into one archive, with an index.

    python scripts/archive_pre_ytgrab.py                       # apps/Research-Acquisition
    python scripts/archive_pre_ytgrab.py --src "D:\\GitHub\\Research-Acquisition"
    python scripts/archive_pre_ytgrab.py --dry-run

Writes data/youtube/_archive/<YYYY-MM-DD>_pre-ytgrab.zip and
<YYYY-MM-DD>_pre-ytgrab.index.md beside it. Files go in byte for byte
(no reformatting); the zip also holds _INDEX.csv. Every entry is read back
and checked against its SHA-256 before the script reports success.

Originals stay where they are. --remove-originals deletes them, and only
after the zip has been verified.

Standard library only.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import os
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "site-packages", "venv", ".venv", "__pycache__", "_archive"}
HEAD = 4096
# A .txt is a transcript only if its head looks like one: yt_scrape.py's
# header block, or subtitle cue timings.
TXT_HEADER = re.compile(r"^(VIDEO_ID|TITLE): ", re.M)
CUE = re.compile(r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{1,2}:\d{2}:\d{2}")


def kind_of(path):
    ext = path.suffix.lower()
    if ext == ".srt":
        return "srt"
    if ext != ".txt":
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(HEAD)
    except OSError:
        return None
    if TXT_HEADER.search(head):
        return "txt-yt_scrape"
    if CUE.search(head):
        return "txt-subtitles"
    return None


def walk(src):
    found, skipped_txt = [], 0
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("venv")]
        for name in filenames:
            p = pathlib.Path(dirpath) / name
            k = kind_of(p)
            if k:
                found.append((p, k))
            elif p.suffix.lower() == ".txt":
                skipped_txt += 1
    return found, skipped_txt


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", action="append",
                    help="folder to search (repeatable); default apps/Research-Acquisition")
    ap.add_argument("--out", default=str(ROOT / "data" / "youtube" / "_archive"))
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true", help="list what would go in; write nothing")
    ap.add_argument("--remove-originals", action="store_true",
                    help="delete each original after the zip is verified")
    args = ap.parse_args()

    srcs = [pathlib.Path(s).resolve() for s in (args.src or [ROOT / "apps" / "Research-Acquisition"])]
    rows = []
    for src in srcs:
        if not src.is_dir():
            sys.exit(f"not a folder: {src}")
        found, skipped = walk(src)
        print(f"{src}: {len(found)} transcript(s); {skipped} other .txt file(s) left out")
        for p, k in found:
            st = p.stat()
            rows.append({
                "archive_path": f"{src.name}/{p.relative_to(src).as_posix()}",
                "original_path": str(p),
                "kind": k,
                "bytes": st.st_size,
                "modified": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                "sha256": sha256(p),
            })

    if not rows:
        print("Nothing to archive.")
        return
    if args.dry_run:
        for r in rows:
            print(f"  {r['kind']:14} {r['bytes']:>9}  {r['archive_path']}")
        print(f"{len(rows)} file(s) would be archived.")
        return

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    zpath = out / f"{args.date}_pre-ytgrab.zip"
    if zpath.exists():
        sys.exit(f"{zpath} already exists; pass another --date or move it first")

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for r in rows:
            z.write(r["original_path"], r["archive_path"])
        z.writestr("_INDEX.csv", buf.getvalue())

    # Read every entry back and compare hashes before touching anything else.
    with zipfile.ZipFile(zpath) as z:
        bad = z.testzip()
        if bad:
            sys.exit(f"zip check failed on {bad}; originals untouched")
        for r in rows:
            if hashlib.sha256(z.read(r["archive_path"])).hexdigest() != r["sha256"]:
                sys.exit(f"hash mismatch on {r['archive_path']}; originals untouched")

    idx = out / f"{args.date}_pre-ytgrab.index.md"
    lines = [f"# {zpath.name}", "",
             f"Made {dt.datetime.now():%Y-%m-%d %H:%M} by scripts/archive_pre_ytgrab.py. "
             f"{len(rows)} files, {sum(r['bytes'] for r in rows):,} bytes before compression, "
             "byte for byte. Unzip to restore; `_INDEX.csv` inside the zip has the same rows.", "",
             "Searched: " + ", ".join(f"`{s}`" for s in srcs), "",
             "| Archive path | Kind | Bytes | Modified | SHA-256 |", "|---|---|---|---|---|"]
    lines += [f"| `{r['archive_path']}` | {r['kind']} | {r['bytes']} | {r['modified']} | `{r['sha256'][:16]}…` |"
              for r in rows]
    idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {zpath} ({zpath.stat().st_size:,} bytes) and {idx.name}; verified {len(rows)} entries")

    if args.remove_originals:
        for r in rows:
            os.remove(r["original_path"])
        print(f"removed {len(rows)} original(s)")
    else:
        print("originals left in place (--remove-originals to delete them)")


if __name__ == "__main__":
    main()
