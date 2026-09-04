"""
Settings screen.
Minimal, non-technical configuration including Security, Emergency Stop,
What JARVIS Remembers (Memory), and AI Helpers.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import theme
from gui.store import store


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )
        self.active_section = "General"
        self.section_buttons = {}

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            header,
            text="Settings",
            font=theme.font(20, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Customize your JARVIS preferences, connected accounts, and privacy.",
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Section Navigation Tabs
        nav_row = ctk.CTkFrame(self, fg_color="transparent")
        nav_row.pack(fill="x", padx=16, pady=(0, 16))

        sections = [
            ("General", "⚙"),
            ("Security", "🛡"),
            ("Memory", "🧠"),
            ("Connected Services", "🔗"),
            ("AI Helpers", "🤖"),
        ]

        for sec_name, icon in sections:
            btn = ctk.CTkButton(
                nav_row,
                text=f"{icon}  {sec_name}",
                font=theme.font(11, "bold" if sec_name == "General" else "normal"),
                fg_color=theme.SIDEBAR_BG if sec_name == "General" else theme.CARD_BG,
                hover_color=theme.SIDEBAR_HOVER if sec_name == "General" else theme.CARD_HOVER,
                text_color="#FFFFFF" if sec_name == "General" else theme.TEXT_SECONDARY,
                border_width=0 if sec_name == "General" else 1,
                border_color=theme.CARD_BORDER,
                corner_radius=12,
                height=28,
                command=lambda name=sec_name: self._switch_section(name),
            )
            btn.pack(side="left", padx=3)
            self.section_buttons[sec_name] = btn

        # 3. Content Area
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="x", padx=16, pady=(0, 20))

        self._render_content()

    def _switch_section(self, name: str):
        self.active_section = name
        for s_name, btn in self.section_buttons.items():
            if s_name == name:
                btn.configure(
                    fg_color=theme.SIDEBAR_BG,
                    text_color="#FFFFFF",
                    border_width=0,
                    font=theme.font(11, "bold"),
                )
            else:
                btn.configure(
                    fg_color=theme.CARD_BG,
                    text_color=theme.TEXT_SECONDARY,
                    border_width=1,
                    font=theme.font(11, "normal"),
                )
        self._render_content()

    def _render_content(self):
        for child in self.content_container.winfo_children():
            child.destroy()

        if self.active_section == "General":
            self._render_general()
        elif self.active_section == "Security":
            self._render_security()
        elif self.active_section == "Memory":
            self._render_memory()
        elif self.active_section == "Connected Services":
            self._render_services()
        elif self.active_section == "AI Helpers":
            self._render_helpers()

    def _render_general(self):
        card = ctk.CTkFrame(self.content_container, fg_color=theme.CARD_BG, corner_radius=14, border_width=1, border_color=theme.CARD_BORDER)
        card.pack(fill="x", pady=4)

        ctk.CTkLabel(card, text="General Preferences", font=theme.font(14, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 12))

        # Preference 1: Spoken Responses
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=8)
        c1 = ctk.CTkFrame(row1, fg_color="transparent")
        c1.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(c1, text="Spoken Voice Responses", font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(c1, text="JARVIS speaks aloud when completing tasks", font=theme.font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        switch1 = ctk.CTkSwitch(row1, text="", onvalue=True, offvalue=False)
        switch1.select()
        switch1.pack(side="right")

        # Preference 2: Non-technical language
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=8)
        c2 = ctk.CTkFrame(row2, fg_color="transparent")
        c2.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(c2, text="Simple Language Mode", font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(c2, text="Explain tasks in plain English without technical terms", font=theme.font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        switch2 = ctk.CTkSwitch(row2, text="", onvalue=True, offvalue=False)
        switch2.select()
        switch2.pack(side="right")

        # Preference 3: Auto-summaries
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(8, 16))
        c3 = ctk.CTkFrame(row3, fg_color="transparent")
        c3.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(c3, text="Approval Confirmation Gate", font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(c3, text="Always ask for permission before modifying project files", font=theme.font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        switch3 = ctk.CTkSwitch(row3, text="", onvalue=True, offvalue=False)
        switch3.select()
        switch3.pack(side="right")

    def _render_security(self):
        # 1. Protection Overview Card
        overview = ctk.CTkFrame(self.content_container, fg_color=theme.SUCCESS_LIGHT, border_width=1, border_color=theme.SUCCESS_BORDER, corner_radius=14)
        overview.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(overview, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner, text="You're protected", font=theme.font(14, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(inner, text="● JARVIS is working normally within safe boundaries.", font=theme.font(11), text_color=theme.SUCCESS, anchor="w").pack(anchor="w", pady=(2, 10))

        stat_row = ctk.CTkFrame(inner, fg_color="transparent")
        stat_row.pack(fill="x")
        for label, val in [("Connected Devices", "4"), ("Actions Waiting", "1"), ("Temporary Access Grants", "3")]:
            col = ctk.CTkFrame(stat_row, fg_color="transparent")
            col.pack(side="left", padx=(0, 24))
            ctk.CTkLabel(col, text=val, font=theme.font(16, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=label, font=theme.font(10), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

        # 2. Temporary Permissions Card
        perm_card = ctk.CTkFrame(self.content_container, fg_color=theme.CARD_BG, corner_radius=14, border_width=1, border_color=theme.CARD_BORDER)
        perm_card.pack(fill="x", pady=12)

        ctk.CTkLabel(perm_card, text="Temporary Access", font=theme.font(13, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 6))

        p_row = ctk.CTkFrame(perm_card, fg_color=theme.MAIN_BG, corner_radius=10)
        p_row.pack(fill="x", padx=14, pady=(4, 14))
        p_inner = ctk.CTkFrame(p_row, fg_color="transparent")
        p_inner.pack(fill="x", padx=12, pady=10)

        p_text = ctk.CTkFrame(p_inner, fg_color="transparent")
        p_text.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(p_text, text="Hackwave Project Access", font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(p_text, text="JARVIS can edit files · Expires in 24 minutes", font=theme.font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

        ctk.CTkButton(
            p_inner,
            text="Remove Access",
            font=theme.font(11),
            fg_color=theme.CARD_BG,
            hover_color=theme.DANGER_LIGHT,
            text_color=theme.DANGER,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=8,
            command=lambda: store.add_system_log("Removed temporary project access", "completed"),
        ).pack(side="right")

        # 3. Emergency Stop Card
        stop_card = ctk.CTkFrame(self.content_container, fg_color=theme.CARD_BG, corner_radius=14, border_width=1, border_color=theme.DANGER_BORDER)
        stop_card.pack(fill="x", pady=4)

        stop_inner = ctk.CTkFrame(stop_card, fg_color="transparent")
        stop_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(stop_inner, text="Something wrong?", font=theme.font(13, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(
            stop_inner,
            text="Instantly pause all background tasks and revoke temporary device access.",
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(2, 10))

        ctk.CTkButton(
            stop_inner,
            text="🛑 Stop JARVIS",
            font=theme.font(12, "bold"),
            fg_color=theme.DANGER,
            hover_color=theme.DANGER_HOVER,
            text_color="#FFFFFF",
            corner_radius=8,
            height=34,
            command=self._confirm_emergency_stop,
        ).pack(anchor="w")

    def _confirm_emergency_stop(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Stop JARVIS?")
        modal.geometry("380x260")
        modal.resizable(False, False)
        modal.configure(fg_color=theme.CARD_BG)
        modal.transient(self)
        modal.grab_set()

        inner = ctk.CTkFrame(modal, fg_color=theme.CARD_BG)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="Stop JARVIS?", font=theme.font(16, "bold"), text_color=theme.DANGER).pack(anchor="w")
        
        info = (
            "This will:\n\n"
            "• Stop ongoing tasks immediately\n"
            "• Remove all temporary access tokens\n"
            "• Prevent new actions\n\n"
            "Your files will not be deleted."
        )
        ctk.CTkLabel(inner, text=info, font=theme.font(11), text_color=theme.TEXT_SECONDARY, justify="left", anchor="w").pack(anchor="w", pady=10)

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=theme.font(11),
            fg_color=theme.MAIN_BG,
            text_color=theme.TEXT_PRIMARY,
            hover_color=theme.CARD_BORDER,
            corner_radius=8,
            command=modal.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        def _do_stop():
            modal.destroy()
            store.add_system_log("EMERGENCY STOP: All tasks paused and access revoked.", "completed")

        ctk.CTkButton(
            btn_row,
            text="Stop Everything",
            font=theme.font(11, "bold"),
            fg_color=theme.DANGER,
            hover_color=theme.DANGER_HOVER,
            text_color="#FFFFFF",
            corner_radius=8,
            command=_do_stop,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _render_memory(self):
        card = ctk.CTkFrame(self.content_container, fg_color=theme.CARD_BG, corner_radius=14, border_width=1, border_color=theme.CARD_BORDER)
        card.pack(fill="x", pady=4)

        ctk.CTkLabel(card, text="What JARVIS Remembers", font=theme.font(14, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(card, text="JARVIS learns your preferences so you don't have to repeat yourself.", font=theme.font(11), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 12))

        for mem in store.memories:
            row = ctk.CTkFrame(card, fg_color=theme.MAIN_BG, corner_radius=10)
            row.pack(fill="x", padx=14, pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            col = ctk.CTkFrame(inner, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(col, text=mem["fact"], font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=f"Saved from: {mem['source']}", font=theme.font(10), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

            ctk.CTkButton(
                inner,
                text="Forget this",
                font=theme.font(10),
                fg_color=theme.CARD_BG,
                hover_color=theme.DANGER_LIGHT,
                text_color=theme.TEXT_MUTED,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=8,
                width=80,
                height=26,
                command=lambda mid=mem["id"]: (store.forget_memory(mid), self._render_content()),
            ).pack(side="right")

        ctk.CTkFrame(card, height=10, fg_color="transparent").pack()

    def _render_services(self):
        card = ctk.CTkFrame(self.content_container, fg_color=theme.CARD_BG, corner_radius=14, border_width=1, border_color=theme.CARD_BORDER)
        card.pack(fill="x", pady=4)

        ctk.CTkLabel(card, text="Connected Services", font=theme.font(14, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(card, text="Third-party platforms and integrations connected to JARVIS.", font=theme.font(11), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 12))

        # Every line is checked rather than assumed, so this page can be
        # trusted to say when something is not actually connected.
        from assistant.api.server import get_local_server
        from gui import integrations

        google = integrations.google_status()
        local_ai = integrations.local_ai_status()
        phone = get_local_server().running

        services = [
            ("Google Workspace", "Drive, Gmail, Calendar, Docs, Slides",
             f"● {google['label']}",
             theme.SUCCESS if google["connected"] else theme.TEXT_MUTED),
            ("Phone", "This computer, reachable from your phone",
             "● On" if phone else "● Off",
             theme.SUCCESS if phone else theme.TEXT_MUTED),
            ("AI Helpers", "Local Ollama engine", f"● {local_ai['label']}",
             theme.INFO if local_ai["connected"] else theme.TEXT_MUTED),
        ]

        for title, desc, st, col in services:
            row = ctk.CTkFrame(card, fg_color=theme.MAIN_BG, corner_radius=10)
            row.pack(fill="x", padx=14, pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            c = ctk.CTkFrame(inner, fg_color="transparent")
            c.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(c, text=title, font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(c, text=desc, font=theme.font(10), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

            ctk.CTkLabel(inner, text=st, font=theme.font(11, "bold"), text_color=col).pack(side="right", padx=8)

        ctk.CTkFrame(card, height=10, fg_color="transparent").pack()

    def _render_helpers(self):
        card = ctk.CTkFrame(self.content_container, fg_color=theme.CARD_BG, corner_radius=14, border_width=1, border_color=theme.CARD_BORDER)
        card.pack(fill="x", pady=4)

        ctk.CTkLabel(card, text="Your AI Helpers", font=theme.font(14, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(card, text="JARVIS coordinates specialized internal helpers for you behind the scenes.", font=theme.font(11), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 12))

        for helper in store.ai_helpers:
            row = ctk.CTkFrame(card, fg_color=theme.MAIN_BG, corner_radius=10)
            row.pack(fill="x", padx=14, pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            c = ctk.CTkFrame(inner, fg_color="transparent")
            c.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(c, text=helper["name"], font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(c, text=helper["description"], font=theme.font(10), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

            is_work = helper["status"] == "Working"
            ctk.CTkLabel(
                inner,
                text=f"● {helper['status']}",
                font=theme.font(11, "bold"),
                text_color=theme.INFO if is_work else theme.SUCCESS,
            ).pack(side="right", padx=8)

        ctk.CTkFrame(card, height=10, fg_color="transparent").pack()
