"""
Custom reusable widgets for the Incident Management System.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class SectionCard(QFrame):
    """A white rounded card container."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self._layout = layout

    def addWidget(self, widget, stretch=0):
        self._layout.addWidget(widget, stretch)

    def addLayout(self, layout):
        self._layout.addLayout(layout)

    def layout(self):
        return self._layout


class FieldLabel(QLabel):
    """Standard field label."""
    def __init__(self, text: str, required: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("fieldLabel")
        if required:
            self.setText(f"{text} <span style='color:#e74c3c'>*</span>")
            self.setTextFormat(Qt.RichText)
        else:
            self.setText(text)


class SectionTitle(QLabel):
    """Card section title in green."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("sectionTitle")
        font = self.font()
        font.setPointSize(13)
        font.setWeight(QFont.Bold)
        self.setFont(font)
        self.setStyleSheet(
            "color: #00915A; border-bottom: 3px solid #e8f5f0; padding-bottom: 8px; margin-bottom: 8px;"
        )


class MultiCheckDropdown(QWidget):
    """
    A custom dropdown that shows checkboxes for multi-select.
    Emits selectionChanged(list[str]) whenever selection changes.
    """
    selectionChanged = Signal(list)

    def __init__(self, placeholder: str, options: list[str], parent=None):
        super().__init__(parent)
        self._options = options
        self._placeholder = placeholder
        self._checkboxes: dict[str, QCheckBox] = {}
        self._popup_open = False

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header button
        self._header = QPushButton(self._placeholder + "  ▼")
        self._header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 9px 14px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background: white;
                color: #2c3e50;
                font-size: 13px;
            }
            QPushButton:hover { border-color: #00915A; background: #f0faf6; }
        """)
        self._header.clicked.connect(self._toggle_popup)
        main_layout.addWidget(self._header)

        # Dropdown panel
        self._panel = QFrame(self)
        self._panel.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #00915A;
                border-radius: 8px;
            }
        """)
        self._panel.setWindowFlags(Qt.Popup)
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(4)

        for option in self._options:
            cb = QCheckBox(option)
            cb.setStyleSheet("padding: 6px 4px; font-size: 13px;")
            cb.stateChanged.connect(self._on_change)
            panel_layout.addWidget(cb)
            self._checkboxes[option] = cb

        self._panel.hide()

    def _toggle_popup(self):
        if self._panel.isVisible():
            self._panel.hide()
        else:
            # Position below header
            pos = self._header.mapToGlobal(self._header.rect().bottomLeft())
            self._panel.setMinimumWidth(self._header.width())
            self._panel.move(pos)
            self._panel.show()
            self._panel.raise_()

    def _on_change(self):
        selected = self.get_selected()
        self._update_header(selected)
        self.selectionChanged.emit(selected)

    def _update_header(self, selected: list[str]):
        if selected:
            text = ", ".join(selected) + "  ▼"
        else:
            text = self._placeholder + "  ▼"
        self._header.setText(text)

    def get_selected(self) -> list[str]:
        return [opt for opt, cb in self._checkboxes.items() if cb.isChecked()]

    def set_selected(self, values: list[str]):
        for opt, cb in self._checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(opt in values)
            cb.blockSignals(False)
        self._update_header(values)

    def set_disabled_options(self, disabled: list[str]):
        for opt, cb in self._checkboxes.items():
            cb.setEnabled(opt not in disabled)

    def reset(self):
        for cb in self._checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.setEnabled(True)
            cb.blockSignals(False)
        self._header.setText(self._placeholder + "  ▼")


class IncidentTag(QFrame):
    """A chip/tag showing a single incident with remove button."""
    removeRequested = Signal(int)

    def __init__(self, index: int, number: str, priority: str = "", parent=None):
        super().__init__(parent)
        self._index = index
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #00915A;
                border-radius: 6px;
                background: #e8f5f0;
                padding: 2px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(6)

        text = number
        if priority:
            text += f" [{priority}]"

        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: 600; color: #007047; border: none; background: transparent;")
        layout.addWidget(lbl)

        remove_btn = QPushButton("×")
        remove_btn.setObjectName("removeBtn")
        remove_btn.setFixedSize(20, 20)
        remove_btn.clicked.connect(lambda: self.removeRequested.emit(self._index))
        layout.addWidget(remove_btn)

    def set_index(self, index: int):
        self._index = index


class StatusBadge(QLabel):
    """Coloured status pill."""
    STATUS_STYLES = {
        "Available":        ("background: #6fc040; color: white;"),
        "Unavailable":      ("background: #e74c3c; color: white;"),
        "Degraded":         ("background: #ffd500; color: black;"),
        "Under Observation":("background: #0070d2; color: white;"),
    }

    def __init__(self, status: str = "", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStatus(status)

    def setStatus(self, status: str):
        base = "border-radius: 5px; padding: 5px 14px; font-weight: 700; font-size: 13px;"
        style = self.STATUS_STYLES.get(status, "background: #aaa; color: white;")
        self.setStyleSheet(base + style)
        self.setText(status)


class CopyField(QWidget):
    """A labelled read-only text line with a copy button."""
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(70)
        lbl.setStyleSheet(
            "color: #7f8c8d; border: 1px solid #bbb; border-radius: 4px;"
            " padding: 4px 8px; background: white; font-weight: 600;"
        )
        layout.addWidget(lbl)

        self._text_lbl = QLabel("")
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._text_lbl.setStyleSheet(
            "border-bottom: 1px solid #2c3e50; padding: 4px 6px;"
            " background: transparent; color: #2c3e50;"
        )
        self._text_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self._text_lbl)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setObjectName("copyBtn")
        self._copy_btn.setFixedWidth(70)
        self._copy_btn.clicked.connect(self._copy)
        layout.addWidget(self._copy_btn)

    def set_text(self, text: str):
        self._text_lbl.setText(text)

    def get_text(self) -> str:
        return self._text_lbl.text()

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.get_text())
        orig = self._copy_btn.text()
        self._copy_btn.setText("✓ Copied!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._copy_btn.setText(orig))
