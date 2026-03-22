"""
Incident Management System - PySide6
Entry point
"""
import resources_rc
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont

from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Incident Management System")
    app.setOrganizationName("FOREX Service Desk")

    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
