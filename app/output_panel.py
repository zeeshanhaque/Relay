"""
Output Panel - displays generated email notification with copy buttons
and the Outlook integration button.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QMessageBox, QApplication
)
from PySide6.QtCore import QSize, QTimer, Qt, QMimeData
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QClipboard

from .widgets import SectionTitle, SectionCard, CopyField, StatusBadge
from .data_manager import (
    get_recipients, format_list, format_datetime_display, load_data, TO_RECIPIENT
)
from .styles import STATUS_COLORS


class OutputPanel(QWidget):
    """Right panel: generated email preview."""

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
        self.to_field = CopyField("To")
        card_layout.addWidget(self.to_field)

        self.bcc_field = CopyField("Bcc")
        card_layout.addWidget(self.bcc_field)

        self.subject_field = CopyField("Subject")
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

        btn_row.addWidget(self._copy_table_btn)
        btn_row.addWidget(self._outlook_btn)
        card_layout.addLayout(btn_row)

        # Initially hide action buttons
        self._copy_table_btn.hide()
        self._outlook_btn.hide()

    # ── Public API ────────────────────────────────────────────────────────────

    def populate(self, payload: dict):
        """Populate all output fields from the generate payload."""
        self._current_payload = payload
        data = load_data()

        services = payload["services"]
        users = payload["users"]
        status = payload["status"]
        incidents = payload["incidents"]

        services_str = format_list(services)
        all_regions = {"APAC", "EMEA", "AMERICAS"}
        if set(users) >= all_regions:
            users_str = "GLOBAL"
        else:
            users_str = format_list(users)

        # Build incident display string
        inc_parts = []
        for inc in incidents:
            p = inc.get("priority", "")
            inc_parts.append(f"{inc['number']} [{p}]" if p else inc["number"])
        incidents_str = ", ".join(inc_parts)

        # Recipients
        to_addr = TO_RECIPIENT
        bcc_emails = get_recipients(users)
        bcc_str = "; ".join(bcc_emails)
        subject = f"[{status}] FOREX Incident Management Notification : {services_str}"

        self.to_field.set_text(to_addr)
        self.bcc_field.set_text(bcc_str)
        self.subject_field.set_text(subject)

        # Times
        start_str = format_datetime_display(payload.get("start_time", ""))
        end_str = format_datetime_display(payload.get("end_time", ""))
        next_str = format_datetime_display(payload.get("next_update", ""))

        # Progress entries from storage
        progress_entries = data.get("progress_entries", [])

        self._table_widget.populate(
            services=services_str,
            users=users_str,
            status=status,
            incidents_str=incidents_str,
            start_time=start_str,
            end_time=end_str,
            next_update=next_str,
            description=payload.get("description", ""),
            impact=payload.get("impact", ""),
            progress_entries=progress_entries,
        )

        self._copy_table_btn.show()
        self._outlook_btn.show()

    
    def clear(self):
        self.to_field.set_text("")
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
            QMessageBox.information(
                self, "pywin32 Not Found",
                "pywin32 is not installed or not available.\n\n"
                "Install it with:  pip install pywin32\n\n"
                "This feature is only available on Windows with Microsoft Outlook installed."
            )
            return

        # Build email content first
        data = load_data()
        payload = self._current_payload
        services = format_list(payload["services"])
        users = payload["users"]
        status = payload["status"]
        incidents = payload["incidents"]

        inc_parts = []
        for inc in incidents:
            p = inc.get("priority", "")
            inc_parts.append(f"{inc['number']} [{p}]" if p else inc["number"])
        incidents_str = ", ".join(inc_parts)

        all_regions = {"APAC", "EMEA", "AMERICAS"}
        users_str = "GLOBAL" if set(users) >= all_regions else format_list(users)

        start_str = format_datetime_display(payload.get("start_time", ""))
        end_str = format_datetime_display(payload.get("end_time", ""))
        next_str = format_datetime_display(payload.get("next_update", ""))

        to_addr = TO_RECIPIENT
        bcc_emails = get_recipients(users)
        bcc_str = "; ".join(bcc_emails)
        subject = f"[{status}] FOREX Incident Management Notification : {services}"

        progress_entries = data.get("progress_entries", [])

        html_body = build_email_html(
            services=services,
            users=users_str,
            status=status,
            incidents_str=incidents_str,
            start_time=start_str,
            end_time=end_str,
            next_update=next_str,
            description=payload.get("description", ""),
            impact=payload.get("impact", ""),
            progress_entries=progress_entries,
        )

        # Try to get/create an Outlook COM instance using multiple strategies
        outlook = _get_outlook_instance(win32com)
        if outlook is None:
            # All COM strategies failed — fall back to mailto: URI
            _open_mailto_fallback(to_addr, subject, self)
            return

        try:
            mail = outlook.CreateItem(0)  # 0 = olMailItem

            # ── To ────────────────────────────────────────────────────────────
            # Use Recipients.Add with Type=1 (olTo) for reliable delivery
            if to_addr:
                recip = mail.Recipients.Add(to_addr)
                recip.Type = 1          # olTo = 1

            # ── BCC ───────────────────────────────────────────────────────────
            # mail.BCC = "string" is unreliable across Outlook versions.
            # Adding each address individually via Recipients.Add with
            # Type=3 (olBCC) is the only approach that works consistently.
            for email in bcc_emails:
                email = email.strip()
                if email:
                    recip = mail.Recipients.Add(email)
                    recip.Type = 3      # olBCC = 3

            # Resolve all recipients (validates addresses)
            mail.Recipients.ResolveAll()

            # ── Subject ───────────────────────────────────────────────────────
            mail.Subject = subject

            # ── Body ──────────────────────────────────────────────────────────
            # HTMLBody MUST be set before Display(); setting it after causes
            # Outlook to silently discard it in newer Microsoft 365 builds.
            # Clear Body first to prevent plain-text clobbering the HTML renderer.
            mail.Body = ""
            mail.HTMLBody = html_body

            # Display the draft — False = non-modal
            mail.Display(False)

        except Exception as e:
            QMessageBox.critical(self, "Outlook Error",
                                 f"Outlook opened but failed to create the email draft:\n{e}")

    # ── Copy table as HTML ────────────────────────────────────────────────────

    def _copy_table_html(self):
        if not self._current_payload:
            return

        data = load_data()
        payload = self._current_payload
        services = format_list(payload["services"])
        users = payload["users"]
        status = payload["status"]
        incidents = payload["incidents"]

        inc_parts = []
        for inc in incidents:
            p = inc.get("priority", "")
            inc_parts.append(f"{inc['number']} [{p}]" if p else inc["number"])
        incidents_str = ", ".join(inc_parts)

        all_regions = {"APAC", "EMEA", "AMERICAS"}
        users_str = "GLOBAL" if set(users) >= all_regions else format_list(users)

        start_str = format_datetime_display(payload.get("start_time", ""))
        end_str = format_datetime_display(payload.get("end_time", ""))
        next_str = format_datetime_display(payload.get("next_update", ""))
        progress_entries = data.get("progress_entries", [])

        html = build_email_html(
            services=services,
            users=users_str,
            status=status,
            incidents_str=incidents_str,
            start_time=start_str,
            end_time=end_str,
            next_update=next_str,
            description=payload.get("description", ""),
            impact=payload.get("impact", ""),
            progress_entries=progress_entries,
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
        "Outlook.Application.15",   # 2013
        "Outlook.Application.14",   # 2010
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


def _open_mailto_fallback(to_addr: str, subject: str, parent):
    """
    When COM is completely unavailable, open a plain mailto: link so the
    user's default mail client opens with at least the To and Subject pre-filled.
    Also show a helpful diagnostic message.
    """
    import urllib.parse, subprocess, sys

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
        "paste it into the email body after it opens."
    )

    params = urllib.parse.urlencode({"subject": subject}, quote_via=urllib.parse.quote)
    mailto = f"mailto:{urllib.parse.quote(to_addr)}?{params}"

    try:
        if sys.platform == "win32":
            import os
            os.startfile(mailto)
        else:
            subprocess.Popen(["xdg-open", mailto])
    except Exception:
        pass  # Nothing more we can do


# ── Notification table widget ─────────────────────────────────────────────────

class NotificationTable(QWidget):
    """Renders the incident notification in a structured QTableWidget."""

    STATUS_COLORS = {
        "Available":        ("#6fc040", "#ffffff"),
        "Unavailable":      ("#e74c3c", "#ffffff"),
        "Degraded":         ("#ffd500", "#000000"),
        "Under Observation":("#0070d2", "#ffffff"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.horizontalHeader().setVisible(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.NoSelection)
        layout.addWidget(self._table)

    def populate(self, services, users, status, incidents_str,
                 start_time, end_time, next_update, description, impact,
                 progress_entries: list[dict]):

        rows_data = []

        # Title row
        rows_data.append(("title", "FOREX Service Desk Incident Notification"))

        # Details rows
        status_bg, status_fg = self.STATUS_COLORS.get(status, ("#aaa", "#fff"))
        rows_data.append(("detail", [
            ("Service/Application(s) Impacted", services),
            ("Service Status", status, status_bg, status_fg),
        ]))
        rows_data.append(("detail_rowspan", [
            ("Users Impacted", users),
            ("Time Started [LT]", start_time),
            ("Time Ended [LT]", end_time),
        ]))
        rows_data.append(("detail", [
            ("Incident #", incidents_str),
            ("Next Update At [LT]", next_update),
        ]))
        rows_data.append(("wide", "Description", description))
        rows_data.append(("wide", "Impact", impact))

        if progress_entries:
            rows_data.append(("progress_header",))
            rows_data.append(("progress_col_header",))
            for entry in progress_entries:
                rows_data.append(("progress_row", entry["datetime"], entry["text"]))

        # Count total rows needed
        total_rows = 0
        for row in rows_data:
            if row[0] == "detail_rowspan":
                total_rows += 2
            else:
                total_rows += 1

        self._table.clearContents()
        self._table.setRowCount(total_rows)

        r = 0
        GREEN = QColor("#00915A")
        GREEN_TEXT = QColor("white")
        GREY = QColor("#f0f0f0")

        for row in rows_data:
            kind = row[0]

            if kind == "title":
                # Logo cell (left half)
                import base64, os
                logo_path = os.path.join(os.path.dirname(__file__), "..", "resources", "assets", "BNPP_logo.jpg")
                if os.path.exists(logo_path):
                    logo_lbl = QLabel()
                    pixmap = QPixmap(logo_path)
                    logo_lbl.setPixmap(pixmap.scaledToHeight(40, Qt.SmoothTransformation))
                    logo_lbl.setAlignment(Qt.AlignCenter)
                    self._table.setCellWidget(r, 0, logo_lbl)
                    self._table.setSpan(r, 0, 1, 2)
                
                # Title cell (right half)
                item = QTableWidgetItem(row[1])
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(self._bold_font(14))
                item.setForeground(QColor("#00915A"))
                self._table.setItem(r, 2, item)
                self._table.setSpan(r, 2, 1, 2)
                self._table.setRowHeight(r, 60)
                r += 1

            elif kind == "detail":
                pairs = row[1]
                # Pairs: list of (label, value) or (label, value, bg, fg)
                col = 0
                for pair in pairs:
                    lbl_item = QTableWidgetItem(pair[0])
                    lbl_item.setBackground(GREEN)
                    lbl_item.setForeground(GREEN_TEXT)
                    lbl_item.setFont(self._bold_font())
                    self._table.setItem(r, col, lbl_item)

                    val_item = QTableWidgetItem(pair[1])
                    if len(pair) > 2:
                        val_item.setBackground(QColor(pair[2]))
                        val_item.setForeground(QColor(pair[3]))
                        val_item.setFont(self._bold_font())
                        val_item.setTextAlignment(Qt.AlignCenter)
                    self._table.setItem(r, col + 1, val_item)
                    col += 2
                self._table.setRowHeight(r, 40)
                r += 1

            elif kind == "detail_rowspan":
                # Row with users spanning 2 rows, and time started/ended
                pairs = row[1]
                # users: col 0-1, spans 2 rows
                lbl_u = QTableWidgetItem(pairs[0][0])
                lbl_u.setBackground(GREEN); lbl_u.setForeground(GREEN_TEXT)
                lbl_u.setFont(self._bold_font())
                self._table.setItem(r, 0, lbl_u)
                val_u = QTableWidgetItem(pairs[0][1])
                self._table.setItem(r, 1, val_u)
                self._table.setSpan(r, 0, 2, 1)
                self._table.setSpan(r, 1, 2, 1)

                # Time Started
                lbl_s = QTableWidgetItem(pairs[1][0])
                lbl_s.setBackground(GREEN); lbl_s.setForeground(GREEN_TEXT)
                lbl_s.setFont(self._bold_font())
                self._table.setItem(r, 2, lbl_s)
                val_s = QTableWidgetItem(pairs[1][1])
                self._table.setItem(r, 3, val_s)
                self._table.setRowHeight(r, 36)
                r += 1

                # Time Ended
                lbl_e = QTableWidgetItem(pairs[2][0])
                lbl_e.setBackground(GREEN); lbl_e.setForeground(GREEN_TEXT)
                lbl_e.setFont(self._bold_font())
                self._table.setItem(r, 2, lbl_e)
                val_e = QTableWidgetItem(pairs[2][1])
                self._table.setItem(r, 3, val_e)
                self._table.setRowHeight(r, 36)
                r += 1

            elif kind == "wide":
                lbl_item = QTableWidgetItem(row[1])
                lbl_item.setBackground(GREEN); lbl_item.setForeground(GREEN_TEXT)
                lbl_item.setFont(self._bold_font())
                self._table.setItem(r, 0, lbl_item)

                val_item = QTableWidgetItem(row[2])
                val_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self._table.setItem(r, 1, val_item)
                self._table.setSpan(r, 1, 1, 3)
                self._table.setRowHeight(r, 60)
                r += 1

            elif kind == "progress_header":
                item = QTableWidgetItem("Progress in Chronological Order")
                item.setBackground(GREY)
                item.setFont(self._bold_font())
                item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(r, 0, item)
                self._table.setSpan(r, 0, 1, 4)
                self._table.setRowHeight(r, 36)
                r += 1

            elif kind == "progress_col_header":
                dt_item = QTableWidgetItem("Date/Time [LT]")
                dt_item.setBackground(GREY)
                dt_item.setFont(self._bold_font())
                dt_item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(r, 0, dt_item)

                det_item = QTableWidgetItem("Details")
                det_item.setBackground(GREY)
                det_item.setFont(self._bold_font())
                det_item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(r, 1, det_item)
                self._table.setSpan(r, 1, 1, 3)
                self._table.setRowHeight(r, 36)
                r += 1

            elif kind == "progress_row":
                dt_item = QTableWidgetItem(row[1])
                dt_item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(r, 0, dt_item)

                text_item = QTableWidgetItem(row[2])
                self._table.setItem(r, 1, text_item)
                self._table.setSpan(r, 1, 1, 3)
                self._table.setRowHeight(r, 36)
                r += 1

        self._table.resizeRowsToContents()

    def _bold_font(self, size: int = 11) -> QFont:
        f = QFont()
        f.setBold(True)
        f.setPointSize(size)
        return f


# ── HTML email builder ─────────────────────────────────────────────────────────

def build_email_html(services, users, status, incidents_str, start_time,
                     end_time, next_update, description, impact,
                     progress_entries: list[dict]) -> str:

    import base64, os
    logo_b64 = ""
    logo_path = os.path.join(os.path.dirname(__file__), "..", "resources", "assets", "BNPP_logo.jpg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
    
    logo_html = (
        f'<img src="data:image/jpeg;base64,{logo_b64}" alt="Logo" style="width:100%; height:100%;"/>'
        if logo_b64 else ""
    )


    status_styles = {
        "Available":        "background:#6fc040;color:white;",
        "Unavailable":      "background:#e74c3c;color:white;",
        "Degraded":         "background:#ffd500;color:black;",
        "Under Observation":"background:#0070d2;color:white;",
    }
    status_style = status_styles.get(status, "background:#aaa;color:white;")

    progress_rows = ""
    if progress_entries:
        progress_rows = """
        <tr>
            <td colspan="4" style="background:#f0f0f0;font-weight:bold;text-align:center;
                border:1px solid #000;padding:8px;">Progress in Chronological Order</td>
        </tr>
        <tr>
            <td style="background:#f0f0f0;font-weight:bold;text-align:center;
                border:1px solid #000;padding:8px;">Date/Time [LT]</td>
            <td colspan="3" style="background:#f0f0f0;font-weight:bold;text-align:center;
                border:1px solid #000;padding:8px;">Details</td>
        </tr>
        """
        for entry in progress_entries:
            progress_rows += f"""
        <tr>
            <td style="text-align:center;border:1px solid #000;padding:8px;">{entry['datetime']}</td>
            <td colspan="3" style="border:1px solid #000;padding:8px;">{entry['text']}</td>
        </tr>"""

    html = f"""
