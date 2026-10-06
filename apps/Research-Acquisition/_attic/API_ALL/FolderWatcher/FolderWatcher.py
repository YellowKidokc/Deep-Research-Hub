"""
FolderWatcher.py
-----------------
A reusable folder-watcher plugin for Linux and macOS built on watchdog.

Supports:
- Recursive or flat watching
- Optional file-extension filtering
- Debounced callbacks to suppress rapid OS events
- File-stability check (waits until file size stops changing)
- Duplicate-event suppression via (path, mtime, event-type) fingerprinting
- Three return modes: "message", "folder", "files"
- Graceful shutdown on Ctrl+C

Python 3.10+ required.
Install dependency: pip install watchdog
"""

from __future__ import annotations

import threading
import time
import logging
from pathlib import Path
from typing import Callable, Literal

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

ReturnMode = Literal["message", "folder", "files"]

# How many seconds to poll a file waiting for its size to stabilise
_STABILITY_POLL_INTERVAL: float = 0.2
_STABILITY_TIMEOUT: float = 5.0

# System/OS noise files that are never worth reporting
import re

_IGNORED_NAMES: frozenset[str] = frozenset({
    ".DS_Store",         # macOS folder metadata
    "Thumbs.db",         # Windows thumbnail cache
    "desktop.ini",       # Windows folder settings
    ".Spotlight-V100",   # macOS Spotlight index
    ".Trashes",          # macOS trash
    ".fseventsd",        # macOS FSEvents
})

# Name prefixes that are always ignored
_IGNORED_PREFIXES: tuple[str, ...] = (
    "._",    # macOS resource forks
    "~$",    # Microsoft Office temp files
    ".~lock.",  # LibreOffice lock files
)

# Name suffixes that are always ignored
_IGNORED_SUFFIXES: tuple[str, ...] = (
    ".tmp",
    ".swp",   # Vim swap
    ".swo",   # Vim swap
    ".swn",   # Vim swap
    "~",      # Emacs / gedit backup  e.g. file.txt~
)

# Regex patterns matched against the full filename
_IGNORED_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\.sb-[0-9a-f]+-\w+$", re.IGNORECASE),  # macOS safe-save  .sb-XXXXXXXX-YYYYYY
    re.compile(r"^4913$"),                                # Vim temp probe file
)


def _file_is_stable(path: Path, poll_interval: float = _STABILITY_POLL_INTERVAL,
                    timeout: float = _STABILITY_TIMEOUT) -> bool:
    """Return True once the file size has not changed for one polling cycle."""
    deadline = time.monotonic() + timeout
    previous_size = -1
    while time.monotonic() < deadline:
        try:
            current_size = path.stat().st_size
        except OSError:
            return False
        if current_size == previous_size:
            return True
        previous_size = current_size
        time.sleep(poll_interval)
    return False


