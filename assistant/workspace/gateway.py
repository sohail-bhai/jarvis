"""Unified Google Workspace Gateway.

Provides a single facade over Google Drive, Gmail, Calendar, Docs, and Sheets.
Maps capability strings to operations and provides status reporting.
"""

import logging
from typing import Dict, Any, List, Optional, Callable

from assistant.workspace.auth import is_workspace_connected
from assistant.workspace.drive import search_drive, read_drive_file, upload_drive_file, list_drive_files
from assistant.workspace.gmail import search_emails, read_email, summarize_emails, draft_email, send_email
from assistant.workspace.calendar import get_upcoming_events, format_upcoming_events_summary, create_calendar_event, detect_scheduling_conflicts
from assistant.workspace.docs_sheets import create_google_doc, append_to_google_doc, read_google_sheet, append_to_google_sheet

logger = logging.getLogger(__name__)


class WorkspaceGateway:
    """Unified Gateway coordinating Google Workspace operations."""

    def __init__(self):
        self._capabilities: Dict[str, Callable] = {
            "google.drive.search": search_drive,
            "google.drive.read": read_drive_file,
            "google.drive.write": upload_drive_file,
            "google.drive.list": list_drive_files,
            "google.gmail.search": search_emails,
            "google.gmail.read": read_email,
            "google.gmail.summary": summarize_emails,
            "google.gmail.draft": draft_email,
            "google.gmail.send": send_email,
            "google.calendar.read": get_upcoming_events,
            "google.calendar.summary": format_upcoming_events_summary,
            "google.calendar.write": create_calendar_event,
            "google.calendar.conflicts": detect_scheduling_conflicts,
            "google.docs.create": create_google_doc,
            "google.docs.append": append_to_google_doc,
            "google.sheets.read": read_google_sheet,
            "google.sheets.write": append_to_google_sheet,
        }

    def is_connected(self) -> bool:
        """Returns True if user has configured Google credentials."""
        return is_workspace_connected()

    def get_status(self) -> Dict[str, Any]:
        """Returns connection and health status of Google Workspace services."""
        connected = self.is_connected()
        return {
            "connected": connected,
            "mode": "live" if connected else "demo",
            "services": {
                "drive": {"status": "online" if connected else "demo", "label": "Google Drive"},
                "gmail": {"status": "online" if connected else "demo", "label": "Gmail"},
                "calendar": {"status": "online" if connected else "demo", "label": "Google Calendar"},
                "docs": {"status": "online" if connected else "demo", "label": "Google Docs"},
                "sheets": {"status": "online" if connected else "demo", "label": "Google Sheets"}
            },
            "capabilities": list(self._capabilities.keys())
        }

    def list_capabilities(self) -> List[str]:
        """Returns all capability IDs supported by the Google Workspace Gateway."""
        return list(self._capabilities.keys())

    def execute_capability(self, capability: str, **kwargs) -> Any:
        """Executes a registered capability with provided keyword arguments."""
        if capability not in self._capabilities:
            raise ValueError(f"Unknown Google Workspace capability: '{capability}'. Supported: {list(self._capabilities.keys())}")

        handler = self._capabilities[capability]
        logger.info(f"[Workspace Gateway] Executing capability '{capability}' with args {kwargs}")
        return handler(**kwargs)


# Global singleton instance
gateway = WorkspaceGateway()
