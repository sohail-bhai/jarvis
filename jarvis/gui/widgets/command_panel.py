from gui import theme

class CommandPanel:
    def __init__(self, ctk, parent, on_send):
        self.frame = ctk.CTkFrame(
            parent,
            fg_color="transparent", # Make frame transparent so the pill stands out
            corner_radius=0,
        )
        self._on_send = on_send

        # The pill container
        self.pill = ctk.CTkFrame(
            self.frame,
            fg_color=theme.SURFACE_ALT,
            border_color=theme.BORDER,
            border_width=1,
            corner_radius=25,
        )
        self.pill.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.pill.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self.pill,
            placeholder_text="Type a command or ask anything...",
            height=50,
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT,
            font=theme.font(14)
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(20, 10), pady=0)
        self.entry.bind("<Return>", self._handle_return)

        self.send_button = ctk.CTkButton(
            self.pill,
            text="➤",
            width=50,
            height=50,
            corner_radius=25,
            fg_color="transparent",
            hover_color=theme.SURFACE,
            text_color=theme.TEXT_MUTED,
            font=theme.font(18, "bold"),
            command=self.submit,
        )
        self.send_button.grid(row=0, column=1, sticky="e", padx=(0, 5), pady=0)

        self.frame.grid_columnconfigure(0, weight=1)

    def _handle_return(self, _event):
        self.submit()

    def submit(self):
        command_text = self.entry.get().strip()

        if not command_text:
            return

        self._on_send(command_text)

    def clear(self):
        self.entry.delete(0, "end")

    def set_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.entry.configure(state=state)
        self.send_button.configure(state=state)
