#!/usr/bin/env python3
"""Portable Windows launcher for GPT Researcher and local-document mode."""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
LAST_DOC_PATH = ROOT / "LOCAL_DOCUMENTS_PATH.txt"
RESEARCH_PROFILE = ROOT / "RESEARCH_PROFILE.env"
PROVIDERS = ROOT / "PROVIDERS.env"
URL = "http://127.0.0.1:8000"


def choose_folder() -> Path | None:
    import tkinter as tk
    from tkinter import filedialog

    saved = read_saved_folder()
    initial = str(saved) if saved else str(ROOT)
    app = tk.Tk(); app.withdraw(); app.attributes("-topmost", True)
    selected = filedialog.askdirectory(title="Choose the local documents folder", initialdir=initial)
    app.destroy()
    return Path(selected).resolve() if selected else None


def read_saved_folder() -> Path | None:
    if not LAST_DOC_PATH.exists():
        return None
    for line in LAST_DOC_PATH.read_text(encoding="utf-8-sig").splitlines():
        value = line.strip().strip('"')
        if value and not value.startswith("#"):
            path = Path(value).expanduser().resolve()
            return path if path.is_dir() else None
    return None


def save_folder(path: Path) -> None:
    LAST_DOC_PATH.write_text(str(path.resolve()) + "\n", encoding="utf-8")


def apply_research_profile(env: dict[str, str]) -> None:
    """Load non-secret KEY=VALUE research-depth settings."""
    if not RESEARCH_PROFILE.exists():
        return
    for raw_line in RESEARCH_PROFILE.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key and value:
            env[key] = value


def apply_providers(env: dict[str, str]) -> None:
    """Provider choices (no keys); anything already set wins."""
    if not PROVIDERS.exists():
        return
    for raw_line in PROVIDERS.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key and value:
            env.setdefault(key, value)


def healthy() -> bool:
    try:
        with urllib.request.urlopen(URL + "/docs", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def port_in_use() -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", 8000)) == 0


def python_command() -> str:
    candidates = [ROOT / ".venv" / "Scripts" / "python.exe", ROOT / "venv" / "Scripts" / "python.exe"]
    return str(next((path for path in candidates if path.is_file()), Path(sys.executable)))


def stop_managed_server_if_needed(mode: str, doc_path: Path | None) -> None:
    state_file = RUNTIME / "server.json"
    if not healthy() or not state_file.exists():
        return
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        same = state.get("mode") == mode and state.get("doc_path") == (str(doc_path) if doc_path else None)
        if same:
            return
        pid = int(state["pid"])
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        for _ in range(20):
            if not healthy():
                return
            time.sleep(0.25)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return


def start(mode: str, no_browser: bool = False, documents: str | None = None) -> int:
    env = os.environ.copy()
    apply_providers(env)
    apply_research_profile(env)
    doc_path = None
    if mode == "local":
        doc_path = Path(documents).expanduser().resolve() if documents else read_saved_folder()
        if doc_path is None:
            doc_path = choose_folder()
        if doc_path is None:
            print("No folder selected; nothing was started.")
            return 1
        if not doc_path.is_dir():
            print(f"Document folder does not exist: {doc_path}")
            return 1
        RUNTIME.mkdir(exist_ok=True)
        save_folder(doc_path)
        env["DOC_PATH"] = str(doc_path)
        # Local documents are a first-class source. MCP is not required for them.
        env.setdefault("RETRIEVER", "tavily")

    stop_managed_server_if_needed(mode, doc_path)
    if not healthy():
        if port_in_use():
            print("Port 8000 is occupied by another program. Run TROUBLESHOOT_GPT_RESEARCHER.bat.")
            return 2
        RUNTIME.mkdir(exist_ok=True)
        log = (RUNTIME / "server.log").open("ab")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = subprocess.Popen(
            [python_command(), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT, env=env, stdout=log, stderr=log, creationflags=flags,
        )
        (RUNTIME / "server.json").write_text(json.dumps({"pid": process.pid, "mode": mode, "doc_path": str(doc_path) if doc_path else None}, indent=2), encoding="utf-8")
        for _ in range(45):
            if healthy():
                break
            if process.poll() is not None:
                print(f"GPT Researcher exited with code {process.returncode}. See {RUNTIME / 'server.log'}")
                return process.returncode or 3
            time.sleep(1)
        else:
            print(f"GPT Researcher did not become ready. See {RUNTIME / 'server.log'}")
            return 3

    if not no_browser:
        webbrowser.open(URL)
    print(f"GPT Researcher is ready at {URL}")
    if mode == "local":
        print(f"Local documents: {doc_path}")
        print('In the page, choose "My Documents" as the Report Source.')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["standard", "local"], nargs="?", default="standard")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--documents", help="Save and use this recursive local-document folder")
    args = parser.parse_args()
    return start(args.mode, args.no_browser, args.documents)


if __name__ == "__main__":
    raise SystemExit(main())
