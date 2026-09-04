"""
My Devices screen.
Shows connected user hardware in human-friendly cards.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import theme
from gui.store import store


class DevicesPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 16))

        ctk.CTkLabel(
            header,
            text="My Devices",
            font=theme.font(20, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="These are the devices JARVIS can work with.",
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Device Cards Grid (2 columns)
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 20))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="dev")

        for idx, dev in enumerate(store.devices):
            r = idx // 2
            c = idx % 2
            self._create_device_card(grid, dev, r, c)

    def _create_device_card(self, parent, dev, r, c):
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=14,
        )
        card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        # Top row: icon + name + status
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=dev.get("icon", "💻"),
            font=theme.font(20),
        ).pack(side="left", padx=(0, 10))

        title_col = ctk.CTkFrame(top_row, fg_color="transparent")
        title_col.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            title_col,
            text=dev.get("name", "Device"),
            font=theme.font(14, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        st_row = ctk.CTkFrame(title_col, fg_color="transparent")
        st_row.pack(anchor="w")

        is_online = dev.get("status") in ["Online", "Connected"]
        ctk.CTkLabel(
            st_row,
            text="●",
            font=theme.font(9, "bold"),
            text_color=theme.SUCCESS if is_online else theme.TEXT_MUTED,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            st_row,
            text=dev.get("status", "Offline"),
            font=theme.font(11),
            text_color=theme.TEXT_SECONDARY,
        ).pack(side="left")

        # Open button
        open_btn = ctk.CTkButton(
            top_row,
            text="Open",
            font=theme.font(11, "bold"),
            fg_color=theme.MAIN_BG,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT_PRIMARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=8,
            width=64,
            height=28,
            command=lambda d=dev: store.open_drawer("device", d),
        )
        open_btn.pack(side="right")

        # Capabilities list
        ctk.CTkLabel(
            inner,
            text="\nJARVIS can:",
            font=theme.font(11, "bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(2, 2))

        for cap in dev.get("capabilities", []):
            cap_row = ctk.CTkFrame(inner, fg_color="transparent")
            cap_row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                cap_row,
                text="•",
                font=theme.font(12),
                text_color=theme.TEXT_MUTED,
                width=14,
            ).pack(side="left")
            ctk.CTkLabel(
                cap_row,
                text=cap,
                font=theme.font(11),
                text_color=theme.TEXT_SECONDARY,
            ).pack(side="left")

        # Click card to open drawer
        card.bind("<Button-1>", lambda e, d=dev: store.open_drawer("device", d))
        inner.bind("<Button-1>", lambda e, d=dev: store.open_drawer("device", d))
