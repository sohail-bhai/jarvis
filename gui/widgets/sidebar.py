"""Primary navigation.

Only user-facing destinations belong here. Helper registries, capabilities,
protocols and permission internals stay out of primary navigation by design.
"""

from gui import theme
from gui.widgets.cards import StatusIndicator

# (key, icon, label)
NAV_ITEMS = [
    ("home", "⌂", "Home"),
    ("devices", "▤", "My Devices"),
    ("files", "🗀", "My Files"),
    ("google", "◈", "Google"),
    ("web", "◍", "Web"),
    ("activity", "≡", "Activity"),
    ("settings", "⚙", "Settings"),
]


class Sidebar:
    def __init__(self, ctk, parent, on_navigate):
        self.ctk = ctk
        self._on_navigate = on_navigate
        self._buttons = {}
        self._active = None

        self.frame = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=0,
                                  width=212)
        self.frame.grid_propagate(False)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(len(NAV_ITEMS) + 1, weight=1)

        wordmark = ctk.CTkLabel(self.frame, text="JARVIS", font=theme.font(15, "bold"),
                                text_color=theme.TEXT, anchor="w")
        wordmark.grid(row=0, column=0, sticky="ew",
                      padx=theme.PAD_LG, pady=(theme.PAD_LG, theme.PAD_LG))

        for index, (key, icon, label) in enumerate(NAV_ITEMS, start=1):
            button = ctk.CTkButton(
                self.frame, text=f"  {icon}   {label}", anchor="w",
                height=38, font=theme.font(13), corner_radius=theme.RADIUS_SM,
                fg_color="transparent", text_color=theme.TEXT_MUTED,
                hover_color=theme.SURFACE_ALT,
                command=lambda k=key: self._on_navigate(k),
            )
            button.grid(row=index, column=0, sticky="ew", padx=theme.PAD_SM, pady=1)
            self._buttons[key] = button

        separator = ctk.CTkFrame(self.frame, height=1, fg_color=theme.BORDER)
        separator.grid(row=len(NAV_ITEMS) + 2, column=0, sticky="ew",
                       padx=theme.PAD, pady=(theme.PAD_SM, theme.PAD_SM))

        self.status = StatusIndicator(self.ctk, self.frame, "JARVIS Online", "online")
        self.status.frame.grid(row=len(NAV_ITEMS) + 3, column=0, sticky="w",
                               padx=theme.PAD, pady=(0, theme.PAD_LG))

    def set_active(self, key):
        for item_key, button in self._buttons.items():
            if item_key == key:
                button.configure(fg_color=theme.ACCENT_SOFT, text_color=theme.ACCENT,
                                 font=theme.font(13, "bold"))
            else:
                button.configure(fg_color="transparent", text_color=theme.TEXT_MUTED,
                                 font=theme.font(13))
        self._active = key

    def set_status(self, text, tone="online"):
        self.status.set(text, tone)
