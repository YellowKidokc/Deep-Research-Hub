from __future__ import annotations

import subprocess
from datetime import datetime, timezone


def _run_powershell(script: str) -> str:
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=3)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "PowerShell clipboard command failed")
    return completed.stdout


class ClipboardManager:
    def __init__(self, slots: int = 75) -> None:
        self.slots: list[str] = [""] * slots

    def get_clipboard_text(self) -> str:
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is not None:
                return app.clipboard().text() or ""
        except Exception:
            pass
        try:
            import pyperclip
            return pyperclip.paste() or ""
        except Exception:
            pass
        return _run_powershell("Get-Clipboard -Raw")

    def set_clipboard_text(self, text: str) -> None:
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is not None:
                app.clipboard().setText(text)
                return
        except Exception:
            pass
        try:
            import pyperclip
            pyperclip.copy(text)
            return
        except Exception:
            pass
        escaped = text.replace("'", "''")
        _run_powershell(f"Set-Clipboard -Value '{escaped}'")

    def build_payload(self, selection: str = "", source_app: str = "") -> dict[str, str]:
        clipboard = self.get_clipboard_text()
        return {
            "selection": selection or "",
            "clipboard": clipboard or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_app": source_app or "",
        }

    def best_text(self, payload: dict[str, str]) -> str:
        return payload.get("selection") or payload.get("clipboard") or ""
