"""
Main Window - orchestrates all panels.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSplitter, QStackedWidget,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QPalette

from .styles import MAIN_STYLE
from .form_panel import FormPanel
from .output_panel import OutputPanel
from .settings_page import SettingsPage
from .data_manager import clear_data, load_data, save_data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Incident Management System")
        self.setMinimumSize(1200, 720)
        self.resize(1400, 820)
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header
        root.addWidget(self._build_header())

        # Stacked: main view vs settings
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        # Main view (form + output side by side)
        main_view = QWidget()
        main_layout = QHBoxLayout(main_view)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        self._form_panel = FormPanel()
        self._output_panel = OutputPanel()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._form_panel)
        splitter.addWidget(self._output_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([600, 600])
        main_layout.addWidget(splitter)

        self._stack.addWidget(main_view)

        # Settings view
        self._settings_page = SettingsPage()
        self._stack.addWidget(self._settings_page)

        # Connect signals
        self._form_panel.generateRequested.connect(self._output_panel.populate)
        self._settings_page.dataChanged.connect(self._on_settings_saved)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("card")
        header.setFixedHeight(72)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)

        # Logo
        logo = QLabel("IM")
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #00915A,stop:1 #007047);"
            "color: white; font-weight: 800; font-size: 16px;"
            "border-radius: 10px;"
        )
        layout.addWidget(logo)

        title = QLabel("Incident Management System")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(title)

        layout.addStretch()

        # Nav buttons
        self._main_btn = QPushButton("📋  Main Form")
        self._main_btn.setObjectName("settingsBtn")
        self._main_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        layout.addWidget(self._main_btn)

        self._settings_btn = QPushButton("⚙  Settings / Data")
        self._settings_btn.setObjectName("settingsBtn")
        self._settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(self._settings_btn)

        clear_btn = QPushButton("🗑  Clear All")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._clear_all)
        layout.addWidget(clear_btn)

        return header

    def _open_settings(self):
        self._settings_page._load()  # Refresh before showing
        self._stack.setCurrentIndex(1)

    def _on_settings_saved(self, data: dict):
        """Called when settings page saves – sync form panel."""
        self._form_panel.reload_from_data(data)
        self._stack.setCurrentIndex(0)

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "This will clear all saved data including incidents and progress entries.\nProceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            clear_data()
            self._form_panel.clear_form()
