"""Theophysics Labeler - a CocoIndex pipeline that labels every file, sidecars it (.fistag),
then reports duplicates and empty folders.

    1. LABEL + SIDECAR (CocoIndex, incremental)
       Every file under the source folders becomes one component. Documents (.md .txt .pdf
       .docx .html) are labeled against the Theophysics tag registry with the Convergence
       Tagger engine (C:\\Theophysics_Tagger); every other file gets a kind label (image,
       audio, code, archive ...) plus filename keywords. Each file gets a `<file>.fistag`
       JSON sidecar beside it (fistag.py's format, which FIS reads) and a row in state/index.db.
       Unchanged files are skipped (memo on path + size + mtime + registry). Delete a file
       and CocoIndex deletes its sidecar and row; edit the registry and everything re-labels.

    2. DUPLICATES  - exact copies (same sha256) and same-text documents (same words, different
       bytes, e.g. a .md copy whose frontmatter differs), sorted by space you would get back.

    3. EMPTY FOLDERS - folders with no real files anywhere beneath them. Reported only, unless
       you pass --remove-empty (removes folders that are completely empty, nothing else).

Usage:
    python main.py run "D:\\folder" ["E:\\another"]           # all three steps
    python main.py run "D:\\folder" --live                     # then keep labeling as files change
    python main.py report "D:\\folder"                         # steps 2 + 3 only
    python main.py run "D:\\folder" --remove-empty

Reports go to state/reports/. Folders are remembered in state/sources.json, so
`python main.py run` with no folders re-runs the last set. Dropping a folder from the list
makes CocoIndex remove the sidecars it wrote there.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

import cocoindex as coco
from cocoindex.connectors import localfs, sqlite
from cocoindex.resources.file import FileLike, PatternFilePathMatcher

HERE = pathlib.Path(__file__).resolve().parent
STATE = pathlib.Path(os.environ.get("LABELER_STATE", HERE / "state"))
REPORTS = STATE / "reports"
SOURCES_FILE = STATE / "sources.json"
TAGGER_ROOT = pathlib.Path(os.environ.get("THEO_TAGGER_ROOT", r"C:\Theophysics_Tagger"))
sys.path.insert(0, str(TAGGER_ROOT / "tools"))
import tagger2 as T2  # noqa: E402  the tagging engine
import tagger3 as T3  # noqa: E402  text extraction (pdf/docx/html) + defaults
import fistag as FT  # noqa: E402  the .fistag sidecar format (domain / stage / context / coco)

SIDECAR = ".fistag"  # JSON beside each file, same format as fistag.py (FIS reads it)
LABELER_VERSION = 2  # bump to force every file to re-label
FULL_HASH_LIMIT = 512 * 1024 * 1024  # above this, hash size + first/last 4 MB
DOC_EXTS = {".md", ".markdown", ".txt", ".pdf", ".docx", ".html", ".htm"}
EXCLUDED = [
    "**/*.fmeta", "**/.folder.fmeta", "**/*.fistag", "**/*.fisnote", "**/*.sidecar.json", "**/*.chi",
    "**/.git", "**/node_modules", "**/.obsidian", "**/.trash", "**/__pycache__",
    "**/.venv", "**/venv", "**/.wrangler", "**/$RECYCLE.BIN", "**/System Volume Information",
    "**/desktop.ini", "**/Thumbs.db", "**/.DS_Store", "**/~$*",
]
JUNK = {"desktop.ini", "thumbs.db", ".ds_store", ".folder.fmeta"}  # these (and sidecars) don't make a folder non-empty
KINDS = {
    "image": ".jpg .jpeg .png .gif .webp .bmp .tif .tiff .svg .heic .ico .psd .raw",
    "audio": ".mp3 .wav .m4a .flac .ogg .aac .wma",
    "video": ".mp4 .mkv .mov .avi .webm .wmv .m4v",
    "archive": ".zip .7z .rar .tar .gz .bz2 .xz .iso",
    "code": ".py .js .ts .tsx .jsx .rs .go .java .c .cpp .h .cs .rb .php .ps1 .sh .bat .ahk .lean .sql",
    "data": ".csv .tsv .json .jsonl .xml .yaml .yml .parquet .db .sqlite .xlsx .xls",
    "config": ".ini .cfg .toml .env .conf",
    "slides": ".pptx .ppt .key",
    "program": ".exe .msi .dll .apk",
    "notebook": ".ipynb",
    "font": ".ttf .otf .woff .woff2",
    "backup": ".bak .old .tmp .orig",
}
EXT_KIND = {e: k for k, exts in KINDS.items() for e in exts.split()}
STOP = set("the a an and or of to in is it for on with as by at from this that be are copy final "
           "new old draft version file files img image scan untitled document doc".split())

SQLITE_DB = coco.ContextKey[sqlite.ManagedConnection]("labeler_index_db")


# ------------------------------------------------------------------------- labeler engine
class Labeler:
    """Registry + corpus statistics from the Convergence Tagger, loaded once per run."""

    def __init__(self) -> None:
        args = T3.build_parser().parse_args(["eval"])
        if args.exclusions and not pathlib.Path(args.exclusions).exists():
            args.exclusions = None
        con = T3.open_db(pathlib.Path(args.db))
        ctx = T3.registry_ctx(args, con, semantic=False)
        hashes, _, _, df = T2.gather(con, ctx.registry_hash, None)
        con.close()
        self.ctx, self.df, self.N = ctx, df, len(hashes)
        self.params = T2.load_params(T2.vars_params(args))
        self.registry_hash = ctx.registry_hash
        self.domains = FT.tag_domains()        # tag -> FIS domain code
        self.coco = FT.coco_hashes()           # sha256s CocoIndex/Canonization already holds

    def label_text(self, path: pathlib.Path, text: str) -> dict:
        tags, index = self.ctx.tags, self.ctx.index
        body, title, paras = T2.parse_doc(path, text)
        h = T2.content_hash(body)
        counts: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])

        def add(c: Counter, slot: int, low: str) -> None:
            for t, k in c.items():
                if tags[t].excludes and any(x in low for x in tags[t].excludes):
                    continue
                counts[tags[t].tag][slot] += k

        add(T2.count_hits(T2.tokens_of(title), index), 0, title.lower())
        for para in paras:
            add(T2.count_hits(T2.tokens_of(para), index), 1 if para.startswith("#") else 2, para.lower())
        doc_counts = {h: {t: tuple(v) for t, v in counts.items()}}
        acc = [r for r in T2.score_doc(h, doc_counts, {}, self.df, max(self.N, 1), self.params,
                                       self.ctx.tag_by_name) if r["accepted"]]
        primary_cat, _ = T2.rollup(acc, self.ctx.tag_by_name)
        refs = list(dict.fromkeys(r[0] for r in T2.find_scripture(T2.FENCE_RE.sub("\n", body))))
        variables = sorted({self.ctx.tag_by_name[r["tag"]].variable for r in acc
                            if r["tag"] in self.ctx.tag_by_name and self.ctx.tag_by_name[r["tag"]].variable})
        # fistag's subject(): weighted hits (3 title, 2 heading, 1 body) -> top tags + FIS domain
        hits = sorted(((3 * a + 2 * b + c, t) for t, (a, b, c) in doc_counts[h].items()), reverse=True)
        score: dict[str, float] = {}
        for sc, t in hits:
            code = self.domains.get(t)
            if code:
                score[code] = score.get(code, 0) + sc * FT.SPEC.get("weights", {}).get(code, 1)
        return {"text_hash": h, "top_tags": [t for _, t in hits[:8]], "domain": max(score, key=score.get) if score else "TPH",
                "tags": [r["tag"] for r in acc], "primary_tag": acc[0]["tag"] if acc else "",
                "primary_category": primary_cat, "variables": variables, "scripture": refs,
                "words": sum(len(p.split()) for p in paras)}


_labeler: Labeler | None = None


def labeler() -> Labeler:
    global _labeler
    if _labeler is None:
        _labeler = Labeler()
    return _labeler


# ------------------------------------------------------------------------------ helpers
def file_hash(path: pathlib.Path, size: int) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        if size <= FULL_HASH_LIMIT:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
            return h.hexdigest()
        h.update(str(size).encode())
        h.update(fh.read(4 << 20))
        fh.seek(-(4 << 20), os.SEEK_END)
        h.update(fh.read(4 << 20))
        return "quick:" + h.hexdigest()


def name_keywords(path: pathlib.Path, n: int = 6) -> list[str]:
    words = re.findall(r"[a-z][a-z0-9]{2,}", T2.camel_split(path.stem).lower())
    return [w for w, _ in Counter(w for w in words if w not in STOP and not w.isdigit()).most_common(n)]


def human(n: float) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{int(n)} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return str(n)


# ----------------------------------------------------------------------- pipeline types
@dataclass
class FileRow:
    path: str
    source: str
    folder: str
    name: str
    ext: str
    kind: str
    size: int
    modified: str
    sha256: str
    text_hash: str
    words: int
    primary_tag: str
    primary_category: str
    tags: str
    variables: str
    scripture: str
    keywords: str
    problem: str


@dataclass
class Labeled:
    row: FileRow
    sidecar: str


# --------------------------------------------------------------------------- pipeline
@coco.fn(memo=True, version=LABELER_VERSION)
async def label_file(path: str, size: int, mtime_ns: int, source: str, registry_hash: str) -> Labeled:
    """Pure: everything about one file. Memoized on (path, size, mtime, registry), so an
    unchanged file is never re-read - not even to fingerprint it."""
    p = pathlib.Path(path)
    ext = p.suffix.lower()
    sha = await asyncio.to_thread(file_hash, p, size)
    kind = "document" if ext in DOC_EXTS else EXT_KIND.get(ext, "other")
    lab: dict = {"text_hash": "", "top_tags": [], "domain": "TPH", "tags": [], "primary_tag": "",
                 "primary_category": "", "variables": [], "scripture": [], "words": 0}
    problem, text = "", ""
    if kind == "document":
        text, err = await asyncio.to_thread(T3.extract, path)
        if err:
            problem = err
        elif not text.strip():
            problem = "no extractable text (image-only PDF?)"
        else:
            lab = await asyncio.to_thread(labeler().label_text, p, text)
    keywords = name_keywords(p)
    modified = datetime.fromtimestamp(mtime_ns / 1e9).strftime("%Y-%m-%d %H:%M:%S")
    row = FileRow(path=path, source=source, folder=str(p.parent), name=p.name, ext=ext, kind=kind, size=size,
                  modified=modified, sha256=sha, text_hash=lab["text_hash"], words=lab["words"],
                  primary_tag=lab["primary_tag"], primary_category=lab["primary_category"],
                  tags="; ".join(lab["tags"]), variables=", ".join(lab["variables"]),
                  scripture="; ".join(lab["scripture"]), keywords=", ".join(keywords), problem=problem)

    # .fistag: same codes and fields as tagger's fistag.py, so FIS reads it; labeler fields added after.
    old: dict = {}
    side = pathlib.Path(path + SIDECAR)
    if side.is_file():
        try:
            old = json.loads(side.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            old = {}
    ctx = "OV" if FT.in_vault(p) else "NO"
    stg = await asyncio.to_thread(FT.stage, p, text, sha, old)
    cc = "CC" if sha in labeler().coco else "--"
    now = datetime.now().isoformat(timespec="seconds")
    sidecar = json.dumps({
        "fistag": f"{ctx}.{lab['domain']} · {stg} · {cc}", "context": ctx, "domain": lab["domain"], "stage": stg,
        "stage_name": FT.SPEC["stages"][stg], "coco": cc == "CC", "top_tags": lab["top_tags"],
        "sha256": sha, "first_sha256": old.get("first_sha256") or sha,
        "first_tagged": old.get("first_tagged") or now, "updated": now,
        "by": f"Theophysics Labeler (CocoIndex) v{LABELER_VERSION}",
        "label": lab["primary_tag"] or kind, "kind": kind,
        "primary_tag": lab["primary_tag"], "primary_category": lab["primary_category"],
        "tags": lab["tags"], "variables": lab["variables"], "scripture": lab["scripture"][:60],
        "keywords": keywords, "size": size, "modified": modified, "text_hash": lab["text_hash"],
        "words": lab["words"], "problem": problem, "registry": registry_hash,
    }, indent=2, ensure_ascii=False) + "\n"
    return Labeled(row=row, sidecar=sidecar)


@coco.fn
async def visit_file(file: FileLike, source: str, registry_hash: str, table: sqlite.TableTarget[FileRow]) -> None:
    p = pathlib.Path(file.file_path.resolve())
    try:
        st = p.stat()
    except OSError:
        return
    res = await label_file(str(p), st.st_size, st.st_mtime_ns, source, registry_hash)
    localfs.declare_file(pathlib.Path(str(p) + SIDECAR), res.sidecar)
    table.declare_row(row=res.row)


@coco.fn
async def label_source(source: str, registry_hash: str, table: sqlite.TableTarget[FileRow]) -> None:
    files = localfs.walk_dir(
        pathlib.Path(source),
        recursive=True,
        path_matcher=PatternFilePathMatcher(excluded_patterns=EXCLUDED),
        live=True,
    )
    await coco.mount_each(visit_file, files.items(), source, registry_hash, table)


@coco.fn
async def app_main(sources: list[str]) -> None:
    table = await sqlite.mount_table_target(
        SQLITE_DB,
        table_name="files",
        table_schema=await sqlite.TableSchema.from_class(FileRow, primary_key=["path"]),
    )
    registry_hash = labeler().registry_hash
    for i, source in enumerate(sources):
        key = hashlib.sha1(source.lower().encode()).hexdigest()[:12]
        await coco.mount(coco.component_subpath("source", key), label_source, source, registry_hash, table)


@coco.lifespan
def coco_lifespan(builder: coco.EnvironmentBuilder) -> Iterator[None]:
    STATE.mkdir(parents=True, exist_ok=True)
    builder.settings.db_path = STATE / "cocoindex.db"
    conn = sqlite.connect(str(STATE / "index.db"), load_vec=False)
    builder.provide(SQLITE_DB, conn)
    yield
    conn.close()


def load_sources() -> list[str]:
    try:
        return json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def make_app(sources: list[str]) -> coco.App:
    return coco.App(coco.AppConfig(name="TheophysicsLabeler"), app_main, sources=sources)


# `cocoindex update main.py` imports this module and uses the last folder set;
# `python main.py ...` builds its own app in main() instead.
if __name__ != "__main__":
    app = make_app(load_sources())


# ---------------------------------------------------------------------------- reports
def write_csv(path: pathlib.Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def find_duplicates(sources: list[str]) -> tuple[list[dict], list[dict]]:
    con = sqlite3.connect(STATE / "index.db")
    con.row_factory = sqlite3.Row
    roots = [s.lower() for s in sources]
    rows = [dict(r) for r in con.execute("SELECT path, size, sha256, text_hash, kind, primary_tag FROM files")
            if any(r["path"].lower().startswith(s) for s in roots) and os.path.exists(r["path"])]
    con.close()
    exact_rows, text_rows = [], []
    by_sha: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["size"] > 0:
            by_sha[r["sha256"]].append(r)
    for i, (sha, group) in enumerate(sorted(by_sha.items(), key=lambda kv: -kv[1][0]["size"] * (len(kv[1]) - 1))):
        if len(group) < 2:
            continue
        keep = min(group, key=lambda r: (len(r["path"]), r["path"]))  # suggest keeping the shortest path
        for r in sorted(group, key=lambda r: r["path"]):
            exact_rows.append({"group": sha.replace("quick:", "")[:12], "copies": len(group), "size": human(r["size"]),
                               "reclaimable": human(r["size"] * (len(group) - 1)),
                               "suggest": "keep" if r is keep else "duplicate", "_bytes": r["size"], "kind": r["kind"],
                               "label": r["primary_tag"], "path": r["path"]})
    by_text: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["text_hash"]:
            by_text[r["text_hash"]].append(r)
    for th, group in by_text.items():
        if len(group) > 1 and len({r["sha256"] for r in group}) > 1:  # same words, different bytes
            for r in sorted(group, key=lambda r: r["path"]):
                text_rows.append({"group": th[:12], "copies": len(group), "size": human(r["size"]),
                                  "label": r["primary_tag"], "path": r["path"]})
    return exact_rows, text_rows


def find_empty_folders(sources: list[str], remove: bool) -> list[dict]:
    skip = {"node_modules", ".git", ".obsidian", "__pycache__", ".venv", "venv", "$RECYCLE.BIN",
            "System Volume Information"}
    out: list[dict] = []
    for source in sources:
        root = pathlib.Path(source)
        has_content: dict[str, bool] = {}
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            if any(part in skip for part in pathlib.Path(dirpath).parts):
                continue
            real = [f for f in filenames if f.lower() not in JUNK and not f.endswith((SIDECAR, ".fmeta", ".fisnote"))]
            sub = [os.path.join(dirpath, d) for d in dirnames if d not in skip]
            # a skipped folder (.obsidian, node_modules ...) is not looked into, so it counts as content
            full = bool(real) or any(d in skip for d in dirnames) or any(has_content.get(s, True) for s in sub)
            has_content[dirpath] = full
            if full or pathlib.Path(dirpath) == root:
                continue
            junk = sorted(set(filenames) - set(real))
            status = "empty" if not filenames and not sub else "only empty subfolders" if not filenames else \
                "only system/sidecar files: " + ", ".join(junk[:5])
            removed = ""
            if remove and not filenames and not os.listdir(dirpath):
                try:
                    os.rmdir(dirpath)
                    removed = "removed"
                except OSError as exc:
                    removed = f"not removed: {exc}"
            out.append({"folder": dirpath, "status": status, "action": removed})
    return out


def run_reports(sources: list[str], remove_empty: bool) -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    exact, same_text = find_duplicates(sources)
    empties = find_empty_folders(sources, remove_empty)
    write_csv(REPORTS / "duplicates.csv", exact,
              ["group", "copies", "size", "reclaimable", "suggest", "kind", "label", "path"])
    write_csv(REPORTS / "same_text.csv", same_text, ["group", "copies", "size", "label", "path"])
    write_csv(REPORTS / "empty_folders.csv", empties, ["folder", "status", "action"])

    con = sqlite3.connect(STATE / "index.db")
    roots = tuple(s.lower() for s in sources)
    rows = [r for r in con.execute("SELECT path, kind, primary_category, primary_tag, problem, size FROM files")
            if r[0].lower().startswith(roots)]
    con.close()
    rows_by_kind = Counter(r[1] for r in rows)
    cats = Counter(r[2] for r in rows if r[2])
    tags = Counter(r[3] for r in rows if r[3])
    problems = [r for r in rows if r[4]]
    write_csv(REPORTS / "problems.csv", [{"path": r[0], "problem": r[4]} for r in problems], ["path", "problem"])
    reclaim = sum(1 for r in exact if r["suggest"] == "duplicate")
    reclaim_bytes = sum(size for size in (r.get("_bytes", 0) for r in exact if r["suggest"] == "duplicate"))
    summary = {
        "files_labeled": len(rows), "by_kind": dict(rows_by_kind.most_common()),
        "top_categories": dict(cats.most_common(8)), "top_primary_tags": dict(tags.most_common(12)),
        "duplicate_copies": reclaim, "duplicate_space_reclaimable": human(reclaim_bytes),
        "same_text_groups": len({r["group"] for r in same_text}), "empty_folders": len(empties),
        "empty_folders_removed": sum(1 for e in empties if e["action"] == "removed"),
        "problems": len(problems), "reports": str(REPORTS),
    }
    md = [f"# Labeler report - {datetime.now():%Y-%m-%d %H:%M}", "", f"Sources: {', '.join(sources)}", ""]
    md += [f"- **{k.replace('_', ' ')}**: {v}" for k, v in summary.items() if not isinstance(v, dict)]
    for k in ("by_kind", "top_categories", "top_primary_tags"):
        md += ["", f"## {k.replace('_', ' ').title()}", ""] + [f"- {a}: {b}" for a, b in summary[k].items()]
    (REPORTS / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


# ------------------------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser(description="Label + sidecar every file, then find duplicates and empty folders.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="label + sidecar, then duplicates + empty folders")
    r.add_argument("folders", nargs="*", help="folders to process (default: the last set)")
    r.add_argument("--live", action="store_true", help="after the reports, keep labeling as files change")
    r.add_argument("--full", action="store_true", help="re-label everything, ignoring the cache")
    r.add_argument("--remove-empty", action="store_true", help="remove folders that are completely empty")
    rp = sub.add_parser("report", help="duplicates + empty folders only")
    rp.add_argument("folders", nargs="*")
    rp.add_argument("--remove-empty", action="store_true")
    a = ap.parse_args()

    sources = [os.path.abspath(f) for f in a.folders] or load_sources()  # abspath keeps \server\share paths intact
    if not sources:
        ap.error("give at least one folder")
    missing = [s for s in sources if not os.path.isdir(s)]
    if missing:
        ap.error(f"not a folder: {', '.join(missing)}")
    STATE.mkdir(parents=True, exist_ok=True)
    SOURCES_FILE.write_text(json.dumps(sources, indent=2), encoding="utf-8")

    the_app = make_app(sources)
    if a.cmd == "run":
        print(f"[1/3] labeling + sidecars: {', '.join(sources)}", flush=True)
        the_app.update_blocking(report_to_stdout=True, full_reprocess=a.full)
    print("[2/3] duplicates   [3/3] empty folders", flush=True)
    print(json.dumps(run_reports(sources, a.remove_empty), indent=2))
    if a.cmd == "run" and a.live:
        print("[live] watching for changes - Ctrl+C to stop (re-run `report` any time)", flush=True)
        the_app.update_blocking(live=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
