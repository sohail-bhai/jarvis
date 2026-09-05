"""
System Log component for the right panel.
Displays transparent, human-friendly timeline of what VAVE is doing behind the scenes.
"""
from __future__ import annotations

import customtkinter as ctk

from gui.redaction import redact
from gui import icons, scrolling, theme
from gui.store import store


class SystemLogPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            width=290,
            fg_color=theme.CARD_BG,
            corner_radius=theme.RADIUS,
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
            text="System Log",
            font=theme.font(15, "bold"),
            text_color=theme.TEXT_PRIMARY,
        )
        title.pack(side="left")

        live_badge = ctk.CTkLabel(
            header,
            text="● Live",
            font=theme.font(10, "bold"),
            text_color=theme.SUCCESS,
            fg_color=theme.SUCCESS_LIGHT,
            corner_radius=theme.RADIUS_SM,
            width=52,
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
        scrolling.tune(self.scroll_area)

        # 3. Bottom note card
        note_card = ctk.CTkFrame(
            self,
            fg_color=theme.MAIN_BG,
            corner_radius=theme.RADIUS_SM,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        note_card.pack(side="bottom", fill="x", padx=14, pady=14)

        note_header = ctk.CTkFrame(note_card, fg_color="transparent")
        note_header.pack(fill="x", padx=10, pady=(8, 2))

        self._note_glyph = icons.image("bulb", theme.ICON_SM, theme.TEXT_SECONDARY)
        bulb_lbl = ctk.CTkLabel(
            note_header,
            image=self._note_glyph,
            text="" if self._note_glyph else "i",
            text_color=theme.TEXT_SECONDARY,
            font=theme.font(12),
        )
        bulb_lbl.pack(side="left")

        note_title = ctk.CTkLabel(
            note_header,
            text=" VAVE is working in the background.",
            font=theme.font(10, "bold"),
            text_color=theme.TEXT_PRIMARY,
        )
        note_title.pack(side="left")

        note_sub = ctk.CTkLabel(
            note_card,
            text="You can continue using your computer.",
            font=theme.font(10),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        )
        note_sub.pack(fill="x", padx=12, pady=(0, 8))

        # Initial render of log entries
        self._render_logs()

        # Listen for store updates
        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        if event != "system_log_added":
            return

        # Rebuilding every row on each new line made the whole window stutter
        # while VAVE was working, which is exactly when it must stay smooth.
        # One new line adds one row; only a dropped line forces a rebuild.
        if isinstance(data, dict) and "entry" in data:
            if data.get("dropped"):
                self._render_logs()
            else:
                self._append_row(data["entry"])
                self._scroll_to_end()
        else:
            self._render_logs()

    def _render_logs(self):
        for child in self.scroll_area.winfo_children():
            child.destroy()
        for item in store.system_logs:
            self._append_row(item)
        self._scroll_to_end()

    def _scroll_to_end(self):
        """Keep the newest line in view without fighting a manual scroll."""
        try:
            self.scroll_area._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _append_row(self, item):
        row = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        row.pack(fill="x", pady=6)

        # Time column
        time_lbl = ctk.CTkLabel(
            row,
            text=item.get("time", ""),
            font=theme.font(10),
            text_color=theme.TEXT_MUTED,
            width=48,
            anchor="w",
        )
        time_lbl.pack(side="left", anchor="n", pady=2)

        # Dot indicator
        status = item.get("status", "working")
        if status == "completed":
            dot_color = theme.SUCCESS
        elif status == "waiting" or status == "approval":
            dot_color = theme.WARNING
        elif status == "info":
            dot_color = theme.TEXT_MUTED
        else:
            dot_color = theme.ACCENT_DEEP

        dot_lbl = ctk.CTkLabel(
            row,
            text="\u25cf",
            font=theme.font(10, "bold"),
            text_color=dot_color,
            width=16,
        )
        dot_lbl.pack(side="left", anchor="n", pady=1)

        # Description text
        desc_lbl = ctk.CTkLabel(
            row,
            text=item.get("text", ""),
            font=theme.font(11),
            text_color=theme.TEXT_PRIMARY,
            wraplength=170,
            justify="left",
            anchor="w",
        )
        desc_lbl.pack(side="left", fill="x", expand=True, padx=(4, 0))
