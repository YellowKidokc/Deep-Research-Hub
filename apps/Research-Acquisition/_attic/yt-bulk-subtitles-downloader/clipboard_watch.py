from __future__ import annotations

import configparser
import ctypes
import ctypes.wintypes
import json
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE = Path(r"D:\DONT TOUCH BOOT UP\AHK")
CONFIG_DIR = BASE / "config"
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SERVICES_INI = CONFIG_DIR / "services.ini"
BRIDGE_INI = CONFIG_DIR / "bridge.ini"
LOG_FILE = LOG_DIR / "clipboard_watch.log"

CF_UNICODETEXT = 13

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.OpenClipboard.argtypes = [ctypes.wintypes.HWND]
user32.OpenClipboard.restype = ctypes.wintypes.BOOL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = ctypes.wintypes.BOOL
user32.GetClipboardData.argtypes = [ctypes.wintypes.UINT]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.GetClipboardSequenceNumber.argtypes = []
user32.GetClipboardSequenceNumber.restype = ctypes.wintypes.DWORD
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = ctypes.wintypes.BOOL


def setup_logging() -> None:
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def _truthy(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> tuple[bool, str, float, int, float, float]:
    services = configparser.ConfigParser()
    services.read(SERVICES_INI, encoding="utf-8")
    active = services.get("CLIPBOARD", "active", fallback="local")
    base_url = services.get("CLIPBOARD", active, fallback="http://127.0.0.1:3456").rstrip("/")

    bridge = configparser.ConfigParser()
    bridge.read(BRIDGE_INI, encoding="utf-8")
    enabled = _truthy(bridge.get("clipboard", "watch_enabled", fallback="0"), default=False)
    poll_ms = bridge.getint("clipboard", "poll_ms", fallback=800)
    read_retries = bridge.getint("clipboard", "read_retries", fallback=5)
    read_retry_ms = bridge.getint("clipboard", "read_retry_ms", fallback=50)
    settle_ms = bridge.getint("clipboard", "settle_ms", fallback=150)

    return (
        enabled,
        base_url,
        max(poll_ms / 1000.0, 0.25),
        max(read_retries, 1),
        max(read_retry_ms / 1000.0, 0.01),
        max(settle_ms / 1000.0, 0.0),
    )


def get_clipboard_sequence() -> int:
    return int(user32.GetClipboardSequenceNumber())


def read_clipboard_text(retries: int = 5, retry_s: float = 0.05) -> str:
    """Read Unicode text without holding the clipboard longer than needed.

    Retries briefly when another app (Ditto, ExtraClipboard, Office) already
    owns the clipboard so we never block Ctrl+C / Ctrl+V.
    """
    text = ""
    for attempt in range(retries):
        opened = bool(user32.OpenClipboard(None))
        if not opened:
            time.sleep(retry_s)
            continue
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            locked = kernel32.GlobalLock(handle)
            if not locked:
                return ""
            try:
                text = ctypes.wstring_at(locked) or ""
            finally:
                kernel32.GlobalUnlock(handle)
            return text
        finally:
            user32.CloseClipboard()
    return text


def clip_title(content: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return "Clipboard"


def post_clip(base_url: str, content: str) -> None:
    payload = json.dumps(
        {
            "content": content,
            "title": clip_title(content),
            "category": "clipboard",
            "tags": ["history"],
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        base_url + "/api/clips",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=3) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"unexpected status {resp.status}")


def run_forever() -> None:
    setup_logging()
    enabled, base_url, poll_s, retries, retry_s, settle_s = load_config()
    if not enabled:
        logging.info(
            "watcher disabled via bridge.ini [clipboard] watch_enabled=0 | "
            "sync_server UI stays up without grabbing the OS clipboard"
        )
        return

    last_seq = get_clipboard_sequence()
    last_text = read_clipboard_text(retries=retries, retry_s=retry_s)
    logging.info(
        "watcher start | base_url=%s | poll_s=%.2f | settle_s=%.2f",
        base_url,
        poll_s,
        settle_s,
    )

    while True:
        try:
            # Hot-reload disable without restarting the whole server.
            enabled, base_url, poll_s, retries, retry_s, settle_s = load_config()
            if not enabled:
                logging.info("watcher disabled at runtime; exiting thread")
                return

            seq = get_clipboard_sequence()
            if seq != last_seq:
                # Let the app that owns the copy finish before we OpenClipboard.
                if settle_s:
                    time.sleep(settle_s)
                seq = get_clipboard_sequence()
                last_seq = seq
                text = read_clipboard_text(retries=retries, retry_s=retry_s)
                if text and text != last_text:
                    post_clip(base_url, text)
                    last_text = text
                    logging.info("post ok | title=%s", clip_title(text))
            time.sleep(poll_s)
        except urllib.error.URLError as exc:
            logging.warning("post fail | %s", exc)
            time.sleep(max(poll_s, 1.0))
        except Exception as exc:
            logging.exception("watcher error | %s", exc)
            time.sleep(max(poll_s, 1.0))


def main() -> None:
    run_forever()


if __name__ == "__main__":
    main()
