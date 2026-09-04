"""Google Workspace Gateway Package for JARVIS."""

from assistant.workspace.gateway import WorkspaceGateway, gateway
from assistant.workspace.drive import search_drive, read_drive_file, upload_drive_file, list_drive_files
from assistant.workspace.gmail import search_emails, read_email, summarize_emails, draft_email, send_email
from assistant.workspace.calendar import get_upcoming_events, format_upcoming_events_summary, create_calendar_event, detect_scheduling_conflicts
from assistant.workspace.docs_sheets import create_google_doc, append_to_google_doc, read_google_sheet, append_to_google_sheet

__all__ = [
    "WorkspaceGateway",
    "gateway",
    "search_drive",
    "read_drive_file",
    "upload_drive_file",
    "list_drive_files",
    "search_emails",
    "read_email",
    "summarize_emails",
    "draft_email",
    "send_email",
    "get_upcoming_events",
    "format_upcoming_events_summary",
    "create_calendar_event",
    "detect_scheduling_conflicts",
    "create_google_doc",
    "append_to_google_doc",
    "read_google_sheet",
    "append_to_google_sheet",
]
