"""
POF 2828 - Clipboard Sync Server (FastAPI)
Port 3456 - Local backend for clipboard3.html, prompt picker, research links, and window state.
"""
from __future__ import annotations

import configparser
import json
import os
import sqlite3
import subprocess
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
import urllib.error
import urllib.request

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


PORT = 3456
MAX_CLIP_LIST_LIMIT = 250
BASE = Path(__file__).parent
DATA_DIR = BASE / "Data"
CONFIG_DIR = BASE / "config"
MODULES_DIR = BASE / "modules"
DB_PATH = DATA_DIR / "clipboard.db"
CLIPBOARD_BACKUP_DIR = MODULES_DIR / "Clipboard" / "backups"
CLIPBOARD_BACKUP_STATE = DATA_DIR / "clipboard_backup_state.json"
PROMPTS_FILE = CONFIG_DIR / "prompts.json"
WINDOW_STATE_FILE = DATA_DIR / "window_state.json"

HOME = Path.home()
FILE_FOLDERS = {
    "documents": HOME / "Documents",
    "videos": HOME / "Videos",
    "music": HOME / "Music",
    "pictures": HOME / "Pictures",
}

DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

LOCK = threading.Lock()
WATCHER_THREAD: Optional[threading.Thread] = None
BACKUP_THREAD: Optional[threading.Thread] = None


def clipboard_watch_enabled() -> bool:
    """Optional OS clipboard poller. Off by default so Ditto/ExtraClipboard
    and normal Ctrl+C/V are not fighting OpenClipboard."""
    try:
        bridge = configparser.ConfigParser()
        bridge.read(CONFIG_DIR / "bridge.ini", encoding="utf-8")
        raw = bridge.get("clipboard", "watch_enabled", fallback="0").strip().lower()
        return raw in {"1", "true", "yes", "on"}
    except Exception:
        return False


def start_clipboard_watch_thread() -> None:
    global WATCHER_THREAD
    if WATCHER_THREAD and WATCHER_THREAD.is_alive():
        return
    if not clipboard_watch_enabled():
        print("Clipboard watcher disabled (bridge.ini watch_enabled=0)")
        return
    try:
        import clipboard_watch

        WATCHER_THREAD = threading.Thread(
            target=clipboard_watch.run_forever,
            name="clipboard-watch",
            daemon=True,
        )
        WATCHER_THREAD.start()
        print("Clipboard watcher thread started")
    except Exception as exc:
        print(f"Clipboard watcher failed to start: {exc}")


def start_clipboard_backup_thread() -> None:
    global BACKUP_THREAD
    if BACKUP_THREAD and BACKUP_THREAD.is_alive():
        return
    BACKUP_THREAD = threading.Thread(
        target=clipboard_backup_loop,
        name="clipboard-daily-backup",
        daemon=True,
    )
    BACKUP_THREAD.start()
    print("Clipboard daily backup thread started")


def clipboard_backup_loop() -> None:
    run_daily_clipboard_backup()
    while True:
        time.sleep(3600)
        run_daily_clipboard_backup()


def run_daily_clipboard_backup(force: bool = False) -> dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    state = load_json_file(CLIPBOARD_BACKUP_STATE, {})
    if not force and state.get("last_backup_date") == today:
        return {"ok": True, "skipped": True, "date": today, "reason": "already backed up today"}

    backup_dir = CLIPBOARD_BACKUP_DIR / today
    backup_dir.mkdir(parents=True, exist_ok=True)
    db_backup_path = backup_dir / "clipboard.db"
    json_backup_path = backup_dir / "clipboard.json"
    manifest_path = backup_dir / "manifest.json"

    with LOCK:
        DB.commit()
        dest = sqlite3.connect(str(db_backup_path))
        try:
            DB.backup(dest)
        finally:
            dest.close()

        rows = DB.execute(
            "SELECT * FROM clips ORDER BY created_at DESC"
        ).fetchall()
        clips = [row_to_dict(row) for row in rows]

    payload = {
        "kind": "pof2828_clipboard_daily_backup",
        "exported_at": datetime.now(UTC).isoformat(),
        "source_db": str(DB_PATH),
        "clip_count": len(clips),
        "clips": clips,
    }
    json_backup_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "date": today,
        "created_at": datetime.now(UTC).isoformat(),
        "source_db": str(DB_PATH),
        "database_backup": str(db_backup_path),
        "json_backup": str(json_backup_path),
        "clip_count": len(clips),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    save_json_file(CLIPBOARD_BACKUP_STATE, {"last_backup_date": today, "last_backup_at": manifest["created_at"]})
    return {"ok": True, "skipped": False, **manifest}

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_clipboard_watch_thread()
    start_clipboard_backup_thread()
    yield


