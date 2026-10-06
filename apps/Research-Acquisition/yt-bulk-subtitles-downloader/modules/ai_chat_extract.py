"""
AI Chat Conversation Extractor
Extracts full conversation text from Claude Desktop and ChatGPT Desktop
using Chrome DevTools Protocol (both are Electron/Chromium apps).

Usage:
    python ai_chat_extract.py              → extract from active AI chat, clipboard it
    python ai_chat_extract.py --file       → also save to E:\Exports\Conversations
    python ai_chat_extract.py --app claude → target specific app
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

EXPORT_DIR = Path(r"E:\Exports\Conversations")

# CDP ports — Electron apps need --remote-debugging-port at launch.
# We'll try common ports and also scan for the debug endpoint.
CDP_PORTS = {
    "claude": [9222, 9223, 9229],
    "chatgpt": [9224, 9225],
}

# JS to extract conversation text from each app's DOM
EXTRACT_JS = {
    "claude": r"""
(() => {
    // Claude uses data-testid or role-based selectors
    const msgs = document.querySelectorAll(
        '[data-testid*="message"], .prose, .font-claude-message, ' +
        '[class*="Message"], [class*="message-content"], ' +
        '.mx-auto .grid > div'
    );
    if (msgs.length > 0) {
        return Array.from(msgs).map(m => m.innerText.trim()).filter(Boolean).join('\n\n---\n\n');
    }
    // Fallback: grab the main conversation container
    const main = document.querySelector('main') || document.querySelector('[role="main"]');
    if (main) return main.innerText;
    return document.body.innerText;
})()
""",
    "chatgpt": r"""
