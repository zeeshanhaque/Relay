"""
Settings Page - view and edit the raw JSON data file.
Changes here sync back to the main form automatically.
"""
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTabWidget, QFrame, QScrollArea, QLineEdit,
    QSplitter, QGroupBox, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from .data_manager import (
    load_data, save_data, SERVICE_STATUSES, SERVICES, USERS,
    EMAIL_LISTS
)
from .widgets import SectionTitle, SectionCard


class SettingsPage(QWidget):
    """
    Full settings/data editor.
    Emits dataChanged(dict) when the user saves, so the main window can
    update the form panel.
    """
    dataChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        title = SectionTitle("⚙  Data & Settings Editor")
        header.addWidget(title)
        header.addStretch()

        self._reload_btn = QPushButton("↺  Reload")
        self._reload_btn.setObjectName("settingsBtn")
        self._reload_btn.clicked.connect(self._load)
        header.addWidget(self._reload_btn)

        self._save_btn = QPushButton("💾  Save All Changes")
        self._save_btn.setObjectName("generateBtn")
        self._save_btn.clicked.connect(self._save)
        header.addWidget(self._save_btn)

        layout.addLayout(header)

        # Tabs
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._tabs.addTab(self._build_form_tab(), "📋  Form State")
        self._tabs.addTab(self._build_progress_tab(), "📝  Progress Log")
        self._tabs.addTab(self._build_recipients_tab(), "📧  Recipients")
        self._tabs.addTab(self._build_raw_tab(), "🔧  Raw JSON")

    # ── Form State Tab ────────────────────────────────────────────────────────

    def _build_form_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        info = QLabel("Edit the current form state. Changes will reflect in the main form when saved.")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 4px;")
        layout.addWidget(info)

        form_frame = QGroupBox("Form Fields")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)

        self._fs_services = QLineEdit()
        self._fs_services.setPlaceholderText("Comma separated, e.g. BD, RN, DGT")
        form_layout.addRow("Selected Services:", self._fs_services)

        self._fs_status = QComboBox()
        self._fs_status.addItems(SERVICE_STATUSES)
        form_layout.addRow("Service Status:", self._fs_status)

        self._fs_users = QLineEdit()
        self._fs_users.setPlaceholderText("GLOBAL  or  APAC, EMEA")
        form_layout.addRow("Selected Users:", self._fs_users)

        self._fs_desc = QTextEdit()
        self._fs_desc.setMaximumHeight(80)
        form_layout.addRow("Description:", self._fs_desc)

        self._fs_impact = QTextEdit()
        self._fs_impact.setMaximumHeight(80)
        form_layout.addRow("Impact:", self._fs_impact)

        self._fs_start = QLineEdit()
        self._fs_start.setPlaceholderText("ISO format: 2025-06-01T09:00:00")
        form_layout.addRow("Start Time (ISO):", self._fs_start)

        self._fs_end = QLineEdit()
        self._fs_end.setPlaceholderText("ISO format: 2025-06-01T10:00:00")
        form_layout.addRow("End Time (ISO):", self._fs_end)

        self._fs_next = QLineEdit()
        self._fs_next.setPlaceholderText("ISO format: 2025-06-01T11:00:00")
        form_layout.addRow("Next Update (ISO):", self._fs_next)

        layout.addWidget(form_frame)

        # Incidents sub-table
        inc_frame = QGroupBox("Incidents")
        inc_layout = QVBoxLayout(inc_frame)

        inc_btn_row = QHBoxLayout()
        add_inc = QPushButton("+ Add Row")
        add_inc.setObjectName("addIncBtn")
        add_inc.clicked.connect(self._add_incident_row)
        del_inc = QPushButton("− Remove Selected")
        del_inc.setObjectName("clearBtn")
        del_inc.clicked.connect(self._del_incident_row)
        inc_btn_row.addWidget(add_inc)
        inc_btn_row.addWidget(del_inc)
        inc_btn_row.addStretch()
        inc_layout.addLayout(inc_btn_row)

        self._inc_table = QTableWidget(0, 2)
        self._inc_table.setHorizontalHeaderLabels(["Incident Number", "Priority (P1/P2 or blank)"])
        self._inc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._inc_table.setMinimumHeight(120)
        inc_layout.addWidget(self._inc_table)

        layout.addWidget(inc_frame)
        layout.addStretch()
        return page

    # ── Progress Log Tab ──────────────────────────────────────────────────────

    def _build_progress_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        info = QLabel("View, edit, or delete progress entries. Each entry is timestamped.")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 4px;")
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add Entry")
        add_btn.setObjectName("addIncBtn")
        add_btn.clicked.connect(self._add_progress_row)
        del_btn = QPushButton("− Remove Selected")
        del_btn.setObjectName("clearBtn")
        del_btn.clicked.connect(self._del_progress_row)
        clear_btn = QPushButton("🗑  Clear All")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._clear_progress)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._prog_table = QTableWidget(0, 2)
        self._prog_table.setHorizontalHeaderLabels(["Date/Time", "Details"])
        self._prog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._prog_table.setMinimumHeight(300)
        layout.addWidget(self._prog_table)

        return page

    # ── Recipients Tab ────────────────────────────────────────────────────────

    def _build_recipients_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        info = QLabel(
            "Edit the To address and BCC email lists for each region. "
            "One email per line."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 4px;")
        layout.addWidget(info)

        to_grp = QGroupBox("To Recipient")
        to_layout = QFormLayout(to_grp)
        self._to_addr = QLineEdit()
        self._to_addr.setPlaceholderText("e.g. manager@company.com")
        to_layout.addRow("To:", self._to_addr)
        layout.addWidget(to_grp)

        bcc_grp = QGroupBox("BCC Recipients by Region")
        bcc_layout = QFormLayout(bcc_grp)

        self._bcc_apac = QTextEdit()
        self._bcc_apac.setMaximumHeight(100)
        self._bcc_apac.setPlaceholderText("One email per line")
        bcc_layout.addRow("APAC:", self._bcc_apac)

        self._bcc_emea = QTextEdit()
        self._bcc_emea.setMaximumHeight(100)
        self._bcc_emea.setPlaceholderText("One email per line")
        bcc_layout.addRow("EMEA:", self._bcc_emea)

        self._bcc_americas = QTextEdit()
        self._bcc_americas.setMaximumHeight(100)
        self._bcc_americas.setPlaceholderText("One email per line")
        bcc_layout.addRow("AMERICAS:", self._bcc_americas)

        layout.addWidget(bcc_grp)
        layout.addStretch()
        return page

    # ── Raw JSON Tab ──────────────────────────────────────────────────────────

    def _build_raw_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(8)

        info = QLabel(
            "⚠  Advanced: edit raw JSON directly. "
            "Invalid JSON will be rejected on save."
        )
        info.setStyleSheet("color: #e74c3c; font-style: italic; padding: 4px;")
        layout.addWidget(info)

        self._raw_editor = QTextEdit()
        self._raw_editor.setFont(QFont("Courier New", 10))
        self._raw_editor.setAcceptRichText(False)
        layout.addWidget(self._raw_editor)

        return page

    # ── Load ──────────────────────────────────────────────────────────────────

    def _load(self):
        data = load_data()
        form = data.get("form", {})

        # Form tab
        self._fs_services.setText(", ".join(form.get("selected_services", [])))
        idx = self._fs_status.findText(form.get("service_status", "Available"))
        self._fs_status.setCurrentIndex(max(0, idx))
        self._fs_users.setText(", ".join(form.get("selected_users", [])))
        self._fs_desc.setPlainText(form.get("description", ""))
        self._fs_impact.setPlainText(form.get("impact", ""))
        self._fs_start.setText(form.get("start_time", ""))
        self._fs_end.setText(form.get("end_time", ""))
        self._fs_next.setText(form.get("next_update", ""))

        # Incidents
        incidents = form.get("incidents", [])
        self._inc_table.setRowCount(len(incidents))
        for i, inc in enumerate(incidents):
            self._inc_table.setItem(i, 0, QTableWidgetItem(inc.get("number", "")))
            self._inc_table.setItem(i, 1, QTableWidgetItem(inc.get("priority", "")))

        # Progress
        entries = data.get("progress_entries", [])
        self._prog_table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            self._prog_table.setItem(i, 0, QTableWidgetItem(entry.get("datetime", "")))
            self._prog_table.setItem(i, 1, QTableWidgetItem(entry.get("text", "")))

        # Recipients
        self._to_addr.setText(data.get("to_recipient", ""))
        bcc = data.get("bcc_recipients", {})
        self._bcc_apac.setPlainText("\n".join(bcc.get("APAC", EMAIL_LISTS["APAC"])))
        self._bcc_emea.setPlainText("\n".join(bcc.get("EMEA", EMAIL_LISTS["EMEA"])))
        self._bcc_americas.setPlainText("\n".join(bcc.get("AMERICAS", EMAIL_LISTS["AMERICAS"])))

        # Raw JSON
        self._raw_editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        # Determine which tab is active
        current_tab = self._tabs.currentIndex()

        if current_tab == 3:
            # Raw JSON tab - parse and save
            try:
                data = json.loads(self._raw_editor.toPlainText())
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON parse error:\n{e}")
                return
        else:
            # Build from UI widgets
            data = load_data()

            # Form state
            svc_text = self._fs_services.text()
            selected_services = [s.strip() for s in svc_text.split(",") if s.strip()]
            usr_text = self._fs_users.text()
            selected_users = [u.strip() for u in usr_text.split(",") if u.strip()]

            incidents = []
            for row in range(self._inc_table.rowCount()):
                num_item = self._inc_table.item(row, 0)
                pri_item = self._inc_table.item(row, 1)
                if num_item and num_item.text().strip():
                    incidents.append({
                        "number": num_item.text().strip(),
                        "priority": pri_item.text().strip() if pri_item else ""
                    })

            data["form"] = {
                "selected_services": selected_services,
                "service_status": self._fs_status.currentText(),
                "selected_users": selected_users,
                "incidents": incidents,
                "description": self._fs_desc.toPlainText(),
                "impact": self._fs_impact.toPlainText(),
                "start_time": self._fs_start.text().strip(),
                "end_time": self._fs_end.text().strip(),
                "next_update": self._fs_next.text().strip(),
            }

            # Progress entries
            entries = []
            for row in range(self._prog_table.rowCount()):
                dt_item = self._prog_table.item(row, 0)
                txt_item = self._prog_table.item(row, 1)
                if dt_item and txt_item:
                    entries.append({
                        "datetime": dt_item.text().strip(),
                        "text": txt_item.text().strip()
                    })
            data["progress_entries"] = entries

            # Recipients
            data["to_recipient"] = self._to_addr.text().strip()
            data["bcc_recipients"] = {
                "APAC": [e.strip() for e in self._bcc_apac.toPlainText().splitlines() if e.strip()],
                "EMEA": [e.strip() for e in self._bcc_emea.toPlainText().splitlines() if e.strip()],
                "AMERICAS": [e.strip() for e in self._bcc_americas.toPlainText().splitlines() if e.strip()],
            }

        save_data(data)
        # Refresh raw tab
        self._raw_editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
        self.dataChanged.emit(data)

        QMessageBox.information(self, "Saved", "Settings saved and synced to main form.")

    # ── Progress table helpers ────────────────────────────────────────────────

    def _add_progress_row(self):
        from datetime import datetime
        row = self._prog_table.rowCount()
        self._prog_table.insertRow(row)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        self._prog_table.setItem(row, 0, QTableWidgetItem(now))
        self._prog_table.setItem(row, 1, QTableWidgetItem(""))
        self._prog_table.editItem(self._prog_table.item(row, 1))

    def _del_progress_row(self):
        rows = {idx.row() for idx in self._prog_table.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            self._prog_table.removeRow(row)

    def _clear_progress(self):
        reply = QMessageBox.question(
            self, "Confirm", "Clear all progress entries?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._prog_table.setRowCount(0)

    # ── Incident table helpers ────────────────────────────────────────────────

    def _add_incident_row(self):
        row = self._inc_table.rowCount()
        self._inc_table.insertRow(row)
        self._inc_table.setItem(row, 0, QTableWidgetItem("INC00000000"))
        self._inc_table.setItem(row, 1, QTableWidgetItem(""))

    def _del_incident_row(self):
        rows = {idx.row() for idx in self._inc_table.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            self._inc_table.removeRow(row)