app = FastAPI(title="POF 2828 Sync Server", version="2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if MODULES_DIR.exists():
    app.mount("/modules", StaticFiles(directory=str(MODULES_DIR)), name="modules")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


DB = get_db()


def init_db() -> None:
    with LOCK:
        DB.executescript(
            """
            CREATE TABLE IF NOT EXISTS clips (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL DEFAULT '',
                title TEXT DEFAULT '',
                category TEXT DEFAULT 'clipboard',
                pinned INTEGER DEFAULT 0,
                starred INTEGER DEFAULT 0,
                deleted INTEGER DEFAULT 0,
                slot INTEGER,
                tags TEXT DEFAULT '[]',
                fields TEXT DEFAULT '[]',
                categories TEXT DEFAULT '[]',
                ts TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS bookmarks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'other',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#888'
            );
            """
        )
        DB.commit()


def load_json_file(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json_file(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_window_state() -> dict:
    return load_json_file(WINDOW_STATE_FILE, {})


def save_window_state(state: dict) -> None:
    save_json_file(WINDOW_STATE_FILE, state)


def panel_key_from_title(title: str) -> str:
    normalized = (title or "").lower()
    if "clipboard" in normalized:
        return "clipboard"
    if "prompt" in normalized:
        return "prompts"
    if "research" in normalized or "links" in normalized:
        return "links"
    if "calendar" in normalized:
        return "calendar"
    key = "".join(ch if ch.isalnum() else "_" for ch in normalized).strip("_")
    return key or "panel"


def save_panel_state_file(panel_key: str, panel_state: dict) -> None:
    path = DATA_DIR / f"panel_state_{panel_key}.json"
    payload = {"panel": panel_key, **panel_state}
    save_json_file(path, payload)


def load_prompts() -> list[dict]:
    data = load_json_file(PROMPTS_FILE, [])
    return data if isinstance(data, list) else []


def save_prompts(prompts: list[dict]) -> None:
    save_json_file(PROMPTS_FILE, prompts)


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    if row is None:
        return None
    d = dict(row)
    for k in ("tags", "fields", "categories"):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                d[k] = []
    for k in ("pinned", "starred", "deleted"):
        if k in d:
            d[k] = bool(d[k])
    return d


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:6]}"


def get_body(payload: dict[str, Any]) -> dict[str, Any]:
    return payload or {}


@app.get("/")
def root() -> dict[str, str]:
    return {"ok": "true", "server": "POF 2828 Sync Server", "port": str(PORT)}


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true"}


FIS_DIR = BASE.parent / "FIS"
FIS_DB  = FIS_DIR / "fis_catalog.db"

def _fis_db() -> sqlite3.Connection:
    if not FIS_DB.exists():
        raise HTTPException(status_code=503, detail="FIS catalog not found — start FIS daemon first")
    c = sqlite3.connect(str(FIS_DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA query_only=ON")
    return c


@app.get("/api/fis/status")
def api_fis_status() -> dict:
    """Combined status for both FIS daemons (file tracker + folder tracker)."""
    def _read(f):
        try:
            with open(FIS_DIR / f) as fh:
                return json.load(fh)
        except FileNotFoundError:
            return {"running": False, "error": f"{f} not found"}
        except Exception as e:
            return {"running": False, "error": str(e)}

    file_status   = _read("fis_status.json")
    folder_status = _read("fis_folder_status.json")
    return {
        "file_tracker":   file_status,
        "folder_tracker": folder_status,
        "both_running":   file_status.get("running") and folder_status.get("running"),
    }


@app.post("/api/fis/classify")
def api_fis_classify(payload: dict[str, Any]) -> dict:
    """Classify a file or folder on-demand using fis_classifier."""
    import sys
    sys.path.insert(0, str(FIS_DIR))
    try:
        from fis_classifier import classify
    except ImportError:
        raise HTTPException(status_code=503, detail="fis_classifier not available")
    path = payload.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="path required")
    folder_class = payload.get("folder_class", "")
    try:
        result = classify(path, folder_class=folder_class)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fis/search")
def api_fis_search(
    q: str = "",
    domain: str = "",
    folder_class: str = "",
    ext: str = "",
    status: str = "active",
    needs_review: int = -1,
    limit: int = 50,
) -> list[dict]:
    """Search the FIS catalog."""
    c = _fis_db()
    clauses = ["1=1"]
    params: list = []
    if status:
        clauses.append("status=?");        params.append(status)
    if q:
        clauses.append("(name LIKE ? OR path LIKE ? OR file_role LIKE ?)");
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if domain:
        clauses.append("chi_domain=?");    params.append(domain)
    if folder_class:
        clauses.append("folder_class=?");  params.append(folder_class)
    if ext:
        clauses.append("ext=?");           params.append(ext if ext.startswith(".") else f".{ext}")
    if needs_review >= 0:
        clauses.append("needs_review=?");  params.append(needs_review)
    params.append(min(max(limit, 1), 500))
    sql = (
        "SELECT path,name,ext,size,folder_class,dominant_chi,chi_domain,chi_law,"
        "chi_confidence,file_role,status,scanned,classified_at,needs_review "
        f"FROM files WHERE {' AND '.join(clauses)} "
        "ORDER BY scanned DESC LIMIT ?"
    )
    rows = c.execute(sql, params).fetchall()
    c.close()
    return [dict(r) for r in rows]


@app.get("/api/fis/review")
def api_fis_review(limit: int = 20) -> list[dict]:
    """List files marked for AI review (confidence too low for local classification)."""
    c = _fis_db()
    rows = c.execute(
        "SELECT path,name,ext,folder_class,chi_confidence,file_role,classified_at "
        "FROM files WHERE needs_review=1 AND status='active' "
        "ORDER BY classified_at DESC LIMIT ?",
        (min(limit, 200),)
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


@app.get("/api/fis/domains")
def api_fis_domains() -> dict:
    """Breakdown of active files by CHI domain."""
    c = _fis_db()
    rows = c.execute(
        "SELECT chi_domain, COUNT(*) as n FROM files "
        "WHERE status='active' AND chi_domain IS NOT NULL "
        "GROUP BY chi_domain ORDER BY n DESC"
    ).fetchall()
    c.close()
    return {r["chi_domain"]: r["n"] for r in rows}


@app.get("/api/fis/folders")
def api_fis_folders(folder_class: str = "") -> list[dict]:
    """List classified folders."""
    c = _fis_db()
    try:
        if folder_class:
            rows = c.execute(
                "SELECT * FROM folders WHERE folder_class=? ORDER BY classified_at DESC LIMIT 100",
                (folder_class,)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM folders ORDER BY classified_at DESC LIMIT 100"
            ).fetchall()
        c.close()
        return [dict(r) for r in rows]
    except Exception:
        c.close()
        return []


@app.get("/api/status")
def api_status() -> dict:
    db_ok = False
    clip_count = 0
    slots_filled = 0
    pinned_count = 0
    last_clip = None
    try:
        with LOCK:
            clip_count = DB.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
            slots_filled = DB.execute("SELECT COUNT(*) FROM clips WHERE slot IS NOT NULL").fetchone()[0]
            pinned_count = DB.execute("SELECT COUNT(*) FROM clips WHERE pinned=1").fetchone()[0]
            row = DB.execute("SELECT created_at FROM clips ORDER BY created_at DESC LIMIT 1").fetchone()
            last_clip = row[0] if row else None
            db_ok = True
    except Exception:
        pass

    ahk_running = False
    ahk_pid = None
    for exe in ("AutoHotkey64.exe", "AutoHotkey.exe", "AutoHotkeyU64.exe"):
        try:
            r = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=3,
            )
            if exe.lower() in r.stdout.lower():
                ahk_running = True
                break
        except Exception:
            pass

    slot_cache_files = len(list(SLOT_CACHE_DIR.glob("slot_*.txt"))) if SLOT_CACHE_DIR.exists() else 0

    return {
        "python": True,
        "db": db_ok,
        "clip_count": clip_count,
        "slots_filled": slots_filled,
        "pinned_count": pinned_count,
        "slot_cache_files": slot_cache_files,
        "ahk_running": ahk_running,
        "last_clip": last_clip,
        "server_time": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


@app.post("/api/clipboard/backup")
def api_clipboard_backup() -> dict:
    return run_daily_clipboard_backup(force=True)


@app.get("/status")
def status_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "status.html")


@app.get("/clipboard")
@app.get("/clipboard3")
def clipboard_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "clipboard3.html")


@app.get("/clipboard-old")
def clipboard_old_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "clipboard_the_one.html")


