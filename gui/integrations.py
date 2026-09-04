"""Honest connection status for the things JARVIS can talk to.

Every check answers "is this actually usable right now?" so the UI can show a
truthful state. Nothing here returns a credential value - only whether one is
present - because credentials must never reach the interface or the logs.
"""

import os
import shutil
import socket
from pathlib import Path

from assistant.config import get_setting

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# config.json ships with placeholders so the repo carries no real credentials.
# A placeholder is not a connection, so it must not read as one.
_PLACEHOLDER_PREFIXES = ("DEMO_", "YOUR_", "CHANGE_ME", "REPLACE_", "<")
_PLACEHOLDER_VALUES = {"demo@example.com", "you@example.com", "none", "null", "todo"}


def _is_placeholder(value):
    text = str(value).strip()
    return (text.upper().startswith(_PLACEHOLDER_PREFIXES)
            or text.lower() in _PLACEHOLDER_VALUES)


def _has_setting(key):
    value = get_setting(key, "")
    if not value or not str(value).strip():
        return False
    return not _is_placeholder(value)


def google_status():
    """Google Workspace access depends on an OAuth client and a stored token."""
    token = PROJECT_ROOT / "token.json"
    credentials = PROJECT_ROOT / "credentials.json"

    if token.exists():
        return {"connected": True, "label": "Connected",
                "detail": "Calendar access is authorized."}
    if credentials.exists():
        return {"connected": False, "label": "Needs sign-in",
                "detail": "Credentials found. Ask JARVIS for your schedule to authorize."}
    return {"connected": False, "label": "Not connected",
            "detail": "Add credentials.json from the Google Cloud Console to connect."}


def gmail_status():
    """Mail currently goes through IMAP with an app password, not OAuth."""
    if _has_setting("email_address") and _has_setting("email_app_password"):
        return {"connected": True, "label": "Connected",
                "detail": "Mail is set up for reading and sending."}
    return {"connected": False, "label": "Not connected",
            "detail": "Add your email address and app password in Settings."}


def phone_status():
    """The phone link is the Telegram bridge."""
    if _has_setting("telegram_bot_token") and _has_setting("telegram_chat_id"):
        return {"connected": True, "label": "Connected",
                "detail": "You can send JARVIS commands from your phone."}
    return {"connected": False, "label": "Not connected",
            "detail": "Connect a Telegram bot to use your phone."}


def internet_status():
    """A quick reachability check, kept short so it never blocks the UI."""
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=1.5).close()
        return {"connected": True, "label": "Ready",
                "detail": "JARVIS can search and read the web."}
    except OSError:
        return {"connected": False, "label": "Offline",
                "detail": "No internet connection right now."}


def local_ai_status():
    """The local brain is Ollama; report whether it is actually running."""
    model = get_setting("llm_model", "qwen2.5:3b")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=1.5)
        if response.status_code == 200:
            return {"connected": True, "label": "Ready",
                    "detail": f"Thinking locally with {model}."}
    except Exception:
        pass
    return {"connected": False, "label": "Not running",
            "detail": "Start Ollama to let JARVIS think locally."}


def computer_status():
    return {"connected": True, "label": "Online",
            "detail": "This computer is ready for JARVIS to use."}


def overwatch_status():
    from assistant.overwatch.engine import is_available
    if is_available():
        return {"connected": True, "label": "Available",
                "detail": "JARVIS can watch windows on this computer."}
    return {"connected": False, "label": "Unavailable",
            "detail": "Watching windows needs Windows."}


def browser_automation_status():
    try:
        import playwright  # noqa: F401
        return {"connected": True, "label": "Ready",
                "detail": "JARVIS can carry out steps in a browser."}
    except ImportError:
        return {"connected": False, "label": "Not installed",
                "detail": "Install Playwright to let JARVIS use a browser."}


def screen_reading_status():
    """OCR needs both the Python binding and the Tesseract binary."""
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return {"connected": False, "label": "Not installed",
                "detail": "Install pytesseract to let JARVIS read the screen."}

    if shutil.which("tesseract") or os.path.exists(
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        return {"connected": True, "label": "Ready",
                "detail": "JARVIS can read what is on your screen."}
    return {"connected": False, "label": "Needs Tesseract",
            "detail": "Install the Tesseract program to enable screen reading."}


def all_integrations():
    """Rows for the Settings > Connected Services list."""
    return [
        ("Google", google_status()),
        ("Email", gmail_status()),
        ("Phone", phone_status()),
        ("Local AI", local_ai_status()),
        ("Internet", internet_status()),
        ("Screen reading", screen_reading_status()),
        ("Browser tasks", browser_automation_status()),
        ("Window watching", overwatch_status()),
    ]
