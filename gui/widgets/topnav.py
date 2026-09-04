"""
The top navigation bar.

The app used to wear a dark rail down the left, like every other dashboard.
This replaces it: the wordmark sits top-left, the sections read as a line of
text links beside it, and the account and command palette sit far right. It
gives the page its full width back, which is the point - the content is wide
and shallow, so the chrome should be too.
"""
from __future__ import annotations

import customtkinter as ctk

from gui import icons, theme


class TopNav(ctk.CTkFrame):
    ITEMS = [
        ("home", "Home"),
        ("devices", "Devices"),
        ("files", "Files"),
        ("google", "Google"),
        ("web", "Web"),
        ("activity", "Activity"),
        ("settings", "Settings"),
    ]

    def __init__(self, parent, on_navigate, on_open_command_palette,
                 on_open_notifications):
        super().__init__(parent, fg_color=theme.MAIN_BG, corner_radius=0, height=72)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.buttons = {}
        self._icons = []

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=theme.PAGE_GUTTER, pady=(20, 0))

        # Brand
        brand = ctk.CTkFrame(inner, fg_color="transparent")
        brand.pack(side="left")

        self.mark = icons.image("sparkle", 14, theme.ACCENT)
        self._icons.append(self.mark)
        if self.mark is not None:
            ctk.CTkLabel(brand, text="", image=self.mark, width=16).pack(
                side="left", padx=(0, 8))

        ctk.CTkLabel(
            brand,
            text=theme.tracked("Vave"),
            font=theme.display(16),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        # Sections, as text rather than as a list of boxes.
        links = ctk.CTkFrame(inner, fg_color="transparent")
        links.pack(side="left", padx=(38, 0))

        for page_id, label in self.ITEMS:
            selected = page_id == "home"
            button = ctk.CTkButton(
                links,
                text=label,
                font=theme.font(theme.SIZE_SMALL,
                                "bold" if selected else "normal"),
                fg_color="transparent",
                hover_color=theme.CARD_HOVER,
                text_color=(theme.TEXT_PRIMARY if selected else theme.TEXT_MUTED),
                corner_radius=theme.RADIUS_PILL,
                width=1, height=30,
                command=lambda pid=page_id: self.on_navigate(pid),
            )
            button.pack(side="left", padx=(0, 4))
            self.buttons[page_id] = button

        # Right: status, notifications, account.
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        self.avatar = ctk.CTkLabel(
            right, text="R",
            font=theme.font(theme.SIZE_SMALL, "bold"),
            text_color=theme.TEXT_LIGHT, fg_color=theme.ACCENT,
            corner_radius=15, width=30, height=30,
        )
        self.avatar.pack(side="right", padx=(12, 0))

        self.bell_icon = icons.image("bell", theme.ICON_INLINE, theme.TEXT_SECONDARY)
        self._icons.append(self.bell_icon)
        self.bell_btn = ctk.CTkButton(
            right, image=self.bell_icon, text=" 1",
            font=theme.font(theme.SIZE_LABEL, "bold"),
            fg_color="transparent", hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            corner_radius=theme.RADIUS_PILL, width=48, height=30,
            compound="left", command=on_open_notifications,
        )
        self.bell_btn.pack(side="right", padx=(8, 0))

        self.search_icon = icons.image("search", 14, theme.TEXT_MUTED)
        self._icons.append(self.search_icon)
        ctk.CTkButton(
            right, image=self.search_icon, compound="left",
            text="  Search    Ctrl K",
            font=theme.font(theme.SIZE_LABEL),
            fg_color=theme.CARD_BG, hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_MUTED,
            border_width=1, border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_PILL, width=186, height=30,
            anchor="w", command=on_open_command_palette,
        ).pack(side="right")

        # A hairline under the whole bar, so the chrome ends somewhere.
        ctk.CTkFrame(self, fg_color=theme.DIVIDER, height=1).pack(
            side="bottom", fill="x", padx=theme.PAGE_GUTTER)

    def highlight(self, page_id: str):
        for pid, button in self.buttons.items():
            current = pid == page_id
            button.configure(
                font=theme.font(theme.SIZE_SMALL, "bold" if current else "normal"),
                text_color=theme.TEXT_PRIMARY if current else theme.TEXT_MUTED,
            )

    def set_unread_count(self, count: int):
        self.bell_btn.configure(text=f" {count}" if count else "")

    # Kept so the controller can report listening state somewhere visible.
    def update_voice_state(self, is_listening: bool):
        self.avatar.configure(
            fg_color=theme.SUCCESS if is_listening else theme.ACCENT)
