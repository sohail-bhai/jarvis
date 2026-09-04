"""
Home screen.

Three things only: what you can ask, what is connected, and what VAVE is
doing right now. Navigation lives in the sidebar, so it is not repeated here.
"""
from __future__ import annotations

import datetime
import customtkinter as ctk
from typing import Callable
from gui import icons, theme
from gui.store import store


class HomePage(ctk.CTkScrollableFrame):
    def __init__(self, parent, on_navigate: Callable[[str], None], on_execute_command: Callable[[str], None], on_voice_toggle: Callable[[], None] | None = None):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
            scrollbar_button_hover_color=theme.TEXT_MUTED,
        )
        self.on_navigate = on_navigate
        self.on_execute_command = on_execute_command
        self.on_voice_toggle = on_voice_toggle

        self._build_header()
        self._build_command_input()
        self._build_suggestion_chips()
        self._build_environment_cards()
        self._build_current_task()

        # Listen for task updates
        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        if event == "task_updated":
            self._update_task_ui()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(18, 14))

        left = ctk.CTkFrame(header_frame, fg_color="transparent")
        left.pack(side="left")

        # Dynamic greeting based on current time
        hour = datetime.datetime.now().hour
        greeting_text = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        ctk.CTkLabel(
            left,
            text=greeting_text,
            font=theme.font(12),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="How can I help you today?",
            font=theme.font(theme.SIZE_DISPLAY, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(3, 0))

        now = datetime.datetime.now()
        date_str = now.strftime(f"%a, {now.day} %b %Y")
        ctk.CTkLabel(
            header_frame,
            text=date_str,
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
        ).pack(side="right", pady=6)

    def _build_command_input(self):
        cmd_card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        cmd_card.pack(fill="x", padx=16, pady=(2, 10))

        row = ctk.CTkFrame(cmd_card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)

        self.cmd_entry = ctk.CTkEntry(
            row,
            placeholder_text="Tell me what you want to do...",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(13),
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT_PRIMARY,
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.cmd_entry.bind("<Return>", lambda e: self._submit_input())

        self.mic_icon = icons.image("mic", theme.ICON_CARD, theme.TEXT_SECONDARY)
        mic_btn = ctk.CTkButton(
            row,
            text="" if self.mic_icon else "Voice",
            image=self.mic_icon,
            font=theme.font(11),
            width=34 if self.mic_icon else 54,
            height=34,
            corner_radius=17,
            fg_color="transparent",
            hover_color=theme.SURFACE_SUBTLE,
            text_color=theme.TEXT_SECONDARY,
            command=self._toggle_voice,
        )
        mic_btn.pack(side="right", padx=(0, 6))

        self.send_icon = icons.image("send", theme.ICON_CARD, theme.TEXT_LIGHT, 2.0)
        send_btn = ctk.CTkButton(
            row,
            text="" if self.send_icon else "Send",
            image=self.send_icon,
            font=theme.font(12, "bold"),
            width=34 if self.send_icon else 54,
            height=34,
            corner_radius=17,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_LIGHT,
            command=self._submit_input,
        )
        send_btn.pack(side="right")

    def _submit_input(self):
        text = self.cmd_entry.get().strip()
        if text:
            self.cmd_entry.delete(0, "end")
            self.on_execute_command(text)

    def _toggle_voice(self):
        if self.on_voice_toggle:
            self.on_voice_toggle()

    def _build_suggestion_chips(self):
        chips_frame = ctk.CTkFrame(self, fg_color="transparent")
        chips_frame.pack(fill="x", padx=18, pady=(2, 22))

        ctk.CTkLabel(
            chips_frame,
            text="TRY",
            font=theme.label_font(),
            text_color=theme.TEXT_MUTED,
        ).pack(side="left", padx=(0, 12))

        chips = [
            "Find my presentation",
            "Continue my project",
            "Research something",
            "Summarize my emails",
        ]

        for text in chips:
            chip = ctk.CTkButton(
                chips_frame,
                text=text,
                font=theme.font(11),
                fg_color="transparent",
                hover_color=theme.CARD_HOVER,
                text_color=theme.TEXT_SECONDARY,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=theme.RADIUS_CONTROL,
                height=30,
                command=lambda t=text: self.on_execute_command(t),
            )
            chip.pack(side="left", padx=(0, 8))

    def _build_environment_cards(self):
        from assistant.api.server import get_local_server
        from gui import integrations

        # Each column says what is true right now. A card that always reads
        # "Connected" teaches the user to ignore all four.
        google = integrations.google_status()
        phone_paired = get_local_server().running

        entries = [
            ("My Computer", "Online", True, "devices", "monitor"),
            ("My Phone", "Ready to pair" if phone_paired else "Not connected",
             phone_paired, "devices", "phone"),
            ("Google", google["label"], google["connected"], "google", "google"),
            ("Internet", "Ready", True, "web", "globe"),
        ]

        ctk.CTkLabel(
            self,
            text="CONNECTED",
            font=theme.label_font(),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(4, 7))

        strip = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_CARD,
        )
        strip.pack(fill="x", padx=16, pady=(0, 20))
        strip.grid_columnconfigure((0, 2, 4, 6), weight=1, uniform="env")
        strip.grid_columnconfigure((1, 3, 5), weight=0)

        # Held on the page: Tk drops an image as soon as the last Python
        # reference to it goes away, and these are built in a loop.
        self.env_icons = []

        for idx, (name, status, is_live, route, glyph) in enumerate(entries):
            column = idx * 2

            if idx:
                # A hairline between columns, not a gap between cards.
                rule = ctk.CTkFrame(strip, fg_color=theme.DIVIDER, width=1, height=42)
                rule.grid(row=0, column=column - 1, sticky="ns", pady=14)

            cell = ctk.CTkFrame(strip, fg_color="transparent")
            cell.grid(row=0, column=column, sticky="nsew", padx=13, pady=14)

            icon_color = theme.TEXT_PRIMARY if is_live else theme.TEXT_MUTED
            icon = icons.image(glyph, theme.ICON_CARD, icon_color)
            self.env_icons.append(icon)

            top = ctk.CTkFrame(cell, fg_color="transparent")
            top.pack(fill="x")

            if icon is not None:
                ctk.CTkLabel(top, text="", image=icon, width=20).pack(side="left", padx=(0, 9))

            ctk.CTkLabel(
                top,
                text=name,
                font=theme.font(theme.SIZE_BODY, "bold"),
                text_color=theme.TEXT_PRIMARY if is_live else theme.TEXT_SECONDARY,
            ).pack(side="left")

            status_row = ctk.CTkFrame(cell, fg_color="transparent")
            status_row.pack(fill="x", pady=(6, 0))

            ctk.CTkLabel(
                status_row,
                text="\u25cf",
                font=theme.font(8, "bold"),
                text_color=theme.SUCCESS if is_live else theme.TEXT_MUTED,
            ).pack(side="left", padx=(1, 6))

            ctk.CTkLabel(
                status_row,
                text=status,
                font=theme.font(theme.SIZE_SMALL),
                text_color=theme.TEXT_SECONDARY if is_live else theme.TEXT_MUTED,
            ).pack(side="left")

            for widget in (cell, top, status_row):
                widget.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))

    def _build_current_task(self):
        self.task_card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        self.task_card.pack(fill="x", padx=16, pady=(0, 20))

        top_row = ctk.CTkFrame(self.task_card, fg_color="transparent")
        top_row.pack(fill="x", padx=18, pady=(16, 4))

        title_col = ctk.CTkFrame(top_row, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        label_row = ctk.CTkFrame(title_col, fg_color="transparent")
        label_row.pack(anchor="w")

        ctk.CTkLabel(
            label_row,
            text="CURRENT TASK",
            font=theme.label_font(),
            text_color=theme.TEXT_MUTED,
        ).pack(side="left")

        ctk.CTkLabel(
            label_row,
            text="  Working",
            font=theme.font(theme.SIZE_LABEL, "bold"),
            text_color=theme.ACCENT,
        ).pack(side="left", padx=(8, 0))

        self.task_title_lbl = ctk.CTkLabel(
            title_col,
            text=store.current_task.get("title", "Preparing your project"),
            font=theme.font(theme.SIZE_TITLE, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.task_title_lbl.pack(anchor="w", pady=(5, 0))

        self.task_sub_lbl = ctk.CTkLabel(
            title_col,
            text=store.current_task.get("subtitle", "VAVE is researching, organizing files and writing a draft for you."),
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.task_sub_lbl.pack(anchor="w", pady=(2, 0))

        details_btn = ctk.CTkButton(
            top_row,
            text="View details",
            font=theme.font(11),
            fg_color="transparent",
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_CONTROL,
            width=92,
            height=28,
            command=lambda: store.open_drawer("task", store.current_task),
        )
        details_btn.pack(side="right", anchor="n")

        rule = ctk.CTkFrame(self.task_card, fg_color=theme.DIVIDER, height=1)
        rule.pack(fill="x", padx=18, pady=(16, 0))

        # The steps sit in their own band so the card has a head and a foot
        # instead of one undifferentiated block of text.
        band = ctk.CTkFrame(self.task_card, fg_color="transparent")
        band.pack(fill="x")

        self.steps_row = ctk.CTkFrame(band, fg_color="transparent")
        self.steps_row.pack(fill="x", padx=18, pady=(13, 16))
        self._render_task_steps()

    def _render_task_steps(self):
        for child in self.steps_row.winfo_children():
            child.destroy()

        # Rebuilt on every task update, so the images are re-held each time.
        self.step_icons = []

        steps = store.current_task.get("steps", [])
        for idx, step in enumerate(steps):
            col = ctk.CTkFrame(self.steps_row, fg_color="transparent")
            col.pack(side="left", padx=(0, 18))

            st = step.get("status")
            if st == "done":
                glyph, color = "✓", theme.SUCCESS
            elif st == "active":
                glyph, color = "●", theme.ACCENT
            else:
                glyph, color = "○", theme.TEXT_MUTED

            if st == "done":
                tick = icons.image("check", 13, theme.SUCCESS, 2.4)
                self.step_icons.append(tick)
            else:
                tick = None

            ctk.CTkLabel(
                col,
                text="" if tick else glyph,
                image=tick,
                font=theme.font(11, "bold"),
                text_color=color,
            ).pack(side="left", padx=(0, 5))

            ctk.CTkLabel(
                col,
                text=step.get("text", ""),
                font=theme.font(11, "bold" if st == "active" else "normal"),
                text_color=theme.TEXT_PRIMARY if st != "pending" else theme.TEXT_MUTED,
            ).pack(side="left")

    def _update_task_ui(self):
        self.task_title_lbl.configure(text=store.current_task.get("title", ""))
        self.task_sub_lbl.configure(text=store.current_task.get("subtitle", ""))
        self._render_task_steps()
