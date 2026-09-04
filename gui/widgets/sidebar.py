"""
Sidebar component for the JARVIS desktop interface.
Clean, dark slate aesthetic matching the reference design.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import theme
from gui.store import store


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate, on_voice_toggle):
        super().__init__(
            parent,
            width=230,
            fg_color=theme.SIDEBAR_BG,
            corner_radius=0,
        )
        self.grid_propagate(False)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.on_voice_toggle = on_voice_toggle
        self.nav_buttons = {}

        # 1. Brand Section
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(6, 24))

        title_lbl = ctk.CTkLabel(
            brand_frame,
            text="JARVIS",
            font=theme.font(18, "bold"),
            text_color=theme.SIDEBAR_TEXT,
            anchor="w",
        )
        title_lbl.pack(anchor="w")

        tagline_lbl = ctk.CTkLabel(
            brand_frame,
            text="Your AI, Everywhere",
            font=theme.font(11),
            text_color=theme.SIDEBAR_TEXT_MUTED,
            anchor="w",
        )
        tagline_lbl.pack(anchor="w", pady=(2, 0))

        # 3. Navigation Items
        self.nav_items = [
            ("home", "Home", "⌂"),
            ("devices", "My Devices", "💻"),
            ("files", "My Files", "📁"),
            ("google", "Google", "G"),
            ("web", "Web", "🌐"),
            ("activity", "Activity", "⏱"),
            ("settings", "Settings", "⚙"),
        ]

        self.nav_container = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_container.pack(fill="x", padx=12, expand=True, anchor="n")

        for page_id, label, icon in self.nav_items:
            btn = ctk.CTkButton(
                self.nav_container,
                text=f"  {icon}   {label}",
                font=theme.font(13, "bold" if page_id == "home" else "normal"),
                fg_color=theme.SIDEBAR_ACTIVE if page_id == "home" else "transparent",
                text_color=theme.SIDEBAR_TEXT,
                hover_color=theme.SIDEBAR_HOVER,
                corner_radius=10,
                height=38,
                anchor="w",
                command=lambda pid=page_id: self._select_page(pid),
            )
            btn.pack(fill="x", pady=3)
            self.nav_buttons[page_id] = btn

        # 4. Bottom Status Pill (JARVIS Online & Voice Control)
        bottom_frame = ctk.CTkFrame(
            self,
            fg_color="#1F2432",
            corner_radius=12,
            border_width=1,
            border_color="#2B3245",
        )
        bottom_frame.pack(side="bottom", fill="x", padx=14, pady=16)

        status_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=12, pady=(12, 4))

        self.dot_label = ctk.CTkLabel(
            status_row,
            text="●",
            font=theme.font(14, "bold"),
            text_color=theme.SUCCESS,
        )
        self.dot_label.pack(side="left")

        self.status_title = ctk.CTkLabel(
            status_row,
            text=" JARVIS Online",
            font=theme.font(12, "bold"),
            text_color=theme.SIDEBAR_TEXT,
        )
        self.status_title.pack(side="left")

        self.status_sub = ctk.CTkLabel(
            bottom_frame,
            text="All systems running",
            font=theme.font(10),
            text_color=theme.SIDEBAR_TEXT_MUTED,
            anchor="w",
        )
        self.status_sub.pack(fill="x", padx=16, pady=(0, 12))

    def _select_page(self, page_id: str):
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    fg_color=theme.SIDEBAR_ACTIVE,
                    font=theme.font(13, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    font=theme.font(13, "normal"),
                )
        self.on_navigate(page_id)

    def _toggle_voice(self):
        self.on_voice_toggle()

    def update_voice_state(self, is_listening: bool):
        if is_listening:
            self.status_sub.configure(text="Listening for voice...")
        else:
            self.status_sub.configure(text="All systems running")
