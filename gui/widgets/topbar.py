"""
TopBar component for the VAVE desktop interface.
Contains global search trigger (Ctrl+K), notification bell, and user avatar.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import icons, theme
from gui.store import store


class TopBar(ctk.CTkFrame):
    def __init__(self, parent, on_open_command_palette, on_open_notifications):
        super().__init__(
            parent,
            height=54,
            fg_color=theme.MAIN_BG,
            corner_radius=0,
        )
        self.pack_propagate(False)
        self.on_open_command_palette = on_open_command_palette
        self.on_open_notifications = on_open_notifications

        # Left: Page Title container
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.pack(side="left", padx=16, fill="y")

        self.title_lbl = ctk.CTkLabel(
            self.left_frame,
            text="Home",
            font=theme.font(15, "bold"),
            text_color=theme.TEXT_PRIMARY,
        )
        self.title_lbl.pack(side="left", pady=12)

        # Right: Bell + Avatar
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", padx=16, fill="y")

        # Avatar
        avatar = ctk.CTkLabel(
            right_frame,
            text="R",
            font=theme.font(12, "bold"),
            text_color=theme.TEXT_SECONDARY,
            fg_color=theme.CARD_HOVER,
            corner_radius=theme.RADIUS_CARD,
            width=28,
            height=28,
        )
        avatar.pack(side="right", padx=(8, 0), pady=13)

        # Notification bell, with the unread count beside it
        self.bell_icon = icons.image("bell", theme.ICON_INLINE, theme.TEXT_SECONDARY)
        self.bell_btn = ctk.CTkButton(
            right_frame,
            image=self.bell_icon,
            text=" 1",
            font=theme.font(11, "bold"),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_CONTROL,
            width=52,
            height=30,
            compound="left",
            command=self.on_open_notifications,
        )
        self.bell_btn.pack(side="right", padx=6, pady=12)

        # Center: Command Search Box Trigger
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(side="right", expand=True, fill="x", padx=(30, 20), pady=8)

        self.search_icon = icons.image("search", theme.ICON_INLINE, theme.TEXT_MUTED)
        self.search_btn = ctk.CTkButton(
            center_frame,
            image=self.search_icon,
            compound="left",
            text="  Ask VAVE anything...",
            font=theme.font(12),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_MUTED,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_CONTROL,
            height=32,
            anchor="w",
            command=self.on_open_command_palette,
        )
        self.search_btn.pack(fill="x")

        # Shortcut hint sits beside the box instead of being padded into it
        # with spaces, which broke alignment at every window width. It is
        # dropped entirely on a narrow window, where it would otherwise sit on
        # top of the placeholder.
        self.shortcut_lbl = ctk.CTkLabel(
            self.search_btn,
            text="Ctrl+K",
            font=theme.font(10),
            text_color=theme.TEXT_MUTED,
        )
        self._shortcut_shown = False
        self.search_btn.bind("<Configure>", self._on_search_resize)

    # Below this the search box has no room for a hint as well as its label.
    SHORTCUT_MIN_WIDTH = 300

    def _on_search_resize(self, event):
        should_show = event.width >= self.SHORTCUT_MIN_WIDTH
        if should_show == self._shortcut_shown:
            return
        self._shortcut_shown = should_show
        if should_show:
            self.shortcut_lbl.place(relx=1.0, rely=0.5, x=-13, anchor="e")
        else:
            self.shortcut_lbl.place_forget()

    def set_title(self, title: str):
        self.title_lbl.configure(text=title)

    def set_unread_count(self, count: int):
        if count > 0:
            self.bell_btn.configure(text=f" {count}", width=52)
        else:
            self.bell_btn.configure(text="", width=34)
