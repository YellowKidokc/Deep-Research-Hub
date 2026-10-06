from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from re import sub

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QUrl

from link_research_engine.modules.dedupe import dedupe_rows
from link_research_engine.modules.discovery import DiscoveryRequest, discover_links
from link_research_engine.modules.exporter import ensure_output_dir, write_csv_rows


TARGET_TYPES = [
    "single_case",
    "category",
    "person",
    "organization",
    "topic",
    "keyword_cluster",
    "link_list",
    "domain",
]

INTENTS = [
    "aggregate_sources",
    "define_it",
    "find_best_evidence",
    "find_outgoing_links",
    "rip_site",
]

SCOPES = [
    "wikipedia_only",
    "trusted_hubs",
    "mixed",
]

DEPTHS = [
    "top_10",
    "top_25",
    "top_50",
    "top_100",
    "top_200",
]

OUTPUTS = [
    "source_inventory",
    "link_list",
    "workbook",
    "package_json",
]

ORGS = [
    "by_case",
    "by_source_type",
    "by_domain",
    "by_confidence",
]


def _slug(text: str) -> str:
    collapsed = sub(r"[^a-zA-Z0-9]+", "_", text.strip()).strip("_")
    return collapsed.lower() or "case"


class IntakeWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.output_dir = Path("data/output")
        self.last_summary_path: Path | None = None
        self.setWindowTitle("Link Research Engine")
        self.resize(1450, 980)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(10)

        topbar = QHBoxLayout()
        title = QLabel("LINK RESEARCH ENGINE")
        title.setObjectName("titleLabel")
        subtitle = QLabel("INTAKE + DISCOVERY + REVIEW")
        subtitle.setObjectName("subtitleLabel")
        left = QVBoxLayout()
        left.setSpacing(0)
        left.addWidget(title)
        left.addWidget(subtitle)
        topbar.addLayout(left)
        topbar.addStretch()
        self.status_label = QLabel("ready")
        self.status_label.setObjectName("statusLabel")
        topbar.addWidget(self.status_label)
        outer.addLayout(topbar)

        self.tabs = QTabWidget()
        self.intake_tab = QWidget()
        self.links_tab = QWidget()
        self.log_tab = QWidget()
        self.tabs.addTab(self.intake_tab, "INTAKE")
        self.tabs.addTab(self.links_tab, "LINKS")
        self.tabs.addTab(self.log_tab, "LOG")
        outer.addWidget(self.tabs, 1)
        self.setCentralWidget(central)

        self._build_intake_tab()
        self._build_links_tab()
        self._build_log_tab()

    def _build_intake_tab(self) -> None:
        layout = QVBoxLayout(self.intake_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        metadata_box = QWidget()
        metadata_layout = QGridLayout(metadata_box)
        metadata_layout.setHorizontalSpacing(12)
        metadata_layout.setVerticalSpacing(10)

        self.run_name = QLineEdit()
        self.case_name = QLineEdit()
        self.author_name = QLineEdit()
        self.author_name.setText("David Lowe")
        self.category = QLineEdit()
        self.tags = QLineEdit()
        self.purpose = QLineEdit()
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("Run notes, aliases, exclusions, or keyword hints...")
        self.notes.setMaximumHeight(90)

        fields = [
            ("Run Name", self.run_name, 0, 0),
            ("Case / Topic", self.case_name, 0, 2),
            ("Author / Owner", self.author_name, 1, 0),
            ("Category", self.category, 1, 2),
            ("Tags", self.tags, 2, 0),
            ("Purpose", self.purpose, 2, 2),
        ]
        for label_text, widget, row, col in fields:
            metadata_layout.addWidget(QLabel(label_text), row, col)
            metadata_layout.addWidget(widget, row, col + 1)

        metadata_layout.addWidget(QLabel("Notes"), 3, 0)
        metadata_layout.addWidget(self.notes, 3, 1, 1, 3)
        layout.addWidget(self._group("Run Metadata", metadata_box))

        intake_box = QWidget()
        intake_layout = QGridLayout(intake_box)
        intake_layout.setHorizontalSpacing(12)
        intake_layout.setVerticalSpacing(10)

        self.q1 = self._combo(TARGET_TYPES)
        self.q2 = self._combo(INTENTS)
        self.q3 = self._combo(SCOPES)
        self.q4 = self._combo(DEPTHS)
        self.q5 = self._combo(OUTPUTS)
        self.q6 = self._combo(ORGS)
        self.q1_notes = QLineEdit()
        self.q2_notes = QLineEdit()
        self.q3_notes = QLineEdit()
        self.q4_notes = QLineEdit()
        self.q5_notes = QLineEdit()
        self.q6_notes = QLineEdit()
        q_fields = [
            ("Q1 Target Type", self.q1, self.q1_notes),
            ("Q2 Research Intent", self.q2, self.q2_notes),
            ("Q3 Source Scope", self.q3, self.q3_notes),
            ("Q4 Depth", self.q4, self.q4_notes),
            ("Q5 Output", self.q5, self.q5_notes),
            ("Q6 Organization", self.q6, self.q6_notes),
        ]
        for row, (label_text, combo, note) in enumerate(q_fields):
            intake_layout.addWidget(QLabel(label_text), row, 0)
            intake_layout.addWidget(combo, row, 1)
            note.setPlaceholderText("Notes / constraints / hints")
            intake_layout.addWidget(note, row, 2, 1, 2)

        layout.addWidget(self._group("Core Intake", intake_box))

        controls_box = QWidget()
        controls_layout = QHBoxLayout(controls_box)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.output_dir_edit = QLineEdit(str(self.output_dir))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_output_dir)
        run_btn = QPushButton("Run Discovery")
        run_btn.setObjectName("primaryButton")
        run_btn.clicked.connect(self._run_discovery)
        open_btn = QPushButton("Open Output Folder")
        open_btn.clicked.connect(self._open_output_folder)
        controls_layout.addWidget(QLabel("Output Folder"))
        controls_layout.addWidget(self.output_dir_edit, 1)
        controls_layout.addWidget(browse_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(run_btn)
        controls_layout.addWidget(open_btn)
        layout.addWidget(self._group("Run Controls", controls_box))

    def _build_links_tab(self) -> None:
        layout = QVBoxLayout(self.links_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Title", "Domain", "Source Type", "Provider", "URL", "Canonical URL", "Snippet"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _build_log_tab(self) -> None:
        layout = QVBoxLayout(self.log_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def _group(self, title: str, child: QWidget) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(10, 8, 10, 10)
        label = QLabel(title)
        label.setObjectName("sectionLabel")
        layout.addWidget(label)
        layout.addWidget(child)
        wrap.setObjectName("groupCard")
        return wrap

    def _combo(self, values: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        return combo

    def _browse_output_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_dir_edit.text())
        if selected:
            self.output_dir_edit.setText(selected)

    def _depth_settings(self) -> tuple[int, int]:
        value = self.q4.currentText()
        if value == "top_10":
            return 10, 1
        if value == "top_100":
            return 100, 12
        if value == "top_200":
            return 100, 24
        if value == "top_50":
            return 50, 5
        return 25, 3

    def _scope_settings(self) -> tuple[bool, bool]:
        scope = self.q3.currentText()
        if scope == "wikipedia_only":
            return True, False
        if scope == "trusted_hubs":
            return False, True
        return True, True

    def _run_discovery(self) -> None:
        case_name = self.case_name.text().strip()
        if not case_name:
            QMessageBox.warning(self, "Missing case", "Enter a case or topic name first.")
            return

        max_wiki, max_domain = self._depth_settings()
        include_wikipedia, include_trusted = self._scope_settings()
        request = DiscoveryRequest(
            case_title=case_name,
            max_wikipedia_links=max_wiki,
            max_results_per_domain=max_domain,
            include_wikipedia=include_wikipedia,
            include_trusted_hubs=include_trusted,
        )
        self._append_log(f"Running discovery for: {case_name}")
        self.status_label.setText("running discovery")
        QApplication.processEvents()

        rows = discover_links(request)
        dedupe_result = dedupe_rows(rows, case_field="case_title")

        output_dir = ensure_output_dir(self.output_dir_edit.text())
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        base_name = f"{_slug(case_name)}_{stamp}"
        raw_path = output_dir / f"{base_name}_discovery_raw.csv"
        deduped_path = output_dir / f"{base_name}_discovery_deduped.csv"
        summary_path = output_dir / f"{base_name}_summary.json"
        write_csv_rows(raw_path, rows)
        write_csv_rows(deduped_path, dedupe_result.unique_rows)
        summary = {
            "case_name": case_name,
            "run_name": self.run_name.text().strip(),
            "author": self.author_name.text().strip(),
            "category": self.category.text().strip(),
            "tags": self.tags.text().strip(),
            "purpose": self.purpose.text().strip(),
            "raw_rows": len(rows),
            "deduped_rows": len(dedupe_result.unique_rows),
            "scope": self.q3.currentText(),
            "depth": self.q4.currentText(),
            "intent": self.q2.currentText(),
            "output": self.q5.currentText(),
            "organization": self.q6.currentText(),
            "notes": {
                "run": self.notes.toPlainText(),
                "q1": self.q1_notes.text(),
                "q2": self.q2_notes.text(),
                "q3": self.q3_notes.text(),
                "q4": self.q4_notes.text(),
                "q5": self.q5_notes.text(),
                "q6": self.q6_notes.text(),
            },
            "outputs": {
                "raw_csv": str(raw_path),
                "deduped_csv": str(deduped_path),
            },
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        self.last_summary_path = summary_path

        self._populate_table(dedupe_result.unique_rows)
        self.status_label.setText(f"{len(dedupe_result.unique_rows)} links ready")
        self._append_log(f"Raw rows: {len(rows)}")
        self._append_log(f"Deduped rows: {len(dedupe_result.unique_rows)}")
        self._append_log(f"Saved deduped CSV: {deduped_path}")
        self._append_log(f"Saved summary JSON: {summary_path}")
        self.tabs.setCurrentWidget(self.links_tab)

    def _populate_table(self, rows: list[dict[str, str]]) -> None:
        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                row_data.get("title", ""),
                row_data.get("domain", ""),
                row_data.get("source_type", ""),
                row_data.get("provider", ""),
                row_data.get("url", ""),
                row_data.get("canonical_url", ""),
                row_data.get("snippet", ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 4:
                    item.setForeground(QColor("#78dce8"))
                self.table.setItem(row, col, item)

    def _open_output_folder(self) -> None:
        output_dir = Path(self.output_dir_edit.text())
        output_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_dir.resolve())))

    def _append_log(self, text: str) -> None:
        self.log.appendPlainText(text)

    def _apply_style(self) -> None:
        font = QFont("Consolas", 11)
        self.setFont(font)
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #0f1320;
                color: #d8ddf0;
            }
            #titleLabel {
                color: #f2b233;
                font-size: 24px;
                font-weight: 700;
                letter-spacing: 2px;
            }
            #subtitleLabel {
                color: #7782a0;
                font-size: 11px;
                letter-spacing: 3px;
            }
            #statusLabel {
                color: #57f287;
                font-size: 12px;
                padding: 6px 10px;
                border: 1px solid #1f5f4a;
                border-radius: 6px;
                background: #111a1a;
            }
            #sectionLabel {
                color: #f2b233;
                font-size: 13px;
                font-weight: 700;
                padding-bottom: 4px;
            }
            #groupCard {
                border: 1px solid #232a45;
                border-radius: 10px;
                background: #121827;
            }
            QLineEdit, QPlainTextEdit, QComboBox, QTableWidget, QTabWidget::pane {
                background: #101624;
                border: 1px solid #28314f;
                border-radius: 8px;
                padding: 6px;
                color: #d8ddf0;
                selection-background-color: #21426f;
            }
            QComboBox QAbstractItemView {
                background: #101624;
                color: #d8ddf0;
                selection-background-color: #21426f;
            }
            QPushButton {
                background: #18213a;
                border: 1px solid #2d3b63;
                border-radius: 8px;
                padding: 9px 14px;
                color: #d8ddf0;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #202b49;
            }
            QPushButton#primaryButton {
                background: #3a2d11;
                border: 1px solid #7a5b19;
                color: #ffcb45;
            }
            QTabBar::tab {
                background: #121827;
                color: #8e98b5;
                padding: 10px 18px;
                border: 1px solid #232a45;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                color: #f2b233;
                border-bottom: 2px solid #f2b233;
            }
            QHeaderView::section {
                background: #131a2c;
                color: #f2b233;
                padding: 8px;
                border: 1px solid #28314f;
                font-weight: 700;
            }
            """
        )


def run_gui() -> None:
    app = QApplication.instance() or QApplication([])
    window = IntakeWindow()
    window.show()
    app.exec()
