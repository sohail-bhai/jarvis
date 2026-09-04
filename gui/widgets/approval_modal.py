"""
Clean approval modal dialog.
Prompts for permission with plain-English context and clear action buttons.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import theme
from gui.store import store


class ApprovalModal(ctk.CTkFrame):
    def __init__(self, parent, approval_data):
        super().__init__(
            parent,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=12,
            width=440,
            height=300
        )
        self.approval_data = approval_data
        
        self.grid_propagate(False)
        self.pack_propagate(False)

        # Place centered in the application window
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.lift()

        # Wrap in a transparent container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=2, pady=2)

        # Header with warning/attention icon
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            hdr,
            text="⚠️",
            font=theme.font(16),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            hdr,
            text=approval_data.get("title", "JARVIS needs your approval"),
            font=theme.font(16, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        # Description box
        desc_card = ctk.CTkFrame(
            container,
            fg_color=theme.WARNING_LIGHT,
            border_width=1,
            border_color=theme.WARNING_BORDER,
            corner_radius=12,
        )
        desc_card.pack(fill="both", expand=True, pady=(0, 16))

        ctk.CTkLabel(
            desc_card,
            text=approval_data.get("description", ""),
            font=theme.font(12),
            text_color=theme.TEXT_PRIMARY,
            justify="left",
            wraplength=360,
            anchor="nw",
        ).pack(fill="both", expand=True, padx=16, pady=14)

        # Action Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text="Not Now",
            font=theme.font(12),
            fg_color=theme.MAIN_BG,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT_SECONDARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=10,
            height=36,
            command=self._reject,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="Approve",
            font=theme.font(12, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color="#FFFFFF",
            corner_radius=10,
            height=36,
            command=self._approve,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _approve(self):
        self.destroy()
        store.resolve_approval(True)

    def _reject(self):
        self.destroy()
        store.resolve_approval(False)
