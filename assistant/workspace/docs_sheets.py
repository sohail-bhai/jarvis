"""Google Docs and Google Sheets Gateway Engine.

Allows creating documents, appending summaries, reading sheets tables,
and exporting reports directly to Google Workspace.
"""

import logging
from typing import List, Dict, Any, Optional

from assistant.workspace.auth import get_google_service

logger = logging.getLogger(__name__)

_mock_docs: Dict[str, Dict[str, Any]] = {}
_mock_sheets: Dict[str, List[List[Any]]] = {
    "mock_sheet_001": [
        ["Task Name", "Status", "Assigned Helper", "Duration (s)"],
        ["Analyze Dependencies", "Completed", "Coding Helper", 12.4],
        ["Run Test Suite", "Completed", "Testing Helper", 8.2],
        ["Deploy to Cloud Run", "Pending Approval", "DevOps Helper", 0.0]
    ]
}


def create_google_doc(title: str, content: str = "") -> Dict[str, Any]:
    """Creates a new Google Doc with optional initial content."""
    service_docs = get_google_service("docs", "v1")
    if service_docs is not None:
        try:
            body = {"title": title}
            doc = service_docs.documents().create(body=body).execute()
            doc_id = doc.get("documentId")
            logger.info(f"Created Google Doc: '{title}' (ID: {doc_id})")

            if content and doc_id:
                requests = [{
                    "insertText": {
                        "location": {"index": 1},
                        "text": content
                    }
                }]
                service_docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

            return doc
        except Exception as e:
            logger.error(f"Failed to create Google Doc: {e}")
            return {"error": str(e)}

    # Mock doc creation
    import uuid
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    _mock_docs[doc_id] = {
        "documentId": doc_id,
        "title": title,
        "content": content,
        "webViewLink": f"https://docs.google.com/document/d/{doc_id}/edit"
    }
    logger.info(f"[Demo Mode] Created Google Doc: '{title}' (ID: {doc_id})")
    return _mock_docs[doc_id]


def append_to_google_doc(document_id: str, text: str) -> bool:
    """Appends text to an existing Google Doc."""
    service_docs = get_google_service("docs", "v1")
    if service_docs is not None:
        try:
            doc = service_docs.documents().get(documentId=document_id).execute()
            content_list = doc.get("body", {}).get("content", [])
            end_index = content_list[-1].get("endIndex", 1) - 1 if content_list else 1

            requests = [{
                "insertText": {
                    "location": {"index": max(1, end_index)},
                    "text": "\n" + text
                }
            }]
            service_docs.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to append to Google Doc {document_id}: {e}")
            return False

    if document_id in _mock_docs:
        _mock_docs[document_id]["content"] += "\n" + text
        logger.info(f"[Demo Mode] Appended text to Doc {document_id}")
        return True
    return False


def read_google_sheet(spreadsheet_id: str, range_name: str = "Sheet1!A1:Z100") -> List[List[Any]]:
    """Reads rows of data from a Google Sheet."""
    service_sheets = get_google_service("sheets", "v4")
    if service_sheets is not None:
        try:
            result = service_sheets.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name
            ).execute()
            return result.get("values", [])
        except Exception as e:
            logger.error(f"Failed to read Google Sheet {spreadsheet_id}: {e}")
            return []

    return _mock_sheets.get(spreadsheet_id, [["Header 1", "Header 2"], ["Data A", "Data B"]])


def append_to_google_sheet(spreadsheet_id: str, rows: Any, range_name: str = "Sheet1!A1") -> bool:
    """Appends one or more rows to a Google Sheet."""
    if not isinstance(rows, list):
        rows = [[rows]]
    elif rows and not isinstance(rows[0], (list, tuple)):
        rows = [rows]

    service_sheets = get_google_service("sheets", "v4")
    if service_sheets is not None:
        try:
            body = {"values": rows}
            service_sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            logger.info(f"Appended {len(rows)} row(s) to Google Sheet {spreadsheet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to append to Google Sheet: {e}")
            return False

    if spreadsheet_id not in _mock_sheets:
        _mock_sheets[spreadsheet_id] = []
    _mock_sheets[spreadsheet_id].extend(rows)
    logger.info(f"[Demo Mode] Appended {len(rows)} row(s) to Sheet {spreadsheet_id}")
    return True
