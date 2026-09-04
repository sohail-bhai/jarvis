"""
Notifications popup dialog.
Displays clean user alerts with direct jump actions.
"""
from __future__ import annotations

import customtkinter as ctk
from typing import Callable
from gui import theme
from gui.store import store


class NotificationsModal(ctk.CTkFrame):
    def __init__(self, parent, on_navigate: Callable[[str], None]):
        # Call super with parent, using the card background and a nice border
        super().__init__(
            parent,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=12,
            width=360,
            height=400
        )
        self.on_navigate = on_navigate
        
        # Don't let it shrink to its contents
        self.grid_propagate(False)
        self.pack_propagate(False)

        # Place at top right of the application window
        # anchor="ne" means x,y coordinates are for the Top-Right corner of the widget
        self.place(relx=1.0, rely=0.0, x=-20, y=65, anchor="ne")
        self.lift()

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            hdr,
            text="Notifications",
            font=theme.font(15, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            hdr,
            text="✕",
            font=theme.font(11),
            width=26,
            height=26,
            fg_color=theme.MAIN_BG,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT_SECONDARY,
            corner_radius=13,
            command=self.destroy,
        ).pack(side="right")

        # Notification Items
        for notif in store.notifications:
            card = ctk.CTkFrame(
                container,
                fg_color=theme.MAIN_BG if not notif.get("unread") else theme.INFO_LIGHT,
                border_width=1,
                border_color=theme.INFO_BORDER if notif.get("unread") else theme.CARD_BORDER,
                corner_radius=10,
            )
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                row,
                text=notif.get("title", ""),
                font=theme.font(12, "bold"),
                text_color=theme.TEXT_PRIMARY,
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=notif.get("time", ""),
                font=theme.font(10),
                text_color=theme.TEXT_MUTED,
            ).pack(side="right")

            ctk.CTkLabel(
                card,
                text=notif.get("message", ""),
                font=theme.font(11),
                text_color=theme.TEXT_SECONDARY,
                wraplength=340,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=10, pady=(0, 8))
