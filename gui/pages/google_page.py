"""
Google workspace integration screen.
Unified view for Drive, Gmail, Calendar, and Docs.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import theme
from gui.store import store


class GooglePage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )
        self.active_tab = "Overview"
        self.tab_buttons = {}

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text="Google",
            font=theme.font(20, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        # Connected badge
        conn_badge = ctk.CTkLabel(
            title_row,
            text="● Connected",
            font=theme.font(11, "bold"),
            text_color=theme.SUCCESS,
            fg_color=theme.SUCCESS_LIGHT,
            corner_radius=10,
            padx=10,
            pady=4,
        )
        conn_badge.pack(side="left", padx=12)

        ctk.CTkLabel(
            header,
            text="JARVIS connects to your Google ecosystem so you never have to juggle tabs.",
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Tabs Row
        tabs_row = ctk.CTkFrame(self, fg_color="transparent")
        tabs_row.pack(fill="x", padx=16, pady=(0, 14))

        tabs = ["Overview", "Drive", "Gmail", "Calendar", "Docs"]
        for t in tabs:
            btn = ctk.CTkButton(
                tabs_row,
                text=t,
                font=theme.font(11, "bold" if t == "Overview" else "normal"),
                fg_color=theme.SIDEBAR_BG if t == "Overview" else theme.CARD_BG,
                hover_color=theme.SIDEBAR_HOVER if t == "Overview" else theme.CARD_HOVER,
                text_color="#FFFFFF" if t == "Overview" else theme.TEXT_SECONDARY,
                border_width=0 if t == "Overview" else 1,
                border_color=theme.CARD_BORDER,
                corner_radius=12,
                height=28,
                command=lambda name=t: self._switch_tab(name),
            )
            btn.pack(side="left", padx=3)
            self.tab_buttons[t] = btn

        # 3. Tab Content Container
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_container.pack(fill="x", padx=16, pady=(0, 20))

        self._render_tab_content()

    def _switch_tab(self, tab_name: str):
        self.active_tab = tab_name
        for name, btn in self.tab_buttons.items():
            if name == tab_name:
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
        self._render_tab_content()

    def _render_tab_content(self):
        for child in self.tab_container.winfo_children():
            child.destroy()

        if self.active_tab == "Overview":
            self._render_overview()
        elif self.active_tab == "Drive":
            self._render_drive()
        elif self.active_tab == "Gmail":
            self._render_gmail()
        elif self.active_tab == "Calendar":
            self._render_calendar()
        elif self.active_tab == "Docs":
            self._render_docs()

    def _render_overview(self):
        # 4 Metric Cards
        grid = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 16))
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="g_ov")

        overview_items = [
            ("Google Drive", store.google["overview"]["drive_files"], "📁", theme.INFO_LIGHT, theme.INFO_BORDER),
            ("Gmail", store.google["overview"]["unread_emails"], "✉", theme.DANGER_LIGHT, theme.DANGER_BORDER),
            ("Calendar", store.google["overview"]["calendar_events"], "📅", theme.SUCCESS_LIGHT, theme.SUCCESS_BORDER),
            ("Recent Docs", store.google["overview"]["recent_docs"], "📄", theme.WARNING_LIGHT, theme.WARNING_BORDER),
        ]

        for idx, (title, val, icon, bg, border) in enumerate(overview_items):
            card = ctk.CTkFrame(
                grid,
                fg_color=bg,
                border_width=1,
                border_color=border,
                corner_radius=12,
                height=84,
            )
            card.grid(row=0, column=idx, padx=4, sticky="nsew")
            card.pack_propagate(False)

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=12, pady=12)

            ctk.CTkLabel(content, text=icon, font=theme.font(18)).pack(anchor="w")
            ctk.CTkLabel(content, text=title, font=theme.font(11, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", pady=(2, 0))

        # Quick Actions Card
        actions_card = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG, corner_radius=14, border_width=1, border_color=theme.CARD_BORDER)
        actions_card.pack(fill="x", pady=8)

        ctk.CTkLabel(actions_card, text="Quick Google Actions with JARVIS", font=theme.font(13, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))

        action_prompts = [
            ("Check today's schedule", "📅"),
            ("Summarize unread emails from today", "✉"),
            ("Find Hackwave presentation in Drive", "🔍"),
            ("Find free time for a team sync tomorrow", "⏰"),
        ]
        for prompt, icon in action_prompts:
            ctk.CTkButton(
                actions_card,
                text=f"  {icon}   {prompt}",
                font=theme.font(12),
                fg_color=theme.MAIN_BG,
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
                corner_radius=8,
                height=32,
                command=lambda p=prompt: store.add_system_log(f"Handling '{p}' via Google", "working"),
            ).pack(fill="x", padx=16, pady=3)

        ctk.CTkFrame(actions_card, height=10, fg_color="transparent").pack()

    def _render_drive(self):
        # Search
        search_row = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG, corner_radius=12, border_width=1, border_color=theme.CARD_BORDER)
        search_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(search_row, text=" 🔍", font=theme.font(12)).pack(side="left", padx=8)
        ctk.CTkEntry(
            search_row,
            placeholder_text="Search your Google Drive...",
            placeholder_text_color=theme.TEXT_MUTED,
            border_width=0,
            fg_color="transparent",
        ).pack(side="left", fill="x", expand=True, pady=8)

        for item in store.google["drive_items"]:
            card = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG, corner_radius=12, border_width=1, border_color=theme.CARD_BORDER)
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            ctk.CTkLabel(row, text=item["icon"], font=theme.font(18)).pack(side="left", padx=(0, 10))

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(col, text=item["name"], font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=f"{item['type']} · {item['date']}", font=theme.font(10), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right")

            ctk.CTkButton(
                actions,
                text="Use with JARVIS",
                font=theme.font(11),
                fg_color=theme.MAIN_BG,
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_PRIMARY,
                corner_radius=8,
                height=26,
                command=lambda n=item["name"]: store.add_system_log(f"Added {n} to JARVIS context", "completed"),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                actions,
                text="Summarize",
                font=theme.font(11),
                fg_color=theme.MAIN_BG,
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_PRIMARY,
                corner_radius=8,
                height=26,
                command=lambda n=item["name"]: store.add_system_log(f"Summarizing {n}", "working"),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                actions,
                text="Open",
                font=theme.font(11, "bold"),
                fg_color=theme.ACCENT,
                hover_color=theme.ACCENT_HOVER,
                text_color="#FFFFFF",
                corner_radius=8,
                height=26,
                command=lambda n=item["name"]: store.add_system_log(f"Opened Google Drive file {n}", "completed"),
            ).pack(side="left", padx=4)

    def _render_gmail(self):
        for email in store.google["emails"]:
            card = ctk.CTkFrame(
                self.tab_container,
                fg_color=theme.INFO_LIGHT if email["unread"] else theme.CARD_BG,
                corner_radius=12,
                border_width=1,
                border_color=theme.INFO_BORDER if email["unread"] else theme.CARD_BORDER,
            )
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)

            sender_row = ctk.CTkFrame(col, fg_color="transparent")
            sender_row.pack(fill="x", anchor="w")

            if email["unread"]:
                ctk.CTkLabel(sender_row, text="●", font=theme.font(9, "bold"), text_color=theme.INFO).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(sender_row, text=email["sender"], font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(sender_row, text=f" · {email['time']}", font=theme.font(10), text_color=theme.TEXT_MUTED).pack(side="left")

            ctk.CTkLabel(col, text=email["subject"], font=theme.font(12), text_color=theme.TEXT_SECONDARY, anchor="w").pack(anchor="w", pady=(2, 0))

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right")

            ctk.CTkButton(
                actions,
                text="Summarize",
                font=theme.font(11),
                fg_color=theme.MAIN_BG,
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_PRIMARY,
                corner_radius=8,
                height=26,
                command=lambda s=email["subject"]: store.add_system_log(f"Summarized email: {s}", "completed"),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                actions,
                text="Draft Reply",
                font=theme.font(11, "bold"),
                fg_color=theme.ACCENT,
                hover_color=theme.ACCENT_HOVER,
                text_color="#FFFFFF",
                corner_radius=8,
                height=26,
                command=lambda s=email["subject"]: store.add_system_log(f"Drafted polite reply to '{s}'", "completed"),
            ).pack(side="left", padx=4)

    def _render_calendar(self):
        ctk.CTkLabel(self.tab_container, text="Today's Schedule", font=theme.font(13, "bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", pady=(4, 10))

        for event in store.google["calendar"]:
            card = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG, corner_radius=12, border_width=1, border_color=theme.CARD_BORDER)
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            time_box = ctk.CTkFrame(row, fg_color=theme.MAIN_BG, corner_radius=8, width=74, height=36)
            time_box.pack(side="left", padx=(0, 12))
            time_box.pack_propagate(False)
            ctk.CTkLabel(time_box, text=event["time"], font=theme.font(11, "bold"), text_color=theme.TEXT_PRIMARY).pack(expand=True)

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(col, text=event["title"], font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=f"{event['duration']} · {event['tag']}", font=theme.font(10), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

        # Natural language buttons
        bot_row = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        bot_row.pack(fill="x", pady=16)

        ctk.CTkButton(
            bot_row,
            text="📅 Find me a free time tomorrow",
            font=theme.font(11),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=10,
            command=lambda: store.add_system_log("Found 2 free slots: 11:30 AM and 3:00 PM tomorrow", "completed"),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            bot_row,
            text="⏰ What do I have this evening?",
            font=theme.font(11),
            fg_color=theme.CARD_BG,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=10,
            command=lambda: store.add_system_log("You have Team Sync & Demo Review at 5:30 PM", "completed"),
        ).pack(side="left")

    def _render_docs(self):
        for doc in store.google["docs"]:
            card = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG, corner_radius=12, border_width=1, border_color=theme.CARD_BORDER)
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(col, text=doc["title"], font=theme.font(13, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=f"{doc['app']} · {doc['desc']}", font=theme.font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right")

            ctk.CTkButton(
                actions,
                text="Ask JARVIS to improve",
                font=theme.font(11),
                fg_color=theme.MAIN_BG,
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_PRIMARY,
                corner_radius=8,
                height=28,
                command=lambda t=doc["title"]: store.add_system_log(f"Generated suggestions to improve {t}", "completed"),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                actions,
                text="Open",
                font=theme.font(11, "bold"),
                fg_color=theme.ACCENT,
                hover_color=theme.ACCENT_HOVER,
                text_color="#FFFFFF",
                corner_radius=8,
                height=28,
                command=lambda t=doc["title"]: store.add_system_log(f"Opened {t}", "completed"),
            ).pack(side="left", padx=4)