@app.get("/clipboard2")
def clipboard2_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "clipboard2.html")


# ── AHK slot cache: one plain .txt per slot so AutoHotkey reads it with no JSON.
SLOT_CACHE_DIR = BASE / "slot_cache"

def write_slot_cache() -> int:
    SLOT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK:
        rows = DB.execute("SELECT slot, content FROM clips WHERE slot IS NOT NULL").fetchall()
    for f in SLOT_CACHE_DIR.glob("slot_*.txt"):
        try:
            f.unlink()
        except OSError:
            pass
    n = 0
    for r in rows:
        try:
            (SLOT_CACHE_DIR / f"slot_{int(r['slot'])}.txt").write_text(r["content"] or "", encoding="utf-8")
            n += 1
        except (OSError, ValueError, TypeError):
            pass
    return n

@app.get("/api/slots/refresh")
def api_slots_refresh() -> dict:
    return {"written": write_slot_cache(), "dir": str(SLOT_CACHE_DIR)}


@app.post("/api/slots/assign")
def api_slot_assign(payload: dict[str, Any]) -> dict:
    """Assign clipboard content to a slot (1-75). Clears any previous holder of that slot."""
    body = get_body(payload)
    try:
        slot = int(body.get("slot", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="slot must be an integer")
    if not 1 <= slot <= 75:
        raise HTTPException(status_code=400, detail="slot must be 1-75")
    content = body.get("content", "")
    if not str(content).strip():
        raise HTTPException(status_code=400, detail="content required")
    title = body.get("title") or content.strip().splitlines()[0][:80]
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    cid = new_id("c")
    with LOCK:
        DB.execute("UPDATE clips SET slot=NULL, updated_at=? WHERE slot=?", (now, slot))
        DB.execute(
            "INSERT INTO clips (id,content,title,category,slot,tags,ts,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, content, title, "clipboard", slot, json.dumps(["slot"]), now, now, now),
        )
        DB.commit()
    write_slot_cache()
    return {"id": cid, "slot": slot}


@app.post("/api/slots/clear")
def api_slot_clear(payload: dict[str, Any]) -> dict:
    """Detach whatever clip currently holds this slot (keeps the clip in history)."""
    body = get_body(payload)
    try:
        slot = int(body.get("slot", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="slot must be an integer")
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with LOCK:
        DB.execute("UPDATE clips SET slot=NULL, updated_at=? WHERE slot=?", (now, slot))
        DB.commit()
    write_slot_cache()
    return {"cleared": slot}


# ── PWA: makes the clipboard installable as an app (manifest + service worker).
@app.get("/manifest.webmanifest")
def pwa_manifest() -> FileResponse:
    return FileResponse(MODULES_DIR / "clipboard.webmanifest", media_type="application/manifest+json")

@app.get("/sw.js")
def pwa_sw() -> FileResponse:
    return FileResponse(MODULES_DIR / "clipboard_sw.js", media_type="application/javascript",
                        headers={"Service-Worker-Allowed": "/"})

@app.get("/clip-icon.svg")
def pwa_icon() -> FileResponse:
    return FileResponse(MODULES_DIR / "clip_icon.svg", media_type="image/svg+xml")


@app.get("/prompts")
def prompts_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "prompt_picker.html")


@app.get("/links")
def links_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "research_links.html")