(() => {
    // ChatGPT uses data-message-author-role
    const msgs = document.querySelectorAll(
        '[data-message-author-role], [class*="markdown"], ' +
        '.text-message, .agent-turn, .user-turn'
    );
    if (msgs.length > 0) {
        return Array.from(msgs).map(m => {
            const role = m.getAttribute('data-message-author-role') || '';
            const prefix = role === 'user' ? 'USER: ' : role === 'assistant' ? 'ASSISTANT: ' : '';
            return prefix + m.innerText.trim();
        }).filter(Boolean).join('\n\n---\n\n');
    }
    const main = document.querySelector('main') || document.querySelector('[role="main"]');
    if (main) return main.innerText;
    return document.body.innerText;
})()
""",
}


def get_foreground_info() -> tuple[int, str, str]:
    """Return (hwnd, process_name, window_title) of foreground window."""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    
    try:
        import psutil
        proc = psutil.Process(pid.value)
        pname = proc.name().lower()
    except Exception:
        # Fallback without psutil
        try:
            r = subprocess.run(
                ["wmic", "process", "where", f"ProcessId={pid.value}", "get", "Name", "/value"],
                capture_output=True, text=True, timeout=3
            )
            for line in r.stdout.splitlines():
                if line.startswith("Name="):
                    pname = line.split("=", 1)[1].strip().lower()
                    break
            else:
                pname = ""
        except Exception:
            pname = ""
    
    length = user32.GetWindowTextLengthW(hwnd) + 1
    buf = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buf, length)
    return hwnd, pname, buf.value


def detect_app(pname: str, title: str) -> str | None:
    if "claude" in pname:
        return "claude"
    if "chatgpt" in pname:
        return "chatgpt"
    tl = title.lower()
    if "claude" in tl:
        return "claude"
    if "chatgpt" in tl:
        return "chatgpt"
    return None


def try_cdp_extract(app: str) -> str | None:
    """Try to connect via CDP and run JS extraction."""
    for port in CDP_PORTS.get(app, [9222]):
        try:
            url = f"http://127.0.0.1:{port}/json"
            with urllib.request.urlopen(url, timeout=2) as resp:
                targets = json.loads(resp.read())
            # Find a page target
            for t in targets:
                if t.get("type") == "page":
                    ws_url = t.get("webSocketDebuggerUrl", "")
                    if ws_url:
                        return _cdp_eval(ws_url, app)
        except Exception:
            continue
    return None


def _cdp_eval(ws_url: str, app: str) -> str | None:
    """Evaluate JS via CDP WebSocket."""
    try:
        import websocket
        ws = websocket.create_connection(ws_url, timeout=5)
        msg = json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": EXTRACT_JS.get(app, EXTRACT_JS["claude"]),
                "returnByValue": True,
            }
        })
        ws.send(msg)
        result = json.loads(ws.recv())
        ws.close()
        value = result.get("result", {}).get("result", {}).get("value", "")
        return value if value else None
    except ImportError:
        return None
    except Exception:
        return None


def extract_via_accessibility(hwnd: int) -> str:
    """Last resort: use Win32 accessibility to get window text."""
    try:
        import comtypes.client
        uia = comtypes.client.CreateObject(
            "{ff48dba4-60ef-4201-aa87-54103eef594e}",
        )
        elem = uia.ElementFromHandle(hwnd)
        if elem:
            name = elem.CurrentName or ""
            # Try to get full document text via Value pattern
            return name
    except Exception:
        pass
    return ""


def clipboard_set(text: str) -> None:
    """Put text on the Windows clipboard."""
    import ctypes
    CF_UNICODETEXT = 13
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    user32.OpenClipboard(0)
    user32.EmptyClipboard()
    
    encoded = text.encode("utf-16-le") + b"\x00\x00"
    h = kernel32.GlobalAlloc(0x0042, len(encoded))  # GMEM_MOVEABLE | GMEM_ZEROINIT
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, encoded, len(encoded))
    kernel32.GlobalUnlock(h)
    user32.SetClipboardData(CF_UNICODETEXT, h)
    user32.CloseClipboard()


def save_to_file(app: str, title: str, text: str) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:80].strip() or "conversation"
    path = EXPORT_DIR / f"{stamp}_{app}_{safe_title}.md"
    
    md = f"---\ntitle: \"{title}\"\napp: {app}\ncaptured: {datetime.now().isoformat()}\ntype: ai_chat_extract\n---\n\n"
    md += f"# {title}\n\n{text}\n"
    path.write_text(md, encoding="utf-8")
    return path


def main() -> int:
    save_file = "--file" in sys.argv
    force_app = None
    if "--app" in sys.argv:
        idx = sys.argv.index("--app")
        if idx + 1 < len(sys.argv):
            force_app = sys.argv[idx + 1].lower()
    
    hwnd, pname, title = get_foreground_info()
    app = force_app or detect_app(pname, title)
    
    if not app:
        print("Not an AI chat window.", file=sys.stderr)
        return 1
    
    print(f"Detected: {app} | {title}")
    
    # Try CDP first
    text = try_cdp_extract(app)
    if text and len(text.strip()) > 50:
        print(f"CDP extract: {len(text)} chars")
    else:
        # Fallback: plain Ctrl+A Ctrl+C with longer wait
        print("CDP unavailable, falling back to clipboard capture")
        text = None
    
    if not text:
        # Last resort — just do the copy but with a scroll-first approach
        print("Using scroll+copy fallback")
        # Send Ctrl+Home first to scroll to top, then Ctrl+A Ctrl+C
        import ctypes
        user32 = ctypes.windll.user32
        # Bring window to front
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.15)
        
        # We'll use SendInput to send keystrokes
        _send_keys([
            ("ctrl", "Home"),   # scroll to top
        ])
        time.sleep(0.5)
        _send_keys([
            ("ctrl", "a"),      # select all
        ])
        time.sleep(0.3)
        _send_keys([
            ("ctrl", "c"),      # copy
        ])
        time.sleep(0.5)
        
        # Read clipboard
        user32.OpenClipboard(0)
        try:
            h = user32.GetClipboardData(13)  # CF_UNICODETEXT
            if h:
                kernel32 = ctypes.windll.kernel32
                p = kernel32.GlobalLock(h)
                text = ctypes.wstring_at(p) if p else ""
                kernel32.GlobalUnlock(h)
            else:
                text = ""
        finally:
            user32.CloseClipboard()
    
    if not text or len(text.strip()) < 10:
        print("Extraction failed — no text captured.", file=sys.stderr)
        return 1
    
    clipboard_set(text)
    print(f"Clipboard set: {len(text)} chars")
    
    if save_file:
        path = save_to_file(app, title, text)
        print(f"Saved: {path}")
    
    return 0


def _send_keys(combos):
    """Send key combos via SendInput."""
    import ctypes
    
    VK = {
        "ctrl": 0x11, "shift": 0x10, "alt": 0x12,
        "Home": 0x24, "End": 0x23,
        "a": 0x41, "c": 0x43,
    }
    
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.wintypes.WORD),
            ("wScan", ctypes.wintypes.WORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]
    
    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _fields_ = [("type", ctypes.wintypes.DWORD), ("_input", _INPUT)]
    
    def make_input(vk, up=False):
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp._input.ki.wVk = vk
        inp._input.ki.dwFlags = KEYEVENTF_KEYUP if up else 0
        return inp
    
    for combo in combos:
        modifiers = combo[:-1]
        key = combo[-1]
        inputs = []
        for mod in modifiers:
            inputs.append(make_input(VK[mod]))
        inputs.append(make_input(VK[key]))
        inputs.append(make_input(VK[key], up=True))
        for mod in reversed(modifiers):
            inputs.append(make_input(VK[mod], up=True))
        
        arr = (INPUT * len(inputs))(*inputs)
        ctypes.windll.user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))
        time.sleep(0.05)


if __name__ == "__main__":
    raise SystemExit(main())
