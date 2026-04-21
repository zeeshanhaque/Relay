"""
Data Manager - Handles JSON persistence for the Incident Management System.
All saved data lives in data/incidents_data.json
"""
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

from .config import DEPARTMENT_DESK, EMAIL_LISTS, SERVICES, USERS, SERVICE_STATUSES


def _get_data_dir() -> Path:
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return Path(sys.executable).parent / "data"
    else:
        # Running as normal Python script
        return Path(__file__).parent.parent / "data"

DATA_DIR = _get_data_dir()
DATA_FILE = DATA_DIR / "incidents_data.json"


def _default_data() -> dict:
    return {
        "form": {
            "selected_services": [],
            "service_status": "Degraded",
            "selected_users": [],
            "incidents": [],
            "start_time": "",
            "end_time": "",
            "next_update": "",
            "description": "",
            "impact": "",
        },
        "progress_entries": [],
    }


def load_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults to handle missing keys from older saves
            defaults = _default_data()
            for key in defaults:
                if key not in data:
                    data[key] = defaults[key]
            return data
        except (json.JSONDecodeError, KeyError):
            pass
    return _default_data()


def save_data(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def clear_data() -> dict:
    data = _default_data()
    save_data(data)
    return data


def get_cc_recipients() -> list[str]:
    """Return LEADS emails for CC — always included regardless of region."""
    return EMAIL_LISTS.get("LEADS", [])


def get_recipients(selected_users: list[str]) -> list[str]:
    all_recipients = []
    if "GLOBAL" in selected_users:
        for region in ["APAC", "EMEA", "AMERICAS"]:
            all_recipients.extend(EMAIL_LISTS.get(region, []))
    else:
        for region in selected_users:
            all_recipients.extend(EMAIL_LISTS.get(region, []))

    # Always add DEPT_TEAMS to BCC
    all_recipients.extend(EMAIL_LISTS.get("DEPT_TEAMS", []))

    # Deduplicate
    seen = set()
    result = []
    for email in all_recipients:
        if email not in seen:
            seen.add(email)
            result.append(email)
    return result


def format_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def format_services(services: list[str]) -> str:
    """Format services list with DL always last if present."""
    if "DL" in services:
        others = [s for s in services if s != "DL"]
        ordered = others + ["DL"]
    else:
        ordered = services
    return format_list(ordered)


def get_cob_date() -> str:
    """Returns the COB date in DD/MM format.
    COB is previous business day — yesterday unless today is Monday,
    in which case it is the previous Friday."""
    from datetime import date, timedelta
    today = date.today()
    if today.weekday() == 0:  # Monday
        cob = today - timedelta(days=3)  # Friday
    else:
        cob = today - timedelta(days=1)
    return cob.strftime("%d/%m")


def round_to_quarter(dt: datetime) -> datetime:
    """Round a datetime to the nearest 15-minute interval."""
    minutes = dt.minute
    rounded = round(minutes / 15) * 15
    if rounded == 60:
        dt = dt.replace(minute=0, second=0, microsecond=0)
        dt = dt + timedelta(hours=1)
    else:
        dt = dt.replace(minute=rounded, second=0, microsecond=0)
    return dt


def format_datetime_display(iso_str: str) -> str:
    """Convert ISO datetime string to DD/MM/YYYY HH:MM display format."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso_str


def validate_incident(num: str) -> tuple[bool, bool]:
    """
    Returns (is_valid, starts_with_zero).
    Format must be INC followed by 7 or 8 digits.
    """
    import re
    if re.match(r"^INC[0-9]{7,8}$", num):
        return True, False
    return False, False


def sort_progress_entries(entries: list[dict]) -> list[dict]:
    """Sort progress entries in descending order by datetime, 
    preserving reverse insertion order for equal timestamps."""
    try:
        # Enumerate to preserve original index for stable reverse sort
        indexed = list(enumerate(entries))
        indexed.sort(
            key=lambda x: (
                datetime.strptime(x[1]["datetime"], "%d/%m/%Y %H:%M"),
                x[0]  # original index as tiebreaker
            ),
            reverse=True
        )
        return [entry for _, entry in indexed]
    except (ValueError, KeyError):
        return entries