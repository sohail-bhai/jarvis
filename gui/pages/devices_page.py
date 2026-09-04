"""
My Devices screen.
Shows connected user hardware in human-friendly cards, and is where a phone
is connected to this computer.
"""
from __future__ import annotations

import customtkinter as ctk

from assistant.api.server import get_local_server
from gui import theme
from gui.store import store


class DevicesPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )

        self.server = get_local_server()

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

        self._build_phone_card()

        # Device Cards Grid (2 columns)
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 20))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="dev")

        for idx, dev in enumerate(store.devices):
            r = idx // 2
            c = idx % 2
            self._create_device_card(grid, dev, r, c)

    # -- connecting a phone -------------------------------------------------

    def _build_phone_card(self):
        """Start the local server, and show what to type on the phone.

        The phone talks to this app, not to a second copy of JARVIS: the server
        runs inside this process, so a task started on the phone appears here.
        """
        card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=14,
        )
        card.pack(fill="x", padx=16, pady=(0, 16))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text="Connect your phone",
            font=theme.font(14, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        self.server_badge = ctk.CTkLabel(
            title_row,
            text="● Off",
            font=theme.font(11, "bold"),
            text_color=theme.TEXT_MUTED,
            fg_color=theme.MAIN_BG,
            corner_radius=10,
            padx=10,
            pady=3,
        )
        self.server_badge.pack(side="right")

        self.server_detail = ctk.CTkLabel(
            inner,
            text="Turn this on to reach this computer's files and tasks from "
                 "your phone on the same Wi-Fi.",
            font=theme.font(11),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.server_detail.pack(fill="x", pady=(6, 10))

        buttons = ctk.CTkFrame(inner, fg_color="transparent")
        buttons.pack(fill="x")

        self.server_button = ctk.CTkButton(
            buttons,
            text="Turn on",
            font=theme.font(11, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_LIGHT,
            corner_radius=8,
            width=110,
            height=30,
            command=self._toggle_server,
        )
        self.server_button.pack(side="left", padx=(0, 8))

        self.pair_button = ctk.CTkButton(
            buttons,
            text="Show pairing code",
            font=theme.font(11, "bold"),
            fg_color=theme.MAIN_BG,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT_PRIMARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=8,
            width=150,
            height=30,
            command=self._show_pairing_code,
        )
        self.pair_button.pack(side="left")

        self.pair_label = ctk.CTkLabel(
            inner,
            text="",
            font=theme.font(12, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.pair_label.pack(fill="x", pady=(10, 0))

        self._refresh_server_card()

    def _refresh_server_card(self):
        running = self.server.running
        self.server_badge.configure(
            text="● On" if running else "● Off",
            text_color=theme.SUCCESS if running else theme.TEXT_MUTED,
            fg_color=theme.SUCCESS_LIGHT if running else theme.MAIN_BG,
        )
        self.server_button.configure(text="Turn off" if running else "Turn on")
        self.pair_button.configure(state="normal" if running else "disabled")

        if running:
            addresses = self.server.addresses()
            typed = addresses[0] if addresses else f"this computer:{self.server.port}"
            self.server_detail.configure(
                text=f"On your phone, enter  {typed}  then tap Connect. "
                     "Both devices must be on the same Wi-Fi.")
        elif self.server.error:
            self.server_detail.configure(text=self.server.error)
        else:
            self.server_detail.configure(
                text="Turn this on to reach this computer's files and tasks "
                     "from your phone on the same Wi-Fi.")

    def _toggle_server(self):
        if self.server.running:
            self.server.stop()
            self.pair_label.configure(text="")
            store.add_system_log("Phone connection turned off", "completed")
        elif self.server.start():
            addresses = self.server.addresses()
            store.add_system_log(
                f"Phone connection ready at {addresses[0]}" if addresses
                else "Phone connection ready", "completed")
        else:
            # Say why rather than leaving the button looking stuck.
            store.add_system_log(
                f"Could not start the phone connection. {self.server.error}", "failed")
        self._refresh_server_card()

    def _show_pairing_code(self):
        code, expires_in = self.server.pairing_code()
        if not code:
            self.pair_label.configure(
                text="Turn the phone connection on first.",
                text_color=theme.TEXT_SECONDARY)
            return

        minutes = max(1, expires_in // 60)
        self.pair_label.configure(
            text=f"Type this code on your phone:   {code}      "
                 f"(it stops working in {minutes} minutes)",
            text_color=theme.TEXT_PRIMARY)
        store.add_system_log("Showed a pairing code for a new phone", "completed")

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
