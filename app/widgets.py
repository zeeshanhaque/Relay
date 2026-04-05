"""
Custom reusable widgets for the Incident Management System.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QScrollArea, QSizePolicy, QDateTimeEdit
)
from PySide6.QtCore import QDateTime, Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

from datetime import datetime, timedelta

from .data_manager import load_data, round_to_quarter


class FiveMinDateTimeEdit(QDateTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSpecialValueText(" ")

    def stepBy(self, steps):
        # If at minimum (blank), set base time before stepping
        if self.dateTime() == self.minimumDateTime():
            self._set_default_datetime()

        if self.currentSection() == QDateTimeEdit.Section.MinuteSection:
            current = self.dateTime()
            minutes = current.time().minute()
            if steps > 0:
                new_minutes = ((minutes // 5) + 1) * 5
            else:
                new_minutes = ((minutes - 1) // 5) * 5
            new_minutes = new_minutes % 60
            new_time = current.addSecs((new_minutes - minutes) * 60)
            self.setDateTime(new_time)
        else:
            super().stepBy(steps)

    def _set_default_datetime(self):
        try:
            data = load_data()
            progress_entries = data.get("progress_entries", [])
            if progress_entries:
                latest = max(
                    progress_entries,
                    key=lambda e: datetime.strptime(e["datetime"], "%d/%m/%Y %H:%M")
                )
                base_dt = datetime.strptime(latest["datetime"], "%d/%m/%Y %H:%M")
            else:
                # Fall back to start_time from form if available
                start_iso = data.get("form", {}).get("start_time", "")
                if start_iso:
                    base_dt = datetime.fromisoformat(start_iso)
                else:
                    base_dt = datetime.now()
            default_dt = round_to_quarter(base_dt + timedelta(hours=1))
            self.setDateTime(QDateTime(
                default_dt.year, default_dt.month, default_dt.day,
                default_dt.hour, default_dt.minute, 0
            ))
        except Exception:
            # Fallback to current time + 1hr
            dt = datetime.now() + timedelta(hours=1)
            self.setDateTime(QDateTime(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, 0
            ))

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # If at minimum (blank), navigate calendar to current month on popup open
        if self.dateTime() == self.minimumDateTime():
            from PySide6.QtCore import QTimer, QDate
            QTimer.singleShot(0, self._fix_calendar_page)

    def _fix_calendar_page(self):
        cal = self.calendarWidget()
        if cal and cal.isVisible():
            from PySide6.QtCore import QDate
            today = QDate.currentDate()
            cal.setCurrentPage(today.year(), today.month())


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
        self.setStyleSheet(
            "color: #00915A; border-bottom: 3px solid #e8f5f0; padding-bottom: 8px; margin-bottom: 8px;"
            "font-size: 13pt; font-weight: bold;"
        )


def make_hover(row, checkbox):
    def enter(e):
        checkbox.setStyleSheet("""
            QCheckBox {
                padding: 4px;
                font-size: 13px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #00915A;
            }
            QCheckBox::indicator:checked {
                background-color: #00915A;
                border-color: #00915A;
            }
        """)
    def leave(e):
        checkbox.setStyleSheet("""
            QCheckBox {
                padding: 4px;
                font-size: 13px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #e0e0e0;
            }
            QCheckBox::indicator:checked {
                background-color: #00915A;
                border-color: #00915A;
            }
        """)
    row.enterEvent = enter
    row.leaveEvent = leave


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
        self._header = QPushButton(self._placeholder)
        self._header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 9px 14px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background: white;
                color: #2c3e50;
                font-size: 13px;
                background-image: url(:/icons/chevron_down.png);
                background-repeat: no-repeat;
                background-position: right center;
                padding-right: 30px;
            }
            QPushButton:hover { border-color: #00915A; background-color: #f0faf6;
                background-image: url(:/icons/chevron_down.png);
                background-repeat: no-repeat;
                background-position: right center;
                padding-right: 30px;
            }
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
        panel_layout.setSpacing(2)

        for option in self._options:
            row_widget = QWidget()
            row_widget.setCursor(Qt.PointingHandCursor)
            row_widget.setStyleSheet("""
                QWidget {
                    border-radius: 4px;
                    background: transparent;
                }
                QWidget:hover {
                    background: #e8f5f0;
                }
                QWidget:hover QCheckBox::indicator {
                    border-color: #00915A;
                }
            """)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(8)

            cb = QCheckBox(option)
            cb.setStyleSheet("""
                QCheckBox {
                    padding: 4px;
                    font-size: 13px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 2px solid #e0e0e0;
                }
                QCheckBox::indicator:checked {
                    background-color: #00915A;
                    border-color: #00915A;
                }
            """)
            cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cb.stateChanged.connect(self._on_change)
            row_layout.addWidget(cb)

            # Click anywhere on row toggles checkbox
            row_widget.mousePressEvent = lambda e, c=cb: c.setChecked(not c.isChecked())

            panel_layout.addWidget(row_widget)
            self._checkboxes[option] = cb
            make_hover(row_widget, cb)

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
            text = ", ".join(selected)
        else:
            text = self._placeholder
        self._header.setText(text)
        self._header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 9px 14px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background: white;
                color: #2c3e50;
                font-size: 13px;
                background-image: url(:/icons/chevron_down.png);
                background-repeat: no-repeat;
                background-position: right center;
                padding-right: 30px;
            }
            QPushButton:hover { border-color: #00915A; background-color: #f0faf6;
                background-image: url(:/icons/chevron_down.png);
                background-repeat: no-repeat;
                background-position: right center;
                padding-right: 30px;
            }
        """)

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
        self._header.setText(self._placeholder)


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

        remove_btn = QPushButton()
        remove_btn.setObjectName("removeBtn")
        remove_btn.setIcon(QIcon(":/icons/remove.png"))
        remove_btn.setIconSize(QSize(14, 14))
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
    def __init__(self, label: str, parent=None, label_width: int = 40, boxed: bool = True):
        super().__init__(parent)
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(label_width)
        lbl.setAlignment(Qt.AlignCenter)
        if boxed:
            lbl.setStyleSheet(
                "color: #7f8c8d; border: 1px solid #bbb; border-radius: 4px;"
                " padding: 4px 6px; background: white; font-weight: 600;"
            )
        else:
            lbl.setStyleSheet(
                "color: #7f8c8d; border: none; background: transparent;"
                " padding: 4px 6px; font-weight: 600;"
            )
        layout.addWidget(lbl)

        self._text_lbl = QLabel("")
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._text_lbl.setStyleSheet(
            "border: none; padding: 4px;"
            " background: transparent; color: #2c3e50;"
        )

        scroll = QScrollArea()
        scroll.setWidget(self._text_lbl)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border-bottom: 1px solid #2c3e50; background: transparent; }"
            "QScrollBar:horizontal { height: 6px; background: #f0f0f0; border-radius: 3px; }"
            "QScrollBar::handle:horizontal { background: #00915A; border-radius: 3px; min-width: 20px; }"
            "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }"
        )
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(scroll)

    def set_text(self, text: str):
        self._text_lbl.setText(text)

    def get_text(self) -> str:
        return self._text_lbl.text()