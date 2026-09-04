"""
Home screen.

Three things only: what you can ask, what is connected, and what VAVE is
doing right now. Navigation lives in the sidebar, so it is not repeated here.
"""
from __future__ import annotations

import os
import datetime
from PIL import Image
import customtkinter as ctk
from typing import Callable
from gui import theme
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
            font=theme.font(23, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(3, 0))

        # Right date, plain text rather than a badge
        date_str = datetime.datetime.now().strftime("%a, %-d %b %Y")
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

        mic_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "mic_hd.png")
        if os.path.exists(mic_icon_path):
            pil_img = Image.open(mic_icon_path)
            self.mic_ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(18, 18))
            mic_btn = ctk.CTkButton(
                row,
                text="",
                image=self.mic_ctk_image,
                width=32,
                height=32,
                corner_radius=16,
                fg_color="transparent",
                hover_color=theme.CARD_HOVER,
                command=self._toggle_voice,
            )
        else:
            mic_btn = ctk.CTkButton(
                row,
                text="Voice",
                font=theme.font(11),
                width=52,
                height=32,
                corner_radius=16,
                fg_color="transparent",
                hover_color=theme.CARD_HOVER,
                text_color=theme.TEXT_SECONDARY,
                command=self._toggle_voice,
            )
        mic_btn.pack(side="right", padx=(0, 6))

        send_btn = ctk.CTkButton(
            row,
            text="↑",
            font=theme.font(14, "bold"),
            width=32,
            height=32,
            corner_radius=16,
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
        chips_frame.pack(fill="x", padx=16, pady=(0, 18))

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
                height=28,
                command=lambda t=text: self.on_execute_command(t),
            )
            chip.pack(side="left", padx=(0, 8))

    def _build_environment_cards(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 18))
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="env")

        from assistant.api.server import get_local_server
        from gui import integrations

        # Each card says what is true right now. A card that always reads
        # "Connected" teaches the user to ignore all four.
        google = integrations.google_status()
        phone_paired = get_local_server().running

        cards_data = [
            ("My Computer", "Online", True, "devices"),
            ("My Phone", "Ready to pair" if phone_paired else "Not connected", phone_paired, "devices"),
            ("Google", google["label"], google["connected"], "google"),
            ("Internet", "Ready", True, "web"),
        ]

        for idx, (name, status, is_live, route) in enumerate(cards_data):
            card = ctk.CTkFrame(
                grid,
                fg_color=theme.CARD_BG,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=theme.RADIUS_CARD,
                height=68,
            )
            card.grid(row=0, column=idx, padx=(0 if idx == 0 else 8, 0), sticky="nsew")
            card.pack_propagate(False)

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=14, pady=12)

            ctk.CTkLabel(
                content,
                text=name,
                font=theme.font(12, "bold"),
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
            ).pack(anchor="w")

            status_row = ctk.CTkFrame(content, fg_color="transparent")
            status_row.pack(anchor="w", pady=(3, 0))

            ctk.CTkLabel(
                status_row,
                text="●",
                font=theme.font(9, "bold"),
                text_color=theme.SUCCESS if is_live else theme.TEXT_MUTED,
            ).pack(side="left", padx=(0, 5))

            ctk.CTkLabel(
                status_row,
                text=status,
                font=theme.font(11),
                text_color=theme.TEXT_SECONDARY,
            ).pack(side="left")

            card.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))
            for child in [content, status_row]:
                child.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))

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

        ctk.CTkLabel(
            title_col,
            text="CURRENT TASK",
            font=theme.font(10, "bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        self.task_title_lbl = ctk.CTkLabel(
            title_col,
            text=store.current_task.get("title", "Preparing your project"),
            font=theme.font(16, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.task_title_lbl.pack(anchor="w", pady=(4, 0))

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

        self.steps_row = ctk.CTkFrame(self.task_card, fg_color="transparent")
        self.steps_row.pack(fill="x", padx=18, pady=(14, 16))
        self._render_task_steps()

    def _render_task_steps(self):
        for child in self.steps_row.winfo_children():
            child.destroy()

        steps = store.current_task.get("steps", [])
        for idx, step in enumerate(steps):
            col = ctk.CTkFrame(self.steps_row, fg_color="transparent")
            col.pack(side="left", padx=(0, 18))

            st = step.get("status")
            if st == "done":
                icon, color = "✓", theme.SUCCESS
            elif st == "active":
                icon, color = "●", theme.ACCENT
            else:
                icon, color = "○", theme.TEXT_MUTED

            ctk.CTkLabel(
                col,
                text=icon,
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
