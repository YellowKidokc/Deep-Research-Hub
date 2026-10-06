"""
YouTube Watch Logger + Downloader (local server)

- Chrome extension POSTs every YouTube video you watch -> logged to watch_log.db
- When you click "Download" in the popup, the video is queued and yt-dlp runs
- Proxies from config.json are rotated / retried on failure
- Dashboard at http://127.0.0.1:8765/ lets you download everything at once
"""

import json
import sqlite3
import subprocess
import threading
import queue
import itertools
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
DB_PATH = HERE / "watch_log.db"
DOWNLOAD_DIR = Path(CONFIG["download_dir"])
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

db_lock = threading.Lock()
job_queue = queue.Queue()
proxy_cycle = itertools.cycle(CONFIG["proxies"]) if CONFIG["proxies"] else None
proxy_lock = threading.Lock()


# ---------------------------------------------------------------- database
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_lock, db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id     TEXT PRIMARY KEY,
                url          TEXT,
                title        TEXT,
                channel      TEXT,
                first_seen   TEXT,
                last_seen    TEXT,
                watch_count  INTEGER DEFAULT 1,
                status       TEXT DEFAULT 'watched',  -- watched|skipped|queued|downloading|done|failed
                error        TEXT
            )""")
        # anything left mid-download from a previous run goes back in the queue
        conn.execute("UPDATE videos SET status='queued' WHERE status='downloading'")


def log_watch(v):
    now = datetime.now().isoformat(timespec="seconds")
    with db_lock, db() as conn:
        conn.execute("""
            INSERT INTO videos (video_id, url, title, channel, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                last_seen=excluded.last_seen,
                watch_count=watch_count+1,
                title=COALESCE(NULLIF(excluded.title,''), title),
                channel=COALESCE(NULLIF(excluded.channel,''), channel)
        """, (v["video_id"], v["url"], v.get("title", ""), v.get("channel", ""), now, now))
        row = conn.execute("SELECT status FROM videos WHERE video_id=?", (v["video_id"],)).fetchone()
    return row["status"]


def set_status(video_id, status, error=None):
    with db_lock, db() as conn:
        conn.execute("UPDATE videos SET status=?, error=? WHERE video_id=?", (status, error, video_id))


def list_videos():
    with db_lock, db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM videos ORDER BY last_seen DESC")]


# ---------------------------------------------------------------- downloading
def next_proxy():
    if not proxy_cycle:
        return None
    with proxy_lock:
        return next(proxy_cycle)


def build_cmd(url, proxy):
    cmd = [
        "yt-dlp",
        "-f", CONFIG["format"],
        "--merge-output-format", "mp4",
        "-o", str(DOWNLOAD_DIR / "%(channel)s/%(title)s [%(id)s].%(ext)s"),
        "--download-archive", str(HERE / "downloaded_archive.txt"),
        *CONFIG.get("extra_args", []),
    ]
    if CONFIG.get("write_subs"):
        cmd += ["--write-subs", "--write-auto-subs", "--sub-lang", "en", "--convert-subs", "srt"]
    if proxy:
        cmd += ["--proxy", proxy]
    cmd.append(url)
    return cmd


def download(video_id, url):
    proxies = CONFIG["proxies"]
    # try each proxy (or no proxy if none configured)
    attempts = (len(proxies) * CONFIG.get("retries_per_proxy", 1)) if proxies else 1
    last_err = ""
    for _ in range(attempts):
        proxy = next_proxy()
        print(f"[download] {video_id} via {proxy or 'direct'}")
        r = subprocess.run(build_cmd(url, proxy), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode == 0:
            set_status(video_id, "done")
            print(f"[done] {video_id}")
            return
        last_err = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["unknown error"]
        last_err = last_err[0]
        print(f"[retry] {video_id}: {last_err}")
    set_status(video_id, "failed", last_err)
    print(f"[failed] {video_id}: {last_err}")


YTBSD_DIR = Path(CONFIG.get("ytbsd_dir", ""))
YTBSD_OUT = YTBSD_DIR / "subtitles"


_head_cache = {}          # path -> (mtime, video_id, head)
_head_lock = threading.Lock()


def _refresh_head_cache():
    """Read the head of only new or changed transcript files.

    Files live in per-channel subfolders, so the walk is recursive. Stat is
    cheap; the 2000-char head is read once per file and cached, so a miss no
    longer rescans thousands of files.
    """
    seen = set()
    for md in YTBSD_OUT.rglob("*.md"):
        try:
            mtime = md.stat().st_mtime
        except OSError:
            continue
        seen.add(md)
        cached = _head_cache.get(md)
        if cached and cached[0] == mtime:
            continue
        try:
            with open(md, encoding="utf-8", errors="replace") as f:
                head = f.read(2000)
        except OSError:
            continue
        vid = ""
        marker = "**Video ID:** `"
        i = head.find(marker)
        if i >= 0:
            vid = head[i + len(marker):head.find("`", i + len(marker))]
        _head_cache[md] = (mtime, vid, head)
    for md in list(_head_cache):
        if md not in seen:
            del _head_cache[md]


def transcript_saved(video_id):
    """ytgrab.py writes <channel>/<title>.md containing the video id; failures are marked 'failed'."""
    with _head_lock:
        _refresh_head_cache()
        for mtime, vid, head in _head_cache.values():
            if vid == video_id:
                return "**Retrieved via:** failed" not in head, head
    return False, ""


def _mark_if_saved(video_id):
    """Flip a video to done/failed the moment its file exists on disk."""
    ok, head = transcript_saved(video_id)
    if not ok and not head:
        return False
    if ok and "**Retrieved via:** no_transcript" in head:
        set_status(video_id, "failed", "video has no transcript")
    elif ok:
        set_status(video_id, "done")
    else:
        set_status(video_id, "failed", "transcript not captured")
    return True


def grab_transcripts(jobs):
    """Run YTBSD's non-interactive ytgrab.py on a batch: direct first, then Webshare, then the 300 free proxies.

    ytgrab writes every transcript to disk the moment it is captured. Output is
    streamed line by line, and each time ytgrab reports a capture the still
    open videos in this batch are checked on disk and flipped to done at once,
    instead of waiting for the whole batch to finish.
    """
    for vid, _ in jobs:
        set_status(vid, "downloading")
    cmd = [str(YTBSD_DIR / "venv/Scripts/python.exe"), "ytgrab.py",
           *[url for _, url in jobs], *CONFIG.get("ytbsd_args", [])]
    print(f"[ytbsd] {len(jobs)} video(s): {' '.join(cmd[2:])}")
    open_ids = {vid for vid, _ in jobs}
    last_line = ""
    proc = subprocess.Popen(cmd, cwd=YTBSD_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", bufsize=1)
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            print(f"  [ytgrab] {line}")
            last_line = line
        if line.startswith("  + ") and open_ids:
            for vid in list(open_ids):
                if _mark_if_saved(vid):
                    open_ids.discard(vid)
    proc.wait()
    for vid in open_ids:
        if not _mark_if_saved(vid):
            set_status(vid, "failed", last_line or "transcript not captured")


def reconcile():
    """Fix watch_log.db against what is really on disk.

    The old done-check ignored per-channel subfolders and marked finished
    videos as failed. Any failed or stuck video whose transcript exists is
    flipped to done; a failure placeholder stays failed so it can be retried.
    """
    fixed = 0
    for v in list_videos():
        if v["status"] not in ("failed", "downloading", "queued"):
            continue
        ok, head = transcript_saved(v["video_id"])
        if ok and "**Retrieved via:** no_transcript" not in head:
            set_status(v["video_id"], "done")
            fixed += 1
    print(f"[reconcile] {fixed} video(s) were already on disk and are now marked done")
    return fixed


def worker():
    while True:
        jobs = [job_queue.get()]
        if CONFIG.get("mode") == "transcript":
            # grab everything else already waiting so bulk downloads run as one YTBSD call
            while len(jobs) < CONFIG.get("batch_size", 25):
                try:
                    jobs.append(job_queue.get_nowait())
                except queue.Empty:
                    break
        try:
            if CONFIG.get("mode") == "transcript":
                grab_transcripts(jobs)
            else:
                for video_id, url in jobs:
                    set_status(video_id, "downloading")
                    download(video_id, url)
        except Exception as e:
            for video_id, _ in jobs:
                set_status(video_id, "failed", str(e))
        finally:
            for _ in jobs:
                job_queue.task_done()


def enqueue(video_id, url=None):
    url = url or f"https://www.youtube.com/watch?v={video_id}"
    set_status(video_id, "queued")
    job_queue.put((video_id, url))


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def _json(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        if self.path == "/":
            self._send(200, (HERE / "dashboard.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/videos":
            self._send(200, list_videos())
        elif self.path == "/api/ping":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        body = self._json()
        if self.path == "/api/watch":
            status = log_watch(body)
            print(f"[watched] {body.get('title') or body['video_id']}")
            # tell the extension whether to ask (don't nag about already handled videos)
            self._send(200, {"status": status, "ask": status in ("watched",)})
        elif self.path == "/api/download":
            enqueue(body["video_id"], body.get("url"))
            self._send(200, {"queued": body["video_id"]})
        elif self.path == "/api/skip":
            set_status(body["video_id"], "skipped")
            self._send(200, {"skipped": body["video_id"]})
        elif self.path == "/api/download-all":
            # body: {"include": ["watched","skipped","failed"]}
            include = body.get("include", ["watched", "failed"])
            ids = [v["video_id"] for v in list_videos() if v["status"] in include]
            for vid in ids:
                enqueue(vid)
            self._send(200, {"queued": len(ids)})
        elif self.path == "/api/reconcile":
            self._send(200, {"fixed": reconcile()})
        elif self.path == "/api/download-selected":
            for vid in body.get("video_ids", []):
                enqueue(vid)
            self._send(200, {"queued": len(body.get("video_ids", []))})
        else:
            self._send(404, {"error": "not found"})


def main():
    init_db()
    if CONFIG.get("mode") == "transcript":
        reconcile()
    for _ in range(CONFIG.get("concurrent_downloads", 2)):
        threading.Thread(target=worker, daemon=True).start()
    for v in list_videos():  # resume unfinished queue
        if v["status"] == "queued":
            job_queue.put((v["video_id"], v["url"]))

    port = CONFIG["port"]
    print("=" * 60)
    print(f"Watch logger running:  http://127.0.0.1:{port}/")
    print(f"Mode:                  {CONFIG.get('mode')}")
    print(f"Downloads ->           {YTBSD_OUT if CONFIG.get('mode') == 'transcript' else DOWNLOAD_DIR}")
    print(f"Proxies:               {len(CONFIG['proxies']) or 'none (direct)'}")
    print("=" * 60)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
