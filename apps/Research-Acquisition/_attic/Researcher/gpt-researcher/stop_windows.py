#!/usr/bin/env python3
"""Stop only the GPT Researcher process recorded by windows_launcher.py."""
from __future__ import annotations

import json
import os
import signal
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".runtime" / "server.json"


def main() -> int:
    if not STATE.exists():
        print("No launcher-owned GPT Researcher process is recorded.")
        return 0
    state = json.loads(STATE.read_text(encoding="utf-8"))
    pid = int(state["pid"])
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        print("The recorded process is no longer running.")
    except PermissionError:
        print(f"Windows refused permission to stop PID {pid}.")
        return 1
    else:
        print(f"Stop requested for launcher-owned GPT Researcher PID {pid}.")
    STATE.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
