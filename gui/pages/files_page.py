"""
My Files screen.
Universal file search across Computer, Phone, Server, and Google Drive.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import icons, theme
from gui.store import store


class FilesPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )
        self.selected_filter = "All"
        self.filter_buttons = {}

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            header,
            text="My Files",
            font=theme.font(20, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Search by what you remember, not by complicated file paths.",
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Search Box
        search_card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=theme.RADIUS_CARD,
        )
        search_card.pack(fill="x", padx=16, pady=(0, 12))

        search_row = ctk.CTkFrame(search_card, fg_color="transparent")
        search_row.pack(fill="x", padx=14, pady=8)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search your files...",
            placeholder_text_color=theme.TEXT_MUTED,
            font=theme.font(13),
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT_PRIMARY,
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self._render_files())

        # 3. Source Filter Tabs
        filters_row = ctk.CTkFrame(self, fg_color="transparent")
        filters_row.pack(fill="x", padx=16, pady=(0, 14))

        categories = ["All", "Computer", "Phone", "Server", "Google Drive"]
        for cat in categories:
            btn = ctk.CTkButton(
                filters_row,
                text=cat,
                font=theme.font(11, "bold" if cat == "All" else "normal"),
                fg_color=theme.SIDEBAR_BG if cat == "All" else theme.CARD_BG,
                hover_color=theme.SIDEBAR_HOVER if cat == "All" else theme.CARD_HOVER,
                text_color="#FFFFFF" if cat == "All" else theme.TEXT_SECONDARY,
                border_width=0 if cat == "All" else 1,
                border_color=theme.CARD_BORDER,
                corner_radius=theme.RADIUS_CARD,
                height=28,
                command=lambda c=cat: self._set_filter(c),
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[cat] = btn

        # 4. Results Container
        self.results_container = ctk.CTkFrame(self, fg_color="transparent")
        self.results_container.pack(fill="x", padx=16, pady=(0, 20))

        self._render_files()

    def _set_filter(self, category: str):
        self.selected_filter = category
        for cat, btn in self.filter_buttons.items():
            if cat == category:
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
        self._render_files()

    def _render_files(self):
        for child in self.results_container.winfo_children():
            child.destroy()

        query = self.search_entry.get().strip().lower()
        files = store.files

        # Apply source filter
        if self.selected_filter != "All":
            files = [f for f in files if f.get("source") == self.selected_filter]

        # Apply query search
        if query:
            files = [f for f in files if query in f.get("name", "").lower() or query in f.get("folder", "").lower()]

        if not files:
            empty_box = ctk.CTkFrame(self.results_container, fg_color=theme.CARD_BG, corner_radius=theme.RADIUS_CARD)
            empty_box.pack(fill="x", pady=20, padx=4)
            ctk.CTkLabel(
                empty_box,
                text="No matching files found.\nAsk VAVE to search for something else.",
                font=theme.font(12),
                text_color=theme.TEXT_MUTED,
                pady=30,
            ).pack()
            return

        for file_item in files:
            card = ctk.CTkFrame(
                self.results_container,
                fg_color=theme.CARD_BG,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=theme.RADIUS_CARD,
            )
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            name = file_item.get("name", "")
            extension = name.rsplit(".", 1)[-1].upper() if "." in name else "FILE"
            ctk.CTkLabel(
                row,
                text=extension[:4],
                font=theme.font(theme.SIZE_LABEL, "bold"),
                text_color=theme.TEXT_SECONDARY,
                fg_color=theme.SURFACE_SUBTLE,
                corner_radius=theme.RADIUS_CHIP,
                width=40,
                height=40,
            ).pack(side="left", padx=(0, 14))

            info_col = ctk.CTkFrame(row, fg_color="transparent")
            info_col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(
                info_col,
                text=file_item.get("name", ""),
                font=theme.font(13, "bold"),
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
            ).pack(anchor="w")

            meta_text = f"{file_item.get('source')} · {file_item.get('folder')} · Modified {file_item.get('modified')} ({file_item.get('size')})"
            ctk.CTkLabel(
                info_col,
                text=meta_text,
                font=theme.font(11),
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

            # Action buttons
            actions_col = ctk.CTkFrame(row, fg_color="transparent")
            actions_col.pack(side="right")

            ctk.CTkButton(
                actions_col,
                text="Send to Phone",
                font=theme.font(11),
                fg_color=theme.MAIN_BG,
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_PRIMARY,
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=theme.RADIUS_CONTROL,
                width=96,
                height=28,
                command=lambda f=file_item: store.add_system_log(f"Sent {f.get('name')} to your phone", "completed"),
            ).pack(side="right", padx=(6, 0))

            ctk.CTkButton(
                actions_col,
                text="Open",
                font=theme.font(11, "bold"),
                fg_color=theme.ACCENT,
                hover_color=theme.ACCENT_HOVER,
                text_color="#FFFFFF",
                corner_radius=theme.RADIUS_CONTROL,
                width=54,
                height=28,
                command=lambda f=file_item: store.open_drawer("file", f),
            ).pack(side="right")

            card.bind("<Button-1>", lambda e, f=file_item: store.open_drawer("file", f))
            info_col.bind("<Button-1>", lambda e, f=file_item: store.open_drawer("file", f))
