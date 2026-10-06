<div align="center">

# 📁👀 FolderWatcher

### *Your folders, but they finally text you back.*

**A tiny, battle-tested Python plugin that watches your folders and fires a callback the instant a file is born, changed, or vanishes.**

Built for **RAG pipelines**, document ingestion, and any workflow that hates stale data.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)
![Dependency](https://img.shields.io/badge/deps-just%20watchdog-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

</div>

---

## ⚡ 30-Second Taste

```python
from FolderWatcher import FolderWatcher

def on_change(changed):
    for event, path in changed:
        print(f"{event}: {path}")

FolderWatcher("/my/docs", callback=on_change).run_forever()
```

```text
created:  /my/docs/notes.txt
modified: /my/docs/report.pdf
deleted:  /my/docs/old.md
```

That's it. No polling loops, no cron jobs, no cleanup. Just changes → your code. 🎯

---

## 🤔 Why Should You Care?

### The RAG Staleness Trap

Your vector store is only as fresh as the files behind it. Edit one PDF and suddenly your LLM is quoting yesterday's news:

```
User edits report.pdf
        │
        ▼
  Vector store still has    ←── 😬 LLM retrieves
  old chunks from report.pdf     outdated context
```

Re-indexing everything on a timer? That's burning compute to fix a problem you didn't have to create. What you *actually* want is **event-driven re-indexing** — touch the pipeline only when something truly changed:

```
User edits report.pdf
        │
        ▼
  FolderWatcher detects change
        │
        ▼
  Your callback: re-embed ONLY report.pdf  ←── ⚡ fast, 💸 cheap, 🎯 accurate
        │
        ▼
  Vector store updated                     ←── ✅ LLM retrieves fresh context
```

FolderWatcher exists for exactly this: **reliable, low-noise, event-driven detection** you can trust in production.

---

## ✨ What Makes It Nice

| | Feature | What you get |
|---|---|---|
| 🗂️ | **Multi-path watching** | One instance, many folders |
| 🌲 | **Recursive or flat** | Descend into subdirs, or don't |
| 🔎 | **Extension filtering** | React only to `.pdf`, `.md`, `.txt`… |
| ⏱️ | **Debouncing** | Collapses OS event bursts into one clean call |
| 🧬 | **Deduplication** | Fingerprints `(path, mtime, event)` — no double-fires |
| 🛡️ | **State verification** | Immune to macOS atomic-save noise |
| 🧊 | **Stability check** | Waits for the write to *finish* before firing |
| 🗑️ | **Deletion awareness** | Kills per-file spam when a whole folder is nuked |
| 🔇 | **Noise filtering** | Ignores `.DS_Store`, `~$`, `.swp`, resource forks & friends |
| 🎛️ | **Three payload modes** | `"files"`, `"folder"`, or `"message"` |
| 🧯 | **Graceful shutdown** | Ctrl+C safe, context-manager friendly |
| 🪶 | **Featherweight** | Two threads, main loop sleeps — CPU barely notices |

---

## 📦 Install

```bash
pip install -r requirements.txt   # just watchdog
pip install .                     # adds the package + `folder-watcher` CLI
```

Requirements: **Python 3.10+**, macOS or Linux, and [`watchdog`](https://pypi.org/project/watchdog/) ≥ 4.0.0.

---

## 🚀 Quick Start

Grab `quickstart.py` — it's the whole integration in a nutshell:

```python
import sys
from pathlib import Path
from FolderWatcher import FolderWatcher


def my_function(changed: list[tuple[str, Path]]) -> None:
    """Swap in your own logic here."""
    for event_type, path in changed:
        print(f"{event_type}: {path}")


folder = sys.argv[1] if len(sys.argv) > 1 else "."
FolderWatcher(path=folder, callback=my_function, return_mode="files").run_forever()
```

```bash
python3 quickstart.py /path/to/watch
```

---

## 🧠 The RAG Pipeline Money Shot

```python
from pathlib import Path
from FolderWatcher import FolderWatcher

def on_docs_changed(changed: list[tuple[str, Path]]) -> None:
    for event_type, path in changed:
        if event_type in ("created", "modified"):
            print(f"Re-embedding: {path}")
            # your_vector_store.upsert(path)
        elif event_type == "deleted":
            print(f"Removing from index: {path}")
            # your_vector_store.delete(path)

FolderWatcher(
    path=["/data/documents", "/data/reports"],   # watch many at once
    callback=on_docs_changed,
    recursive=True,
    extensions=[".pdf", ".md", ".txt", ".docx"],
    debounce=1.0,
    return_mode="files",
).run_forever()
```

Only touched files get re-embedded. Your GPU thanks you. 💚

---

## 🎨 Pick Your Payload Style

Same watcher, three flavors of callback data — choose whatever your code likes best:

| Mode | You receive | Example |
|---|---|---|
| `"files"` | `list[tuple[str, Path]]` | `[("modified", Path("/docs/a.pdf"))]` |
| `"folder"` | `Path` or `list[Path]` | `Path("/data/documents")` |
| `"message"` | `str` | `"Folder updated: /docs — 1 created, 2 modified"` |

---

## 🧩 Other Ways to Wire It In

```python
# Context manager — auto-stops when the block ends
with FolderWatcher("/path/to/watch", callback=on_change):
    time.sleep(60)

# Manual start / stop
watcher = FolderWatcher("/path/to/watch", callback=on_change)
watcher.start()
# ... your app runs ...
watcher.stop()

# One-liner convenience helper
from FolderWatcher import watch
watch("/path/to/watch", lambda msg: print(msg), return_mode="message")
```

---

## 🖥️ Run It in the Background (macOS)

**Right now, this session:**
```bash
nohup python3 quickstart.py /your/folder > watcher.log 2>&1 &
echo $!   # save this PID to stop it later
```

**Forever, from login (launchd):**
```bash
cat > ~/Library/LaunchAgents/com.folderwatcher.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.folderwatcher</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>/path/to/quickstart.py</string>
    <string>/your/folder</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/folderwatcher.log</string>
  <key>StandardErrorPath</key><string>/tmp/folderwatcher.log</string>
</dict></plist>
EOF

launchctl load ~/Library/LaunchAgents/com.folderwatcher.plist
```

---

## ⌨️ CLI in One Line

After `pip install .`:
```bash
folder-watcher /path/to/watch
folder-watcher /path/to/watch message
folder-watcher /path/to/watch files 0.5   # 0.5s debounce
```

---

## 🔬 Under the Hood

FolderWatcher wraps `watchdog` and runs every raw OS event through a gauntlet before it ever reaches you:

```
raw OS event (FSEvents / inotify)
        │
        ▼
  ① Ignore junk?  .DS_Store · .swp · ~$ · .sb-* · …    ──► drop
  ② Inside a deleted directory?                        ──► drop
  ③ Extension allowed?                                 ──► drop
  ④ Verify filesystem state at event time              ──► drop
  ⑤ Duplicate? (path + mtime_ns + event_type)          ──► drop
  ⑥ File stable? (size unchanged across two polls)     ──► drop
  ⑦ Add to pending  { path → highest-priority event }
  ⑧ Reset debounce timer  ◄── resets on every new event
        │  (quiet for `debounce` seconds)
        ▼
  ⑨ _fire() → format payload → your callback  ✅
```

Result: **clean, deduplicated, verified events** — not a firehose of OS noise.

---

## 📖 API Reference

### `FolderWatcher(path, callback, *, recursive, extensions, debounce, return_mode)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str \| Path \| list[str \| Path]` | required | One or more directories to watch |
| `callback` | `Callable` | required | Fired on change; payload shaped by `return_mode` |
| `recursive` | `bool` | `True` | Watch subdirectories |
| `extensions` | `list[str] \| None` | `None` | Filter by extension, e.g. `[".pdf", ".md"]`. `None` = all |
| `debounce` | `float` | `1.0` | Seconds of quiet after the last event before firing |
| `return_mode` | `str` | `"files"` | Shape of the callback payload |

**Event types:** `"created"` · `"modified"` · `"deleted"` · `"moved"`

**Methods:**
```python
watcher.start()        # start background observer (non-blocking)
watcher.stop()         # stop and join
watcher.run_forever()  # start + block until Ctrl+C
```

---

## 🔇 Noise It Silently Swallows

Ignored no matter your extension filters:

| Pattern | Example | Why |
|---|---|---|
| `.DS_Store` | `.DS_Store` | macOS Finder metadata |
| `._*` prefix | `._myfile.txt` | macOS resource forks |
| `.sb-*` suffix | `file.rtf.sb-ca0e059b-dfz` | macOS safe-save temp |
| `~$` prefix | `~$document.docx` | MS Office temp |
| `.~lock.` prefix | `.~lock.file.odt#` | LibreOffice lock |
| `*.tmp` / `*.swp` / `*~` | `file.tmp` | Editor temp / backup |
| `Thumbs.db` / `desktop.ini` | — | Windows system files |

---

## 🗺️ Project Structure

```
FolderWatcher/
├── FolderWatcher.py    # self-contained plugin — copy or import this
├── quickstart.py       # minimal integration example
├── requirements.txt    # watchdog>=4.0.0
├── pyproject.toml      # package metadata + CLI entry point
├── llms.txt            # AI-readable project summary
└── README.md
```

---

## ❓ FAQ

<details>
<summary><strong>Does it work on Windows?</strong></summary>

Designed and tested for **macOS and Linux**. Windows noise files (`Thumbs.db`, `desktop.ini`) are filtered out, but Windows is not a supported target.
</details>

<details>
<summary><strong>How do I watch multiple folders?</strong></summary>

Pass a list to `path`, e.g. `FolderWatcher(["/a", "/b"], callback=cb)`.
</details>

<details>
<summary><strong>How do I only react to certain file types?</strong></summary>

Set `extensions=[".pdf", ".md"]`. Everything else is ignored. Omit it to watch all files.
</details>

<details>
<summary><strong>Will I get called before a big file finishes writing?</strong></summary>

No. The file-stability check waits until the size stops changing (up to 5s) before reporting — so you never touch a half-written file.
</details>

<details>
<summary><strong>How do I reduce chattiness on bursty writes?</strong></summary>

Increase `debounce` (in seconds). Rapid event bursts collapse into a single callback after that much quiet.
</details>

<details>
<summary><strong>How do I run it without blocking?</strong></summary>

Use `.start()` / `.stop()` instead of `run_forever()`, or the `with FolderWatcher(...)` context manager.
</details>

<details>
<summary><strong>What does the callback receive?</strong></summary>

Depends on `return_mode`: a list of `(event_type, Path)` tuples (`"files"`), a `Path`/list of roots (`"folder"`), or a summary string (`"message"`).
</details>

---

<div align="center">

**Built for people who'd rather ship features than babysit file timestamps.**

Give it a folder. Give it a callback. Go build something. 🚀

*MIT licensed — take it, fork it, ship it.*

</div>
