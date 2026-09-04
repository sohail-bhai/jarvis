"""
Home screen.

Two columns, not a stack of cards. The left is a statement: who is here, what
it can be asked, and the box to ask it in. The right is the live column - what
is happening now, what it is connected to, and what it just did, in that order,
because that is the order someone watching asks about them.

Nothing here is boxed unless the box means something. Sections are separated by
space and a rule, which is what a printed page does and what a dashboard
usually forgets.
"""
from __future__ import annotations

import datetime
import customtkinter as ctk
from typing import Callable

from gui import icons, theme
from gui.store import store
from gui.widgets.card import Card


class HomePage(ctk.CTkFrame):
    # The statement column stops growing; the live column takes the rest.
    STATEMENT_WIDTH = 430

    def __init__(self, parent, on_navigate: Callable[[str], None],
                 on_execute_command: Callable[[str], None],
                 on_voice_toggle: Callable[[], None] | None = None):
        super().__init__(parent, fg_color="transparent")
        self.on_navigate = on_navigate
        self.on_execute_command = on_execute_command
        self.on_voice_toggle = on_voice_toggle
        self._icons = []          # Tk drops images with no live reference.

        self.grid_columnconfigure(0, weight=0, minsize=self.STATEMENT_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_statement()
        self._build_live_column()

        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        if event == "task_updated":
            self._update_task_ui()
        elif event == "system_log_added":
            self._render_log()

    # -- left: the statement --------------------------------------------------

    def _build_statement(self):
        column = ctk.CTkFrame(self, fg_color="transparent")
        column.grid(row=0, column=0, sticky="nsew",
                    padx=(theme.PAGE_GUTTER, theme.COLUMN_GAP), pady=(38, 34))

        hour = datetime.datetime.now().hour
        greeting = ("Good morning" if hour < 12
                    else "Good afternoon" if hour < 17 else "Good evening")

        ctk.CTkLabel(
            column, text=theme.tracked(greeting), font=theme.label_font(),
            text_color=theme.TEXT_MUTED, anchor="w",
        ).pack(fill="x")

        # Set on three lines on purpose: one long line would decide the width
        # of the whole column.
        ctk.CTkLabel(
            column,
            text="Tell me\nwhat you want.\nI handle the rest.",
            font=theme.display(theme.SIZE_DISPLAY),
            text_color=theme.TEXT_PRIMARY,
            justify="left", anchor="w",
        ).pack(fill="x", pady=(14, 0))

        ctk.CTkLabel(
            column,
            text="Your computer, your phone, Google and the web.\n"
                 "One place to ask, and a record of what happened.",
            font=theme.font(theme.SIZE_BODY),
            text_color=theme.TEXT_SECONDARY,
            justify="left", anchor="w",
        ).pack(fill="x", pady=(18, 0))

        # The command box anchors the bottom of the column, where the eye lands.
        anchor = ctk.CTkFrame(column, fg_color="transparent")
        anchor.pack(side="bottom", fill="x", pady=(0, 2))

        self._build_suggestions(anchor)
        self._build_command_input(anchor)

    def _build_suggestions(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))

        for text in ["Find my presentation", "Continue my project"]:
            ctk.CTkButton(
                row, text=text, font=theme.font(theme.SIZE_SMALL),
                fg_color="transparent", hover_color=theme.CARD_HOVER,
                text_color=theme.TEXT_MUTED,
                border_width=1, border_color=theme.CARD_BORDER,
                corner_radius=theme.RADIUS_PILL, height=30,
                command=lambda t=text: self.on_execute_command(t),
            ).pack(side="left", padx=(0, 7))

    def _build_command_input(self, parent):
        card = Card(parent, radius=16, elevation=theme.ELEVATION_LOW,
                    border=theme.CARD_BORDER)
        card.pack(fill="x", padx=0)
        card.configure(height=64 + card.inset * 2)
        card.pack_propagate(False)

        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=16, pady=13)

        self.cmd_entry = ctk.CTkEntry(
            row,
            placeholder_text="Ask for anything…",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(theme.SIZE_TITLE),
            fg_color="transparent", border_width=0,
            text_color=theme.TEXT_PRIMARY,
        )
        self.cmd_entry.pack(side="left", fill="both", expand=True, padx=(4, 10))
        self.cmd_entry.bind("<Return>", lambda e: self._submit_input())

        self.mic_icon = icons.image("mic", theme.ICON_CARD, theme.TEXT_MUTED)
        self._icons.append(self.mic_icon)
        ctk.CTkButton(
            row, text="" if self.mic_icon else "Voice", image=self.mic_icon,
            width=38, height=38, corner_radius=19,
            fg_color="transparent", hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_SECONDARY, command=self._toggle_voice,
        ).pack(side="right", padx=(0, 6))

        self.send_icon = icons.image("send", theme.ICON_CARD, theme.TEXT_LIGHT, 2.0)
        self._icons.append(self.send_icon)
        ctk.CTkButton(
            row, text="" if self.send_icon else "Send", image=self.send_icon,
            width=38, height=38, corner_radius=19,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_LIGHT, command=self._submit_input,
        ).pack(side="right")

    def _submit_input(self):
        text = self.cmd_entry.get().strip()
        if text:
            self.cmd_entry.delete(0, "end")
            self.on_execute_command(text)

    def _toggle_voice(self):
        if self.on_voice_toggle:
            self.on_voice_toggle()

    # -- right: the live column -----------------------------------------------

    def _build_live_column(self):
        column = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=0)
        column.grid(row=0, column=1, sticky="nsew")

        # A single hairline is all that separates the two halves.
        ctk.CTkFrame(column, fg_color=theme.DIVIDER, width=1).pack(
            side="left", fill="y")

        inner = ctk.CTkFrame(column, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=30, pady=(38, 30))

        self._build_task(inner)
        self._build_connected(inner)
        self._build_log(inner)

    def _rule(self, parent, pady=(22, 22)):
        ctk.CTkFrame(parent, fg_color=theme.DIVIDER, height=1).pack(
            fill="x", pady=pady)

    def _label(self, parent, text, right_text=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(row, text=theme.tracked(text), font=theme.label_font(),
                     text_color=theme.TEXT_MUTED).pack(side="left")
        if right_text:
            ctk.CTkLabel(row, text=right_text, font=theme.font(theme.SIZE_LABEL),
                         text_color=theme.TEXT_MUTED).pack(side="right")
        return row

    def _build_task(self, parent):
        steps = store.current_task.get("steps", [])
        done = sum(1 for step in steps if step.get("status") == "done")
        self._label(parent, "In progress",
                    f"Step {min(done + 1, len(steps))} of {len(steps)}" if steps else "")

        state = ctk.CTkFrame(parent, fg_color="transparent")
        state.pack(fill="x")

        ctk.CTkLabel(state, text="●", font=theme.font(9, "bold"),
                     text_color=theme.ACCENT).pack(side="left", padx=(0, 8))

        self.task_title_lbl = ctk.CTkLabel(
            state,
            text=store.current_task.get("title", "Preparing your project"),
            font=theme.display(theme.SIZE_HEADING),
            text_color=theme.TEXT_PRIMARY, anchor="w",
        )
        self.task_title_lbl.pack(side="left")

        ctk.CTkButton(
            state, text="Details", font=theme.font(theme.SIZE_LABEL),
            fg_color="transparent", hover_color=theme.SURFACE_SUBTLE,
            text_color=theme.TEXT_MUTED,
            border_width=1, border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_PILL, width=74, height=26,
            command=lambda: store.open_drawer("task", store.current_task),
        ).pack(side="right")

        self.task_sub_lbl = ctk.CTkLabel(
            parent,
            text=store.current_task.get(
                "subtitle",
                "Researching, organising files and writing a draft for you."),
            font=theme.font(theme.SIZE_SMALL),
            text_color=theme.TEXT_SECONDARY, anchor="w", justify="left",
        )
        self.task_sub_lbl.pack(fill="x", pady=(9, 0))

        self.steps_row = ctk.CTkFrame(parent, fg_color="transparent")
        self.steps_row.pack(fill="x", pady=(14, 0))
        self._render_task_steps()

        self._rule(parent)

    def _render_task_steps(self):
        for child in self.steps_row.winfo_children():
            child.destroy()
        self.step_icons = []

        for step in store.current_task.get("steps", []):
            status = step.get("status")
            row = ctk.CTkFrame(self.steps_row, fg_color="transparent")
            row.pack(fill="x", pady=2)

            if status == "done":
                tick = icons.image("check", 12, theme.SUCCESS, 2.4)
                self.step_icons.append(tick)
                marker = ctk.CTkLabel(row, text="" if tick else "✓", image=tick,
                                      width=16, font=theme.font(10, "bold"),
                                      text_color=theme.SUCCESS)
                colour = theme.TEXT_MUTED
            else:
                dot = theme.ACCENT if status == "active" else theme.CARD_BORDER
                marker = ctk.CTkLabel(row, text="●", width=16,
                                      font=theme.font(9, "bold"), text_color=dot)
                colour = (theme.TEXT_PRIMARY if status == "active"
                          else theme.TEXT_MUTED)

            marker.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                row, text=step.get("text", ""),
                font=theme.font(theme.SIZE_SMALL,
                                "bold" if status == "active" else "normal"),
                text_color=colour,
            ).pack(side="left")

    def _update_task_ui(self):
        self.task_title_lbl.configure(text=store.current_task.get("title", ""))
        self.task_sub_lbl.configure(text=store.current_task.get("subtitle", ""))
        self._render_task_steps()

    def _build_connected(self, parent):
        from assistant.api.server import get_local_server
        from gui import integrations

        # Each line says what is true right now. A list that always reads
        # "Connected" teaches the user to ignore all four.
        google = integrations.google_status()
        phone_paired = get_local_server().running

        entries = [
            ("My Computer", "Online", True, "devices", "monitor"),
            ("My Phone", "Ready to pair" if phone_paired else "Not connected",
             phone_paired, "devices", "phone"),
            ("Google", google["label"], google["connected"], "google", "google"),
            ("The web", "Ready", True, "web", "globe"),
        ]

        self._label(parent, "Connected")

        for name, status, is_live, route, glyph in entries:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=4)

            icon = icons.image(glyph, 15,
                               theme.TEXT_SECONDARY if is_live else theme.TEXT_MUTED)
            self._icons.append(icon)
            if icon is not None:
                ctk.CTkLabel(row, text="", image=icon, width=18).pack(
                    side="left", padx=(0, 12))

            ctk.CTkLabel(
                row, text=name, font=theme.font(theme.SIZE_SMALL),
                text_color=theme.TEXT_PRIMARY if is_live else theme.TEXT_SECONDARY,
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=status, font=theme.font(theme.SIZE_SMALL),
                text_color=theme.SUCCESS if is_live else theme.TEXT_MUTED,
            ).pack(side="right")

            row.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))

        self._rule(parent)

    def _build_log(self, parent):
        self._label(parent, "Just now", "Live")
        self.log_holder = ctk.CTkFrame(parent, fg_color="transparent")
        self.log_holder.pack(fill="both", expand=True)
        self._render_log()

    def _render_log(self):
        if not hasattr(self, "log_holder") or not self.log_holder.winfo_exists():
            return

        for child in self.log_holder.winfo_children():
            child.destroy()

        # Only the most recent few: this is a pulse, not an archive. The full
        # record is the Activity page.
        for item in list(store.system_logs)[-5:][::-1]:
            row = ctk.CTkFrame(self.log_holder, fg_color="transparent")
            row.pack(fill="x", pady=4)

            status = item.get("status", "working")
            colour = {"completed": theme.SUCCESS, "waiting": theme.WARNING,
                      "approval": theme.WARNING, "failed": theme.DANGER,
                      "info": theme.TEXT_MUTED}.get(status, theme.ACCENT)

            ctk.CTkLabel(row, text="●", font=theme.font(8, "bold"),
                         text_color=colour, width=14).pack(
                side="left", anchor="n", pady=(4, 0))
            ctk.CTkLabel(row, text=item.get("time", ""),
                         font=theme.font(theme.SIZE_LABEL),
                         text_color=theme.TEXT_MUTED).pack(side="right", anchor="n")
            ctk.CTkLabel(
                row, text=item.get("text", ""), font=theme.font(theme.SIZE_SMALL),
                text_color=theme.TEXT_SECONDARY, anchor="w", justify="left",
                wraplength=300,
            ).pack(side="left", fill="x", expand=True)
