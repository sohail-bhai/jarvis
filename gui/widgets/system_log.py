"""
System Log component for the right panel.
Displays transparent, human-friendly timeline of what VAVE is doing behind the scenes.
"""
from __future__ import annotations

import customtkinter as ctk

from gui.redaction import redact
from gui import theme
from gui.store import store


class SystemLogPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            width=290,
            fg_color=theme.CARD_BG,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        # 1. Header with "Live" badge
        header = ctk.CTkFrame(self, fg_color="transparent", height=44)
        header.pack(fill="x", padx=16, pady=(14, 6))

        title = ctk.CTkLabel(
            header,
            text="SYSTEM LOG",
            font=theme.label_font(),
            text_color=theme.TEXT_MUTED,
        )
        title.pack(side="left")

        live_badge = ctk.CTkLabel(
            header,
            text="● Live",
            font=theme.font(10),
            text_color=theme.SUCCESS,
            fg_color="transparent",
            width=44,
            height=20,
        )
        live_badge.pack(side="right")

        # 2. Scrollable Timeline Container
        self.scroll_area = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
            scrollbar_button_hover_color=theme.TEXT_MUTED,
        )
        self.scroll_area.pack(fill="both", expand=True, padx=12, pady=4)

        # Initial render of log entries
        self._render_logs()

        # Listen for store updates
        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        if event == "system_log_added":
            self._render_logs()

    def _render_logs(self):
        # Clear existing items
        for child in self.scroll_area.winfo_children():
            child.destroy()

        logs = store.system_logs
        for item in logs:
            row = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
            row.pack(fill="x", pady=(0, 2))

            status = item.get("status", "working")
            if status == "completed":
                dot_color = theme.SUCCESS
            elif status in ("waiting", "approval"):
                dot_color = theme.WARNING
            elif status == "failed":
                dot_color = theme.DANGER
            elif status == "info":
                dot_color = theme.TEXT_MUTED
            else:
                dot_color = theme.ACCENT

            rail = ctk.CTkFrame(row, fg_color="transparent", width=18)
            rail.pack(side="left", fill="y")
            rail.pack_propagate(False)

            ctk.CTkLabel(
                rail,
                text="\u25cf",
                font=theme.font(9, "bold"),
                text_color=dot_color,
            ).pack(anchor="n", pady=(4, 0))

            body = ctk.CTkFrame(row, fg_color="transparent")
            body.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                body,
                text=item.get("time", ""),
                font=theme.font(9),
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                body,
                text=item.get("text", ""),
                font=theme.font(theme.SIZE_SMALL),
                text_color=theme.TEXT_PRIMARY,
                wraplength=200,
                justify="left",
                anchor="w",
            ).pack(fill="x", pady=(1, 8))
