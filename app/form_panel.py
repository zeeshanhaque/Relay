"""
Form Panel - left side of main window.
Collects all incident details.
"""
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QCheckBox, QDateTimeEdit, QFrame, QScrollArea,
    QMessageBox, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDateTime, QTimer
from PySide6.QtGui import QFont

from .widgets import (
    SectionTitle, FieldLabel, MultiCheckDropdown,
    IncidentTag, SectionCard
)
from .data_manager import (
    SERVICES, USERS, SERVICE_STATUSES, validate_incident,
    round_to_quarter, save_data, load_data
)


class FormPanel(QWidget):
    """Left panel: all input fields."""
    generateRequested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._incidents: list[dict] = []
        self._build_ui()
        self._load_data()
        self._connect_signals()

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        # Card
        card = SectionCard()
        layout.addWidget(card)
        layout.addStretch()

        card_layout = card.layout()
        card_layout.addWidget(SectionTitle("Incident Details"))

        # Row 1: Service + Status
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        svc_group = self._field_group("Service/Application(s) Impacted", required=True)
        self.svc_dropdown = MultiCheckDropdown("Select Service/Application(s)", SERVICES)
        svc_group.addWidget(self.svc_dropdown)
        row1.addLayout(svc_group)

        status_group = self._field_group("Service Status", required=True)
        self.status_combo = QComboBox()
        self.status_combo.addItems(SERVICE_STATUSES)
        status_group.addWidget(self.status_combo)
        row1.addLayout(status_group)

        card_layout.addLayout(row1)

        # Row 2: Users + Incident
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        users_group = self._field_group("User(s) Impacted", required=True)
        self.users_dropdown = MultiCheckDropdown("Select User(s)", USERS)
        users_group.addWidget(self.users_dropdown)
        row2.addLayout(users_group)

        inc_group = self._build_incident_group()
        row2.addLayout(inc_group)

        card_layout.addLayout(row2)

        # Incidents list
        self._incidents_container = QWidget()
        self._incidents_layout = QHBoxLayout(self._incidents_container)
        self._incidents_layout.setContentsMargins(0, 0, 0, 0)
        self._incidents_layout.setSpacing(8)
        self._incidents_layout.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(self._incidents_container)

        # Row 3: Times
        row3 = QHBoxLayout()
        row3.setSpacing(16)

        start_grp = self._field_group("Time Started [LT]", required=True)
        self.start_time = QDateTimeEdit()
        self.start_time.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.start_time.setCalendarPopup(True)
        self.start_time.setDateTime(QDateTime.currentDateTime())
        start_grp.addWidget(self.start_time)
        row3.addLayout(start_grp)

        self.end_time_grp = self._field_group("Time Ended [LT]", required=True)
        self.end_time = QDateTimeEdit()
        self.end_time.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.end_time.setCalendarPopup(True)
        self.end_time.setDateTime(QDateTime.currentDateTime())
        self.end_time_grp.addWidget(self.end_time)
        row3.addLayout(self.end_time_grp)

        self.next_update_grp = self._field_group("Next Update At [LT]")
        self.next_update = QDateTimeEdit()
        self.next_update.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.next_update.setCalendarPopup(True)
        self.next_update.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.next_update_grp.addWidget(self.next_update)
        row3.addLayout(self.next_update_grp)

        card_layout.addLayout(row3)

        # Row 4: Description + Impact + Progress
        self.description = QTextEdit()
        self.description.setPlaceholderText("Describe the incident...")
        self.description.setMinimumHeight(80)
        card_layout.addLayout(self._labelled("Description", self.description, required=True))

        self.impact = QTextEdit()
        self.impact.setPlaceholderText("Describe the impact...")
        self.impact.setMinimumHeight(80)
        card_layout.addLayout(self._labelled("Impact", self.impact, required=True))

        self.progress = QTextEdit()
        self.progress.setPlaceholderText("Add progress notes (will be timestamped and appended)...")
        self.progress.setMinimumHeight(60)
        card_layout.addLayout(self._labelled("Progress", self.progress))

        # Generate button
        self.gen_btn = QPushButton("GENERATE NOTIFICATION")
        self.gen_btn.setObjectName("generateBtn")
        self.gen_btn.setMinimumHeight(48)
        card_layout.addWidget(self.gen_btn)

    def _field_group(self, label_text: str, required: bool = False) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        lbl = FieldLabel(label_text, required)
        vbox.addWidget(lbl)
        return vbox

    def _labelled(self, label_text: str, widget: QWidget, required: bool = False) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        vbox.addWidget(FieldLabel(label_text, required))
        vbox.addWidget(widget)
        return vbox

    def _build_incident_group(self) -> QVBoxLayout:
        grp = QVBoxLayout()
        grp.setSpacing(4)
        grp.addWidget(FieldLabel("Incident #", required=True))

        row = QHBoxLayout()
        row.setSpacing(8)

        self.inc_input = QLineEdit()
        self.inc_input.setPlaceholderText("INC00000000")
        self.inc_input.setMaxLength(11)
        row.addWidget(self.inc_input)

        self.p1_check = QCheckBox("P1")
        self.p2_check = QCheckBox("P2")
        row.addWidget(self.p1_check)
        row.addWidget(self.p2_check)

        self.add_inc_btn = QPushButton("Add →")
        self.add_inc_btn.setObjectName("addIncBtn")
        row.addWidget(self.add_inc_btn)

        grp.addLayout(row)

        self.inc_error = QLabel("⚠ Format must be INC + 8 digits (e.g. INC00000001)")
        self.inc_error.setStyleSheet("color: #e74c3c; font-size: 11px;")
        self.inc_error.hide()
        grp.addWidget(self.inc_error)

        return grp

    # ── Signals ──────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        self.add_inc_btn.clicked.connect(self._add_incident)
        self.inc_input.returnPressed.connect(self._add_incident)
        self.gen_btn.clicked.connect(self._on_generate)

        self.p1_check.stateChanged.connect(self._on_p1_changed)
        self.p2_check.stateChanged.connect(self._on_p2_changed)

        self.users_dropdown.selectionChanged.connect(self._on_users_changed)

        # Save on each change
        for w in [self.description, self.impact, self.progress]:
            w.textChanged.connect(self._auto_save)
        self.status_combo.currentTextChanged.connect(self._auto_save)
        self.svc_dropdown.selectionChanged.connect(self._auto_save)
        self.users_dropdown.selectionChanged.connect(self._auto_save)
        self.start_time.dateTimeChanged.connect(self._auto_save)
        self.end_time.dateTimeChanged.connect(self._auto_save)
        self.next_update.dateTimeChanged.connect(self._auto_save)

        self._on_status_changed(self.status_combo.currentText())

    # ── Status change handler ─────────────────────────────────────────────────

    def _on_status_changed(self, status: str):
        is_available = status == "Available"
        # Show end_time only if Available; show next_update otherwise
        end_widget = self.end_time_grp.itemAt(0).widget() if self.end_time_grp.count() > 0 else None
        next_widget = self.next_update_grp.itemAt(0).widget() if self.next_update_grp.count() > 0 else None

        self.end_time.setVisible(is_available)
        self.next_update.setVisible(not is_available)

        # Also hide/show the labels (index 0 in each group)
        for i in range(self.end_time_grp.count()):
            item = self.end_time_grp.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(is_available)

        for i in range(self.next_update_grp.count()):
            item = self.next_update_grp.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(not is_available)

    # ── User checkbox mutual exclusion ────────────────────────────────────────

    def _on_users_changed(self, selected: list[str]):
        if "GLOBAL" in selected:
            self.users_dropdown.set_disabled_options(["APAC", "EMEA", "AMERICAS"])
        elif any(r in selected for r in ["APAC", "EMEA", "AMERICAS"]):
            self.users_dropdown.set_disabled_options(["GLOBAL"])
        else:
            self.users_dropdown.set_disabled_options([])

    # ── Priority checkboxes ───────────────────────────────────────────────────

    def _on_p1_changed(self, state):
        if state:
            self.p2_check.setChecked(False)
            self.p2_check.setEnabled(False)
        else:
            self.p2_check.setEnabled(True)

    def _on_p2_changed(self, state):
        if state:
            self.p1_check.setChecked(False)
            self.p1_check.setEnabled(False)
        else:
            self.p1_check.setEnabled(True)

    # ── Incident management ───────────────────────────────────────────────────

    def _add_incident(self):
        num = self.inc_input.text().strip().upper()
        if not num:
            QMessageBox.warning(self, "Missing", "Please enter an incident number.")
            return

        is_valid, starts_zero = validate_incident(num)
        if not is_valid:
            self.inc_error.show()
            return
        self.inc_error.hide()

        if any(i["number"] == num for i in self._incidents):
            QMessageBox.warning(self, "Duplicate", "This incident has already been added.")
            return

        if starts_zero:
            reply = QMessageBox.question(
                self, "Confirm", "Incident number starts with Zero. Add anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        priority = "P1" if self.p1_check.isChecked() else ("P2" if self.p2_check.isChecked() else "")
        self._incidents.append({"number": num, "priority": priority})

        # Reset inputs
        self.inc_input.clear()
        self.p1_check.setChecked(False)
        self.p2_check.setChecked(False)
        self.p1_check.setEnabled(True)
        self.p2_check.setEnabled(True)

        self._render_incidents()
        self._auto_save()

    def _remove_incident(self, index: int):
        if 0 <= index < len(self._incidents):
            self._incidents.pop(index)
            self._render_incidents()
            self._auto_save()

    def _render_incidents(self):
        # Clear existing tags
        while self._incidents_layout.count():
            item = self._incidents_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, inc in enumerate(self._incidents):
            tag = IncidentTag(i, inc["number"], inc.get("priority", ""))
            tag.removeRequested.connect(self._remove_incident)
            self._incidents_layout.addWidget(tag)

    # ── Generate ─────────────────────────────────────────────────────────────

    def _on_generate(self):
        services = self.svc_dropdown.get_selected()
        users = self.users_dropdown.get_selected()
        status = self.status_combo.currentText()

        if not services:
            QMessageBox.warning(self, "Validation", "Please select at least one Service/Application.")
            return
        if not users:
            QMessageBox.warning(self, "Validation", "Please select at least one User Impacted.")
            return
        if not self._incidents:
            QMessageBox.warning(self, "Validation", "Please add at least one incident number.")
            return

        start_dt = self.start_time.dateTime().toPython()
        if not start_dt:
            QMessageBox.warning(self, "Validation", "Please provide a Start Time.")
            return

        desc = self.description.toPlainText().strip()
        impact = self.impact.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Validation", "Please provide a Description.")
            return
        if not impact:
            QMessageBox.warning(self, "Validation", "Please provide an Impact.")
            return

        if status == "Available":
            end_dt = self.end_time.dateTime().toPython()
        else:
            end_dt = None

        if status == "Available" and not end_dt:
            QMessageBox.warning(self, "Validation", "Please provide an End Time.")
            return

        progress_text = self.progress.toPlainText().strip()
        if not progress_text:
            reply = QMessageBox.question(
                self, "Confirm", "Progress is empty. Proceed anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Round times
        start_dt = round_to_quarter(start_dt)
        end_dt = round_to_quarter(end_dt) if end_dt else None

        if status != "Available":
            next_dt_raw = self.next_update.dateTime().toPython()
            next_dt = round_to_quarter(next_dt_raw) if next_dt_raw else \
                round_to_quarter(datetime.now() + timedelta(hours=1))
        else:
            next_dt = None

        # Save progress entry
        if progress_text:
            self._save_progress_entry(progress_text, round_to_quarter(datetime.now()))
            self.progress.clear()

        # Update and save form state
        self._auto_save()

        payload = {
            "services": services,
            "users": users,
            "status": status,
            "incidents": self._incidents,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat() if end_dt else "",
            "next_update": next_dt.isoformat() if next_dt else "",
            "description": desc,
            "impact": impact,
        }
        self.generateRequested.emit(payload)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_progress_entry(self, text: str, dt: datetime):
        data = load_data()
        data["progress_entries"].append({
            "datetime": dt.strftime("%d/%m/%Y %H:%M"),
            "text": text
        })
        save_data(data)

    def _auto_save(self):
        data = load_data()
        data["form"]["selected_services"] = self.svc_dropdown.get_selected()
        data["form"]["service_status"] = self.status_combo.currentText()
        data["form"]["selected_users"] = self.users_dropdown.get_selected()
        data["form"]["incidents"] = self._incidents
        data["form"]["description"] = self.description.toPlainText()
        data["form"]["impact"] = self.impact.toPlainText()
        data["form"]["start_time"] = self.start_time.dateTime().toString(Qt.ISODate)
        data["form"]["end_time"] = self.end_time.dateTime().toString(Qt.ISODate)
        data["form"]["next_update"] = self.next_update.dateTime().toString(Qt.ISODate)
        save_data(data)

    def _load_data(self):
        data = load_data()
        form = data.get("form", {})

        self.svc_dropdown.set_selected(form.get("selected_services", []))
        idx = self.status_combo.findText(form.get("service_status", "Available"))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        self.users_dropdown.set_selected(form.get("selected_users", []))
        self._on_users_changed(form.get("selected_users", []))

        self._incidents = form.get("incidents", [])
        self._render_incidents()

        if form.get("start_time"):
            self.start_time.setDateTime(QDateTime.fromString(form["start_time"], Qt.ISODate))
        if form.get("end_time"):
            self.end_time.setDateTime(QDateTime.fromString(form["end_time"], Qt.ISODate))
        if form.get("next_update"):
            self.next_update.setDateTime(QDateTime.fromString(form["next_update"], Qt.ISODate))

        self.description.setPlainText(form.get("description", ""))
        self.impact.setPlainText(form.get("impact", ""))

        self._on_status_changed(self.status_combo.currentText())

    def reload_from_data(self, data: dict):
        """Called when settings page saves new data."""
        form = data.get("form", {})
        self.svc_dropdown.set_selected(form.get("selected_services", []))
        idx = self.status_combo.findText(form.get("service_status", "Available"))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.users_dropdown.set_selected(form.get("selected_users", []))
        self._on_users_changed(form.get("selected_users", []))
        self._incidents = form.get("incidents", [])
        self._render_incidents()
        self.description.setPlainText(form.get("description", ""))
        self.impact.setPlainText(form.get("impact", ""))
        if form.get("start_time"):
            self.start_time.setDateTime(QDateTime.fromString(form["start_time"], Qt.ISODate))
        if form.get("end_time"):
            self.end_time.setDateTime(QDateTime.fromString(form["end_time"], Qt.ISODate))
        if form.get("next_update"):
            self.next_update.setDateTime(QDateTime.fromString(form["next_update"], Qt.ISODate))
        self._on_status_changed(self.status_combo.currentText())

    def clear_form(self):
        self.svc_dropdown.reset()
        self.users_dropdown.reset()
        self.status_combo.setCurrentIndex(0)
        self._incidents.clear()
        self._render_incidents()
        self.description.clear()
        self.impact.clear()
        self.progress.clear()
        self.inc_input.clear()
        self.p1_check.setChecked(False)
        self.p2_check.setChecked(False)
        self.p1_check.setEnabled(True)
        self.p2_check.setEnabled(True)
        self.start_time.setDateTime(QDateTime.currentDateTime())
        self.end_time.setDateTime(QDateTime.currentDateTime())
        self.next_update.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self._on_status_changed("Available")
