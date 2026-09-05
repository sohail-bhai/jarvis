"""
Global Command Palette modal (Ctrl+K / ⌘K).
Allows natural language input and one-click execution of suggestions.
"""
from __future__ import annotations

import customtkinter as ctk
from typing import Callable
from gui import theme
from gui.store import store


class CommandPalette(ctk.CTkToplevel):
    def __init__(self, parent, on_execute: Callable[[str], None]):
        super().__init__(parent)
        self.on_execute = on_execute

        self.title("Ask VAVE")
        self.geometry("540x380")
        self.resizable(False, False)
        self.configure(fg_color=theme.CARD_BG)

        # Center over parent
        self.transient(parent)
        self.grab_set()

        # Center calculation
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w // 2) - 270
        y = parent_y + (parent_h // 2) - 190
        self.geometry(f"+{max(10, x)}+{max(10, y)}")

        # Container
        main_frame = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=16)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))

        sparkle = ctk.CTkLabel(
            header,
            text="✦",
            font=theme.font(16, "bold"),
            text_color=theme.ACCENT,
        )
        sparkle.pack(side="left", padx=(0, 6))

        title = ctk.CTkLabel(
            header,
            text="What would you like me to do?",
            font=theme.font(16, "bold"),
            text_color=theme.TEXT_PRIMARY,
        )
        title.pack(side="left")

        esc_hint = ctk.CTkLabel(
            header,
            text="ESC to close",
            font=theme.font(10),
            text_color=theme.TEXT_MUTED,
        )
        esc_hint.pack(side="right")

        # Input field
        input_container = ctk.CTkFrame(
            main_frame,
            fg_color=theme.MAIN_BG,
            corner_radius=12,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        input_container.pack(fill="x", pady=(0, 16))

        self.entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Tell me in your own words...",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(13),
            fg_color="transparent",
            border_width=0,
            height=42,
            text_color=theme.TEXT_PRIMARY,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=12)
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._submit())
        self.bind("<Escape>", lambda e: self.destroy())

        submit_btn = ctk.CTkButton(
            input_container,
            text="↑",
            font=theme.font(14, "bold"),
            width=32,
            height=32,
            corner_radius=16,
            fg_color=theme.TEXT_PRIMARY,
            hover_color=theme.SIDEBAR_BG,
            text_color="#FFFFFF",
            command=self._submit,
        )
        submit_btn.pack(side="right", padx=6, pady=5)

        # Suggestions list
        ctk.CTkLabel(
            main_frame,
            text="Try something like:",
            font=theme.font(11, "bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        suggestions = [
            ("Continue my project", "▷"),
            ("Find my presentation", "📄"),
            ("Check my emails", "✉"),
            ("Research something online", "🔍"),
            ("Send this file to my phone", "📱"),
            ("Find a free time for a meeting tomorrow", "📅"),
        ]

        for text, icon in suggestions:
            btn = ctk.CTkButton(
                main_frame,
                text=f"  {icon}   {text}",
                font=theme.font(12),
                fg_color="transparent",
                hover_color=theme.MAIN_BG,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
                height=32,
                corner_radius=8,
                command=lambda t=text: self._execute_suggestion(t),
            )
            btn.pack(fill="x", pady=2)

    def _submit(self):
        cmd = self.entry.get().strip()
        if cmd:
            self.destroy()
            self.on_execute(cmd)

    def _execute_suggestion(self, text: str):
        self.destroy()
        self.on_execute(text)
