"""Google Slides gateway engine.

Turns an outline - a title and a list of slides - into a real presentation.
Falls back to a described deck when Google is not connected, and says so.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from assistant.workspace.auth import get_google_service

logger = logging.getLogger(__name__)

_mock_decks: Dict[str, Dict[str, Any]] = {}


def _normalise(slides: Optional[List[Any]]) -> List[Dict[str, Any]]:
    """Accept ["A", "B"] or [{"title": .., "bullets": [..]}] alike."""
    normalised = []
    for entry in slides or []:
        if isinstance(entry, dict):
            title = str(entry.get("title", "")).strip() or "Slide"
            bullets = entry.get("bullets") or entry.get("body") or []
            if isinstance(bullets, str):
                bullets = [line for line in bullets.splitlines() if line.strip()]
        else:
            title = str(entry).strip() or "Slide"
            bullets = []
        normalised.append({"title": title, "bullets": [str(b) for b in bullets]})
    return normalised


def create_google_slides(title: str, slides: Optional[List[Any]] = None) -> Dict[str, Any]:
    """Creates a presentation with a title slide plus one slide per entry."""
    deck = _normalise(slides)
    service = get_google_service("slides", "v1")

    if service is not None:
        try:
            presentation = service.presentations().create(body={"title": title}).execute()
            deck_id = presentation.get("presentationId")

            # The new deck opens with one blank slide; use it for the title.
            first_slide = presentation.get("slides", [{}])[0]
            requests: List[Dict[str, Any]] = []
            title_placeholder = _placeholder_id(first_slide, "CENTERED_TITLE") \
                or _placeholder_id(first_slide, "TITLE")
            if title_placeholder:
                requests.append({"insertText": {"objectId": title_placeholder, "text": title}})

            for index, entry in enumerate(deck):
                slide_id = f"slide_{index}_{uuid.uuid4().hex[:6]}"
                requests.append({
                    "createSlide": {
                        "objectId": slide_id,
                        "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                        "placeholderIdMappings": [
                            {"layoutPlaceholder": {"type": "TITLE", "index": 0},
                             "objectId": f"{slide_id}_title"},
                            {"layoutPlaceholder": {"type": "BODY", "index": 0},
                             "objectId": f"{slide_id}_body"},
                        ],
                    }
                })
                requests.append({"insertText": {"objectId": f"{slide_id}_title",
                                                "text": entry["title"]}})
                if entry["bullets"]:
                    requests.append({"insertText": {"objectId": f"{slide_id}_body",
                                                    "text": "\n".join(entry["bullets"])}})

            if requests:
                service.presentations().batchUpdate(
                    presentationId=deck_id, body={"requests": requests}).execute()

            logger.info("Created Google Slides deck '%s' (%s)", title, deck_id)
            return {
                "presentationId": deck_id,
                "title": title,
                "slides": len(deck) + 1,
                "webViewLink": f"https://docs.google.com/presentation/d/{deck_id}/edit",
                "live": True,
            }
        except Exception as error:
            logger.error("Failed to create Google Slides deck: %s", error)
            return {"error": str(error), "live": True}

    deck_id = f"deck_{uuid.uuid4().hex[:8]}"
    _mock_decks[deck_id] = {
        "presentationId": deck_id,
        "title": title,
        "slides": len(deck) + 1,
        "outline": deck,
        "webViewLink": f"https://docs.google.com/presentation/d/{deck_id}/edit",
        "live": False,
    }
    logger.info("[Demo Mode] Described Slides deck '%s' (%s)", title, deck_id)
    return _mock_decks[deck_id]


def _placeholder_id(slide: Dict[str, Any], kind: str) -> str:
    for element in slide.get("pageElements", []):
        placeholder = element.get("shape", {}).get("placeholder", {})
        if placeholder.get("type") == kind:
            return element.get("objectId", "")
    return ""
