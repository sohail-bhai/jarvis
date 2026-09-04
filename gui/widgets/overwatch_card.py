from gui import theme
from assistant import overwatch

class OverwatchCard:
    def __init__(self, ctk, parent):
        self.frame = ctk.CTkFrame(
            parent,
            fg_color=theme.SURFACE,
            border_color=theme.BORDER,
            border_width=1,
            corner_radius=8,
        )

        self.label = ctk.CTkLabel(
            self.frame,
            text="Autonomous Overwatch",
            font=theme.font(14, "bold"),
            text_color=theme.TEXT,
            anchor="w",
        )
        self.label.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        
        self.status_label = ctk.CTkLabel(
            self.frame,
            text="Status: Stopped",
            font=theme.font(12),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))

        self.btn_start = ctk.CTkButton(
            self.frame,
            text="Start",
            width=60,
            fg_color=theme.SUCCESS,
            hover_color=theme.SUCCESS,
            command=self.start
        )
        self.btn_start.grid(row=0, column=1, rowspan=2, sticky="e", padx=(0, 18))
        
        self.btn_stop = ctk.CTkButton(
            self.frame,
            text="Stop",
            width=60,
            fg_color=theme.ERROR,
            hover_color=theme.ERROR,
            command=self.stop,
            state="disabled"
        )
        self.btn_stop.grid(row=0, column=2, rowspan=2, sticky="e", padx=(0, 18))
        
        self.frame.grid_columnconfigure(0, weight=1)

    def start(self):
        overwatch.start_overwatch()
        
    def stop(self):
        overwatch.stop_overwatch()
        
    def update_state(self, message):
        self.status_label.configure(text=message)
        if "activated" in message.lower() or "started" in message.lower():
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.status_label.configure(text_color=theme.SUCCESS)
        else:
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.status_label.configure(text_color=theme.TEXT_MUTED)
