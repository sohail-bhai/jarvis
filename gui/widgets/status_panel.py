from gui import theme


class StatusPanel:
    def __init__(self, ctk, parent):
        self.frame = ctk.CTkFrame(
            parent,
            fg_color=theme.SURFACE,
            border_color=theme.BORDER,
            border_width=1,
            corner_radius=8,
        )

        self.title = ctk.CTkLabel(
            self.frame,
            text="System Status",
            font=theme.font(16, "bold"),
            text_color=theme.TEXT,
            anchor="w",
        )
        self.title.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))

        self.state_label = ctk.CTkLabel(
            self.frame,
            text="IDLE",
            font=theme.font(32, "bold"),
            text_color=theme.ACCENT,
            anchor="w",
        )
        self.state_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 4))

        self.status_label = ctk.CTkLabel(
            self.frame,
            text="Ready",
            font=theme.font(14),
            text_color=theme.TEXT_MUTED,
            anchor="w",
            wraplength=420,
        )
        self.status_label.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))

        self.frame.grid_columnconfigure(0, weight=1)

    def set_state(self, state):
        self.state_label.configure(text=str(state).upper())

    def set_status(self, message):
        self.status_label.configure(text=message or "Ready")
