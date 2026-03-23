"""
Main Window - orchestrates all panels.
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSplitter, QStackedWidget,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap

from .styles import MAIN_STYLE
from .form_panel import FormPanel
from .output_panel import OutputPanel
from .settings_page import SettingsPage
from .data_manager import clear_data, load_data


def _get_logo_path() -> str:
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent
    return str(base / "resources" / "assets" / "BNPP_logo.jpg")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relay - Incident Communication")
        self.setWindowIcon(QIcon(":/icons/relay_icon.png"))
        self.setMinimumSize(1200, 720)
        self.resize(1400, 820)
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        self.showMaximized()

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

        self._switch_main_view(0)
        self._auto_populate()

    
    def _auto_populate(self):
        data = load_data()
        form = data.get("form", {})

        if not (
            form.get("selected_services")
            and form.get("selected_users")
            and form.get("incidents")
            and form.get("description")
            and form.get("impact")
        ):
            return

        status = form.get("service_status", "Degraded")

        payload = {
            "services":    form.get("selected_services", []),
            "users":       form.get("selected_users", []),
            "status":      status,
            "incidents":   form.get("incidents", []),
            "start_time":  form.get("start_time", ""),
            "end_time":    form.get("end_time", ""),
            "next_update": form.get("next_update", ""),
            "description": form.get("description", ""),
            "impact":      form.get("impact", ""),
        }

        QTimer.singleShot(100, lambda: self._output_panel.populate(payload))


    def _switch_main_view(self, index: int):
        self._stack.setCurrentIndex(index)
        active_style = (
            "border: 2px solid #00915A; border-radius: 8px;"
            "padding: 8px 16px; background: #e8f5f0;"
        )
        inactive_style = (
            "border: 2px solid #e0e0e0; border-radius: 8px;"
            "padding: 8px 16px; background: white;"
        )
        self._main_btn.setStyleSheet(active_style if index == 0 else inactive_style)
        self._settings_btn.setStyleSheet(active_style if index == 1 else inactive_style)


    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("card")
        header.setFixedHeight(72)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)

        # Logo
        logo = QLabel()
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(":/icons/relay_icon.png")
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(logo)

        title = QLabel("Relay - Incident Communication")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(title)

        layout.addStretch()

        self._main_btn = QPushButton()
        self._main_btn.setObjectName("settingsBtn")
        self._main_btn.setIcon(QIcon(":/icons/home.png"))
        self._main_btn.setIconSize(QSize(20, 20))
        self._main_btn.clicked.connect(lambda: self._switch_main_view(0))
        layout.addWidget(self._main_btn)

        self._settings_btn = QPushButton()
        self._settings_btn.setObjectName("settingsBtn")
        self._settings_btn.setIcon(QIcon(":/icons/settings.png"))
        self._settings_btn.setIconSize(QSize(20, 20))
        self._settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(self._settings_btn)

        clear_btn = QPushButton()
        clear_btn.setObjectName("clearBtn")
        clear_btn.setIcon(QIcon(":/icons/trash.png"))
        clear_btn.setIconSize(QSize(20, 20))
        clear_btn.clicked.connect(self._clear_all)
        layout.addWidget(clear_btn)

        return header
    

    def _open_settings(self):
        self._settings_page._load()  # Refresh before showing
        self._switch_main_view(1)

    def _on_settings_saved(self, data: dict):
        """Called when settings page saves - sync form panel."""
        self._form_panel.reload_from_data(data)
        self._switch_main_view(0)
        self._auto_populate()

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "This will clear all saved data including incidents and progress entries.\nProceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            clear_data()
            self._form_panel.clear_form()
            self._output_panel.clear()          # ← clear output panel
            self._settings_page._load()         # ← refresh JSON view
