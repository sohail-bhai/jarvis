"""
Home Screen component.
Ultra-minimalist ChatGPT-style interface requested by the user.
"""
from __future__ import annotations

import os
import datetime
from PIL import Image
import customtkinter as ctk
from typing import Callable
from gui import theme
from gui.store import store


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, on_navigate: Callable[[str], None], on_execute_command: Callable[[str], None], on_voice_toggle: Callable[[], None] | None = None):
        super().__init__(
            parent,
            fg_color="transparent",
        )
        self.on_navigate = on_navigate
        self.on_execute_command = on_execute_command
        self.on_voice_toggle = on_voice_toggle

        # Center wrapper to push everything to the middle of the screen
        center_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        center_wrapper.pack(expand=True, fill="both")

        # Inner container for the actual content
        inner_container = ctk.CTkFrame(center_wrapper, fg_color="transparent")
        inner_container.place(relx=0.5, rely=0.45, anchor="center")

        # 1. Big Centered Greeting (Like ChatGPT)
        self._build_header(inner_container)

        # 2. Main Command Input Box
        self._build_command_input(inner_container)
        
        # We listen for store updates just in case, but no UI to update anymore
        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        pass

    def _build_header(self, parent):
        ctk.CTkLabel(
            parent,
            text="What's on your mind today?",
            font=theme.font(28, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(pady=(0, 30))

    def _build_command_input(self, parent):
        cmd_card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            corner_radius=24,
            border_width=1,
            border_color=theme.CARD_BORDER,
            width=700,
            height=56
        )
        cmd_card.pack(pady=(0, 10))
        cmd_card.pack_propagate(False) # Keep the fixed height/width

        row = ctk.CTkFrame(cmd_card, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=16, pady=2)

        ctk.CTkLabel(
            row,
            text="?",
            font=theme.font(16, "bold"),
            text_color=theme.TEXT_MUTED,
        ).pack(side="left", padx=(4, 10))

        self.cmd_entry = ctk.CTkEntry(
            row,
            placeholder_text="Ask JARVIS anything...",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(15),
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT_PRIMARY,
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self._submit_input())

        # Aesthetic mic icon like modern AI assistants
        mic_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "mic_hd.png")
        if os.path.exists(mic_icon_path):
            pil_img = Image.open(mic_icon_path)
            self.mic_ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(18, 18))
            mic_btn = ctk.CTkButton(
                row,
                text="",
                image=self.mic_ctk_image,
                width=36,
                height=36,
                corner_radius=18,
                fg_color="transparent",
                hover_color=theme.CARD_BORDER,
                command=self._toggle_voice,
            )
        else:
            mic_btn = ctk.CTkButton(
                row,
                text="??",
                font=theme.font(16),
                width=36,
                height=36,
                corner_radius=18,
                fg_color="transparent",
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_SECONDARY,
                command=self._toggle_voice,
            )
        mic_btn.pack(side="right", padx=(0, 8))

        arrow_btn = ctk.CTkButton(
            row,
            text="?",
            font=theme.font(18, "bold"),
            width=36,
            height=36,
            corner_radius=18,
            fg_color=theme.TEXT_PRIMARY,
            hover_color=theme.TEXT_SECONDARY,
            text_color="#000000",
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

