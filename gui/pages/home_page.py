"""
Home screen.

Three things, in the order a person needs them: what you can ask, what VAVE is
doing right now, and what it is connected to. Navigation lives in the sidebar,
so it is not repeated here.

The layout is deliberately editorial - a serif greeting with room around it, one
raised surface for the thing you actually came to do, and everything else
sitting quietly below it.
"""
from __future__ import annotations

import datetime
import customtkinter as ctk
from typing import Callable

from gui import icons, theme
from gui.store import store
from gui.widgets.card import Card


class HomePage(ctk.CTkScrollableFrame):
    # Room down either side of the page. Generous on purpose: whitespace is
    # most of what separates a considered interface from a dense one.
    GUTTER = 34

    def __init__(self, parent, on_navigate: Callable[[str], None],
                 on_execute_command: Callable[[str], None],
                 on_voice_toggle: Callable[[], None] | None = None):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
            scrollbar_button_hover_color=theme.TEXT_MUTED,
        )
        self.on_navigate = on_navigate
        self.on_execute_command = on_execute_command
        self.on_voice_toggle = on_voice_toggle
        self._icons = []          # Tk drops images with no live reference.

        self._build_header()
        self._build_command_input()
        self._build_suggestions()
        self._build_current_task()
        self._build_connected()

        store.subscribe(self._on_store_update)

    def _on_store_update(self, event: str, data: any):
        if event == "task_updated":
            self._update_task_ui()

    # -- header -------------------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=self.GUTTER, pady=(30, 22))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")

        hour = datetime.datetime.now().hour
        greeting = ("Good morning" if hour < 12
                    else "Good afternoon" if hour < 17 else "Good evening")

        ctk.CTkLabel(
            left,
            text=theme.tracked(greeting),
            font=theme.label_font(),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="What would you like to do?",
            font=theme.display(theme.SIZE_DISPLAY),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

        now = datetime.datetime.now()
        date_str = now.strftime(f"%A, {now.day} %B")
        ctk.CTkLabel(
            header,
            text=date_str,
            font=theme.font(theme.SIZE_SMALL),
            text_color=theme.TEXT_MUTED,
        ).pack(side="right", pady=(18, 0))

    # -- the one thing you came here to do -----------------------------------

    def _build_command_input(self):
        card = Card(self, radius=16, elevation=theme.ELEVATION_HIGH)
        card.pack(fill="x", padx=self.GUTTER - card.inset, pady=(0, 6))
        card.configure(height=78 + card.inset * 2)
        card.pack_propagate(False)

        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=20, pady=16)

        self.cmd_entry = ctk.CTkEntry(
            row,
            placeholder_text="Ask for anything. VAVE works out the rest.",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(theme.SIZE_TITLE),
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT_PRIMARY,
        )
        self.cmd_entry.pack(side="left", fill="both", expand=True, padx=(2, 12))
        self.cmd_entry.bind("<Return>", lambda e: self._submit_input())

        self.mic_icon = icons.image("mic", theme.ICON_CARD, theme.TEXT_MUTED)
        mic = ctk.CTkButton(
            row,
            text="" if self.mic_icon else "Voice",
            image=self.mic_icon,
            width=40, height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color=theme.SURFACE_SUBTLE,
            text_color=theme.TEXT_SECONDARY,
            command=self._toggle_voice,
        )
        mic.pack(side="right", padx=(0, 8))

        self.send_icon = icons.image("send", theme.ICON_CARD, theme.TEXT_LIGHT, 2.0)
        send = ctk.CTkButton(
            row,
            text="" if self.send_icon else "Send",
            image=self.send_icon,
            width=40, height=40,
            corner_radius=20,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_LIGHT,
            command=self._submit_input,
        )
        send.pack(side="right")

    def _submit_input(self):
        text = self.cmd_entry.get().strip()
        if text:
            self.cmd_entry.delete(0, "end")
            self.on_execute_command(text)

    def _toggle_voice(self):
        if self.on_voice_toggle:
            self.on_voice_toggle()

    def _build_suggestions(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=self.GUTTER, pady=(4, 30))

        for text in ["Find my presentation", "Continue my project",
                     "Check my email"]:
            ctk.CTkButton(
                row,
                text=text,
                font=theme.font(theme.SIZE_SMALL),
                fg_color="transparent",
                hover_color=theme.SURFACE_SUBTLE,
                text_color=theme.TEXT_SECONDARY,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=theme.RADIUS_PILL,
                height=32,
                command=lambda t=text: self.on_execute_command(t),
            ).pack(side="left", padx=(0, 8))

    # -- what is happening now ------------------------------------------------

    def _section_label(self, text: str, top: int = 0):
        ctk.CTkLabel(
            self,
            text=theme.tracked(text),
            font=theme.label_font(),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=self.GUTTER, pady=(top, 10))

    def _build_current_task(self):
        self._section_label("Now")

        card = Card(self, elevation=theme.ELEVATION_LOW, border=theme.CARD_BORDER)
        card.pack(fill="x", padx=self.GUTTER - card.inset, pady=(0, 30))

        head = ctk.CTkFrame(card.body, fg_color="transparent")
        head.pack(fill="x", padx=22, pady=(20, 0))

        title_col = ctk.CTkFrame(head, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        state = ctk.CTkFrame(title_col, fg_color="transparent")
        state.pack(anchor="w")

        ctk.CTkLabel(state, text="●", font=theme.font(9, "bold"),
                     text_color=theme.ACCENT).pack(side="left", padx=(0, 7))
        ctk.CTkLabel(state, text=theme.tracked("Working"), font=theme.label_font(),
                     text_color=theme.ACCENT).pack(side="left")

        self.task_title_lbl = ctk.CTkLabel(
            title_col,
            text=store.current_task.get("title", "Preparing your project"),
            font=theme.display(theme.SIZE_HEADING),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.task_title_lbl.pack(anchor="w", pady=(9, 0))

        self.task_sub_lbl = ctk.CTkLabel(
            title_col,
            text=store.current_task.get(
                "subtitle",
                "VAVE is researching, organising files and writing a draft for you."),
            font=theme.font(theme.SIZE_BODY),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.task_sub_lbl.pack(anchor="w", pady=(5, 0))

        ctk.CTkButton(
            head,
            text="View details",
            font=theme.font(theme.SIZE_SMALL),
            fg_color="transparent",
            hover_color=theme.SURFACE_SUBTLE,
            text_color=theme.TEXT_SECONDARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_PILL,
            width=106, height=30,
            command=lambda: store.open_drawer("task", store.current_task),
        ).pack(side="right", anchor="n", pady=(2, 0))

        ctk.CTkFrame(card.body, fg_color=theme.DIVIDER, height=1).pack(
            fill="x", padx=22, pady=(20, 0))

        self.steps_row = ctk.CTkFrame(card.body, fg_color="transparent")
        self.steps_row.pack(fill="x", padx=22, pady=(16, 20))
        self._render_task_steps()

    def _render_task_steps(self):
        for child in self.steps_row.winfo_children():
            child.destroy()
        self.step_icons = []

        steps = store.current_task.get("steps", [])
        if not steps:
            return

        # Markers for the whole run, then the name of the step in hand. Four
        # full labels never fit, and three of them are not what you are
        # waiting on anyway.
        markers = ctk.CTkFrame(self.steps_row, fg_color="transparent")
        markers.pack(side="left")

        active_index, active_text = 0, ""
        for index, step in enumerate(steps):
            status = step.get("status")
            if status == "done":
                colour, glyph = theme.SUCCESS, "\u25cf"
            elif status == "active":
                colour, glyph = theme.ACCENT, "\u25cf"
                active_index, active_text = index, step.get("text", "")
            else:
                colour, glyph = theme.CARD_BORDER, "\u25cf"

            ctk.CTkLabel(markers, text=glyph, font=theme.font(9, "bold"),
                         text_color=colour).pack(side="left", padx=(0, 6))

        if not active_text:
            # Everything finished, or nothing started yet.
            done = sum(1 for s in steps if s.get("status") == "done")
            active_text = "All steps finished" if done == len(steps) else "Starting"
            active_index = max(done - 1, 0)

        ctk.CTkLabel(
            self.steps_row,
            text=active_text,
            font=theme.font(theme.SIZE_SMALL, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            self.steps_row,
            text=f"Step {active_index + 1} of {len(steps)}",
            font=theme.font(theme.SIZE_SMALL),
            text_color=theme.TEXT_MUTED,
        ).pack(side="right")

    def _update_task_ui(self):
        self.task_title_lbl.configure(text=store.current_task.get("title", ""))
        self.task_sub_lbl.configure(text=store.current_task.get("subtitle", ""))
        self._render_task_steps()

    # -- what it is connected to ----------------------------------------------

    def _build_connected(self):
        from assistant.api.server import get_local_server
        from gui import integrations

        # Each column says what is true right now. A row that always reads
        # "Connected" teaches the user to ignore all four.
        google = integrations.google_status()
        phone_paired = get_local_server().running

        entries = [
            ("My Computer", "Online", True, "devices", "monitor"),
            ("My Phone", "Ready to pair" if phone_paired else "Not connected",
             phone_paired, "devices", "phone"),
            ("Google", google["label"], google["connected"], "google", "google"),
            ("Internet", "Ready", True, "web", "globe"),
        ]

        self._section_label("Connected")

        card = Card(self, elevation=theme.ELEVATION_LOW, border=theme.CARD_BORDER)
        card.pack(fill="x", padx=self.GUTTER - card.inset, pady=(0, 34))

        grid = card.body
        grid.grid_columnconfigure((0, 2, 4, 6), weight=1, uniform="env")

        for index, (name, status, is_live, route, glyph) in enumerate(entries):
            column = index * 2

            if index:
                ctk.CTkFrame(grid, fg_color=theme.DIVIDER, width=1, height=44).grid(
                    row=0, column=column - 1, sticky="ns", pady=18)

            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=0, column=column, sticky="nsew", padx=14, pady=18)

            icon = icons.image(glyph, theme.ICON_CARD,
                               theme.TEXT_PRIMARY if is_live else theme.TEXT_MUTED)
            self._icons.append(icon)

            top = ctk.CTkFrame(cell, fg_color="transparent")
            top.pack(fill="x")

            if icon is not None:
                ctk.CTkLabel(top, text="", image=icon, width=18).pack(
                    side="left", padx=(0, 8))

            ctk.CTkLabel(
                top,
                text=name,
                font=theme.font(theme.SIZE_BODY, "bold"),
                text_color=theme.TEXT_PRIMARY if is_live else theme.TEXT_SECONDARY,
            ).pack(side="left")

            status_row = ctk.CTkFrame(cell, fg_color="transparent")
            status_row.pack(fill="x", pady=(7, 0))

            ctk.CTkLabel(
                status_row,
                text="●",
                font=theme.font(8, "bold"),
                text_color=theme.SUCCESS if is_live else theme.TEXT_MUTED,
            ).pack(side="left", padx=(1, 7))

            ctk.CTkLabel(
                status_row,
                text=status,
                font=theme.font(theme.SIZE_SMALL),
                text_color=theme.TEXT_SECONDARY if is_live else theme.TEXT_MUTED,
            ).pack(side="left")

            for widget in (cell, top, status_row):
                widget.bind("<Button-1>", lambda e, r=route: self.on_navigate(r))
