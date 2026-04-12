"""
Email Builder - notification table widget and HTML email generator.
"""
import sys, os, base64
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPixmap

from .config import DEPARTMENT_NAME, DEPARTMENT_DESK


def _get_logo_path() -> str:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent / "_internal"
    else:
        base = Path(__file__).parent.parent
    return str(base / "resources" / "assets" / "BNPP_logo.jpg")


# ── Notification table widget ─────────────────────────────────────────────────

class NotificationTable(QWidget):
    """Renders the incident notification in a structured QTableWidget."""

    STATUS_COLORS = {
        "Available":         ("#6fc040", "#ffffff"),
        "Unavailable":       ("#e74c3c", "#ffffff"),
        "Degraded":          ("#ffd500", "#000000"),
        "Under Observation": ("#0070d2", "#ffffff"),
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

    def populate(
        self,
        services,
        users,
        status,
        incidents_str,
        start_time,
        end_time,
        next_update,
        description,
        impact,
        progress_entries: list[dict],
    ):
        rows_data = []

        rows_data.append(("title", f"{DEPARTMENT_NAME} Service Desk Incident Notification"))

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

        rows_data.append(("footer",))

        # Count total rows
        total_rows = 0
        for row in rows_data:
            if row[0] == "detail_rowspan":
                total_rows += 2
            else:
                total_rows += 1

        self._table.clearContents()
        self._table.clearSpans()
        self._table.setRowCount(total_rows)

        r = 0
        GREEN      = QColor("#00915A")
        GREEN_TEXT = QColor("white")
        GREY       = QColor("#f0f0f0")

        for row in rows_data:
            kind = row[0]

            if kind == "title":
                logo_path = _get_logo_path()
                if os.path.exists(logo_path):
                    logo_lbl = QLabel()
                    pixmap = QPixmap(logo_path)
                    logo_lbl.setPixmap(pixmap.scaledToHeight(40, Qt.SmoothTransformation))
                    logo_lbl.setAlignment(Qt.AlignCenter)
                    self._table.setCellWidget(r, 0, logo_lbl)
                    self._table.setSpan(r, 0, 1, 2)

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
                pairs = row[1]
                lbl_u = QTableWidgetItem(pairs[0][0])
                lbl_u.setBackground(GREEN); lbl_u.setForeground(GREEN_TEXT)
                lbl_u.setFont(self._bold_font())
                self._table.setItem(r, 0, lbl_u)
                val_u = QTableWidgetItem(pairs[0][1])
                self._table.setItem(r, 1, val_u)
                self._table.setSpan(r, 0, 2, 1)
                self._table.setSpan(r, 1, 2, 1)

                lbl_s = QTableWidgetItem(pairs[1][0])
                lbl_s.setBackground(GREEN); lbl_s.setForeground(GREEN_TEXT)
                lbl_s.setFont(self._bold_font())
                self._table.setItem(r, 2, lbl_s)
                val_s = QTableWidgetItem(pairs[1][1])
                self._table.setItem(r, 3, val_s)
                self._table.setRowHeight(r, 36)
                r += 1

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
                item = QTableWidgetItem("Progress (Latest First)")
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

            elif kind == "footer":
                footer_item = QTableWidgetItem(
                    f"For any further queries, please contact: "
                    f"{DEPARTMENT_NAME} Service Desk - {DEPARTMENT_DESK}"
                )
                footer_item.setTextAlignment(Qt.AlignCenter)
                footer_item.setBackground(QColor("#00915A"))
                footer_item.setForeground(QColor("white"))
                f = QFont()
                f.setPointSize(10)
                f.setBold(True)
                footer_item.setFont(f)
                self._table.setItem(r, 0, footer_item)
                self._table.setSpan(r, 0, 1, 4)
                self._table.setRowHeight(r, 28)
                r += 1

        self._table.resizeRowsToContents()

    def _bold_font(self, size: int = 10) -> QFont:
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        return f


# ── HTML email builder ────────────────────────────────────────────────────────

def build_email_html(
    services,
    users,
    status,
    incidents_str,
    start_time,
    end_time,
    next_update,
    description,
    impact,
    progress_entries: list[dict],
) -> str:

    logo_b64 = ""
    logo_path = _get_logo_path()
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    logo_html = (
        f'<img src="data:image/jpeg;base64,{logo_b64}" alt="Logo" '
        f'style="max-width:150px; width:auto; height:auto;"/>'
        if logo_b64 else ""
    )

    status_styles = {
        "Available":         "background:#6fc040;color:white;",
        "Unavailable":       "background:#e74c3c;color:white;",
        "Degraded":          "background:#ffd500;color:black;",
        "Under Observation": "background:#0070d2;color:white;",
    }
    status_style = status_styles.get(status, "background:#aaa;color:white;")

    progress_rows = ""
    if progress_entries:
        progress_rows = """
        <tr>
            <td colspan="4" style="background:#f0f0f0;font-weight:bold;text-align:center;
                border:1px solid #000;padding:8px;">Progress (Latest First)</td>
        </tr>
        <tr>
            <td style="background:#f0f0f0;font-weight:bold;text-align:center;
                border:1px solid #000;padding:8px;">Date/Time [LT]</td>
            <td colspan="3" style="background:#f0f0f0;font-weight:bold;text-align:center;
                border:1px solid #000;padding:8px;">Details</td>
        </tr>"""
        for entry in progress_entries:
            progress_rows += f"""
        <tr>
            <td style="text-align:center;border:1px solid #000;padding:8px;">{entry['datetime']}</td>
            <td colspan="3" style="border:1px solid #000;padding:8px;">{entry['text']}</td>
        </tr>"""

    return f"""
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
    <td colspan="2" style="text-align:center;vertical-align:middle;border:1px solid #000;">
      {logo_html}
    </td>
    <td colspan="2" class="title">{DEPARTMENT_NAME} Service Desk Incident Notification</td>
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
  <tr>
    <td colspan="4" style="background:#00915A;color:white;font-weight:bold;
        text-align:center;border:1px solid #000;padding:0px;height:28px;">
      For any further queries, please contact: {DEPARTMENT_NAME} Service Desk - <u>{DEPARTMENT_DESK}</u>
    </td>
  </tr>
</table>
</body>
</html>"""