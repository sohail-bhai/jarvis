import datetime
from gui import theme

class HistoryPanel:
    def __init__(self, ctk, parent, max_lines=1000):
        self.max_lines = max_lines
        self.frame = ctk.CTkFrame(
            parent,
            fg_color=theme.SURFACE,
            border_color=theme.BORDER,
            border_width=1,
            corner_radius=8,
        )

        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        header_frame.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            header_frame,
            text="Activity Log",
            font=theme.font(16, "bold"),
            text_color=theme.TEXT,
            anchor="w",
        )
        self.label.grid(row=0, column=0, sticky="ew")

        self.clear_btn = ctk.CTkButton(
            header_frame,
            text="Clear",
            width=60,
            height=24,
            font=theme.font(11),
            fg_color=theme.SURFACE_ALT,
            text_color=theme.TEXT_MUTED,
            hover_color=theme.BORDER,
            command=self.clear
        )
        self.clear_btn.grid(row=0, column=1, sticky="e")

        self.textbox = ctk.CTkTextbox(
            self.frame,
            fg_color=theme.SURFACE_ALT,
            border_color=theme.BORDER,
            border_width=1,
            text_color=theme.TEXT,
            font=theme.font(12),
            wrap="word",
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        
        self.textbox.tag_config("time", foreground=theme.TEXT_MUTED)
        self.textbox.tag_config("INFO", foreground=theme.SUCCESS)
        self.textbox.tag_config("WARNING", foreground=theme.WARNING)
        self.textbox.tag_config("ERROR", foreground=theme.ERROR)
        self.textbox.tag_config("TOOL", foreground=theme.ACCENT)
        self.textbox.tag_config("USER", foreground=theme.TEXT)
        self.textbox.tag_config("SYS", foreground=theme.TEXT_MUTED)

        self.textbox.configure(state="disabled")

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

    def add_entry(self, level, message):
        self.textbox.configure(state="normal")
        
        lines = int(self.textbox.index('end-1c').split('.')[0])
        if lines > self.max_lines:
            self.textbox.delete("1.0", f"{lines - self.max_lines}.0")
            
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        self.textbox.insert("end", f"[{timestamp}] ", "time")
        self.textbox.insert("end", f"[{level}] ", level)
        self.textbox.insert("end", f"{message}\n")
        
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
        
    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
