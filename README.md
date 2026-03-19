# Incident Management System — PySide6

A full Python/PySide6 desktop port of the original HTML/CSS/JS web app,
with Outlook integration via pywin32 and JSON-backed persistence.

---

## Project Structure

```
incident_management/
├── main.py                   ← Entry point
├── requirements.txt
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
> The app will still run on macOS/Linux — the Outlook button will show an informational dialog instead.

### 2. Run

```bash
cd incident_management
python main.py
```

---

## Features

### Main Form (Left Panel)
- **Service/Application(s)** — multi-select dropdown (BD, MR V, MR L, RN, etc.)
- **Service Status** — Available / Unavailable / Degraded / Under Observation
- **Users Impacted** — GLOBAL / APAC / EMEA / AMERICAS with mutual exclusion (GLOBAL disables regions and vice versa)
- **Incident Numbers** — Add multiple INC########s with P1/P2 priority tags; remove individually
- **Time fields** — Start, End (shown for Available), Next Update (shown for other statuses); all rounded to nearest 15 min on generate
- **Description / Impact / Progress** — textarea fields; Progress entries are timestamped and appended to the progress log on each generate

### Generated Output (Right Panel)
- **To / Bcc / Subject** fields — each individually copyable
- **Notification table** — mirrors the original HTML table with colour-coded status cell
- **Copy Table** — copies the table as HTML (paste directly into Outlook)
- **Open in Outlook** — uses pywin32 to open a pre-filled Outlook compose window with HTML body

### Settings / Data Page
Accessible via the **⚙ Settings / Data** button in the header.

Four tabs:
1. **Form State** — edit services, status, users, incidents, description, impact, times; changes sync back to the main form on Save
2. **Progress Log** — view, add, edit, delete progress entries
3. **Recipients** — edit the To address and per-region BCC email lists
4. **Raw JSON** — direct JSON editor for power users

### Data Persistence
All data is saved to `data/incidents_data.json` automatically on every field change.
The JSON file is human-readable and can be edited externally; use Settings → Raw JSON or reload to reflect external edits.

---

## Outlook Integration

Clicking **Open in Outlook** will:
1. Launch `win32com.client.Dispatch("Outlook.Application")`
2. Create a new mail item with:
   - **To:** configured To address (editable in Settings → Recipients)
   - **Bcc:** all emails for the selected regions
   - **Subject:** `[{Status}] FOREX Incident Management Notification : {Services}`
   - **HTMLBody:** the full formatted incident table
3. Display the draft (`.Display(False)`) — you review and send manually

---

## Customisation

| What | Where |
|------|-------|
| Service list | `app/data_manager.py` → `SERVICES` |
| User regions | `app/data_manager.py` → `USERS` |
| Default email lists | `app/data_manager.py` → `EMAIL_LISTS` (also editable at runtime via Settings) |
| Colour scheme | `app/styles.py` → `MAIN_STYLE` |
| Status colours | `app/styles.py` → `STATUS_COLORS` |
