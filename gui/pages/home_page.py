"""
Home Screen component.
Faithful reproduction of the calm, minimal reference interface.
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

        # 1. Header with greeting and date badge
        self._build_header()

        # 2. Main Command Input Box
        self._build_command_input()

        # 3. Suggestion Chips
        self._build_suggestion_chips()

        # 4. Connected Environment (4 cards)
        self._build_environment_cards()

        # 5. Current Task Card
        self._build_current_task()

        # 6. Quick Access Cards (3 cards)
        self._build_quick_access()

        # 7. Bottom Simple Explanation
        self._build_bottom_explanation()

        # Listen for task updates
        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        if event == "task_updated":
            self._update_task_ui()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(16, 12))

        left = ctk.CTkFrame(header_frame, fg_color="transparent")
        left.pack(side="left")

        # Greeting with sun icon
        greet_row = ctk.CTkFrame(left, fg_color="transparent")
        greet_row.pack(anchor="w")

        ctk.CTkLabel(
            greet_row,
            text="☀️",
            font=theme.font(13),
        ).pack(side="left", padx=(0, 6))

        # Dynamic greeting based on current time
        hour = datetime.datetime.now().hour
        greeting_text = "Good morning," if hour < 12 else ("Good afternoon," if hour < 17 else "Good evening,")
        ctk.CTkLabel(
            greet_row,
            text=greeting_text,
            font=theme.font(13),
            text_color=theme.TEXT_SECONDARY,
        ).pack(side="left")

        # Big bold question
        ctk.CTkLabel(
            left,
            text="How can I help you today?",
            font=theme.font(22, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(2, 0))

        # Right date badge
        now = datetime.datetime.now()
        date_str = f"{now.strftime('%a')}, {now.day} {now.strftime('%b %Y')}" if hasattr(now, "strftime") else "Thu, 4 Sep 2025"
        date_badge = ctk.CTkLabel(
            header_frame,
            text=date_str,
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
            fg_color=theme.CARD_BG,
            corner_radius=12,
            padx=12,
            pady=6,
        )
        date_badge.pack(side="right", pady=6)

    def _build_command_input(self):
        cmd_card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        cmd_card.pack(fill="x", padx=16, pady=(4, 10))

        row = ctk.CTkFrame(cmd_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            row,
            text="✦",
            font=theme.font(15, "bold"),
            text_color=theme.ACCENT,
        ).pack(side="left", padx=(0, 10))

        self.cmd_entry = ctk.CTkEntry(
            row,
            placeholder_text="Tell me what you want to do...",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(13),
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT_PRIMARY,
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self._submit_input())

        # Aesthetic mic icon like modern AI assistants (ChatGPT / Claude / Gemini)
        mic_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "mic_hd.png")
        if os.path.exists(mic_icon_path):
            pil_img = Image.open(mic_icon_path)
            self.mic_ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(20, 20))
            mic_btn = ctk.CTkButton(
                row,
                text="",
                image=self.mic_ctk_image,
                width=34,
                height=34,
                corner_radius=17,
                fg_color="transparent",
                hover_color=theme.CARD_BORDER,
                command=self._toggle_voice,
            )
        else:
            mic_btn = ctk.CTkButton(
                row,
                text="🎙",
                font=theme.font(14),
                width=34,
                height=34,
                corner_radius=17,
                fg_color="transparent",
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_SECONDARY,
                command=self._toggle_voice,
            )
        mic_btn.pack(side="right", padx=(0, 6))

        arrow_btn = ctk.CTkButton(
            row,
            text="↑",
            font=theme.font(14, "bold"),
            width=34,
            height=34,
            corner_radius=17,
            fg_color=theme.TEXT_PRIMARY,
            hover_color=theme.SIDEBAR_BG,
            text_color="#FFFFFF",
            command=self._submit_input,
        )
        arrow_btn.pack(side="right")

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
        chips_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(
            chips_frame,
            text="Try something like:",
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
        ).pack(side="left", padx=(0, 10))

        chips = [
            ("Find my presentation", "📄"),
            ("Continue my project", "▷"),
            ("Research something", "🔍"),
            ("Summarize my emails", "✉"),
        ]

        for text, icon in chips:
            chip = ctk.CTkButton(
                chips_frame,
                text=f"{icon}  {text}",
                font=theme.font(11),
                fg_color=theme.CARD_BG,
                hover_color=theme.CARD_HOVER,
                text_color=theme.TEXT_SECONDARY,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=12,
                height=28,
                command=lambda t=text: self.on_execute_command(t),
            )
            chip.pack(side="left", padx=4)

    def _build_environment_cards(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 16))
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="env")

        cards_data = [
            ("My Computer", "Online", "💻", theme.INFO_LIGHT, theme.INFO_BORDER, theme.INFO, "devices"),
            ("My Phone", "Connected", "📱", theme.SUCCESS_LIGHT, theme.SUCCESS_BORDER, theme.SUCCESS, "devices"),
            ("Google Drive", "Connected", "📁", theme.WARNING_LIGHT, theme.WARNING_BORDER, theme.WARNING, "google"),
            ("Internet", "Ready", "🌐", theme.PURPLE_LIGHT, theme.PURPLE_BORDER, theme.PURPLE, "web"),
        ]

        for idx, (name, status, icon, bg, border, dot_col, route) in enumerate(cards_data):
            card = ctk.CTkFrame(
                grid,
                fg_color=bg,
                border_width=1,
                border_color=border,
                corner_radius=14,
                height=76,
            )
            card.grid(row=0, column=idx, padx=4, sticky="nsew")
            card.pack_propagate(False)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(14, 2))

            ctk.CTkLabel(
                row,
                text=icon,
                font=theme.font(18),
            ).pack(side="left", padx=(0, 8))

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(
                text_col,
                text=name,
                font=theme.font(12, "bold"),
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
            ).pack(anchor="w")

            status_row = ctk.CTkFrame(text_col, fg_color="transparent")
            status_row.pack(anchor="w")

            ctk.CTkLabel(
                status_row,
                text="●",
                font=theme.font(9, "bold"),
                text_color=dot_col,
            ).pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                status_row,
                text=status,
                font=theme.font(11),
                text_color=theme.TEXT_SECONDARY,
            ).pack(side="left")

            # Clickable overlay to navigate
            card.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))
            for child in [row, text_col, status_row]:
                child.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))

    def _build_current_task(self):
        self.task_card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        self.task_card.pack(fill="x", padx=16, pady=(0, 16))

        # Top row: title & details button
        top_row = ctk.CTkFrame(self.task_card, fg_color="transparent")
        top_row.pack(fill="x", padx=18, pady=(16, 4))

        title_col = ctk.CTkFrame(top_row, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        badge_row = ctk.CTkFrame(title_col, fg_color="transparent")
        badge_row.pack(anchor="w")

        ctk.CTkLabel(
            badge_row,
            text="↻",
            font=theme.font(12, "bold"),
            text_color=theme.INFO,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            badge_row,
            text="Current Task",
            font=theme.font(11, "bold"),
            text_color=theme.TEXT_MUTED,
        ).pack(side="left")

        self.task_title_lbl = ctk.CTkLabel(
            title_col,
            text=store.current_task.get("title", "Preparing your project"),
            font=theme.font(16, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.task_title_lbl.pack(anchor="w", pady=(2, 0))

        self.task_sub_lbl = ctk.CTkLabel(
            title_col,
            text=store.current_task.get("subtitle", "JARVIS is researching, organizing files and writing a draft for you."),
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.task_sub_lbl.pack(anchor="w", pady=(2, 0))

        # View Details button
        details_btn = ctk.CTkButton(
            top_row,
            text="View Details",
            font=theme.font(11),
            fg_color=theme.MAIN_BG,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT_PRIMARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=10,
            width=90,
            height=28,
            command=lambda: store.open_drawer("task", store.current_task),
        )
        details_btn.pack(side="right", anchor="n")

        # Step indicators container
        self.steps_row = ctk.CTkFrame(self.task_card, fg_color="transparent")
        self.steps_row.pack(fill="x", padx=18, pady=(12, 16))
        self._render_task_steps()

    def _render_task_steps(self):
        for child in self.steps_row.winfo_children():
            child.destroy()

        steps = store.current_task.get("steps", [])
        for idx, step in enumerate(steps):
            col = ctk.CTkFrame(self.steps_row, fg_color="transparent")
            col.pack(side="left", padx=(0, 16))

            st = step.get("status")
            if st == "done":
                icon, color = "✓", theme.SUCCESS
            elif st == "active":
                icon, color = "●", theme.INFO
            else:
                icon, color = "○", theme.TEXT_MUTED

            ctk.CTkLabel(
                col,
                text=icon,
                font=theme.font(12, "bold"),
                text_color=color,
            ).pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                col,
                text=f"{idx+1}. {step.get('text', '')}",
                font=theme.font(11, "bold" if st == "active" else "normal"),
                text_color=theme.TEXT_PRIMARY if st != "pending" else theme.TEXT_MUTED,
            ).pack(side="left")

    def _update_task_ui(self):
        self.task_title_lbl.configure(text=store.current_task.get("title", ""))
        self.task_sub_lbl.configure(text=store.current_task.get("subtitle", ""))
        self._render_task_steps()

    def _build_quick_access(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 16))
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="quick")

        items = [
            ("My Files", "Find and access your files from any device", "📁", "files"),
            ("Google", "Search your Drive, Gmail, Calendar and more", "G", "google"),
            ("Web", "Ask JARVIS to search the internet or do online tasks", "🌐", "web"),
        ]

        for idx, (title, desc, icon, route) in enumerate(items):
            card = ctk.CTkFrame(
                grid,
                fg_color=theme.CARD_BG,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=14,
                height=82,
            )
            card.grid(row=0, column=idx, padx=4, sticky="nsew")
            card.pack_propagate(False)

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=14, pady=12)

            left_icon = ctk.CTkLabel(
                content,
                text=icon,
                font=theme.font(18),
            )
            left_icon.pack(side="left", padx=(0, 10))

            text_col = ctk.CTkFrame(content, fg_color="transparent")
            text_col.pack(side="left", fill="both", expand=True)

            title_row = ctk.CTkFrame(text_col, fg_color="transparent")
            title_row.pack(fill="x", anchor="w")

            ctk.CTkLabel(
                title_row,
                text=title,
                font=theme.font(12, "bold"),
                text_color=theme.TEXT_PRIMARY,
            ).pack(side="left")

            ctk.CTkLabel(
                title_row,
                text=" ›",
                font=theme.font(12),
                text_color=theme.TEXT_MUTED,
            ).pack(side="left")

            ctk.CTkLabel(
                text_col,
                text=desc,
                font=theme.font(10),
                text_color=theme.TEXT_SECONDARY,
                wraplength=170,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

            card.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))
            for child in [content, left_icon, text_col, title_row]:
                child.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))

    def _build_bottom_explanation(self):
        bar = ctk.CTkFrame(
            self,
            fg_color="#EFF2F9",
            corner_radius=14,
        )
        bar.pack(fill="x", padx=16, pady=(0, 20))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        # Left: Sparkle + core idea
        left_col = ctk.CTkFrame(inner, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True)

        heading_row = ctk.CTkFrame(left_col, fg_color="transparent")
        heading_row.pack(anchor="w")

        ctk.CTkLabel(
            heading_row,
            text="✦",
            font=theme.font(12, "bold"),
            text_color=theme.ACCENT,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            heading_row,
            text="You can just ask in normal language.",
            font=theme.font(12, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        examples = ctk.CTkLabel(
            left_col,
            text='"Send this file to my phone"   "Find my last email from college"   "Open my project folder"',
            font=theme.font(11),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        )
        examples.pack(anchor="w", pady=(2, 0))

        # Right note
        right_lbl = ctk.CTkLabel(
            inner,
            text="JARVIS understands. No technical knowledge needed.",
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
        )
        right_lbl.pack(side="right")