@app.get("/calendar")
def calendar_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "task-calendar.html")


@app.get("/fis")
def fis_intelligent_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "fis-intelligent.html")

@app.get("/fis/workbench")
def fis_workbench_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "fis-workbench.html")

@app.get("/fis/walkthrough")
def fis_walkthrough_page() -> FileResponse:
    return FileResponse(MODULES_DIR / "fis-walkthrough.html")


@app.get("/api/clips")
def api_get_clips(limit: int = 500) -> list[dict]:
    safe_limit = min(max(limit, 1), MAX_CLIP_LIST_LIMIT)
    with LOCK:
        rows = DB.execute(
            "SELECT * FROM clips ORDER BY created_at DESC LIMIT ?",
            (safe_limit,),
        ).fetchall()
    return [row_to_dict(r) for r in rows]


@app.get("/api/clips/{clip_id}")
def api_get_clip(clip_id: str) -> dict:
    with LOCK:
        row = DB.execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row_to_dict(row) or {}


@app.post("/api/clips")
def api_create_clip(payload: dict[str, Any]) -> JSONResponse:
    body = get_body(payload)
    cid = body.get("id") or new_id("c")
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with LOCK:
        DB.execute(
            """
            INSERT OR REPLACE INTO clips
            (id,content,title,category,pinned,starred,deleted,slot,tags,fields,categories,ts,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                cid,
                body.get("content", ""),
                body.get("title", ""),
                body.get("category", "clipboard"),
                int(bool(body.get("pinned", False))),
                int(bool(body.get("starred", False))),
                int(bool(body.get("deleted", False))),
                body.get("slot"),
                json.dumps(body.get("tags", [])),
                json.dumps(body.get("fields", [])),
                json.dumps(body.get("categories", [])),
                body.get("ts", now),
                now,
                now,
            ),
        )
        DB.commit()
    return JSONResponse({"id": cid}, status_code=201)


@app.put("/api/clips/{clip_id}")
@app.patch("/api/clips/{clip_id}")
def api_update_clip(clip_id: str, payload: dict[str, Any]) -> dict:
    body = get_body(payload)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    sets: list[str] = []
    vals: list[Any] = []
    for k in ("content", "title", "category"):
        if k in body:
            sets.append(f"{k}=?")
            vals.append(body[k])
    for k in ("pinned", "starred", "deleted"):
        if k in body:
            sets.append(f"{k}=?")
            vals.append(int(bool(body[k])))
    if "slot" in body:
        sets.append("slot=?")
        vals.append(body["slot"])
    for k in ("tags", "fields", "categories"):
        if k in body:
            val = body[k]
            sets.append(f"{k}=?")
            vals.append(json.dumps(val) if isinstance(val, list) else val)
    sets.append("updated_at=?")
    vals.append(now)
    vals.append(clip_id)
    if sets:
        with LOCK:
            DB.execute(f"UPDATE clips SET {','.join(sets)} WHERE id=?", vals)
            DB.commit()
    return {"id": clip_id}


@app.delete("/api/clips/{clip_id}")
def api_delete_clip(clip_id: str) -> Response:
    with LOCK:
        DB.execute("DELETE FROM clips WHERE id=?", (clip_id,))
        DB.commit()
    return Response(status_code=204)


@app.get("/api/bookmarks")
def api_get_bookmarks() -> list[dict]:
    with LOCK:
        rows = DB.execute("SELECT * FROM bookmarks ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/bookmarks")
def api_create_bookmark(payload: dict[str, Any]) -> JSONResponse:
    body = get_body(payload)
    bid = body.get("id") or new_id("b")
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with LOCK:
        DB.execute(
            "INSERT OR REPLACE INTO bookmarks (id,title,url,description,category,created_at) VALUES (?,?,?,?,?,?)",
            (bid, body.get("title", ""), body.get("url", ""), body.get("description", ""), body.get("category", "other"), now),
        )
        DB.commit()
    return JSONResponse({"id": bid}, status_code=201)


@app.delete("/api/bookmarks/{bookmark_id}")
def api_delete_bookmark(bookmark_id: str) -> Response:
    with LOCK:
        DB.execute("DELETE FROM bookmarks WHERE id=?", (bookmark_id,))
        DB.commit()
    return Response(status_code=204)


@app.get("/api/tags")
def api_get_tags() -> list[dict]:
    with LOCK:
        rows = DB.execute("SELECT * FROM tags").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/tags")
def api_create_tag(payload: dict[str, Any]) -> JSONResponse:
    body = get_body(payload)
    tid = body.get("id") or new_id("t")
    with LOCK:
        DB.execute(
            "INSERT OR IGNORE INTO tags (id,name,color) VALUES (?,?,?)",
            (tid, body.get("name", ""), body.get("color", "#888")),
        )
        DB.commit()
    return JSONResponse({"id": tid}, status_code=201)


@app.delete("/api/tags/{tag_id}")
def api_delete_tag(tag_id: str) -> Response:
    with LOCK:
        DB.execute("DELETE FROM tags WHERE id=?", (tag_id,))
        DB.commit()
    return Response(status_code=204)


@app.get("/api/prompts")
def api_get_prompts() -> list[dict]:
    return load_prompts()


@app.post("/api/prompts")
def api_create_prompt(payload: dict[str, Any]) -> JSONResponse:
    body = get_body(payload)
    prompts = load_prompts()
    pid = body.get("id") or new_id("p")
    body["id"] = pid
    prompts = [p for p in prompts if p.get("id") != pid]
    prompts.append(body)
    save_prompts(prompts)
    return JSONResponse({"id": pid}, status_code=201)


@app.delete("/api/prompts/{prompt_id}")
def api_delete_prompt(prompt_id: str) -> Response:
    prompts = [p for p in load_prompts() if p.get("id") != prompt_id]
    save_prompts(prompts)
    return Response(status_code=204)


# ------------------------------------------------------------------
# AI REWRITE  (DeepSeek — OpenAI-compatible chat completions)
# POST /api/rewrite  {text, style, mode?}  ->  {result}
# ------------------------------------------------------------------
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


def _deepseek_chat(system: str, user: str) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="DEEPSEEK_API_KEY is not set")
    model = os.environ.get("DEEPSEEK_MODEL", "").strip() or "deepseek-v4-flash"
    payload = json.dumps({
        "model": model,
        "temperature": 0.8,
        "max_tokens": 4000,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise HTTPException(status_code=502, detail=f"DeepSeek {exc.code}: {detail}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"DeepSeek request failed: {exc}") from exc
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise HTTPException(status_code=502, detail="Unexpected DeepSeek response") from exc


@app.post("/api/rewrite")
def api_rewrite(payload: dict[str, Any]) -> JSONResponse:
    body = get_body(payload)
    text = (body.get("text") or "").strip()
    style = (body.get("style") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    system = (
        "You are a master prose stylist. You rewrite the user's text so it embodies "
        "the requested writing technique. Preserve the meaning and the facts, keep the "
        "author's core content, and match the technique precisely. Return ONLY the "
        "rewritten text with no preamble, no explanation, and no quotation marks around it."
    )
    user = (
        f"WRITING TECHNIQUE TO APPLY:\n{style}\n\n"
        f"----- TEXT TO REWRITE -----\n{text}"
        if style else text
    )
    result = _deepseek_chat(system, user)
    return JSONResponse({"result": result})


@app.get("/api/window-state")
def api_window_state() -> dict:
    return load_window_state()


@app.get("/window-state")
def window_state() -> dict:
    return load_window_state()


@app.post("/window/pin")
def api_window_pin(payload: dict[str, Any]) -> dict:
    state = load_window_state()
    state["pin"] = payload
    title = str(payload.get("title", ""))
    panel_key = panel_key_from_title(title)
    panels = state.setdefault("panels", {})
    panel_state = panels.setdefault(panel_key, {})
    panel_state["pin"] = payload
    save_panel_state_file(panel_key, panel_state)
    save_window_state(state)
    return {"ok": True}


@app.post("/window/position")
def api_window_position(payload: dict[str, Any]) -> dict:
    state = load_window_state()
    state["position"] = payload
    title = str(payload.get("title", ""))
    panel_key = panel_key_from_title(title)
    panels = state.setdefault("panels", {})
    panel_state = panels.setdefault(panel_key, {})
    panel_state["position"] = payload
    save_panel_state_file(panel_key, panel_state)
    save_window_state(state)
    return {"ok": True}


@app.get("/api/files/{folder_key}")
def api_list_files(folder_key: str) -> list[dict]:
    folder_path = FILE_FOLDERS.get(folder_key)
    if not folder_path or not folder_path.exists():
        raise HTTPException(status_code=404, detail=f"folder '{folder_key}' not found")
    files: list[dict] = []
    for entry in sorted(folder_path.iterdir(), key=lambda e: e.stat().st_mtime, reverse=True):
        if entry.is_file() and not entry.name.startswith("."):
            st = entry.stat()
            files.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "size": st.st_size,
                    "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
                }
            )
        if len(files) >= 100:
            break
    return files


@app.post("/api/files/open")
def api_open_file(payload: dict[str, Any]) -> dict:
    body = get_body(payload)
    file_path = body.get("path", "")
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="file not found")
    resolved = Path(file_path).resolve()
    allowed = any(str(resolved).startswith(str(fp.resolve())) for fp in FILE_FOLDERS.values())
    if not allowed:
        raise HTTPException(status_code=403, detail="path not in allowed folders")
    try:
        os.startfile(str(resolved))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "opened": str(resolved)}


if __name__ == "__main__":
    print(f"POF 2828 Sync Server running on port {PORT}")
    print(f"DB: {DB_PATH}")
    print("Serving clipboard3, prompt picker, research links, and calendar panels")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