class _DebouncedHandler(FileSystemEventHandler):
    """
    Internal watchdog event handler.

    Collects raw filesystem events, verifies actual filesystem state,
    deduplicates, waits for file stability, and fires the user callback
    after the debounce window expires.
    """

    def __init__(
        self,
        watch_paths: list[Path],
        callback: Callable,
        return_mode: ReturnMode,
        debounce: float,
        extensions: set[str] | None,
    ) -> None:
        super().__init__()
        self._watch_paths = watch_paths   # all watched roots
        self._callback = callback
        self._return_mode = return_mode
        self._debounce = debounce
        self._extensions = extensions
        self._callback = callback
        self._return_mode = return_mode
        self._debounce = debounce
        self._extensions = extensions

        # Pending changed files: path → highest-priority event type seen so far
        self._pending: dict[Path, str] = {}
        self._pending_lock = threading.Lock()

        # Recently deleted directories: path → expiry time
        # Used to suppress per-file noise when a whole folder is deleted.
        self._deleted_dirs: dict[Path, float] = {}
        self._deleted_dirs_lock = threading.Lock()

        # Fingerprint cache: (str_path, mtime_ns, event_type) → expiry time
        self._seen: dict[tuple[str, int, str], float] = {}
        self._seen_lock = threading.Lock()

        self._timer: threading.Timer | None = None
        self._timer_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Watchdog overrides
    # ------------------------------------------------------------------

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(Path(event.src_path), "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(Path(event.src_path), "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        path = Path(event.src_path)
        if event.is_directory:
            with self._deleted_dirs_lock:
                self._deleted_dirs[path] = time.monotonic() + self._debounce * 3
            self._handle_dir_deleted(path)
        else:
            self._handle(path, "deleted")

    def on_moved(self, event: FileMovedEvent) -> None:
        if not event.is_directory:
            self._handle(Path(event.dest_path), "moved")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_inside_deleted_dir(self, path: Path) -> bool:
        """Return True if path's parent no longer exists (folder was deleted)."""
        if not path.parent.exists():
            return True
        now = time.monotonic()
        with self._deleted_dirs_lock:
            expired = [d for d, exp in self._deleted_dirs.items() if exp < now]
            for d in expired:
                del self._deleted_dirs[d]
            return any(path == d or d in path.parents for d in self._deleted_dirs)

    def _is_ignored(self, path: Path) -> bool:
        """Return True for OS/editor noise files that should never be reported."""
        name = path.name
        if name in _IGNORED_NAMES:
            return True
        if any(name.startswith(p) for p in _IGNORED_PREFIXES):
            return True
        if any(name.endswith(s) for s in _IGNORED_SUFFIXES):
            return True
        if any(pat.search(name) for pat in _IGNORED_PATTERNS):
            return True
        return False

    def _find_watch_root(self, path: Path) -> Path:
        """Return the watched root that contains *path*, or the path itself."""
        for root in self._watch_paths:
            try:
                path.relative_to(root)
                return root
            except ValueError:
                continue
        return path.parent  # fallback

    def _extension_allowed(self, path: Path) -> bool:
        if self._extensions is None:
            return True
        return path.suffix.lower() in self._extensions


        if self._extensions is None:
            return True
        return path.suffix.lower() in self._extensions

    def _is_duplicate(self, path: Path, event_type: str) -> bool:
        """Return True if an identical (path, mtime, event_type) was seen recently."""
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError:
            mtime_ns = 0

        key = (str(path), mtime_ns, event_type)
        now = time.monotonic()
        with self._seen_lock:
            expired = [k for k, exp in self._seen.items() if exp < now]
            for k in expired:
                del self._seen[k]
            if key in self._seen:
                return True
            self._seen[key] = now + self._debounce * 2
            return False

    def _handle_dir_deleted(self, path: Path) -> None:
        """Report a deleted directory (only if it truly no longer exists)."""
        if path.exists():
            return
        if self._is_duplicate(path, "deleted"):
            return
        with self._pending_lock:
            _PRIORITY = {"deleted": 4, "created": 3, "moved": 2, "modified": 1}
            current = self._pending.get(path)
            if current is None or _PRIORITY["deleted"] > _PRIORITY.get(current, 0):
                self._pending[path] = "deleted"
        self._reset_timer()

    def _handle(self, path: Path, event_type: str) -> None:
        if self._is_ignored(path):
            return
        if self._is_inside_deleted_dir(path):
            return
        if not self._extension_allowed(path):
            return

        # Verify actual filesystem state — skip events that don't match reality.
        # This naturally resolves atomic-save noise, spurious macOS pre-delete
        # modified events, and any other OS-level event ordering quirks.
        exists = path.exists()
        if event_type in ("created", "modified") and not exists:
            return
        if event_type == "deleted" and exists:
            return

        if self._is_duplicate(path, event_type):
            return

        # Wait for created/modified files to stop growing before reporting
        if event_type in ("created", "modified"):
            if not _file_is_stable(path):
                logger.debug("Stability timeout for %s, skipping.", path)
                return

        with self._pending_lock:
            _PRIORITY = {"deleted": 4, "created": 3, "moved": 2, "modified": 1}
            current = self._pending.get(path)
            if current is None or _PRIORITY[event_type] > _PRIORITY[current]:
                self._pending[path] = event_type

        self._reset_timer()

    def _reset_timer(self) -> None:
        """Restart the debounce countdown."""
        with self._timer_lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        """Invoke the user callback with the accumulated changed files."""
        with self._pending_lock:
            if not self._pending:
                return
            # Re-verify state at fire time: if a 'deleted' path now exists,
            # it was atomically replaced (delete → create) — report as modified.
            verified = {
                path: ("modified" if etype == "deleted" and path.exists() else etype)
                for path, etype in self._pending.items()
            }
            changed: list[tuple[str, Path]] = [
                (etype, path) for path, etype in sorted(verified.items())
            ]
            self._pending.clear()

        match self._return_mode:
            case "files":
                payload = changed
            case "folder":
                # Return the distinct watched root(s) that contain changed files.
                roots = sorted({self._find_watch_root(p) for _, p in changed})
                payload = roots[0] if len(roots) == 1 else roots
            case "message":
                from collections import Counter
                counts = Counter(etype for etype, _ in changed)
                summary = ", ".join(
                    f"{n} {etype}" for etype, n in sorted(counts.items())
                )
                roots = sorted({self._find_watch_root(p) for _, p in changed})
                roots_str = ", ".join(str(r) for r in roots)
                payload = f"Folder updated: {roots_str} — {summary}"
            case _:
                logger.error("Unknown return_mode %r — skipping callback.", self._return_mode)
                return

        try:
            self._callback(payload)
        except Exception:
            logger.exception("Exception raised inside watcher callback.")


class FolderWatcher:
    """
    Watch one or more folders for filesystem changes and invoke a callback.

    Parameters
    ----------
    path:
        Directory or list of directories to watch.  Accepts a single
        ``str``/``Path`` or a list of them.
    callback:
        Called when one or more files change.  Receives a single argument
        whose type depends on *return_mode*.
    recursive:
        Watch subdirectories as well.  Default: ``True``.
    extensions:
        Optional iterable of file extensions to monitor (e.g. ``[".py", ".txt"]``).
        Pass ``None`` (default) to watch all file types.
    debounce:
        Seconds to wait after the last event before firing the callback.
        Default: ``1.0``.
    return_mode:
        Determines what the callback receives:

        - ``"message"`` – a human-readable string, e.g.
          ``"Folder updated: /some/path — 1 modified"``
        - ``"folder"``  – the affected watched root as a :class:`pathlib.Path`,
          or a list of roots when changes span multiple watched paths.
        - ``"files"``   – a list of ``(event_type, Path)`` tuples.

        Default: ``"files"``.

    Example
    -------
    >>> def on_change(payload):
    ...     print(payload)
    ...
    >>> # Single path
    >>> watcher = FolderWatcher("/tmp/demo", callback=on_change)
    >>>
    >>> # Multiple paths
    >>> watcher = FolderWatcher(["/tmp/a", "/tmp/b"], callback=on_change)
    >>>
    >>> watcher.start()
    >>> # … do other work …
    >>> watcher.stop()
    """

    def __init__(
        self,
        path: str | Path | list[str | Path],
        callback: Callable,
        *,
        recursive: bool = True,
        extensions: list[str] | None = None,
        debounce: float = 1.0,
        return_mode: ReturnMode = "files",
    ) -> None:
        # Normalise to a list of resolved Paths
        raw = path if isinstance(path, list) else [path]
        self._paths: list[Path] = []
        for p in raw:
            resolved = Path(p).resolve()
            if not resolved.is_dir():
                raise ValueError(f"Watch path is not a directory: {resolved}")
            self._paths.append(resolved)

        ext_set: set[str] | None = None
        if extensions is not None:
            ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}"
                       for e in extensions}

        self._handler = _DebouncedHandler(
            watch_paths=self._paths,
            callback=callback,
            return_mode=return_mode,
            debounce=debounce,
            extensions=ext_set,
        )
        self._observer = Observer()
        for p in self._paths:
            self._observer.schedule(self._handler, str(p), recursive=recursive)
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start watching in a background thread."""
        if self._running:
            return
        self._observer.start()
        self._running = True
        for p in self._paths:
            logger.info("FolderWatcher started on %s", p)

    def stop(self) -> None:
        """Stop the observer and wait for the background thread to exit."""
        if not self._running:
            return
        self._observer.stop()
        self._observer.join()
        self._running = False
        logger.info("FolderWatcher stopped.")

    def __enter__(self) -> "FolderWatcher":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Convenience: block until Ctrl+C
    # ------------------------------------------------------------------

    def run_forever(self) -> None:
        """
        Start watching and block the calling thread until Ctrl+C.

        Performs a graceful shutdown on :exc:`KeyboardInterrupt`.
        """
        self.start()
        paths_str = "\n  ".join(str(p) for p in self._paths)
        print(f"Watching:\n  {paths_str}\nPress Ctrl+C to stop.")
        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nInterrupt received, shutting down…")
        finally:
            self.stop()


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def watch(
    path: str | Path | list[str | Path],
    callback: Callable,
    *,
    recursive: bool = True,
    extensions: list[str] | None = None,
    debounce: float = 1.0,
    return_mode: ReturnMode = "files",
) -> None:
    """
    Shorthand: create a :class:`FolderWatcher` and block until Ctrl+C.

    All parameters are forwarded to :class:`FolderWatcher`.
    """
    FolderWatcher(
        path,
        callback,
        recursive=recursive,
        extensions=extensions,
        debounce=debounce,
        return_mode=return_mode,
    ).run_forever()


# ---------------------------------------------------------------------------
# CLI entry point (used by pyproject.toml [project.scripts])
# ---------------------------------------------------------------------------

def _cli_entry() -> None:
    """
    Minimal command-line interface::

        folder-watcher <path> [mode] [debounce]

    Examples::

        folder-watcher /tmp/demo
        folder-watcher /tmp/demo message
        folder-watcher /tmp/demo files 0.5
    """
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    args = sys.argv[1:]
    if not args:
        print("Usage: folder-watcher <path> [mode=files|folder|message] [debounce=1.0]")
        sys.exit(1)

    watch_path = Path(args[0])
    mode: ReturnMode = args[1] if len(args) > 1 else "files"  # type: ignore[assignment]
    debounce = float(args[2]) if len(args) > 2 else 1.0

    def _default_cb(payload: object) -> None:
        print(payload)

    watch(watch_path, _default_cb, return_mode=mode, debounce=debounce)


