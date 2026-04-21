"""
Output Panel - displays generated email notification and the Outlook integration button.
"""

import sys, os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,QScrollArea, QMessageBox, QApplication
)
from PySide6.QtCore import QSize, QTimer, Qt, QMimeData
from PySide6.QtGui import QIcon

from .widgets import SectionTitle, SectionCard, CopyField
from .config import DEPARTMENT_DESK, DEPARTMENT_NAME
from .data_manager import (
    get_recipients, get_cc_recipients, format_list, format_services,
    format_datetime_display, load_data, sort_progress_entries, get_cob_date
)
from .email_builder import NotificationTable, build_email_html


class OutputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_payload: dict | None = None
        self._build_ui()


    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(16)

        card = SectionCard()
        layout.addWidget(card)

        card_layout = card.layout()
        card_layout.addWidget(SectionTitle("Generated Notification"))

        # Email header fields
        self.to_field = CopyField("To", label_width=60, boxed=True)
        card_layout.addWidget(self.to_field)

        self.cc_field = CopyField("Cc", label_width=60, boxed=True)   # ← add this
        card_layout.addWidget(self.cc_field)

        self.bcc_field = CopyField("Bcc", label_width=60, boxed=True)
        card_layout.addWidget(self.bcc_field)

        self.subject_field = CopyField("Subject", label_width=60, boxed=False)
        card_layout.addWidget(self.subject_field)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        card_layout.addWidget(sep)

        # Notification table
        self._table_widget = NotificationTable()
        card_layout.addWidget(self._table_widget)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._copy_table_btn = QPushButton()
        self._copy_table_btn.setObjectName("copyBtn")
        self._copy_table_btn.setIcon(QIcon(":/icons/copy.png"))
        self._copy_table_btn.setIconSize(QSize(20, 20))
        self._copy_table_btn.setMinimumHeight(40)
        self._copy_table_btn.clicked.connect(self._copy_table_html)

        self._outlook_btn = QPushButton()
        self._outlook_btn.setObjectName("generateBtn")
        self._outlook_btn.setIcon(QIcon(":/icons/outlook.png"))
        self._outlook_btn.setIconSize(QSize(20, 20))
        self._outlook_btn.setMinimumHeight(40)
        self._outlook_btn.clicked.connect(self._open_outlook)

        btn_row.addWidget(self._copy_table_btn, 1)
        btn_row.addWidget(self._outlook_btn, 3)
        card_layout.addLayout(btn_row)

        # Initially hide action buttons
        self._copy_table_btn.hide()
        self._outlook_btn.hide()


    def _build_incident_str(self, incidents: list) -> str:
        """Build incident display string, omitting P4 priority."""
        parts = []
        for inc in incidents:
            p = inc.get("priority", "")
            parts.append(f"{inc['number']} [{p}]" if p and p != "P4" else inc["number"])
        return ", ".join(parts)

    def _build_email_data(self, payload: dict, data: dict) -> dict:
        """Extract and format all common fields needed for email generation."""
        services_raw = payload["services"]
        services_str = format_services(services_raw)
        users = payload["users"]
        status = payload["status"]

        all_regions = {"APAC", "EMEA", "AMERICAS"}
        users_str = "GLOBAL" if set(users) >= all_regions else format_list(users)

        if "DL" in services_raw:
            subject = f"[{status}] {DEPARTMENT_NAME} Incident Management Notification : {services_str} for COB {get_cob_date()}"
        else:
            subject = f"[{status}] {DEPARTMENT_NAME} Incident Management Notification : {services_str}"

        return {
            "services_raw": services_raw,
            "services_str": services_str,
            "users_str": users_str,
            "status": status,
            "subject": subject,
            "incidents_str": self._build_incident_str(payload["incidents"]),
            "start_str": format_datetime_display(payload.get("start_time", "")),
            "end_str": format_datetime_display(payload.get("end_time", "")),
            "next_str": format_datetime_display(payload.get("next_update", "")),
            "description": payload.get("description", ""),
            "impact": payload.get("impact", ""),
            "progress_entries": sort_progress_entries(data.get("progress_entries", [])),
            "bcc_emails": get_recipients(payload["users"]),
            "cc_emails": get_cc_recipients(),
        }


    # ── Public API ────────────────────────────────────────────────────────────
    def populate(self, payload: dict):
        self._current_payload = payload
        data = load_data()
        d = self._build_email_data(payload, data)

        self.to_field.set_text(DEPARTMENT_DESK)
        self.cc_field.set_text("; ".join(d["cc_emails"]))
        self.bcc_field.set_text("; ".join(d["bcc_emails"]))
        self.subject_field.set_text(d["subject"])

        self._table_widget.populate(
            services=d["services_str"],
            users=d["users_str"],
            status=d["status"],
            incidents_str=d["incidents_str"],
            start_time=d["start_str"],
            end_time=d["end_str"],
            next_update=d["next_str"],
            description=d["description"],
            impact=d["impact"],
            progress_entries=d["progress_entries"],
        )
        self._copy_table_btn.show()
        self._outlook_btn.show()


    def clear(self):
        self.to_field.set_text("")
        self.cc_field.set_text("")
        self.bcc_field.set_text("")
        self.subject_field.set_text("")
        self._table_widget._table.clearContents()
        self._table_widget._table.setRowCount(0)
        self._copy_table_btn.hide()
        self._outlook_btn.hide()
        self._current_payload = None


    # ── Outlook integration ───────────────────────────────────────────────────
    def _open_outlook(self):
        if not self._current_payload:
            return
        try:
            import win32com.client
        except ImportError:
            QMessageBox.information(self, "pywin32 Not Found", "pywin32 is not installed.\nInstall with: pip install pywin32")
            return

        data = load_data()
        d = self._build_email_data(self._current_payload, data)

        html_body = build_email_html(
            services=d["services_str"], users=d["users_str"], status=d["status"],
            incidents_str=d["incidents_str"], start_time=d["start_str"],
            end_time=d["end_str"], next_update=d["next_str"],
            description=d["description"], impact=d["impact"],
            progress_entries=d["progress_entries"],
        )

        outlook = _get_outlook_instance(win32com)
        if outlook is None:
            _open_mailto_fallback(DEPARTMENT_DESK, d["subject"], self)
            return

        try:
            mail = outlook.CreateItem(0)
            if DEPARTMENT_DESK:
                mail.To = DEPARTMENT_DESK
            mail.CC = "; ".join(d["cc_emails"])
            mail.BCC = "; ".join(d["bcc_emails"])
            mail.Subject = d["subject"]
            mail.Body = ""
            mail.HTMLBody = html_body
            mail.Display(False)
        except Exception as e:
            QMessageBox.critical(self, "Outlook Error", f"Failed to create email draft:\n{e}")


    # ── Copy table as HTML ────────────────────────────────────────────────────
    def _copy_table_html(self):
        if not self._current_payload:
            return
        data = load_data()
        d = self._build_email_data(self._current_payload, data)

        html = build_email_html(
            services=d["services_str"], users=d["users_str"], status=d["status"],
            incidents_str=d["incidents_str"], start_time=d["start_str"],
            end_time=d["end_str"], next_update=d["next_str"],
            description=d["description"], impact=d["impact"],
            progress_entries=d["progress_entries"],
        )
        mime = QMimeData()
        mime.setHtml(html)
        mime.setText(html)
        QApplication.clipboard().setMimeData(mime)

        orig_icon = self._copy_table_btn.icon()
        self._copy_table_btn.setIcon(QIcon(":/icons/copy_done.png"))
        QTimer.singleShot(1500, lambda: self._copy_table_btn.setIcon(orig_icon))


