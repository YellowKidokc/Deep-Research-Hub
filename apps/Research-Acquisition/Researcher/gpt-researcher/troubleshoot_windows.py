#!/usr/bin/env python3
"""Read-only readiness report for the Windows GPT Researcher checkout."""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def present(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    env_file = ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    print("GPT Researcher Windows readiness")
    print(f"Repository : {ROOT}")
    print(f"Python     : {sys.version.split()[0]} ({sys.executable})")
    required = ["fastapi", "uvicorn", "dotenv", "langchain", "mcp"]
    missing = [name for name in required if not present(name)]
    for name in required:
        print(f"Package    : {name:<12} {'OK' if name not in missing else 'MISSING'}")
    keys = ["OPENAI_API_KEY", "DEEPSEEK_API_KEY", "TAVILY_API_KEY"]
    for key in keys:
        print(f"Credential : {key:<20} {'SET' if os.getenv(key) else 'not set'}")
    doc_path = Path(os.getenv("DOC_PATH", ROOT / "my-docs")).expanduser()
    print(f"DOC_PATH   : {doc_path} ({'available' if doc_path.is_dir() else 'not created'})")
    with socket.socket() as probe:
        occupied = probe.connect_ex(("127.0.0.1", 8000)) == 0
    print(f"Port 8000 : {'in use (server may already be running)' if occupied else 'available'}")
    print("MCP note   : local-document mode does not require MCP; MCP is for additional tool/data servers.")
    mcp_file = ROOT / ".mcp.json"
    try:
        json.loads(mcp_file.read_text(encoding="utf-8"))
        print("MCP config : valid JSON")
    except Exception as exc:
        print(f"MCP config : invalid ({exc})")
    print(f"Environment: {'found' if env_file.exists() else 'missing .env; copy .env.example and add the keys you use'}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
