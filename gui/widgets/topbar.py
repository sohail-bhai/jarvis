"""
TopBar component for the VAVE desktop interface.
Contains global search trigger (Ctrl+K), notification bell, and user avatar.
"""
from __future__ import annotations

import os
from PIL import Image
import customtkinter as ctk
from gui import theme
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
            text_color="#374151",
            fg_color="#E5E7EB",
            corner_radius=14,
            width=28,
            height=28,
        )
        avatar.pack(side="right", padx=(8, 0), pady=13)

        # Notification Bell (Modern aesthetic icon with optional badge)
        bell_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "bell_hd.png")
        if os.path.exists(bell_icon_path):
            pil_bell = Image.open(bell_icon_path)
            self.bell_ctk_image = ctk.CTkImage(light_image=pil_bell, dark_image=pil_bell, size=(18, 18))
            self.bell_btn = ctk.CTkButton(
                right_frame,
                image=self.bell_ctk_image,
                text=" 1",
                font=theme.font(11, "bold"),
                fg_color=theme.CARD_BG,
                hover_color=theme.CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=14,
                width=48,
                height=28,
                compound="left",
                command=self.on_open_notifications,
            )
        else:
            self.bell_btn = ctk.CTkButton(
                right_frame,
                text="1",
                font=theme.font(11, "bold"),
                fg_color=theme.CARD_BG,
                hover_color=theme.CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=14,
                width=46,
                height=28,
                command=self.on_open_notifications,
            )
        self.bell_btn.pack(side="right", padx=4, pady=13)

        # Center: Command Search Box Trigger
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(side="right", expand=True, fill="x", padx=(30, 20), pady=8)

        self.search_btn = ctk.CTkButton(
            center_frame,
            text=" ✦  Ask VAVE anything...                                            ⌘K / Ctrl+K",
            font=theme.font(12),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_MUTED,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=16,
            height=34,
            anchor="w",
            command=self.on_open_command_palette,
        )
        self.search_btn.pack(fill="x")

    def set_title(self, title: str):
        self.title_lbl.configure(text=title)

    def set_unread_count(self, count: int):
        if hasattr(self, "bell_ctk_image"):
            if count > 0:
                self.bell_btn.configure(text=f" {count}", width=48)
            else:
                self.bell_btn.configure(text="", width=32)
        else:
            if count > 0:
                self.bell_btn.configure(text=str(count))
            else:
                self.bell_btn.configure(text="")
