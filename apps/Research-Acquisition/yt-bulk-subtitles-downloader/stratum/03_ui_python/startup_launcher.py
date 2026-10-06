from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(r"D:\DONT TOUCH BOOT UP\Codex-Powershell_GUI\config\startup_manifest.json")


def is_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


class StartupLauncher(QWidget):
    def __init__(self, manifest_path: Path = DEFAULT_MANIFEST) -> None:
        super().__init__()
        self.manifest_path = manifest_path
        self.manifest = {}
        self.items = []
        self.setWindowTitle("Startup Launcher")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(920, 620)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self.load_manifest()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.title = QLabel("STARTUP / FRONT DOOR")
        self.title.setObjectName("title")
        layout.addWidget(self.title)

        self.subtitle = QLabel("")
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("subtitle")
        layout.addWidget(self.subtitle)

        row = QHBoxLayout()

        self.listing = QListWidget()
        self.listing.currentRowChanged.connect(self._show_current_item)
        row.addWidget(self.listing, 2)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        row.addWidget(self.details, 3)

        layout.addLayout(row, 1)

        buttons = QHBoxLayout()
        self.launch_btn = QPushButton("Launch")
        self.launch_btn.clicked.connect(self.launch_current)
        self.open_file_btn = QPushButton("Open File")
        self.open_file_btn.clicked.connect(self.open_current_file)
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.open_current_folder)
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.clicked.connect(self.load_manifest)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        buttons.addWidget(self.launch_btn)
        buttons.addWidget(self.open_file_btn)
        buttons.addWidget(self.open_folder_btn)
        buttons.addWidget(self.reload_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def load_manifest(self) -> None:
        if not self.manifest_path.exists():
            self.manifest = {
                "title": "Startup Launchers",
                "description": f"Manifest not found: {self.manifest_path}",
                "items": [],
            }
        else:
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        self.items = self.manifest.get("items", [])
        self.title.setText((self.manifest.get("title") or "Startup Launchers").upper())
        self.subtitle.setText(self.manifest.get("description") or "")
        self.listing.clear()

        for item in self.items:
            raw_path = item.get("path", "")
            exists = is_url(raw_path) or Path(raw_path).exists()
            prefix = "OK" if exists else "MISSING"
            path = Path(raw_path) if not is_url(raw_path) else None
            label = f"[{prefix}] {item.get('label', (path.name if path else raw_path) or 'Unnamed')}"
            widget_item = QListWidgetItem(label)
            self.listing.addItem(widget_item)

        if self.items:
            self.listing.setCurrentRow(0)
        else:
            self.details.setPlainText("No startup items found in manifest.")

    def current_item(self) -> dict | None:
        idx = self.listing.currentRow()
        if idx < 0 or idx >= len(self.items):
            return None
        return self.items[idx]

    def _show_current_item(self) -> None:
        item = self.current_item()
        if not item:
            self.details.setPlainText("No item selected.")
            return

        raw_path = item.get("path", "")
        is_web = is_url(raw_path)
        path = Path(raw_path) if not is_web else None
        lines = [
            f"Label: {item.get('label', '')}",
            f"Type: {item.get('type', '')}",
            f"Path: {raw_path}",
            f"Exists: {'Yes' if (is_web or (path and path.exists())) else 'No'}",
            "",
            f"Notes: {item.get('notes', '')}",
        ]
        self.details.setPlainText("\n".join(lines))

    def launch_current(self) -> None:
        item = self.current_item()
        if not item:
            return
        raw_path = item.get("path", "")
        if is_url(raw_path):
            os.startfile(raw_path)
            return
        path = Path(raw_path)
        if not path.exists():
            QMessageBox.warning(self, "Missing File", f"File not found:\n{path}")
            return
        self.launch_path(path)

    def open_current_file(self) -> None:
        item = self.current_item()
        if not item:
            return
        raw_path = item.get("path", "")
        if is_url(raw_path):
            os.startfile(raw_path)
            return
        path = Path(raw_path)
        if path.exists():
            os.startfile(str(path))
        else:
            QMessageBox.warning(self, "Missing File", f"File not found:\n{path}")

    def open_current_folder(self) -> None:
        item = self.current_item()
        if not item:
            return
        raw_path = item.get("path", "")
        if is_url(raw_path):
            QMessageBox.information(self, "Web Item", f"This item is a URL:\n{raw_path}")
            return
        path = Path(raw_path)
        folder = path.parent
        if folder.exists():
            os.startfile(str(folder))
        else:
            QMessageBox.warning(self, "Missing Folder", f"Folder not found:\n{folder}")

    @staticmethod
    def launch_path(path: Path) -> None:
        suffix = path.suffix.lower()
        if suffix == ".ahk":
            subprocess.Popen(["cmd", "/c", "start", "", str(path)], shell=False)
            return
        if suffix in {".bat", ".cmd"}:
            subprocess.Popen(["cmd", "/c", "start", "", str(path)], shell=False)
            return
        if suffix == ".py":
            subprocess.Popen([sys.executable, str(path)], cwd=str(path.parent))
            return
        os.startfile(str(path))


STYLE = """
QWidget { background: #101114; color: #e7e2d8; font-family: Consolas, 'Cascadia Mono', monospace; font-size: 13px; }
#title { color: #ffcc66; font-weight: 700; letter-spacing: 1px; padding: 4px; }
#subtitle { color: #b9b3a7; padding: 0 4px 10px 4px; }
QPlainTextEdit, QListWidget { background: #17191f; border: 1px solid #333845; selection-background-color: #4b3f72; padding: 8px; }
QPushButton { background: #262a33; border: 1px solid #555b6b; padding: 7px 12px; }
QPushButton:hover { background: #343946; }
"""


def main() -> int:
    manifest = DEFAULT_MANIFEST
    if len(sys.argv) > 1:
        manifest = Path(sys.argv[1]).expanduser()
    app = QApplication(sys.argv)
    popup = StartupLauncher(manifest)
    popup.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
