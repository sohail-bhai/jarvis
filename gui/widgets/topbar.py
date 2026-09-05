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
            fg_color=theme.SURFACE_SUBTLE,
            corner_radius=15,
            width=30,
            height=30,
        )
        avatar.pack(side="right", padx=(10, 0), pady=12)

        # Notification bell, drawn at the size and colour it is shown at
        # rather than loaded from a bundled bitmap.
        self.bell_image = icons.image("bell", theme.ICON, theme.TEXT_SECONDARY)
        self.bell_btn = ctk.CTkButton(
            right_frame,
            image=self.bell_image,
            text="1",
            font=theme.font(11, "bold"),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=15,
            width=52 if self.bell_image else 44,
            height=30,
            compound="left",
            command=self.on_open_notifications,
        )
        self.bell_btn.pack(side="right", padx=4, pady=12)

        # Center: Command Search Box Trigger
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(side="right", expand=True, fill="x",
                          padx=(theme.SPACE_LG, theme.SPACE_MD), pady=8)

        self.search_image = icons.image("search", theme.ICON_SM, theme.TEXT_MUTED)
        self.search_btn = ctk.CTkButton(
            center_frame,
            image=self.search_image,
            text="   Ask VAVE anything\u2026",
            font=theme.font(12),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_MUTED,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS,
            height=36,
            anchor="w",
            compound="left",
            command=self.on_open_command_palette,
        )
        # A search field the full width of a wide monitor reads as a banner
        # rather than a control, so it stops growing at a usable width.
        self.search_btn.pack(side="left", fill="x", expand=True)
        self.search_btn.configure(width=460)

    def set_title(self, title: str):
        self.title_lbl.configure(text=title)

    def set_unread_count(self, count: int):
        if count > 0:
            self.bell_btn.configure(text=str(count),
                                    width=52 if self.bell_image else 44)
        else:
            self.bell_btn.configure(text="", width=36)
