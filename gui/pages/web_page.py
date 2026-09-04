"""
Web tasks and research screen.
Shows web searches, background research tasks, and live browser progress.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import theme
from gui.store import store


class WebPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            header,
            text="Web",
            font=theme.font(20, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Ask JARVIS to find answers, research topics, or perform web actions for you.",
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Main Input Box
        input_card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=14,
        )
        input_card.pack(fill="x", padx=16, pady=(0, 12))

        row = ctk.CTkFrame(input_card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            row,
            text="🌐",
            font=theme.font(16),
        ).pack(side="left", padx=(0, 8))

        self.web_entry = ctk.CTkEntry(
            row,
            placeholder_text="What should I find or do online?",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(13),
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT_PRIMARY,
        )
        self.web_entry.pack(side="left", fill="x", expand=True)
        self.web_entry.bind("<Return>", lambda e: self._submit_web_task())

        arrow_btn = ctk.CTkButton(
            row,
            text="↑",
            font=theme.font(14, "bold"),
            width=32,
            height=32,
            corner_radius=16,
            fg_color=theme.TEXT_PRIMARY,
            hover_color=theme.SIDEBAR_BG,
            text_color="#FFFFFF",
            command=self._submit_web_task,
        )
        arrow_btn.pack(side="right")

        # 3. Suggestions
        chips_row = ctk.CTkFrame(self, fg_color="transparent")
        chips_row.pack(fill="x", padx=16, pady=(0, 16))

        prompts = [
            "Research latest AI tools",
            "Find React documentation",
            "Compare GPU cloud pricing",
            "Summarize news on space tech",
        ]
        for p in prompts:
            ctk.CTkButton(
                chips_row,
                text=p,
                font=theme.font(11),
                fg_color=theme.CARD_BG,
                hover_color=theme.CARD_HOVER,
                text_color=theme.TEXT_SECONDARY,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=10,
                height=26,
                command=lambda text=p: self._trigger_prompt(text),
            ).pack(side="left", padx=3)

        # 4. Browser Task Live Progress Card
        self._build_browser_progress()

        # 5. Recent Web Tasks List
        self._build_recent_tasks()

    def _trigger_prompt(self, text: str):
        self.web_entry.delete(0, "end")
        self.web_entry.insert(0, text)
        self._submit_web_task()

    def _submit_web_task(self):
        text = self.web_entry.get().strip()
        if text:
            self.web_entry.delete(0, "end")
            store.add_system_log(f"Starting web research: '{text}'", "working")
            new_task = {"id": f"w-{len(store.web_tasks)+1}", "query": text, "status": "Working", "time": "Just now"}
            store.web_tasks.insert(0, new_task)
            self._render_recent_tasks()

    def _build_browser_progress(self):
        card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=14,
        )
        card.pack(fill="x", padx=16, pady=(0, 16))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top,
            text="Active Browser Task",
            font=theme.font(11, "bold"),
            text_color=theme.TEXT_MUTED,
        ).pack(anchor="w")

        ctk.CTkLabel(
            top,
            text=store.browser_progress["title"],
            font=theme.font(14, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(2, 0))

        # Steps
        steps_row = ctk.CTkFrame(inner, fg_color=theme.MAIN_BG, corner_radius=10)
        steps_row.pack(fill="x", pady=4)

        for step in store.browser_progress["steps"]:
            row = ctk.CTkFrame(steps_row, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)

            if step.get("done"):
                icon, col = "✓", theme.SUCCESS
            elif step.get("active"):
                icon, col = "●", theme.INFO
            else:
                icon, col = "○", theme.TEXT_MUTED

            ctk.CTkLabel(row, text=icon, font=theme.font(11, "bold"), text_color=col, width=18).pack(side="left")
            ctk.CTkLabel(row, text=step["text"], font=theme.font(11), text_color=theme.TEXT_PRIMARY).pack(side="left", padx=4)

    def _build_recent_tasks(self):
        ctk.CTkLabel(
            self,
            text="Recent Web Tasks",
            font=theme.font(13, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(4, 8))

        self.tasks_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tasks_container.pack(fill="x", padx=16, pady=(0, 20))

        self._render_recent_tasks()

    def _render_recent_tasks(self):
        for child in self.tasks_container.winfo_children():
            child.destroy()

        for t in store.web_tasks:
            card = ctk.CTkFrame(
                self.tasks_container,
                fg_color=theme.CARD_BG,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=12,
            )
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(col, text=t["query"], font=theme.font(12, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=t["time"], font=theme.font(10), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

            # Status pill
            is_work = t["status"] == "Working"
            badge = ctk.CTkLabel(
                row,
                text=f"{'●' if is_work else '✓'} {t['status']}",
                font=theme.font(10, "bold"),
                text_color=theme.INFO if is_work else theme.SUCCESS,
                fg_color=theme.INFO_LIGHT if is_work else theme.SUCCESS_LIGHT,
                corner_radius=8,
                padx=10,
                pady=4,
            )
            badge.pack(side="right")
