from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_core"))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QListWidget, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget

from action_registry import ActionRegistry
from clipboard_manager import ClipboardManager


class ActionPopup(QWidget):
    def __init__(self, selection: str = "", source_app: str = "") -> None:
        super().__init__()
        self.registry = ActionRegistry()
        self.clipboard = ClipboardManager()
        self.payload = self.clipboard.build_payload(selection=selection, source_app=source_app)
        self.setWindowTitle("Stratum Actions")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(820, 560)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._load_actions()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("STRATUM / ACTION POPUP")
        title.setObjectName("title")
        layout.addWidget(title)

        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("Selected text or clipboard text appears here.")
        self.input_text.setPlainText(self.payload.get("selection") or self.payload.get("clipboard") or "")
        layout.addWidget(self.input_text, 2)

        row = QHBoxLayout()
        self.actions = QListWidget()
        row.addWidget(self.actions, 1)
        self.result = QPlainTextEdit()
        self.result.setPlaceholderText("Action result...")
        row.addWidget(self.result, 2)
        layout.addLayout(row, 4)

        buttons = QHBoxLayout()
        run_btn = QPushButton("Run Action")
        run_btn.clicked.connect(self.run_selected_action)
        copy_btn = QPushButton("Copy Result")
        copy_btn.clicked.connect(self.copy_result)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        buttons.addWidget(run_btn)
        buttons.addWidget(copy_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _load_actions(self) -> None:
        for action in self.registry.list_actions():
            self.actions.addItem(f"{action.id} - {action.name}")
        if self.actions.count():
            self.actions.setCurrentRow(0)

    def run_selected_action(self) -> None:
        item = self.actions.currentItem()
        if item is None:
            self.result.setPlainText("No action selected.")
            return
        action_id = item.text().split(" - ", 1)[0]
        payload = dict(self.payload)
        edited = self.input_text.toPlainText()
        if self.payload.get("selection"):
            payload["selection"] = edited
        else:
            payload["clipboard"] = edited
        try:
            self.result.setPlainText(self.registry.run(action_id, payload))
        except Exception as exc:
            self.result.setPlainText(f"Action failed clearly:\n{type(exc).__name__}: {exc}")

    def copy_result(self) -> None:
        self.clipboard.set_clipboard_text(self.result.toPlainText())


STYLE = """
QWidget { background: #101114; color: #e7e2d8; font-family: Consolas, 'Cascadia Mono', monospace; font-size: 13px; }
#title { color: #ffcc66; font-weight: 700; letter-spacing: 1px; padding: 4px; }
QPlainTextEdit, QListWidget { background: #17191f; border: 1px solid #333845; selection-background-color: #4b3f72; padding: 8px; }
QPushButton { background: #262a33; border: 1px solid #555b6b; padding: 7px 12px; }
QPushButton:hover { background: #343946; }
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", default="")
    parser.add_argument("--selection-file", default="")
    parser.add_argument("--source-app", default="")
    args = parser.parse_args()
    selection = args.selection
    if args.selection_file:
        path = Path(args.selection_file)
        if path.exists():
            selection = path.read_text(encoding="utf-8", errors="replace")
            try:
                path.unlink()
            except OSError:
                pass
    app = QApplication(sys.argv)
    popup = ActionPopup(selection=selection, source_app=args.source_app)
    popup.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