# ── Outlook helpers ───────────────────────────────────────────────────────────
def _get_outlook_instance(win32com):
    """
    Try every known strategy to get an Outlook COM Application object.
    Returns the object on success, or None if all attempts fail.

    Strategy order:
      1. GetActiveObject  - reuse an already-running Outlook instance
         (avoids re-registering COM class; works even when registry ProgID
          is missing for Dispatch)
      2. Dispatch with the canonical ProgID "Outlook.Application"
      3. Dispatch with the versioned ProgIDs for Outlook 2016-2021/365
         (sometimes only the versioned key exists in the registry)
      4. EnsureDispatch   - forces early-binding / COM type-lib generation
    """
    # 1. Latch onto a running Outlook process (most reliable)
    try:
        return win32com.client.GetActiveObject("Outlook.Application")
    except Exception:
        pass

    # 2. Standard Dispatch
    try:
        return win32com.client.Dispatch("Outlook.Application")
    except Exception:
        pass

    # 3. Versioned ProgIDs  (Outlook 16.0 = 2016 / 2019 / 2021 / 365)
    for progid in (
        "Outlook.Application.16",
        "Outlook.Application.15",  # 2013
        "Outlook.Application.14",  # 2010
    ):
        try:
            return win32com.client.Dispatch(progid)
        except Exception:
            continue

    # 4. EnsureDispatch (generates type-lib on the fly)
    try:
        return win32com.client.EnsureDispatch("Outlook.Application")
    except Exception:
        pass

    return None


def _open_mailto_fallback(dept_desk: str, subject: str, parent):
    """
    When COM is completely unavailable, open a plain mailto: link so the
    user's default mail client opens with at least the To and Subject pre-filled.
    Also show a helpful diagnostic message.
    """
    import urllib.parse, subprocess

    QMessageBox.warning(
        parent,
        "Outlook COM Unavailable",
        "Could not connect to Microsoft Outlook via COM.\n\n"
        "Common causes:\n"
        "  • Outlook is not installed, or is a Store/UWP edition\n"
        "    (Store versions don't register COM — use the MSI/EXE installer)\n"
        "  • The COM registration is broken — try running:\n"
        "      outlook.exe /regserver\n"
        "    in a command prompt, then retry\n"
        "  • Run 'pip install --upgrade pywin32' and then\n"
        "    'python Scripts/pywin32_postinstall.py -install'\n\n"
        "Falling back to your default mail client (Subject and To will be pre-filled;\n"
        "the HTML table body cannot be passed via mailto).\n\n"
        "Tip: use the 'Copy Table' button to copy the formatted table, then\n"
        "paste it into the email body after it opens.",
    )

    params = urllib.parse.urlencode({"subject": subject}, quote_via=urllib.parse.quote)
    mailto = f"mailto:{urllib.parse.quote(dept_desk)}?{params}"

    try:
        if sys.platform == "win32":
            os.startfile(mailto)
        else:
            subprocess.Popen(["xdg-open", mailto])
    except Exception:
        pass  # Nothing more we can do
