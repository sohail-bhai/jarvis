"""Keeps credentials out of anything the desktop UI shows.

The System Log is a record of what JARVIS is doing, not a place a token
should ever appear. This lives in its own module, free of tkinter, so it can
be tested without a display and reused by any panel that renders text.
"""

import re

# Anything matching these is replaced before a line reaches the screen.
_SECRET_PATTERNS = [
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|secret)"
               r"\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+"),  # JWT
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}"),                                   # Google API key
    re.compile(r"\bya29\.[0-9A-Za-z_\-]+"),                                     # Google OAuth token
    re.compile(r"\bgh[pousr]_[0-9A-Za-z]{20,}"),                                # GitHub token
    re.compile(r"\bsk-[0-9A-Za-z]{20,}"),                                       # generic secret key
]

REDACTED = "[hidden]"


def redact(message):
    """Strip anything that looks like a credential out of a line of text."""
    text = str(message)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text
