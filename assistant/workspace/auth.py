"""Google Workspace Authentication and Service Factory.

Handles unified OAuth2 credentials across Google Drive, Gmail, Calendar,
Docs, and Sheets. Provides graceful simulation/fallback if credentials.json
is not yet configured by the user.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

_services_cache: Dict[str, Any] = {}


def get_project_root() -> str:
    """Returns root directory of the JARVIS assistant project."""
    # current file is assistant/workspace/auth.py -> parent of parent of parent
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_token_paths() -> list:
    root = get_project_root()
    return [os.path.join(root, "token_workspace.json"), os.path.join(root, "token.json")]


def get_token_path() -> str:
    # Prefer existing token file if present, else default to token_workspace.json
    for p in get_token_paths():
        if os.path.exists(p):
            return p
    return os.path.join(get_project_root(), "token_workspace.json")


def get_credentials_path() -> str:
    return os.path.join(get_project_root(), "credentials.json")


def is_workspace_connected() -> bool:
    """Returns True if valid workspace credentials or token exist."""
    creds_p = get_credentials_path()
    has_token = any(os.path.exists(p) for p in get_token_paths())
    return has_token or os.path.exists(creds_p)


def get_oauth_credentials():
    """Loads or refreshes user OAuth credentials."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        logger.warning("Google auth libraries not available.")
        return None

    token_path = get_token_path()
    creds_path = get_credentials_path()
    creds = None

    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to read token_workspace.json: {e}")
            try:
                os.remove(token_path)
            except OSError:
                pass
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            return creds
        except Exception as e:
            logger.warning(f"Could not refresh Google OAuth credentials: {e}")
            creds = None

    if not os.path.exists(creds_path):
        logger.info("No credentials.json found; Google Workspace in local demo mode.")
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        return creds
    except Exception as e:
        logger.error(f"Google OAuth authorization flow failed: {e}")
        return None


def get_google_service(service_name: str, version: str):
    """Returns a Google API client service instance or None."""
    global _services_cache
    cache_key = f"{service_name}_{version}"
    if cache_key in _services_cache:
        return _services_cache[cache_key]

    creds = get_oauth_credentials()
    if not creds:
        return None

    try:
        from googleapiclient.discovery import build
        service = build(service_name, version, credentials=creds)
        _services_cache[cache_key] = service
        return service
    except Exception as e:
        logger.error(f"Failed to build Google service {service_name} ({version}): {e}")
        return None
