"""Google Calendar Gateway Engine.

Handles retrieving schedule, creating events, detecting scheduling conflicts,
and formatting reminders.
"""

import datetime
import logging
from typing import List, Dict, Any, Optional

from assistant.workspace.auth import get_google_service

logger = logging.getLogger(__name__)

_mock_events: List[Dict[str, Any]] = [
    {
        "id": "event_mock_001",
        "summary": "Hackwave Demo Presentation",
        "start": {"dateTime": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).isoformat()},
        "end": {"dateTime": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).isoformat()},
        "description": "Presenting JARVIS Personal AI Control Plane to Judges."
    },
    {
        "id": "event_mock_002",
        "summary": "Architecture Review Sync",
        "start": {"dateTime": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1, hours=4)).isoformat()},
        "end": {"dateTime": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1, hours=5)).isoformat()},
        "description": "Reviewing Phase 2 connected infrastructure and cross-service orchestration."
    }
]


def get_upcoming_events(max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetches upcoming events starting from now."""
    service = get_google_service("calendar", "v3")
    if service is not None:
        try:
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now_iso,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            items = events_result.get("items", [])
            logger.info(f"Google Calendar returned {len(items)} upcoming events.")
            return items
        except Exception as e:
            logger.error(f"Google Calendar API error: {e}")

    # Fallback to demo mode
    return _mock_events[:max_results]


def format_upcoming_events_summary(max_results: int = 5) -> str:
    """Returns human-readable text summarizing upcoming schedule."""
    events = get_upcoming_events(max_results=max_results)
    if not events:
        return "You have no upcoming events on your calendar."

    summary = f"You have {len(events)} upcoming event(s):\n"
    for idx, event in enumerate(events, start=1):
        start_str = event["start"].get("dateTime", event["start"].get("date", "Unknown time"))
        summary += f"{idx}. {event.get('summary', 'Untitled Event')} at {start_str}\n"
    return summary


def create_calendar_event(
    summary: str,
    start_time_iso: Optional[str] = None,
    duration_minutes: int = 60,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new event on the user's primary calendar."""
    if not start_time_iso:
        start_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    else:
        try:
            start_dt = datetime.datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
        except Exception:
            start_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

    duration_int = int(duration_minutes) if duration_minutes is not None else 60
    end_dt = start_dt + datetime.timedelta(minutes=duration_int)

    event_body = {
        "summary": summary,
        "description": description or f"Created autonomously via JARVIS Control Plane.",
        "start": {"dateTime": start_dt.isoformat()},
        "end": {"dateTime": end_dt.isoformat()}
    }

    service = get_google_service("calendar", "v3")
    if service is not None:
        try:
            created = service.events().insert(calendarId="primary", body=event_body).execute()
            logger.info(f"Created Calendar event: {summary} (ID: {created.get('id')})")
            return created
        except Exception as e:
            logger.error(f"Failed to create Calendar event: {e}")
            return {"error": str(e)}

    import uuid
    new_event = {
        "id": f"event_{uuid.uuid4().hex[:8]}",
        "summary": summary,
        "description": event_body["description"],
        "start": event_body["start"],
        "end": event_body["end"],
        "status": "confirmed"
    }
    _mock_events.append(new_event)
    logger.info(f"[Demo Mode] Created Calendar event: '{summary}' from {start_dt.isoformat()} to {end_dt.isoformat()}")
    return new_event


def detect_scheduling_conflicts(start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
    """Checks whether the requested window overlaps with any scheduled events."""
    try:
        req_start = datetime.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        req_end = datetime.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        if req_start.tzinfo is None:
            req_start = req_start.replace(tzinfo=datetime.timezone.utc)
        if req_end.tzinfo is None:
            req_end = req_end.replace(tzinfo=datetime.timezone.utc)
    except Exception as e:
        logger.error(f"Invalid timestamp format: {e}")
        return []

    events = get_upcoming_events(max_results=20)
    conflicts = []
    for ev in events:
        s_raw = ev["start"].get("dateTime")
        e_raw = ev["end"].get("dateTime")
        if not s_raw or not e_raw:
            continue
        try:
            ev_start = datetime.datetime.fromisoformat(s_raw.replace("Z", "+00:00"))
            ev_end = datetime.datetime.fromisoformat(e_raw.replace("Z", "+00:00"))
            if ev_start.tzinfo is None:
                ev_start = ev_start.replace(tzinfo=datetime.timezone.utc)
            if ev_end.tzinfo is None:
                ev_end = ev_end.replace(tzinfo=datetime.timezone.utc)
            # Overlap condition: req_start < ev_end and req_end > ev_start
            if req_start < ev_end and req_end > ev_start:
                conflicts.append(ev)
        except Exception:
            continue
    return conflicts
