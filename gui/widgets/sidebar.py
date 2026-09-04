"""
Sidebar component for the VAVE desktop interface.

Navigation on a dark surface: one line icon and one short label per row. The
selected row is filled and its icon takes the accent, so the current page is
readable at a glance without a second cue.
"""
from __future__ import annotations

import customtkinter as ctk
from gui import icons, theme
from gui.store import store


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate, on_voice_toggle):
        super().__init__(
            parent,
            width=230,
            fg_color=theme.SIDEBAR_BG,
            corner_radius=0,
        )
        self.grid_propagate(False)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.on_voice_toggle = on_voice_toggle
        self.nav_buttons = {}

        # 1. Brand Section
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(6, 24))

        mark_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        mark_row.pack(anchor="w")

        # A small accent mark beside the wordmark: the only piece of colour in
        # the sidebar that is not tied to state.
        self.brand_icon = icons.image("sparkle", 15, theme.SIDEBAR_ACCENT)
        if self.brand_icon is not None:
            ctk.CTkLabel(
                mark_row,
                text="",
                image=self.brand_icon,
                width=18,
            ).pack(side="left", padx=(0, 7))

        title_lbl = ctk.CTkLabel(
            mark_row,
            text="VAVE",
            font=theme.font(18, "bold"),
            text_color=theme.SIDEBAR_TEXT,
            anchor="w",
        )
        title_lbl.pack(side="left")

        tagline_lbl = ctk.CTkLabel(
            brand_frame,
            text="Your AI, Everywhere",
            font=theme.font(11),
            text_color=theme.SIDEBAR_TEXT_MUTED,
            anchor="w",
        )
        tagline_lbl.pack(anchor="w", pady=(2, 0))

        # 3. Navigation Items
        # Grouped, because seven equal rows give the eye nothing to hold on
        # to. The first group is what you own, the second is what VAVE reaches
        # on your behalf, the third is the record and the controls.
        self.nav_groups = [
            ("", [("home", "Home", "home")]),
            ("YOURS", [("devices", "My Devices", "devices"),
                       ("files", "My Files", "files")]),
            ("REACHES", [("google", "Google", "google"),
                         ("web", "Web", "globe")]),
            ("", [("activity", "Activity", "activity"),
                  ("settings", "Settings", "settings")]),
        ]

        self.nav_items = [item for _, group in self.nav_groups for item in group]

        # Two renderings of each glyph: muted when the row is idle, accent when
        # it is selected. Held on self so Tk does not drop the images.
        self.nav_icons = {
            key: (icons.image(glyph, theme.ICON_NAV, theme.SIDEBAR_TEXT_MUTED),
                  icons.image(glyph, theme.ICON_NAV, theme.SIDEBAR_ACCENT))
            for key, _, glyph in self.nav_items
        }

        self.nav_container = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_container.pack(fill="x", padx=12, expand=True, anchor="n")

        for group_label, group in self.nav_groups:
            if group_label:
                ctk.CTkLabel(
                    self.nav_container,
                    text=f"  {group_label}",
                    font=theme.label_font(),
                    text_color=theme.SIDEBAR_LABEL,
                    anchor="w",
                ).pack(fill="x", pady=(14, 5))
            else:
                ctk.CTkFrame(self.nav_container, fg_color="transparent",
                             height=8).pack(fill="x")

            self._build_group(group)

        # 4. Bottom status line
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=18)

        status_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        status_row.pack(fill="x")

        self.dot_label = ctk.CTkLabel(
            status_row,
            text="●",
            font=theme.font(11, "bold"),
            text_color=theme.SUCCESS,
        )
        self.dot_label.pack(side="left")

        self.status_title = ctk.CTkLabel(
            status_row,
            text="  VAVE Online",
            font=theme.font(12, "bold"),
            text_color=theme.SIDEBAR_TEXT,
        )
        self.status_title.pack(side="left")

        self.status_sub = ctk.CTkLabel(
            bottom_frame,
            text="All systems running",
            font=theme.font(10),
            text_color=theme.SIDEBAR_TEXT_MUTED,
            anchor="w",
        )
        self.status_sub.pack(fill="x", pady=(3, 0))


    def _build_group(self, group):
        """Pack one group's rows into the shared nav container."""
        for page_id, label, _ in group:
            selected = page_id == "home"
            idle_icon, active_icon = self.nav_icons[page_id]
            btn = ctk.CTkButton(
                self.nav_container,
                text=f"  {label}",
                image=active_icon if selected else idle_icon,
                compound="left",
                font=theme.font(13, "bold" if selected else "normal"),
                fg_color=theme.SIDEBAR_ACTIVE if selected else "transparent",
                text_color=theme.SIDEBAR_TEXT if selected else theme.SIDEBAR_TEXT_MUTED,
                hover_color=theme.SIDEBAR_HOVER,
                corner_radius=theme.RADIUS_CONTROL,
                height=38,
                anchor="w",
                command=lambda pid=page_id: self._select_page(pid),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[page_id] = btn

    def _select_page(self, page_id: str):
        self.highlight(page_id)
        self.on_navigate(page_id)

    def highlight(self, page_id: str):
        """Mark one row as current, without navigating anywhere."""
        for pid, btn in self.nav_buttons.items():
            idle_icon, active_icon = self.nav_icons[pid]
            if pid == page_id:
                btn.configure(
                    fg_color=theme.SIDEBAR_ACTIVE,
                    font=theme.font(13, "bold"),
                    text_color=theme.SIDEBAR_TEXT,
                    image=active_icon,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    font=theme.font(13, "normal"),
                    text_color=theme.SIDEBAR_TEXT_MUTED,
                    image=idle_icon,
                )

    def _toggle_voice(self):
        self.on_voice_toggle()

    def update_voice_state(self, is_listening: bool):
        if is_listening:
            self.status_sub.configure(text="Listening for voice...")
        else:
            self.status_sub.configure(text="All systems running")
