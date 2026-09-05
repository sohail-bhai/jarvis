"""
Reusable Right-Side Detail Drawer component.
Displays unified details for Devices, Files, Tasks, Activities, and Approvals.
"""
from __future__ import annotations

import customtkinter as ctk
from typing import Dict, Any, Callable
from gui import icons, theme
from gui.store import store


class DetailDrawer(ctk.CTkFrame):
    def __init__(self, parent, on_close: Callable[[], None]):
        super().__init__(
            parent,
            width=300,
            fg_color=theme.CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.on_close = on_close

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=44)
        self.header.pack(fill="x", padx=16, pady=(14, 8))

        self.title_lbl = ctk.CTkLabel(
            self.header,
            text="Details",
            font=theme.font(15, "bold"),
            text_color=theme.TEXT_PRIMARY,
        )
        self.title_lbl.pack(side="left")

        self._glyphs = []
        close_glyph = icons.image("x", theme.ICON_SM, theme.TEXT_SECONDARY)
        self._glyphs.append(close_glyph)
        close_btn = ctk.CTkButton(
            self.header,
            image=close_glyph,
            text="" if close_glyph else "X",
            font=theme.font(12),
            width=28,
            height=28,
            fg_color=theme.MAIN_BG,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT_SECONDARY,
            corner_radius=14,
            command=self.on_close,
        )
        close_btn.pack(side="right")

        # Scrollable content area
        self.content_area = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )
        self.content_area.pack(fill="both", expand=True, padx=14, pady=4)

    def set_content(self, drawer_type: str, data: Dict[str, Any]):
        # Clear existing content
        for child in self.content_area.winfo_children():
            child.destroy()

        if drawer_type == "device":
            self._render_device(data)
        elif drawer_type == "file":
            self._render_file(data)
        elif drawer_type == "task":
            self._render_task(data)
        elif drawer_type == "activity":
            self._render_activity(data)
        elif drawer_type == "approval":
            self._render_approval(data)
        else:
            self._render_generic(data)

    def _render_device(self, data: Dict[str, Any]):
        self.title_lbl.configure(text=data.get("name", "Device Details"))

        # Status badge
        status_box = ctk.CTkFrame(self.content_area, fg_color=theme.SUCCESS_LIGHT, corner_radius=8)
        status_box.pack(fill="x", pady=(4, 14), padx=2)
        ctk.CTkLabel(
            status_box,
            text=f"● {data.get('status', 'Online')} · {data.get('type', 'Connected Device')}",
            font=theme.font(11, "bold"),
            text_color=theme.SUCCESS,
            padx=10,
            pady=6,
        ).pack(anchor="w")

        # Capabilities section
        ctk.CTkLabel(
            self.content_area,
            text="VAVE can use this device to:",
            font=theme.font(12, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(4, 6))

        for cap in data.get("capabilities", []):
            row = ctk.CTkFrame(self.content_area, fg_color="transparent")
            row.pack(fill="x", pady=2)
            tick = icons.image("check", 13, theme.SUCCESS, stroke_width=2.4)
            self._glyphs.append(tick)
            ctk.CTkLabel(row, image=tick, text="" if tick else "+",
                         font=theme.font(12, "bold"), text_color=theme.SUCCESS,
                         width=18).pack(side="left")
            ctk.CTkLabel(row, text=cap, font=theme.font(12), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=4)

        # Connected AI Helpers
        ctk.CTkLabel(
            self.content_area,
            text="\nConnected AI helpers:",
            font=theme.font(12, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(4, 4))

        for helper in data.get("connected_helpers", []):
            ctk.CTkLabel(
                self.content_area,
                text=f"• {helper}",
                font=theme.font(12),
                text_color=theme.TEXT_SECONDARY,
                anchor="w",
            ).pack(fill="x", padx=6, pady=1)

        # Recent Activity
        ctk.CTkLabel(
            self.content_area,
            text="\nRecent activity:",
            font=theme.font(12, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(4, 2))

        ctk.CTkLabel(
            self.content_area,
            text=data.get("recent_activity", "No recent activity"),
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
            wraplength=250,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=2)

        # Disconnect button
        ctk.CTkButton(
            self.content_area,
            text="Disconnect Device",
            font=theme.font(11),
            fg_color=theme.MAIN_BG,
            hover_color=theme.DANGER_LIGHT,
            text_color=theme.DANGER,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=8,
            command=self.on_close,
        ).pack(fill="x", pady=(24, 10))

    def _render_file(self, data: Dict[str, Any]):
        self.title_lbl.configure(text=data.get("name", "File Details"))

        # Details card
        info_card = ctk.CTkFrame(self.content_area, fg_color=theme.MAIN_BG, corner_radius=10)
        info_card.pack(fill="x", pady=(4, 16), padx=2)

        fields = [
            ("Located on:", data.get("source", "My Computer")),
            ("Folder:", data.get("folder", "Projects")),
            ("Modified:", data.get("modified", "Recently")),
            ("Size:", data.get("size", "Unknown")),
        ]
        for label, val in fields:
            row = ctk.CTkFrame(info_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=label, font=theme.font(11), text_color=theme.TEXT_MUTED, width=70, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=theme.font(11, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left")

        # Action Buttons
        ctk.CTkLabel(
            self.content_area,
            text="Actions:",
            font=theme.font(12, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(4, 8))

        actions = [
            ("Open File", theme.ACCENT, theme.ON_ACCENT),
            ("Send to Phone", theme.CARD_BG, theme.TEXT_PRIMARY),
            ("Give to VAVE to analyze", theme.CARD_BG, theme.TEXT_PRIMARY),
            ("Share File", theme.CARD_BG, theme.TEXT_PRIMARY),
        ]
        for act_text, bg, fg in actions:
            ctk.CTkButton(
                self.content_area,
                text=act_text,
                font=theme.font(12, "bold" if bg == theme.ACCENT else "normal"),
                fg_color=bg,
                text_color=fg,
                hover_color=theme.ACCENT_HOVER if bg == theme.ACCENT else theme.CARD_HOVER,
                border_width=0 if bg == theme.ACCENT else 1,
                border_color=theme.CARD_BORDER,
                corner_radius=8,
                height=32,
                command=lambda t=act_text: store.add_system_log(f"Action '{t}' triggered for {data.get('name')}", "working"),
            ).pack(fill="x", pady=3)

    def _render_task(self, data: Dict[str, Any]):
        self.title_lbl.configure(text="Task Progress")

        ctk.CTkLabel(
            self.content_area,
            text=data.get("title", "Current Task"),
            font=theme.font(15, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(4, 2))

        ctk.CTkLabel(
            self.content_area,
            text=data.get("subtitle", ""),
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            wraplength=250,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 14))

        # Steps
        steps_frame = ctk.CTkFrame(self.content_area, fg_color=theme.MAIN_BG, corner_radius=10)
        steps_frame.pack(fill="x", pady=4, padx=2)

        for step in data.get("steps", []):
            row = ctk.CTkFrame(steps_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)

            st = step.get("status")
            if st == "done":
                mark, color = "check", theme.SUCCESS
            elif st == "active":
                mark, color = None, theme.ACCENT_DEEP
            else:
                mark, color = None, theme.TEXT_MUTED

            glyph = icons.image(mark, 13, color, stroke_width=2.4) if mark else None
            self._glyphs.append(glyph)
            ctk.CTkLabel(row, image=glyph,
                         text="" if glyph else ("\u25cf" if st == "active" else "\u25cb"),
                         font=theme.font(11, "bold"), text_color=color,
                         width=18).pack(side="left")
            ctk.CTkLabel(row, text=step.get("text", ""), font=theme.font(12), text_color=theme.TEXT_PRIMARY).pack(side="left", padx=4)

        # Helper attribution
        ctk.CTkLabel(
            self.content_area,
            text=f"\n{data.get('helper', 'Handled by VAVE')}",
            font=theme.font(11, "bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=4)

        ctk.CTkLabel(
            self.content_area,
            text=data.get("details", ""),
            font=theme.font(11),
            text_color=theme.TEXT_SECONDARY,
            wraplength=250,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=2)

    def _render_activity(self, data: Dict[str, Any]):
        self.title_lbl.configure(text="What happened?")

        desc = ctk.CTkLabel(
            self.content_area,
            text=data.get("detail", ""),
            font=theme.font(13),
            text_color=theme.TEXT_PRIMARY,
            wraplength=250,
            justify="left",
            anchor="w",
        )
        desc.pack(fill="x", pady=(4, 16))

        info_card = ctk.CTkFrame(self.content_area, fg_color=theme.MAIN_BG, corner_radius=10)
        info_card.pack(fill="x", pady=4, padx=2)

        items = [
            ("Used:", data.get("used", "Computer")),
            ("Found:", data.get("found", "-")),
            ("Reason:", data.get("reason", "-")),
            ("Time:", data.get("time", "-")),
        ]
        for lbl, val in items:
            row = ctk.CTkFrame(info_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(row, text=lbl, font=theme.font(11), text_color=theme.TEXT_MUTED, width=60, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=theme.font(11, "bold"), text_color=theme.TEXT_PRIMARY, wraplength=170, justify="left", anchor="w").pack(side="left")

    def _render_approval(self, data: Dict[str, Any]):
        self.title_lbl.configure(text="Approval Required")

        card = ctk.CTkFrame(
            self.content_area,
            fg_color=theme.WARNING_LIGHT,
            border_width=1,
            border_color=theme.WARNING_BORDER,
            corner_radius=12,
        )
        card.pack(fill="x", pady=8, padx=2)

        ctk.CTkLabel(
            card,
            text=data.get("title", "VAVE needs your approval"),
            font=theme.font(14, "bold"),
            text_color=theme.TEXT_PRIMARY,
            wraplength=240,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 6))

        ctk.CTkLabel(
            card,
            text=data.get("description", ""),
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            wraplength=240,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 14))

        # Actions
        btn_row = ctk.CTkFrame(self.content_area, fg_color="transparent")
        btn_row.pack(fill="x", pady=12)

        ctk.CTkButton(
            btn_row,
            text="Not Now",
            font=theme.font(12),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=8,
            height=34,
            command=lambda: store.resolve_approval(False),
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="Approve",
            font=theme.font(12, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.ON_ACCENT,
            corner_radius=8,
            height=34,
            command=lambda: store.resolve_approval(True),
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _render_generic(self, data: Dict[str, Any]):
        self.title_lbl.configure(text="Details")
        ctk.CTkLabel(
            self.content_area,
            text=str(data),
            font=theme.font(11),
            text_color=theme.TEXT_SECONDARY,
            wraplength=250,
        ).pack(fill="x", pady=10)
