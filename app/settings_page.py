"""
Settings Page - view and edit the raw JSON data file.
Changes here sync back to the main form automatically.
"""
import json

from PySide6.QtWidgets import (
    QDateTimeEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QStackedWidget, QStyledItemDelegate
)
from PySide6.QtCore import QSize, Qt, Signal, QDateTime
from PySide6.QtGui import QFont, QIcon

from .data_manager import load_data, save_data, sort_progress_entries, round_to_quarter
from .widgets import FiveMinDateTimeEdit

from datetime import datetime

class DateTimeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = FiveMinDateTimeEdit(parent)
        editor.setDisplayFormat("dd/MM/yyyy HH:mm")
        editor.setCalendarPopup(True)
        editor.setButtonSymbols(QDateTimeEdit.UpDownArrows)
        editor.setWrapping(True)
        return editor

    def setEditorData(self, editor, index):
        text = index.data() or ""
        dt = QDateTime.fromString(text, "dd/MM/yyyy HH:mm")
        if dt.isValid():
            editor.setDateTime(dt)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.dateTime().toString("dd/MM/yyyy HH:mm"))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class MultiLineDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QTextEdit(parent)
        editor.setAcceptRichText(False)
        return editor

    def setEditorData(self, editor, index):
        editor.setPlainText(index.data() or "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText())

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 50)


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

        self._progress_btn = QPushButton()
        self._progress_btn.setObjectName("settingsBtn")
        self._progress_btn.setIcon(QIcon(":/icons/progress.png"))
        self._progress_btn.setIconSize(QSize(20, 20))
        self._progress_btn.clicked.connect(lambda: self._switch_view(0))
        header.addWidget(self._progress_btn)

        self._raw_btn = QPushButton()
        self._raw_btn.setObjectName("settingsBtn")
        self._raw_btn.setIcon(QIcon(":/icons/json.png"))
        self._raw_btn.setIconSize(QSize(20, 20))
        self._raw_btn.clicked.connect(lambda: self._switch_view(1))
        header.addWidget(self._raw_btn)

        header.addStretch()

        self._reload_btn = QPushButton()
        self._reload_btn.setObjectName("settingsBtn")
        self._reload_btn.setIcon(QIcon(":/icons/reload.png"))
        self._reload_btn.setIconSize(QSize(20, 20))
        self._reload_btn.clicked.connect(self._load)
        header.addWidget(self._reload_btn)

        self._save_btn = QPushButton()
        self._save_btn.setObjectName("generateBtn")
        self._save_btn.setIcon(QIcon(":/icons/save.png"))
        self._save_btn.setIconSize(QSize(20, 20))
        self._save_btn.clicked.connect(self._save)
        header.addWidget(self._save_btn)

        layout.addLayout(header)

        # Stacked widget
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_progress_tab())
        self._stack.addWidget(self._build_raw_tab())
        layout.addWidget(self._stack)

        self._switch_view(0)


    def _switch_view(self, index: int):
        self._stack.setCurrentIndex(index)
        active_style = (
            "border: 2px solid #00915A; border-radius: 8px;"
            "padding: 8px 16px; background: #e8f5f0; color: #00915A;"
        )
        inactive_style = (
            "border: 2px solid #e0e0e0; border-radius: 8px;"
            "padding: 8px 16px; background: white; color: #2c3e50;"
        )
        self._progress_btn.setStyleSheet(active_style if index == 0 else inactive_style)
        self._raw_btn.setStyleSheet(active_style if index == 1 else inactive_style)


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
        del_btn = QPushButton("— Remove Selected")
        del_btn.setObjectName("clearBtn")
        del_btn.clicked.connect(self._del_progress_row)
        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._clear_progress)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._prog_table = QTableWidget(0, 2)
        self._prog_table.setHorizontalHeaderLabels(["Date/Time", "Details"])
        self._prog_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._prog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._prog_table.setColumnWidth(0, 360)
        self._prog_table.setMinimumHeight(300)
        self._prog_table.setItemDelegateForColumn(0, DateTimeDelegate(self._prog_table))
        self._prog_table.setItemDelegateForColumn(1, MultiLineDelegate(self._prog_table))
        layout.addWidget(self._prog_table)

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

        # Progress
        entries = sort_progress_entries(data.get("progress_entries", []))
        self._prog_table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            dt_item = QTableWidgetItem(entry.get("datetime", ""))
            dt_item.setTextAlignment(Qt.AlignCenter)
            self._prog_table.setItem(i, 0, dt_item)
            self._prog_table.setItem(i, 1, QTableWidgetItem(entry.get("text", "")))
            self._prog_table.setRowHeight(i, 80)

        # Raw JSON
        self._raw_editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        if self._stack.currentIndex() == 1:
            try:
                data = json.loads(self._raw_editor.toPlainText())
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON parse error:\n{e}")
                return
        else:
            data = load_data()
            entries = []
            for row in range(self._prog_table.rowCount()):
                dt_item = self._prog_table.item(row, 0)
                txt_item = self._prog_table.item(row, 1)
                if dt_item and txt_item:
                    dt_str = dt_item.text().strip()
                    # Round to nearest 15 minutes
                    try:
                        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
                        dt = round_to_quarter(dt)
                        dt_str = dt.strftime("%d/%m/%Y %H:%M")
                    except ValueError:
                        pass  # keep original if parsing fails
                    entries.append({
                        "datetime": dt_str,
                        "text": txt_item.text().strip()
                    })
            data["progress_entries"] = entries

        save_data(data)
        self._raw_editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
        self._load()  # ← reload to reflect sorted order in table
        self.dataChanged.emit(data)
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    # ── Progress table helpers ────────────────────────────────────────────────

    def _add_progress_row(self):
        from datetime import datetime
        row = self._prog_table.rowCount()
        self._prog_table.insertRow(row)
        self._prog_table.setRowHeight(row, 80)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        dt_item = QTableWidgetItem(now)
        dt_item.setTextAlignment(Qt.AlignCenter)
        self._prog_table.setItem(row, 0, dt_item)
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
