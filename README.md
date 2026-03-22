# Relay — Incident Communication
A Python/PySide6 desktop application for generating and sending incident 
notification emails, with Outlook integration via pywin32 and JSON-backed persistence.

---

## Project Structure
```
Relay/
├── main.py                   ← Entry point
├── requirements.txt
├── resources.qrc             ← Qt resource file for icons
├── resources_rc.py           ← Compiled Qt resources (auto-generated)
├── resources/
│   ├── icons/                ← UI icons (home, settings, trash, copy, etc.)
│   └── assets/               ← App assets (company logo)
├── data/
│   └── incidents_data.json   ← Auto-created on first run
└── app/
    ├── __init__.py
    ├── main_window.py        ← QMainWindow, header, navigation
    ├── form_panel.py         ← Left panel: all input fields
    ├── output_panel.py       ← Right panel: generated notification + Outlook
    ├── settings_page.py      ← Settings/JSON editor page
    ├── data_manager.py       ← JSON load/save helpers, email lists
    ├── styles.py             ← Qt stylesheet (green/white design)
    └── widgets.py            ← Reusable custom widgets
```

---

## Setup

### 1. Install dependencies
```bash
pip install PySide6 pywin32
```

> **pywin32** is Windows-only and required only for the Outlook integration button.
> The app will still run on macOS/Linux — the Outlook button will show an
> informational dialog instead.

### 2. Compile resources
```bash
pyside6-rcc resources.qrc -o resources_rc.py
```

### 3. Run
```bash
python main.py
```

---

## Features

### Main Form (Left Panel)
- **Service/Application(s)** — multi-select dropdown with chevron icon
- **Service Status** — Degraded / Unavailable / Under Observation / Available (default: Degraded)
- **Users Impacted** — GLOBAL / APAC / EMEA / AMERICAS with mutual exclusion
- **Incident Numbers** — Add multiple INC########s with P1/P2 priority tags inside the input box; remove individually with icon button
- **Time fields:**
  - **Time Started** — defaults to current time
  - **Time Ended** — shown only for Available status; defaults to latest progress entry + 1hr (or start time + 1hr if no progress entries); cannot be before Time Started
  - **Next Update** — shown for non-Available statuses; defaults to blank; if left blank, generates as time of clicking Generate + 1hr; cannot be before Time Started; cleared after each Generate
  - All times use 5-minute scroll intervals and only respond to scroll when focused
  - Calendar popup uses light green theme
- **Description / Impact** — fixed-height textarea fields
- **Progress** — auto-expanding textarea; entries are timestamped and appended to the progress log on Generate
- **Generate Notification** — validates all required fields and emits payload to output panel

### Generated Notification (Right Panel)
- Auto-populates on startup if saved data exists
- **To / Bcc / Subject** fields — each individually copyable with icon button
- **Notification table** — structured table with colour-coded status cell and company logo
- **Copy Table** — copies the table as HTML (paste directly into Outlook) with icon button
- **Open in Outlook** — uses pywin32 to open a pre-filled Outlook compose window with HTML body

### Settings Page
Accessible via the settings icon in the header. Contains two views toggled from the header:

1. **Progress Log** — view, add, edit, delete progress entries with datetime picker and multiline text editor
2. **Raw JSON** — direct JSON editor for power users; invalid JSON is rejected on save

### Navigation
- **Home icon** — returns to main form/output view
- **Settings icon** — opens settings page
- **Trash icon** — clears all saved data, form fields, and output panel
- Active view is highlighted in the header

### Data Persistence
All data is saved to `data/incidents_data.json` automatically on field changes.

Fields saved automatically: services, users, incidents, description, impact, start time, next update (when not blank).

Fields saved only on Generate: service status, end time (Available only), next update (computed if blank).

---

## Outlook Integration
Clicking **Open in Outlook** will:
1. Try multiple strategies to connect to Outlook via COM
2. Create a new mail item with:
   - **To:** hardcoded recipient (`TO_RECIPIENT` in `data_manager.py`)
   - **Bcc:** all emails for the selected regions (from `EMAIL_LISTS` in `data_manager.py`)
   - **Subject:** `[{Status}] FOREX Incident Management Notification : {Services}`
   - **HTMLBody:** the full formatted incident table with company logo
3. Display the draft (`.Display(False)`) — you review and send manually

If Outlook COM is unavailable, falls back to a `mailto:` link with Subject and To pre-filled.

---

## Customisation

| What          | Where                                                                         |
|---------------|-------------------------------------------------------------------------------|
| Service list  | `app/data_manager.py` → `SERVICES`                                            |
| User regions  | `app/data_manager.py` → `USERS`                                               |
| Email lists   | `app/data_manager.py` → `EMAIL_LISTS`                                         |
| To recipient  | `app/data_manager.py` → `TO_RECIPIENT`                                        |
| Colour scheme | `app/styles.py` → `MAIN_STYLE`                                                |
| Status colours| `app/styles.py` → `STATUS_COLORS`                                             |
| Icons         | `resources/icons/` + `resources.qrc` → recompile with `pyside6-rcc`           |
| Company logo  | `resources/assets/` → update path in `build_email_html()` in `output_panel.py`|