<html>
<head>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td {{ border: 1px solid #000; padding: 6px; height: 36px; }}
  .q {{ background: #00915A; color: white; font-weight: bold; width: 25%; }}
  .a {{ width: 25%; }}
  .title {{ color: #00915A; font-weight: bold; font-size: 17px; text-align: center; }}
</style>
</head>
<body>
<table>
  <tr>
    <td colspan="2" style="text-align:center; vertical-align:middle; border:1px solid #000; width:100%; height:100%; padding:0;">
      {logo_html}
    </td>
    <td colspan="2" class="title">FOREX Service Desk Incident Notification</td>
  </tr>
  <tr>
    <td class="q">Service/Application(s) Impacted</td>
    <td class="a">{services}</td>
    <td class="q">Service Status</td>
    <td class="a" style="{status_style};font-weight:bold;text-align:center;">{status}</td>
  </tr>
  <tr>
    <td class="q" rowspan="2">Users Impacted</td>
    <td class="a" rowspan="2">{users}</td>
    <td class="q">Time Started [LT]</td>
    <td class="a">{start_time}</td>
  </tr>
  <tr>
    <td class="q">Time Ended [LT]</td>
    <td class="a">{end_time}</td>
  </tr>
  <tr>
    <td class="q">Incident #</td>
    <td class="a">{incidents_str}</td>
    <td class="q">Next Update At [LT]</td>
    <td class="a">{next_update}</td>
  </tr>
  <tr>
    <td class="q">Description</td>
    <td colspan="3" class="a">{description}</td>
  </tr>
  <tr>
    <td class="q">Impact</td>
    <td colspan="3" class="a">{impact}</td>
  </tr>
  {progress_rows}
</table>
</body>
</html>
"""
    return html
