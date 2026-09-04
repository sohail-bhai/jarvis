"""Small reusable building blocks: cards, status dots, task progress, approvals."""

from gui import theme

# Status tones shared by the dot indicator and the environment cards.
TONE_COLORS = {
    "online": theme.SUCCESS,
    "ready": theme.SUCCESS,
    "connected": theme.SUCCESS,
    "waiting": theme.WARNING,
    "offline": theme.TEXT_FAINT,
    "not connected": theme.TEXT_FAINT,
    "error": theme.ERROR,
}


def tone_color(tone):
    return TONE_COLORS.get(str(tone).lower(), theme.TEXT_MUTED)


def card(ctk, parent, **kwargs):
    """A plain white surface with a hairline border and soft radius."""
    options = dict(
        fg_color=theme.SURFACE,
        corner_radius=theme.RADIUS,
        border_width=1,
        border_color=theme.BORDER,
    )
    options.update(kwargs)
    return ctk.CTkFrame(parent, **options)


def section_title(ctk, parent, text):
    return ctk.CTkLabel(parent, text=text, font=theme.font(13, "bold"),
                        text_color=theme.TEXT_MUTED, anchor="w")


class StatusIndicator:
    """A coloured dot plus a label, e.g. '● JARVIS Online'."""

    def __init__(self, ctk, parent, text="", tone="online"):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")

        self.dot = ctk.CTkLabel(self.frame, text="●", font=theme.font(12),
                                text_color=tone_color(tone))
        self.dot.grid(row=0, column=0, padx=(0, 6))

        self.label = ctk.CTkLabel(self.frame, text=text, font=theme.font(12),
                                  text_color=theme.TEXT_MUTED, anchor="w")
        self.label.grid(row=0, column=1, sticky="w")

    def set(self, text, tone="online"):
        self.label.configure(text=text)
        self.dot.configure(text_color=tone_color(tone))


class EnvironmentCard:
    """Home-page tile: 'My Computer — Online'."""

    def __init__(self, ctk, parent, icon, name, status, tone="online"):
        self.frame = card(ctk, parent)
        self.frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame, text=icon, font=theme.font(20)).grid(
            row=0, column=0, rowspan=2, padx=(theme.PAD, theme.PAD_SM), pady=theme.PAD)

        ctk.CTkLabel(self.frame, text=name, font=theme.font(13, "bold"),
                     text_color=theme.TEXT, anchor="w").grid(
            row=0, column=1, sticky="w", pady=(theme.PAD, 0))

        self.status_label = ctk.CTkLabel(self.frame, text=status, font=theme.font(11),
                                         text_color=tone_color(tone), anchor="w")
        self.status_label.grid(row=1, column=1, sticky="w", pady=(0, theme.PAD))

    def set_status(self, status, tone="online"):
        self.status_label.configure(text=status, text_color=tone_color(tone))


class TaskProgress:
    """The '✓ done / ● working / ○ pending' step list for the current task."""

    DONE, ACTIVE, PENDING = "done", "active", "pending"
    _GLYPH = {DONE: "✓", ACTIVE: "●", PENDING: "○"}
    _COLOR = {DONE: theme.SUCCESS, ACTIVE: theme.ACCENT, PENDING: theme.TEXT_FAINT}

    def __init__(self, ctk, parent):
        self.ctk = ctk
        self.frame = card(ctk, parent)
        self.frame.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(self.frame, text="Nothing running", font=theme.font(14, "bold"),
                                  text_color=theme.TEXT, anchor="w")
        self.title.grid(row=0, column=0, sticky="ew", padx=theme.PAD,
                        pady=(theme.PAD, theme.PAD_SM))

        self.steps_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.steps_frame.grid(row=1, column=0, sticky="ew", padx=theme.PAD,
                              pady=(0, theme.PAD))
        self.steps_frame.grid_columnconfigure(1, weight=1)

        self._rows = []
        self.set_idle()

    def set_idle(self):
        self.title.configure(text="Nothing running")
        self.set_steps([])
        self._placeholder = self.ctk.CTkLabel(
            self.steps_frame, text="When you ask JARVIS for something, "
                                   "the steps will appear here.",
            font=theme.font(12), text_color=theme.TEXT_MUTED,
            anchor="w", justify="left", wraplength=420)
        self._placeholder.grid(row=0, column=0, columnspan=2, sticky="w")
        self._rows.append(self._placeholder)

    def set_task(self, title, steps):
        """steps: list of (label, state) where state is done/active/pending."""
        self.title.configure(text=title)
        self.set_steps(steps)

    def set_steps(self, steps):
        for widget in self._rows:
            widget.destroy()
        self._rows = []

        for index, (label, state) in enumerate(steps):
            glyph = self.ctk.CTkLabel(
                self.steps_frame, text=self._GLYPH.get(state, "○"),
                font=theme.font(12), text_color=self._COLOR.get(state, theme.TEXT_FAINT))
            glyph.grid(row=index, column=0, sticky="w", padx=(0, theme.PAD_SM), pady=2)

            text_color = theme.TEXT if state != self.PENDING else theme.TEXT_MUTED
            text = self.ctk.CTkLabel(self.steps_frame, text=label, font=theme.font(12),
                                     text_color=text_color, anchor="w")
            text.grid(row=index, column=1, sticky="w", pady=2)

            self._rows.extend([glyph, text])


class ApprovalCard:
    """Asks the user to approve a consequential action, in plain language."""

    def __init__(self, ctk, parent, on_resolve):
        self.ctk = ctk
        self._on_resolve = on_resolve
        self.request_id = None

        self.frame = ctk.CTkFrame(parent, fg_color=theme.WARNING_SOFT,
                                  corner_radius=theme.RADIUS,
                                  border_width=1, border_color=theme.WARNING)
        self.frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.frame, text="JARVIS needs your approval",
                     font=theme.font(13, "bold"), text_color=theme.TEXT,
                     anchor="w").grid(row=0, column=0, sticky="ew",
                                      padx=theme.PAD, pady=(theme.PAD, 2))

        self.detail = ctk.CTkLabel(self.frame, text="", font=theme.font(12),
                                   text_color=theme.TEXT_MUTED, anchor="w",
                                   justify="left", wraplength=260)
        self.detail.grid(row=1, column=0, sticky="ew", padx=theme.PAD, pady=(0, theme.PAD_SM))

        buttons = ctk.CTkFrame(self.frame, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="ew", padx=theme.PAD, pady=(0, theme.PAD))
        buttons.grid_columnconfigure((0, 1), weight=1)

        self.decline_button = ctk.CTkButton(
            buttons, text="Not now", height=32, font=theme.font(12),
            fg_color=theme.SURFACE, text_color=theme.TEXT, hover_color=theme.SURFACE_ALT,
            border_width=1, border_color=theme.BORDER_STRONG,
            corner_radius=theme.RADIUS_SM, command=lambda: self._resolve(False))
        self.decline_button.grid(row=0, column=0, sticky="ew", padx=(0, theme.PAD_XS))

        self.approve_button = ctk.CTkButton(
            buttons, text="Approve", height=32, font=theme.font(12, "bold"),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            corner_radius=theme.RADIUS_SM, command=lambda: self._resolve(True))
        self.approve_button.grid(row=0, column=1, sticky="ew", padx=(theme.PAD_XS, 0))

    def show(self, request_id, message):
        self.request_id = request_id
        self.detail.configure(text=message)

    def _resolve(self, approved):
        request_id, self.request_id = self.request_id, None
        self._on_resolve(request_id, approved)
