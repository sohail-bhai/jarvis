"""System Log: a plain-English record of what JARVIS is actually doing.

This panel shows observable actions only ("Searching your Google Drive",
"Found 4 matching files"). It is not a model-reasoning window, and it must
never surface credentials, so every line is redacted before display.
"""

import datetime
import re

from gui import theme

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

_REDACTED = "[hidden]"


def _clock(moment=None):
    """Format a time the way a person reads it, e.g. '3:24 PM'.

    strftime has no portable hour-without-zero-padding flag, so strip it here.
    """
    moment = moment or datetime.datetime.now()
    return moment.strftime("%I:%M %p").lstrip("0")


def redact(message):
    """Strip anything that looks like a credential out of a log line."""
    text = str(message)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(_REDACTED, text)
    return text


class SystemLog:
    """Right-hand panel showing recent activity in human language."""

    def __init__(self, ctk, parent, max_entries=500):
        self.ctk = ctk
        self.max_entries = max_entries
        self._entries = []

        self.frame = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=theme.RADIUS,
                                  border_width=1, border_color=theme.BORDER)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD, theme.PAD_SM))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="System Log", font=theme.font(14, "bold"),
                     text_color=theme.TEXT, anchor="w").grid(row=0, column=0, sticky="w")

        self.clear_button = ctk.CTkButton(
            header, text="Clear", width=54, height=24, font=theme.font(11),
            fg_color="transparent", text_color=theme.TEXT_MUTED,
            hover_color=theme.SURFACE_ALT, command=self.clear,
        )
        self.clear_button.grid(row=0, column=1, sticky="e")

        self.textbox = ctk.CTkTextbox(
            self.frame, fg_color=theme.SURFACE, border_width=0,
            text_color=theme.TEXT, font=theme.font(12), wrap="word",
            activate_scrollbars=True,
        )
        self.textbox.grid(row=1, column=0, sticky="nsew",
                          padx=theme.PAD_SM, pady=(0, theme.PAD_SM))

        self.textbox.tag_config("time", foreground=theme.TEXT_FAINT)
        self.textbox.tag_config("normal", foreground=theme.TEXT)
        self.textbox.tag_config("muted", foreground=theme.TEXT_MUTED)
        self.textbox.tag_config("success", foreground=theme.SUCCESS)
        self.textbox.tag_config("warning", foreground=theme.WARNING)
        self.textbox.tag_config("error", foreground=theme.ERROR)

        self._empty_label = ctk.CTkLabel(
            self.frame,
            text="Nothing yet.\nAsk JARVIS to do something and\nyou'll see the steps here.",
            font=theme.font(12), text_color=theme.TEXT_FAINT, justify="center",
        )
        self._empty_label.place(relx=0.5, rely=0.5, anchor="center")

        self.textbox.configure(state="disabled")

    def add(self, message, tone="normal"):
        """Append one plain-English line. `tone` selects the colour only."""
        message = redact(message).strip()
        if not message:
            return

        if self._empty_label is not None:
            self._empty_label.destroy()
            self._empty_label = None

        timestamp = _clock()
        self._entries.append((timestamp, message, tone))

        self.textbox.configure(state="normal")
        if len(self._entries) > self.max_entries:
            # Trim the oldest entry; each entry occupies two rendered lines.
            self._entries.pop(0)
            self.textbox.delete("1.0", "3.0")

        self.textbox.insert("end", f"{timestamp}\n", "time")
        self.textbox.insert("end", f"{message}\n\n", tone)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        self._entries.clear()
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    def entries(self):
        """Recent entries, oldest first. Used by the Activity page."""
        return list(self._entries)
