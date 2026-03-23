# Relay — Incident Communication
A Python/PySide6 desktop application for generating and sending incident 
notification emails, with Outlook integration via pywin32 and JSON-backed persistence.

---

## Project Structure
```
Relay/
├── main.py                   ← Entry point
├── requirements.txt
├── make_icon.py              ← One-time utility to generate .ico from .png
├── Relay.spec                ← PyInstaller build spec
├── resources.qrc             ← Qt resource file for icons
├── resources_rc.py           ← Compiled Qt resources (auto-generated, not committed)
├── resources/
│   ├── icons/                ← UI icons (home, settings, trash, copy, etc.)
│   │   └── relay_icon.png    ← App icon source (512x512 PNG)
│   │   └── relay.ico         ← Generated .ico (multi-size, for PyInstaller)
│   └── assets/               ← App assets (company logo)
│       └── BNPP_logo.jpg
├── data/
│   └── incidents_data.json   ← Auto-created on first run (not committed)
└── app/
    ├── __init__.py
    ├── config.py             ← Static constants (services, users, emails, etc.)
    ├── main_window.py        ← QMainWindow, header, navigation
    ├── form_panel.py         ← Left panel: all input fields
    ├── output_panel.py       ← Right panel: generated notification + Outlook
    ├── settings_page.py      ← Settings/JSON editor page
    ├── data_manager.py       ← JSON load/save helpers, formatting utilities
    ├── styles.py             ← Qt stylesheet (green/white design)
    └── widgets.py            ← Reusable custom widgets
```

---

## Development Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd Relay
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **pywin32** is Windows-only and required only for the Outlook integration button.
> The app will still run on macOS/Linux — the Outlook button will show an
> informational dialog instead.

### 4. Compile Qt resources
```bash
pyside6-rcc resources.qrc -o resources_rc.py
```

> This must be re-run whenever icons or assets in `resources/` are added or changed.

### 5. Run
```bash
python main.py
```

---

## Building a Standalone Executable (Windows)

### 1. Generate the app icon (one-time only)
Ensure you have a 512x512 PNG at `resources/icons/relay_icon.png`, then:
```bash
pip install Pillow
python make_icon.py
```
This creates `resources/icons/relay.ico` with embedded sizes (16, 32, 48, 64, 128, 256px).

### 2. Install PyInstaller
```bash
pip install pyinstaller
```

### 3. Generate the spec file (first time only)
```bash
pyinstaller --windowed --name "Relay" main.py
```

### 4. Edit `Relay.spec`
Update the generated spec to include resources and hidden imports:
```python
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('resources_rc.py', '.'),
    ],
    hiddenimports=[
        'win32com',
        'win32com.client',
        'win32api',
        'pywintypes',
    ],
    ...
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Relay',
    debug=False,
    console=False,
    icon='resources/icons/relay.ico',
)
```

### 5. Build
```bash
pyinstaller Relay.spec
```

### 6. Output
The standalone application is in:
```
dist/
└── Relay/
    └── Relay.exe    ← distribute this entire folder
```

> The entire `Relay/` folder must be kept together — do not move `Relay.exe` on its own.
> The `data/` folder for JSON persistence will be auto-created next to the `.exe` on first run.

### Troubleshooting: Failed to load Python DLL
If you see `Failed to load Python DLL` when running the `.exe`, add the Python DLL explicitly to the spec:
```python
import sys, os
a = Analysis(
    ['main.py'],
    pathex=[os.path.dirname(sys.executable)],
    binaries=[
        (os.path.join(os.path.dirname(sys.executable), 'python311.dll'), '.'),
    ],
    ...
)
```

---

## Features

### Main Form (Left Panel)
- **Service/Application(s)** — multi-select dropdown with chevron icon
- **Service Status** — Degraded / Unavailable / Under Observation / Available (default: Degraded)
- **Users Impacted** — GLOBAL / APAC / EMEA / AMERICAS with mutual exclusion
- **Incident Numbers** — Add INC####### or INC######## with P1/P2 priority tags; remove individually
- **Time fields:**
  - **Time Started** — defaults to current time
  - **Time Ended** — shown only for Available; defaults to latest progress entry + 1hr (or start time + 1hr); cannot be before Time Started
  - **Next Update** — shown for non-Available statuses; blank by default; if left blank, defaults to time of Generate click + 1hr; cannot be before Time Started; cleared after each Generate
  - All times use 5-minute scroll intervals, only respond to scroll when focused, 15-minute rounding on Generate
  - Calendar popup uses light green theme
- **Description / Impact** — fixed-height textarea fields
- **Progress** — auto-expanding textarea; entries are timestamped and appended on Generate
- **Generate Notification** — validates all required fields and populates the output panel

### Generated Notification (Right Panel)
- Auto-populates on startup if saved data exists
- **To / Bcc / Subject** — each individually copyable with icon button
- **Notification table** — structured table with colour-coded status cell and company logo
- **Copy Table** — copies the table as HTML for pasting into Outlook
- **Open in Outlook** — opens a pre-filled Outlook compose window via pywin32

### Settings Page
Accessible via the settings icon in the header. Two views:
1. **Progress Log** — view, add, edit, delete progress entries; sorted latest first
2. **Raw JSON** — direct JSON editor; invalid JSON rejected on save

### Navigation
- **App icon / Home** — returns to main form/output view
- **Settings icon** — opens settings page
- **Trash icon** — clears all saved data, form, and output panel
- Active view is highlighted in the header

---

## Data Persistence
All data saved to `data/incidents_data.json` automatically.

| Field | When saved |
|-------|-----------|
| Services, users, incidents, description, impact, start time | On every change |
| Next update (if filled) | On every change |
| Service status, end time, next update (computed) | Only on Generate |

---

## Outlook Integration
1. Connects to Outlook via COM (tries multiple strategies)
2. Creates a draft with To, Bcc, Subject, and HTML body pre-filled
3. Displays the draft for review before sending
4. Falls back to `mailto:` link if Outlook COM is unavailable

---

## Customisation

| What | Where |
|------|-------|
| Service list | `app/config.py` → `SERVICES` |
| User regions | `app/config.py` → `USERS` |
| Email lists | `app/config.py` → `EMAIL_LISTS` |
| To recipient | `app/config.py` → `TO_RECIPIENT` |
| Department name | `app/config.py` → `DEPARTMENT_NAME` |
| Colour scheme | `app/styles.py` → `MAIN_STYLE` |
| Company logo | `resources/assets/` → update path in `output_panel.py` |
| App icon | `resources/icons/relay_icon.png` → rerun `make_icon.py` + recompile resources |