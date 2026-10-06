"""Lossless Meaning Packet action.

This is the Stratum popup bridge for the local lossless prompt compressor.
It takes selected text, builds a compact AI handoff packet, and returns it to
the popup so David can copy it into Kimi/Codex/DeepSeek/etc.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL_PATH = Path(r"D:\GitHub\Python-WEB\lossless-prompt-compressor\lossless_prompt_tool.py")


def _load_tool():
    if not TOOL_PATH.exists():
        raise FileNotFoundError(f"Lossless compressor not found: {TOOL_PATH}")
    spec = importlib.util.spec_from_file_location("lossless_prompt_tool", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import lossless compressor: {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def process(data: dict) -> str:
    text = (data.get("selection") or data.get("clipboard") or "").strip()
    if not text:
        return "Lossless Meaning Packet: nothing selected. Select text or copy text first, then run again."

    tool = _load_tool()
    source = data.get("source_app") or "stratum-popup-selection"
    packet = tool.make_packet(text, source_name=source, include_literal=False, compact=True)

    return (
        packet
        + "\n\n<!-- STRATUM_POPUP_NOTE: local semantic-lossless packet; "
        + "use literal mode in the standalone tool if exact byte recovery is required. -->\n"
    )
