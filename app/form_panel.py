"""
Form Panel - left side of main window.
Collects all incident details.
"""
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QCheckBox, QFrame, QScrollArea,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDateTime, QTimer, QSize
from PySide6.QtGui import QFont, QPalette, QColor, QIcon

from .widgets import (
    SectionTitle, FieldLabel, MultiCheckDropdown,
    IncidentTag, SectionCard, FiveMinDateTimeEdit
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
        self.status_combo.setStyleSheet("""
            QComboBox {
                background: white;
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                color: #2c3e50;
            }
            QComboBox:focus {
                border: 2px solid #00915A;
                background-color: #f0faf6;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #00915A;
                border-radius: 6px;
                selection-background-color: #e8f5f0;
                selection-color: #00915A;
            }
        """)
        palette = self.status_combo.palette()
        palette.setColor(QPalette.Base, QColor("white"))
        palette.setColor(QPalette.Button, QColor("white"))
        self.status_combo.setPalette(palette)
        status_group.addWidget(self.status_combo)
        row1.addLayout(status_group)

        card_layout.addLayout(row1)

        # Row 2: Users + Incident
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        users_group = self._field_group("User(s) Impacted", required=True)
        self.users_dropdown = MultiCheckDropdown("Select User(s)", USERS)
        users_group.addWidget(self.users_dropdown)
        row2.addLayout(users_group, 1)

        inc_group = self._build_incident_group()
        row2.addLayout(inc_group, 1)

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
        self.start_time = FiveMinDateTimeEdit()
        self.start_time.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.start_time.setCalendarPopup(True)
        self.start_time.setDateTime(QDateTime.currentDateTime())
        start_grp.addWidget(self.start_time)
        row3.addLayout(start_grp)

        self.end_time_grp = self._field_group("Time Ended [LT]", required=True)
        self.end_time = FiveMinDateTimeEdit()
        self.end_time.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.end_time.setCalendarPopup(True)
        end_dt = datetime.now()
        end_dt_floored = end_dt.replace(
            minute=(end_dt.minute // 15) * 15,
            second=0, microsecond=0
        )
        self.end_time.setDateTime(QDateTime(
            end_dt_floored.year, end_dt_floored.month, end_dt_floored.day,
            end_dt_floored.hour, end_dt_floored.minute, 0
        ))
        self.end_time_grp.addWidget(self.end_time)
        row3.addLayout(self.end_time_grp)

        self.next_update_grp = self._field_group("Next Update At [LT]")
        self.next_update = FiveMinDateTimeEdit()
        self.next_update.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.next_update.setCalendarPopup(True)
        self.next_update.setMinimumDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
        self.next_update.setDateTime(self.next_update.minimumDateTime())
        self.next_update_grp.addWidget(self.next_update)
        row3.addLayout(self.next_update_grp)

        card_layout.addLayout(row3)

        # Row 4: Description + Impact + Progress
        self.description = QTextEdit()
        self.description.setPlaceholderText("Describe the incident...")
        self.description.setMinimumHeight(65)
        self.description.setMaximumHeight(65)
        card_layout.addLayout(self._labelled("Description", self.description, required=True))

        self.impact = QTextEdit()
        self.impact.setPlaceholderText("Describe the impact...")
        self.impact.setMinimumHeight(65)
        self.impact.setMaximumHeight(65)
        card_layout.addLayout(self._labelled("Impact", self.impact, required=True))

        self.progress = QTextEdit()
        self.progress.setPlaceholderText("Add progress notes (will be timestamped and appended)...")
        self.progress.setMinimumHeight(80)
        self.progress.textChanged.connect(self._adjust_progress_height)
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

        # Outer row: input container + Add button
        row = QHBoxLayout()
        row.setSpacing(8)

        # Container that mimics an input box with checkboxes inside
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background: white;
            }
            QFrame:focus-within {
                border: 2px solid #00915A;
                background: #f0faf6;
            }
        """)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(8, 2, 8, 2)
        container_layout.setSpacing(6)

        self.inc_input = QLineEdit()
        self.inc_input.setPlaceholderText("INC00000000")
        self.inc_input.setMaxLength(11)
        self.inc_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                padding: 6px 0px;
            }
            QLineEdit:focus {
                border: none;
                background: transparent;
            }
        """)
        container_layout.addWidget(self.inc_input)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #e0e0e0; background: #e0e0e0;")
        div.setFixedWidth(1)
        container_layout.addWidget(div)

        self.p1_check = QCheckBox("P1")
        self.p2_check = QCheckBox("P2")
        self.p1_check.setStyleSheet("QCheckBox { border: none; background: transparent; padding: 0px; }")
        self.p2_check.setStyleSheet("QCheckBox { border: none; background: transparent; padding: 0px; }")
        container_layout.addWidget(self.p1_check)
        container_layout.addWidget(self.p2_check)

        row.addWidget(container)

        self.add_inc_btn = QPushButton()
        self.add_inc_btn.setObjectName("addIncBtn")
        self.add_inc_btn.setIcon(QIcon(":/icons/include.png"))
        self.add_inc_btn.setIconSize(QSize(20, 20))
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
        self.next_update.dateTimeChanged.connect(self._auto_save)


    # ── Status change handler ─────────────────────────────────────────────────

    def _on_status_changed(self, status: str):
        is_available = status == "Available"

        self.end_time.setVisible(is_available)
        self.next_update.setVisible(not is_available)

        for i in range(self.end_time_grp.count()):
            item = self.end_time_grp.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(is_available)

        for i in range(self.next_update_grp.count()):
            item = self.next_update_grp.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(not is_available)

        # Set end time default when switching to Available
        if is_available:
            data = load_data()
            progress_entries = data.get("progress_entries", [])
            if progress_entries:
                # Use latest progress entry time + 1hr
                try:
                    latest = max(
                        progress_entries,
                        key=lambda e: datetime.strptime(e["datetime"], "%d/%m/%Y %H:%M")
                    )
                    base_dt = datetime.strptime(latest["datetime"], "%d/%m/%Y %H:%M")
                except (ValueError, KeyError):
                    base_dt = self.start_time.dateTime().toPython()
            else:
                # Fall back to start time + 1hr
                base_dt = self.start_time.dateTime().toPython()

            end_default = round_to_quarter(base_dt + timedelta(hours=1))
            self.end_time.blockSignals(True)
            self.end_time.setDateTime(QDateTime(
                end_default.year, end_default.month, end_default.day,
                end_default.hour, end_default.minute, 0
            ))
            self.end_time.blockSignals(False)

        # Clear end_time from JSON when switching away from Available
        if not is_available:
            data = load_data()
            if data["form"].get("end_time"):
                data["form"]["end_time"] = ""
                save_data(data)

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


    # ── Text Inputs ─────────────────────────────────────────────────────────────
    def _adjust_progress_height(self):
        doc_height = self.progress.document().size().height()
        self.progress.setFixedHeight(max(80, int(doc_height) + 15))


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


        # Round times
        start_dt = round_to_quarter(start_dt)
        end_dt = round_to_quarter(end_dt) if end_dt else None

        if status != "Available":
            if self.next_update.dateTime() != self.next_update.minimumDateTime():
                next_dt_raw = self.next_update.dateTime().toPython()
                next_dt = round_to_quarter(next_dt_raw)
                # Validate next_update is after start_time
                if next_dt <= start_dt:
                    QMessageBox.warning(
                        self, "Validation",
                        "Next Update time must be after Time Started."
                    )
                    return
            else:
                next_dt = round_to_quarter(datetime.now() + timedelta(hours=1))
        else:
            next_dt = None

        # Validate end_time is after start_time
        if end_dt and end_dt <= start_dt:
            QMessageBox.warning(
                self, "Validation",
                "Time Ended must be after Time Started."
            )
            return

        # Save progress entry
        progress_text = self.progress.toPlainText().strip()
        if progress_text:
            self._save_progress_entry(progress_text, round_to_quarter(datetime.now()))
            self.progress.clear()

        # Update and save form state
        self._auto_save()

        # Write generate-only fields to JSON
        data = load_data()
        data["form"]["service_status"] = status
        if end_dt:
            data["form"]["end_time"] = end_dt.isoformat()
        if next_dt:
            data["form"]["next_update"] = next_dt.isoformat()
        save_data(data)

        # Reset next_update input to blank
        self.next_update.blockSignals(True)
        self.next_update.setDateTime(self.next_update.minimumDateTime())
        self.next_update.blockSignals(False)

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
        data["form"]["selected_users"] = self.users_dropdown.get_selected()
        data["form"]["incidents"] = self._incidents
        data["form"]["description"] = self.description.toPlainText()
        data["form"]["impact"] = self.impact.toPlainText()
        data["form"]["start_time"] = self.start_time.dateTime().toString(Qt.ISODate)

        # Only save next_update if not blank
        if self.next_update.dateTime() != self.next_update.minimumDateTime():
            data["form"]["next_update"] = self.next_update.dateTime().toString(Qt.ISODate)
        else:
            data["form"]["next_update"] = ""

        save_data(data)


    def _load_data(self):
        data = load_data()
        form = data.get("form", {})

        self.svc_dropdown.set_selected(form.get("selected_services", []))
        idx = self.status_combo.findText(form.get("service_status", "Degraded"))
        if idx >= 0:
            self.status_combo.blockSignals(True)
            self.status_combo.setCurrentIndex(idx)
            self.status_combo.blockSignals(False)

        self.users_dropdown.set_selected(form.get("selected_users", []))
        self._on_users_changed(form.get("selected_users", []))

        self._incidents = form.get("incidents", [])
        self._render_incidents()

        self.start_time.blockSignals(True)
        if form.get("start_time"):
            self.start_time.setDateTime(QDateTime.fromString(form["start_time"], Qt.ISODate))
        self.start_time.blockSignals(False)

        self.end_time.blockSignals(True)
        if form.get("end_time"):
            self.end_time.setDateTime(QDateTime.fromString(form["end_time"], Qt.ISODate))
        self.end_time.blockSignals(False)

        self.next_update.blockSignals(True)
        if form.get("next_update"):
            self.next_update.setDateTime(QDateTime.fromString(form["next_update"], Qt.ISODate))
        else:
            self.next_update.setDateTime(self.next_update.minimumDateTime())
        self.next_update.blockSignals(False)

        self.description.blockSignals(True)
        self.description.setPlainText(form.get("description", ""))
        self.description.blockSignals(False)

        self.impact.blockSignals(True)
        self.impact.setPlainText(form.get("impact", ""))
        self.impact.blockSignals(False)

        self._on_status_changed(self.status_combo.currentText())


    def reload_from_data(self, data: dict):
        """Called when settings page saves new data."""
        form = data.get("form", {})
        self.svc_dropdown.set_selected(form.get("selected_services", []))
        idx = self.status_combo.findText(form.get("service_status", "Degraded"))
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
        else:
            self.next_update.setDateTime(self.next_update.minimumDateTime())  # ← blank
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
        self.next_update.setDateTime(self.next_update.minimumDateTime())
        self._on_status_changed("Degraded")
