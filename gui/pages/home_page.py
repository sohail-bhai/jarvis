"""
Home Screen component.
Ultra-minimalist ChatGPT-style interface with chat history support.
"""
from __future__ import annotations

import os
from PIL import Image
import customtkinter as ctk
from typing import Callable, List, Dict
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
        self.rendered_msg_count = 0

        # Main layout: chat area (top/expand) and input area (bottom)
        
        # 1. Chat Area (Scrollable) - Hidden if empty
        self.chat_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
            scrollbar_button_hover_color=theme.TEXT_MUTED,
        )
        # We will pack this later when there is history

        # 2. Empty State (Centered greeting)
        self.empty_center = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(
            self.empty_center,
            text="What's on your mind today?",
            font=theme.font(28, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(pady=(0, 20))

        # 3. Input Area (Always at bottom)
        self.input_container = ctk.CTkFrame(self, fg_color="transparent")
        self.input_container.pack(side="bottom", fill="x", pady=(0, 30))
        
        self._build_command_input(self.input_container)

        # Initial layout determination
        self._update_layout_state()
        
        # Listen for chat updates
        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        if event == "chat_message_added":
            # Update layout (hide empty state, show scroll)
            self._update_layout_state()
            self._render_new_messages()

    def _update_layout_state(self):
        if len(store.chat_history) == 0:
            self.chat_scroll.pack_forget()
            self.empty_center.place(relx=0.5, rely=0.45, anchor="center")
        else:
            self.empty_center.place_forget()
            if not self.chat_scroll.winfo_ismapped():
                self.chat_scroll.pack(fill="both", expand=True, padx=40, pady=(20, 20))
            self._render_new_messages()

    def _render_new_messages(self):
        history = store.chat_history
        if self.rendered_msg_count >= len(history):
            return
            
        for i in range(self.rendered_msg_count, len(history)):
            msg = history[i]
            self._build_chat_bubble(msg["role"], msg["text"])
            
        self.rendered_msg_count = len(history)
        
        # Scroll to bottom after a short delay to allow UI to update
        self.after(50, self.chat_scroll._parent_canvas.yview_moveto, 1.0)

    def _build_chat_bubble(self, role: str, text: str):
        # A container for the bubble to allow aligning left/right or just max width
        bubble_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        bubble_row.pack(fill="x", pady=10)
        
        if role == "user":
            # User bubble (aligned right, lighter bg)
            bubble = ctk.CTkFrame(
                bubble_row, 
                fg_color=theme.CARD_BG,
                corner_radius=16,
                border_width=1,
                border_color=theme.CARD_BORDER
            )
            bubble.pack(side="right", padx=10)
            
            lbl = ctk.CTkLabel(
                bubble,
                text=text,
                font=theme.font(14),
                text_color=theme.TEXT_PRIMARY,
                wraplength=500,
                justify="left"
            )
            lbl.pack(padx=16, pady=12)
            
        else:
            # Assistant bubble (aligned left, transparent bg like ChatGPT)
            bubble = ctk.CTkFrame(bubble_row, fg_color="transparent")
            bubble.pack(side="left", padx=10, fill="x", expand=True)
            
            lbl = ctk.CTkLabel(
                bubble,
                text=text,
                font=theme.font(14),
                text_color=theme.TEXT_SECONDARY,
                wraplength=700,
                justify="left",
                anchor="w"
            )
            lbl.pack(padx=10, pady=10, fill="x")

    def _build_command_input(self, parent):
        # Center the input bar horizontally within the bottom container
        center_wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        center_wrapper.pack(anchor="center")

        cmd_card = ctk.CTkFrame(
            center_wrapper,
            fg_color=theme.CARD_BG,
            corner_radius=24,
            border_width=1,
            border_color=theme.CARD_BORDER,
            width=700,
            height=56
        )
        cmd_card.pack()
        cmd_card.pack_propagate(False)

        row = ctk.CTkFrame(cmd_card, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=16, pady=2)

        ctk.CTkLabel(
            row,
            text="✦",
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

        # Aesthetic mic icon
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
                text="🎙",
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
            text="↑",
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

