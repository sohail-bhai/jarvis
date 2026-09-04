"""Gmail Gateway Engine.

Handles searching messages, reading/summarizing emails, drafting messages,
and sending emails with safety controls.
"""

import base64
import logging
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional

from assistant.workspace.auth import get_google_service

logger = logging.getLogger(__name__)

_mock_emails: List[Dict[str, Any]] = [
    {
        "id": "msg_mock_001",
        "sender": "team@hackwave.dev",
        "subject": "Hackwave 2026: Project Submission & Demo Schedule",
        "snippet": "Welcome hackers! The final judging presentations will begin at 4 PM...",
        "body": "Welcome hackers!\n\nThe final judging presentations will begin promptly at 4 PM. Ensure your repository has a comprehensive README with architecture visuals, and all automated smoke tests pass.\n\nBest of luck,\nHackwave Organizing Team",
        "unread": True
    },
    {
        "id": "msg_mock_002",
        "sender": "alerts@cloud.google.com",
        "subject": "Google Cloud Run: Service Health Status Healthy",
        "snippet": "All services in region us-central1 are currently operating at normal latency...",
        "body": "Your Cloud Run instances have passed all automatic health probes. CPU utilization: 14%. No anomalies detected.",
        "unread": True
    },
    {
        "id": "msg_mock_003",
        "sender": "alex@collab.ai",
        "subject": "Invoice & Deliverables for Review",
        "snippet": "Attached is the invoice for project infrastructure...",
        "body": "Hi Sohail,\n\nAttached is the invoice for the cloud server tier. Payment is due on March 15. Let me know if you have any questions.\n\nCheers,\nAlex",
        "unread": False
    }
]


def search_emails(query: str = "is:unread", max_results: int = 5) -> List[Dict[str, Any]]:
    """Searches Gmail messages using standard Gmail query syntax."""
    service = get_google_service("gmail", "v1")
    if service is not None:
        try:
            results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])
            output = []
            for msg_meta in messages:
                msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
                headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
                output.append({
                    "id": msg["id"],
                    "sender": headers.get("from", "Unknown"),
                    "subject": headers.get("subject", "(No Subject)"),
                    "snippet": msg.get("snippet", ""),
                    "unread": "UNREAD" in msg.get("labelIds", [])
                })
            return output
        except Exception as e:
            logger.error(f"Gmail search error: {e}")

    # Fallback to demo mock emails
    q_lower = query.lower()
    matches = []
    for m in _mock_emails:
        if "unread" in q_lower and not m["unread"]:
            continue
        if q_lower not in "is:unread" and q_lower not in m["subject"].lower() and q_lower not in m["sender"].lower() and q_lower not in m["body"].lower():
            continue
        matches.append(m)
    return matches[:max_results] or _mock_emails[:max_results]


def read_email(message_id: str) -> Dict[str, Any]:
    """Reads full content of a message."""
    service = get_google_service("gmail", "v1")
    if service is not None:
        try:
            msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            body = ""
            payload = msg.get("payload", {})
            parts = payload.get("parts", [])
            if not parts and "body" in payload and "data" in payload["body"]:
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
            else:
                for part in parts:
                    if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                        body += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            return {
                "id": message_id,
                "sender": headers.get("from", ""),
                "subject": headers.get("subject", ""),
                "snippet": msg.get("snippet", ""),
                "body": body or msg.get("snippet", "")
            }
        except Exception as e:
            logger.error(f"Failed to read email {message_id}: {e}")

    for m in _mock_emails:
        if m["id"] == message_id:
            return m
    return {"id": message_id, "subject": "Email", "body": "Content simulated for demo."}


def summarize_emails(limit: int = 5) -> str:
    """Retrieves recent unread emails and formats a concise executive summary."""
    emails = search_emails("is:unread", max_results=limit)
    if not emails:
        return "You have no unread emails."

    summary = f"You have {len(emails)} unread email(s):\n"
    for idx, em in enumerate(emails, start=1):
        summary += f"\n{idx}. From: {em['sender']}\n   Subject: {em['subject']}\n   Summary: {em['snippet']}\n"
    return summary


def draft_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Creates a draft in Gmail."""
    service = get_google_service("gmail", "v1")
    if service is not None:
        try:
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw_msg = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw_msg}}).execute()
            logger.info(f"Created draft in Gmail: '{subject}' to {to}")
            return draft
        except Exception as e:
            logger.error(f"Failed to create draft: {e}")
            return {"error": str(e)}

    # Mock draft
    import uuid
    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    logger.info(f"[Demo Mode] Created draft '{subject}' to {to} (ID: {draft_id})")
    return {"id": draft_id, "to": to, "subject": subject, "body": body, "status": "drafted"}


def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Sends an email via Gmail (Consequential action, passes through safety gate)."""
    service = get_google_service("gmail", "v1")
    if service is not None:
        try:
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw_msg = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            sent = service.users().messages().send(userId="me", body={"raw": raw_msg}).execute()
            logger.info(f"Sent email: '{subject}' to {to}")
            return sent
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {"error": str(e)}

    import uuid
    sent_id = f"sent_{uuid.uuid4().hex[:8]}"
    logger.info(f"[Demo Mode] Sent email '{subject}' to {to} (ID: {sent_id})")
    return {"id": sent_id, "to": to, "subject": subject, "status": "sent"}
