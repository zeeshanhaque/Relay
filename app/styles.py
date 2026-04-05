"""
Qt Stylesheet - mirrors the web app's green/white design language.
"""

MAIN_STYLE = """
/* ── Global ── */
QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    color: #2c3e50;
    background-color: transparent;
}

QMainWindow, QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f5f7fa, stop:1 #c3cfe2);
}

/* ── Cards / Frames ── */
QFrame#card {
    background: white;
    border-radius: 12px;
    border: none;
}

/* ── Labels ── */
QLabel#sectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: #00915A;
    padding-bottom: 4px;
}

QLabel#fieldLabel {
    font-weight: 600;
    font-size: 12px;
    color: #2c3e50;
}

QLabel#requiredStar {
    color: #e74c3c;
    font-weight: bold;
}

/* ── Line edits / text inputs ── */
QLineEdit, QTextEdit, QDateTimeEdit, QComboBox {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 8px 12px;
    background: white;
    background-color: white;
    color: #2c3e50;
    selection-background-color: #00915A;
}

QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus, QComboBox:focus {
    border: 2px solid #00915A;
    background: #f0faf6;
    background-color: #f0faf6;
}

QDateTimeEdit::drop-down {
    border: none;
    width: 24px;
}

QDateTimeEdit::down-arrow {
    image: url(:/icons/chevron_down.png);
    width: 12px;
    height: 12px;
}

QLineEdit#invalidField {
    border: 2px solid #e74c3c;
    background: #fff5f5;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    border: 2px solid #00915A;
    border-radius: 6px;
    selection-background-color: #e8f5f0;
    selection-color: #00915A;
}

/* ── Calendar Popup ── */
QCalendarWidget {
    background-color: white;
    color: #2c3e50;
}

QCalendarWidget QToolButton {
    background-color: white;
    color: #2c3e50;
    border: none;
    padding: 6px;
}

QCalendarWidget QToolButton:hover {
    background-color: #e8f5f0;
    color: #00915A;
    border-radius: 4px;
}

QCalendarWidget QMenu {
    background-color: white;
    color: #2c3e50;
}

QCalendarWidget QSpinBox {
    background-color: white;
    color: #2c3e50;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}

QCalendarWidget QAbstractItemView {
    background-color: white;
    color: #2c3e50;
    selection-background-color: #00915A;
    selection-color: white;
    outline: none;
}

QCalendarWidget QAbstractItemView:disabled {
    color: #bbb;
}

QCalendarWidget #qt_calendar_navigationbar {
    background-color: #00915A;
    padding: 4px;
}

QCalendarWidget #qt_calendar_prevmonth,
QCalendarWidget #qt_calendar_nextmonth {
    color: white;
    border: none;
    padding: 6px;
}

QCalendarWidget #qt_calendar_prevmonth:hover,
QCalendarWidget #qt_calendar_nextmonth:hover {
    background-color: #007047;
    border-radius: 4px;
}

QCalendarWidget #qt_calendar_monthbutton,
QCalendarWidget #qt_calendar_yearbutton {
    color: white;
    background: transparent;
    border: none;
    padding: 4px 8px;
    font-weight: 700;
}

/* ── Buttons ── */
QPushButton#generateBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00915A, stop:1 #007047);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
QPushButton#generateBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #007047, stop:1 #005a36);
}
QPushButton#generateBtn:pressed { background: #005a36; }

QPushButton#clearBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #e74c3c, stop:1 #c0392b);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton#clearBtn:hover { background: #c0392b; }

QPushButton#addIncBtn {
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    color: #2c3e50;
}
QPushButton#addIncBtn:hover {
    border-color: #00915A;
    background: #e8f5f0;
    color: #00915A;
}

QPushButton#copyBtn {
    background: white;
    border: 2px solid #00a1e0;
    border-radius: 6px;
    padding: 6px;
    color: #00a1e0;
    font-weight: 600;
    min-width: 40px;
}
QPushButton#copyBtn:hover {
    background: #00a1e0;
    color: white;
}

QPushButton#removeBtn {
    background: transparent;
    border: none;
    color: #aaa;
    font-size: 18px;
    font-weight: bold;
    padding: 0 4px;
}
QPushButton#removeBtn:hover { color: #e74c3c; }

QPushButton#settingsBtn, QPushButton#historyBtn {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton#settingsBtn:hover, QPushButton#historyBtn:hover {
    border-color: #00915A;
    background: #e8f5f0;
    color: #00915A;
}

/* ── Checkboxes ── */
QCheckBox {
    spacing: 6px;
    font-weight: 500;
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
    image: url(none);
}
QCheckBox::indicator:hover { border-color: #00915A; }

/* ── Scroll Area ── */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    width: 8px;
    background: #f5f7fa;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #00915A;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ── Table Widget ── */
QTableWidget {
    gridline-color: #e0e0e0;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background: white;
}
QTableWidget::item { padding: 4px; }
QTableWidget::item:selected {
    background: #e8f5f0;
    color: #00915A;
}
QHeaderView::section {
    background-color: #00915A;
    color: white;
    font-weight: 700;
    padding: 8px;
    border: none;
}

/* ── Tab Widget ── */
QTabWidget::pane {
    border: none;
    background: transparent;
}
QTabBar::tab {
    background: white;
    border: 2px solid #e0e0e0;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    font-weight: 600;
    color: #7f8c8d;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #00915A;
    color: white;
    border-color: #00915A;
}
QTabBar::tab:hover:!selected {
    background: #e8f5f0;
    color: #00915A;
    border-color: #00915A;
}

/* ── Status Colors ── */
QLabel#statusAvailable  { background: #6fc040; color: white; border-radius: 4px; padding: 4px 10px; font-weight: 700; }
QLabel#statusUnavailable{ background: #e74c3c; color: white; border-radius: 4px; padding: 4px 10px; font-weight: 700; }
QLabel#statusDegraded   { background: #ffd500; color: black; border-radius: 4px; padding: 4px 10px; font-weight: 700; }
QLabel#statusObservation{ background: #0070d2; color: white; border-radius: 4px; padding: 4px 10px; font-weight: 700; }

/* ── Group Boxes ── */
QGroupBox {
    font-weight: 700;
    color: #00915A;
    border: 2px solid #e8f5f0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    background: white;
}

/* ── Separator ── */
QFrame[frameShape="4"] { color: #e0e0e0; }
"""

STATUS_COLORS = {
    "Available": ("status-available", "#6fc040", "white"),
    "Unavailable": ("status-unavailable", "#e74c3c", "white"),
    "Degraded": ("status-degraded", "#ffd500", "black"),
    "Under Observation": ("status-observation", "#0070d2", "white"),
}
