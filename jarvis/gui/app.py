import logging
logger = logging.getLogger(__name__)

import io
import threading
import datetime
import traceback
from contextlib import redirect_stdout

import customtkinter as ctk

from assistant.controller import AssistantController
from assistant.events import (
    EVENT_ASSISTANT_RESPONSE,
    EVENT_ERROR,
    EVENT_RECOGNIZED_TEXT,
    EVENT_STATE_CHANGED,
    EVENT_STATUS,
    EVENT_LOG,
    EVENT_AUDIT,
    EVENT_TOOL_CALL,
    EVENT_OVERWATCH_CANDIDATE,
    EVENT_OVERWATCH_ACTION,
    EVENT_OVERWATCH_STATE,
    EVENT_CONFIRMATION_REQUEST,
    EventBus,
    set_global_event_bus
)
from assistant import logging_setup
from assistant.smoke_test import run_smoke_tests
from gui import theme


class JarvisDashboardApp(ctk.CTk):
    def __init__(self):
        theme.configure_theme(ctk)
        super().__init__()

        self.title("JARVIS Desktop Assistant")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=theme.BACKGROUND)

        self.event_bus = EventBus(maxsize=2000)
        set_global_event_bus(self.event_bus)
        logging_setup.configure_logging(event_bus=self.event_bus)
        
        from assistant import audit, guard, confirm, overwatch
        from pathlib import Path
        audit.configure(Path("logs/audit.jsonl"), max_bytes=5_000_000, backup_count=20)
        guard.configure(event_bus=self.event_bus)
        confirm.configure(event_bus=self.event_bus)
        overwatch.configure(event_bus=self.event_bus)

        self.controller = AssistantController(
            event_bus=self.event_bus,
            speech_enabled=True,
        )
        self.listener_thread = None
        self.text_thread = None
        self.listening_active = False

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_events)

    def _build_layout(self):
        # 3 Column Layout: Left Nav (220px) | Center Content (Flex) | Right System Log (320px)
        self.grid_columnconfigure(0, minsize=220, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, minsize=320, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # =========================================================
        # 1. LEFT SIDEBAR (DARK NAVY #111827)
        # =========================================================
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=theme.SIDEBAR_BG, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Header Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 25), padx=20)
        
        logo_title = ctk.CTkLabel(logo_frame, text="JARVIS", font=theme.font(20, "bold"), text_color=theme.SIDEBAR_TEXT)
        logo_title.pack(anchor="w")
        
        logo_sub = ctk.CTkLabel(logo_frame, text="Your AI, Everywhere", font=theme.font(11), text_color=theme.SIDEBAR_TEXT_MUTED)
        logo_sub.pack(anchor="w")

        # Navigation Items matching reference image
        nav_items = [
            ("🏠", "Home", True),
            ("💻", "My Devices", False),
            ("📁", "My Files", False),
            ("G", "Google", False),
            ("🌐", "Web", False),
            ("⏱", "Activity", False),
            ("⚙", "Settings", False),
        ]

        for icon, label, is_active in nav_items:
            btn_color = theme.SIDEBAR_CARD if is_active else "transparent"
            txt_color = theme.SIDEBAR_TEXT if is_active else theme.SIDEBAR_TEXT_MUTED
            
            nav_btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}   {label}",
                font=theme.font(13, "bold" if is_active else "normal"),
                fg_color=btn_color,
                text_color=txt_color,
                hover_color=theme.SIDEBAR_CARD,
                anchor="w",
                height=38,
                corner_radius=8,
                command=lambda l=label: self._on_nav_click(l)
            )
            nav_btn.pack(fill="x", padx=15, pady=3)

        # Bottom Status Card
        status_card = ctk.CTkFrame(self.sidebar, fg_color=theme.SIDEBAR_CARD, corner_radius=12)
        status_card.pack(side="bottom", fill="x", padx=15, pady=20)
        
        status_lbl = ctk.CTkLabel(
            status_card, 
            text="● JARVIS Online", 
            font=theme.font(12, "bold"), 
            text_color=theme.SUCCESS
        )
        status_lbl.pack(anchor="w", padx=15, pady=(12, 2))
        
        status_sub = ctk.CTkLabel(
            status_card, 
            text="All systems running", 
            font=theme.font(11), 
            text_color=theme.SIDEBAR_TEXT_MUTED
        )
        status_sub.pack(anchor="w", padx=15, pady=(0, 12))

        # =========================================================
        # 2. CENTER CANVAS (LIGHT BACKGROUND #F3F5F9)
        # =========================================================
        self.canvas_scroll = ctk.CTkScrollableFrame(self, fg_color=theme.BACKGROUND, corner_radius=0)
        self.canvas_scroll.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        # Top Bar (Heading | Search Bar | Notifications | Avatar)
        top_bar = ctk.CTkFrame(self.canvas_scroll, fg_color="transparent")
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        home_title = ctk.CTkLabel(top_bar, text="Home", font=theme.font(18, "bold"), text_color=theme.TEXT)
        home_title.pack(side="left")

        # Top Search Input matching image
        search_frame = ctk.CTkFrame(top_bar, fg_color=theme.SURFACE, border_color=theme.BORDER, border_width=1, corner_radius=20, height=36)
        search_frame.pack(side="left", padx=20, expand=True, fill="x")

        search_icon = ctk.CTkLabel(search_frame, text="✦", font=theme.font(12), text_color=theme.ACCENT)
        search_icon.pack(side="left", padx=(15, 5))

        self.top_search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Ask JARVIS anything...", 
            font=theme.font(12), 
            fg_color="transparent", 
            border_width=0,
            text_color=theme.TEXT
        )
        self.top_search_entry.pack(side="left", fill="x", expand=True)
        self.top_search_entry.bind("<Return>", lambda e: self.submit_command(self.top_search_entry.get()))

        shortcut_pill = ctk.CTkLabel(search_frame, text="⌘K / Ctrl+K", font=theme.font(10), text_color=theme.TEXT_MUTED, fg_color=theme.BACKGROUND, corner_radius=6)
        shortcut_pill.pack(side="right", padx=(5, 12), pady=4)

        # Notification Bell & Profile Avatar
        notif_btn = ctk.CTkButton(top_bar, text="🔔 1", width=42, height=36, fg_color=theme.SURFACE, text_color=theme.TEXT, border_color=theme.BORDER, border_width=1, corner_radius=18)
        notif_btn.pack(side="right", padx=(10, 0))

        avatar = ctk.CTkLabel(top_bar, text="R", width=36, height=36, fg_color=theme.ACCENT, text_color="#FFFFFF", font=theme.font(14, "bold"), corner_radius=18)
        avatar.pack(side="right")

        # Greeting Banner
        greeting_frame = ctk.CTkFrame(self.canvas_scroll, fg_color="transparent")
        greeting_frame.pack(fill="x", padx=25, pady=(15, 10))

        time_of_day = "evening" if datetime.datetime.now().hour >= 17 else "afternoon" if datetime.datetime.now().hour >= 12 else "morning"
        greet_sub = ctk.CTkLabel(greeting_frame, text=f"☀️ Good {time_of_day},", font=theme.font(13), text_color=theme.TEXT_MUTED)
        greet_sub.pack(anchor="w")

        greet_heading = ctk.CTkLabel(greeting_frame, text="How can I help you today?", font=theme.font(24, "bold"), text_color=theme.TEXT)
        greet_heading.pack(anchor="w", pady=(2, 0))

        date_str = datetime.datetime.now().strftime("%a, %d %b %Y")
        date_tag = ctk.CTkLabel(greeting_frame, text=date_str, font=theme.font(11), text_color=theme.TEXT_MUTED, fg_color=theme.SURFACE, corner_radius=8)
        date_tag.place(relx=1.0, rely=0.3, anchor="e")

        # Main Input Card matching reference image
        input_card = ctk.CTkFrame(self.canvas_scroll, fg_color=theme.SURFACE, border_color=theme.BORDER, border_width=1, corner_radius=16)
        input_card.pack(fill="x", padx=25, pady=(5, 15))

        prompt_icon = ctk.CTkLabel(input_card, text="✦", font=theme.font(16), text_color=theme.ACCENT)
        prompt_icon.pack(side="left", padx=(20, 10), pady=18)

        self.main_cmd_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="Tell me what you want to do...",
            font=theme.font(14),
            fg_color="transparent",
            border_width=0,
            text_color=theme.TEXT
        )
        self.main_cmd_entry.pack(side="left", fill="x", expand=True, pady=18)
        self.main_cmd_entry.bind("<Return>", lambda e: self.submit_command(self.main_cmd_entry.get()))

        # Send Button & Mic Button
        send_btn = ctk.CTkButton(
            input_card, 
            text="↑", 
            width=36, 
            height=36, 
            fg_color=theme.TEXT, 
            text_color="#FFFFFF", 
            font=theme.font(16, "bold"), 
            corner_radius=18,
            command=lambda: self.submit_command(self.main_cmd_entry.get())
        )
        send_btn.pack(side="right", padx=(5, 15))

        self.mic_btn = ctk.CTkButton(
            input_card, 
            text="🎙", 
            width=36, 
            height=36, 
            fg_color=theme.SURFACE_ALT, 
            text_color=theme.TEXT, 
            font=theme.font(16), 
            corner_radius=18,
            command=self.toggle_voice
        )
        self.mic_btn.pack(side="right", padx=(5, 5))

        # Suggestion Chips Row
        chips_frame = ctk.CTkFrame(self.canvas_scroll, fg_color="transparent")
        chips_frame.pack(fill="x", padx=25, pady=(0, 15))

        chips_lbl = ctk.CTkLabel(chips_frame, text="Try something like:", font=theme.font(11), text_color=theme.TEXT_MUTED)
        chips_lbl.pack(side="left", padx=(0, 10))

        suggestions = [
            ("📄", "Find my presentation"),
            ("▷", "Continue my project"),
            ("🔍", "Research something"),
            ("✉", "Summarize my emails")
        ]

        for icon, text in suggestions:
            chip = ctk.CTkButton(
                chips_frame,
                text=f"{icon}  {text}",
                font=theme.font(11),
                fg_color=theme.SURFACE,
                text_color=theme.TEXT,
                border_color=theme.BORDER,
                border_width=1,
                corner_radius=14,
                height=28,
                command=lambda t=text: self.submit_command(t)
            )
            chip.pack(side="left", padx=4)

        # Environment Connection Status Row (4 Colored Cards matching reference image)
        env_row = ctk.CTkFrame(self.canvas_scroll, fg_color="transparent")
        env_row.pack(fill="x", padx=25, pady=(0, 15))
        env_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="env")

        env_cards = [
            ("💻", "My Computer", "● Online", "#EBF2FC", theme.ACCENT),
            ("📱", "My Phone", "● Connected", "#EDF7F0", theme.SUCCESS),
            ("📁", "Google Drive", "● Connected", "#FEF6E8", theme.WARNING),
            ("🌐", "Internet", "● Ready", "#F3EEFA", "#8B5CF6"),
        ]

        for i, (icon, title, status, bg_col, dot_col) in enumerate(env_cards):
            card = ctk.CTkFrame(env_row, fg_color=bg_col, corner_radius=12, border_color=theme.BORDER, border_width=1)
            card.grid(row=0, column=i, sticky="nsew", padx=4)
            
            lbl_icon = ctk.CTkLabel(card, text=icon, font=theme.font(20))
            lbl_icon.pack(anchor="w", padx=12, pady=(10, 2))
            
            lbl_title = ctk.CTkLabel(card, text=title, font=theme.font(12, "bold"), text_color=theme.TEXT)
            lbl_title.pack(anchor="w", padx=12)
            
            lbl_status = ctk.CTkLabel(card, text=status, font=theme.font(10), text_color=dot_col)
            lbl_status.pack(anchor="w", padx=12, pady=(0, 10))

        # Current Task Card (Matching reference image)
        task_card = ctk.CTkFrame(self.canvas_scroll, fg_color=theme.SURFACE, corner_radius=16, border_color=theme.BORDER, border_width=1)
        task_card.pack(fill="x", padx=25, pady=(0, 15))

        task_header = ctk.CTkFrame(task_card, fg_color="transparent")
        task_header.pack(fill="x", padx=20, pady=(15, 5))

        task_hdr_lbl = ctk.CTkLabel(task_header, text="🔄  Current Task", font=theme.font(12, "bold"), text_color=theme.ACCENT)
        task_hdr_lbl.pack(side="left")

        view_details_btn = ctk.CTkButton(
            task_header, 
            text="View Details", 
            font=theme.font(11), 
            fg_color=theme.SURFACE_ALT, 
            text_color=theme.TEXT, 
            height=26, 
            corner_radius=13,
            command=lambda: self.submit_command("show task details")
        )
        view_details_btn.pack(side="right")

        self.task_title_lbl = ctk.CTkLabel(task_card, text="Preparing your project", font=theme.font(16, "bold"), text_color=theme.TEXT)
        self.task_title_lbl.pack(anchor="w", padx=20, pady=(5, 2))

        self.task_desc_lbl = ctk.CTkLabel(
            task_card, 
            text="JARVIS is researching, organizing files and writing a draft for you.", 
            font=theme.font(12), 
            text_color=theme.TEXT_MUTED
        )
        self.task_desc_lbl.pack(anchor="w", padx=20, pady=(0, 15))

        # Timeline step pills
        steps_frame = ctk.CTkFrame(task_card, fg_color="transparent")
        steps_frame.pack(fill="x", padx=20, pady=(0, 18))

        steps = [
            ("✓ 1. Finding relevant files", theme.SUCCESS, "#EDF7F0"),
            ("● 2. Researching on the web", theme.ACCENT, theme.ACCENT_MUTED),
            ("○ 3. Writing draft", theme.TEXT_MUTED, theme.SURFACE_ALT),
            ("○ 4. Finalizing", theme.TEXT_MUTED, theme.SURFACE_ALT),
        ]

        for st_text, st_col, st_bg in steps:
            st_pill = ctk.CTkLabel(
                steps_frame,
                text=st_text,
                font=theme.font(11, "bold" if st_col != theme.TEXT_MUTED else "normal"),
                text_color=st_col,
                fg_color=st_bg,
                corner_radius=12,
                padx=10,
                pady=4
            )
            st_pill.pack(side="left", padx=3)

        # Quick Access Category Navigation Row (3 Columns)
        cats_row = ctk.CTkFrame(self.canvas_scroll, fg_color="transparent")
        cats_row.pack(fill="x", padx=25, pady=(0, 15))
        cats_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="cats")

        categories = [
            ("📁", "My Files >", "Find and access your files from any device", "find files"),
            ("G", "Google >", "Search your Drive, Gmail, Calendar and more", "check google workspace"),
            ("🌐", "Web >", "Ask JARVIS to search the internet or do online tasks", "search web"),
        ]

        for i, (icon, title, desc, cmd) in enumerate(categories):
            card = ctk.CTkFrame(cats_row, fg_color=theme.SURFACE, corner_radius=14, border_color=theme.BORDER, border_width=1)
            card.grid(row=0, column=i, sticky="nsew", padx=4)
            
            lbl_icon = ctk.CTkLabel(card, text=icon, font=theme.font(18))
            lbl_icon.pack(anchor="w", padx=15, pady=(12, 2))
            
            lbl_title = ctk.CTkLabel(card, text=title, font=theme.font(13, "bold"), text_color=theme.TEXT)
            lbl_title.pack(anchor="w", padx=15)
            
            lbl_desc = ctk.CTkLabel(card, text=desc, font=theme.font(10), text_color=theme.TEXT_MUTED, wraplength=180, justify="left")
            lbl_desc.pack(anchor="w", padx=15, pady=(2, 12))

        # Natural Language Tip Banner
        tip_box = ctk.CTkFrame(self.canvas_scroll, fg_color="#EBF2FC", corner_radius=14, border_color="#D0E2FF", border_width=1)
        tip_box.pack(fill="x", padx=25, pady=(0, 25))

        tip_title = ctk.CTkLabel(tip_box, text="✦ You can just ask in normal language.", font=theme.font(12, "bold"), text_color=theme.ACCENT)
        tip_title.pack(anchor="w", padx=18, pady=(12, 4))

        tip_samples = ctk.CTkLabel(
            tip_box, 
            text='"Send this file to my phone"   "Find my last email from college"   "Open my project folder"',
            font=theme.font(11), 
            text_color=theme.TEXT
        )
        tip_samples.pack(anchor="w", padx=18, pady=(0, 12))

        tip_sub = ctk.CTkLabel(tip_box, text="JARVIS understands. No technical knowledge needed.", font=theme.font(10), text_color=theme.TEXT_MUTED)
        tip_sub.place(relx=0.98, rely=0.5, anchor="e")

        # =========================================================
        # 3. RIGHT SIDEBAR / SYSTEM LOG (WHITE CARD #FFFFFF)
        # =========================================================
        self.right_panel = ctk.CTkFrame(self, width=320, fg_color=theme.SURFACE, corner_radius=0, border_color=theme.BORDER, border_width=1)
        self.right_panel.grid(row=0, column=2, sticky="nsew")
        self.right_panel.grid_propagate(False)

        # Header
        log_hdr = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        log_hdr.pack(fill="x", padx=20, pady=(20, 10))

        log_title = ctk.CTkLabel(log_hdr, text="System Log", font=theme.font(16, "bold"), text_color=theme.TEXT)
        log_title.pack(side="left")

        live_badge = ctk.CTkLabel(log_hdr, text="● Live", font=theme.font(11, "bold"), text_color=theme.SUCCESS, fg_color="#EDF7F0", corner_radius=10, padx=8, pady=2)
        live_badge.pack(side="right")

        # Scrollable Log Feed Container
        self.log_scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.log_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # Initial seed timeline entries matching reference image
        self.log_entries = [
            ("3:24 PM", "Searching your files for 'Hackwave presentation'", theme.ACCENT),
            ("3:24 PM", "Found 3 documents on your computer", theme.ACCENT),
            ("3:25 PM", "Also checking Google Drive", theme.ACCENT),
            ("3:25 PM", "Downloaded the latest version", theme.SUCCESS),
            ("3:26 PM", "Researching latest competitors online", theme.ACCENT),
            ("3:27 PM", "Reading and summarizing information", theme.ACCENT),
            ("3:28 PM", "Writing a draft for your presentation", theme.WARNING),
            ("3:28 PM", "Waiting for next step...", theme.TEXT_MUTED),
        ]

        for time_str, text, color in self.log_entries:
            self._add_log_ui_row(time_str, text, color)

        # Footer Banner matching reference image
        bg_banner = ctk.CTkFrame(self.right_panel, fg_color=theme.BACKGROUND, corner_radius=12, border_color=theme.BORDER, border_width=1)
        bg_banner.pack(fill="x", padx=15, pady=15, side="bottom")

        banner_title = ctk.CTkLabel(bg_banner, text="💡  JARVIS is working in the background.", font=theme.font(11, "bold"), text_color=theme.TEXT)
        banner_title.pack(anchor="w", padx=12, pady=(10, 2))

        banner_sub = ctk.CTkLabel(bg_banner, text="You can continue using your computer.", font=theme.font(10), text_color=theme.TEXT_MUTED)
        banner_sub.pack(anchor="w", padx=12, pady=(0, 10))

    def _add_log_ui_row(self, time_str, text, color):
        row = ctk.CTkFrame(self.log_scroll, fg_color="transparent")
        row.pack(fill="x", pady=4, padx=5)

        t_lbl = ctk.CTkLabel(row, text=time_str, font=theme.font(10), text_color=theme.TEXT_MUTED, width=50, anchor="e")
        t_lbl.pack(side="left", padx=(0, 8))

        dot_lbl = ctk.CTkLabel(row, text="●", font=theme.font(10), text_color=color, width=12)
        dot_lbl.pack(side="left", padx=(0, 5))

        txt_lbl = ctk.CTkLabel(row, text=text, font=theme.font(11), text_color=theme.TEXT, anchor="w", wraplength=200, justify="left")
        txt_lbl.pack(side="left", fill="x", expand=True)

    def _on_nav_click(self, label):
        self.add_log_entry(f"Navigated to {label}")
        if label == "My Devices":
            self.controller.handle_text_command("check my devices")
        elif label == "My Files":
            self.controller.handle_text_command("find my files")
        elif label == "Google":
            self.controller.handle_text_command("check google workspace")
        elif label == "Web":
            self.controller.handle_text_command("search web")
        elif label == "Activity":
            self.controller.handle_text_command("show activity history")

    def submit_command(self, cmd_text):
        if not cmd_text or not cmd_text.strip():
            return
        
        clean_cmd = cmd_text.strip()
        self.main_cmd_entry.delete(0, "end")
        self.top_search_entry.delete(0, "end")
        
        time_str = datetime.datetime.now().strftime("%I:%M %p")
        self._add_log_ui_row(time_str, f"User: {clean_cmd}", theme.ACCENT)
        self.task_title_lbl.configure(text=f"Executing: {clean_cmd[:30]}...")
        self.task_desc_lbl.configure(text=f"JARVIS is processing '{clean_cmd}'...")
        
        self.text_thread = threading.Thread(
            target=self._run_cmd_worker,
            args=(clean_cmd,),
            daemon=True
        )
        self.text_thread.start()

    def _run_cmd_worker(self, cmd_text):
        try:
            self.controller.handle_text_command(cmd_text)
        except Exception as e:
            logger.error(f"Execution error: {e}")

    def toggle_voice(self):
        if self.listening_active:
            self.listening_active = False
            self.mic_btn.configure(fg_color=theme.SURFACE_ALT)
            self.controller.stop()
            self.add_log_entry("Voice listening stopped.")
        else:
            self.listening_active = True
            self.mic_btn.configure(fg_color=theme.ACCENT)
            self.add_log_entry("Voice listening started...")
            self.listener_thread = threading.Thread(target=self.controller.run_forever, daemon=True)
            self.listener_thread.start()

    def add_log_entry(self, text, color=theme.ACCENT):
        time_str = datetime.datetime.now().strftime("%I:%M %p")
        self._add_log_ui_row(time_str, text, color)

    def _poll_events(self):
        for event in self.event_bus.poll(max_events=100):
            self._handle_event(event)
        self.after(50, self._poll_events)

    def _handle_event(self, event):
        if event.event_type == EVENT_STATUS:
            self.add_log_entry(event.message, theme.TEXT_MUTED)
        elif event.event_type == EVENT_RECOGNIZED_TEXT:
            self.task_title_lbl.configure(text=f"Recognized: {event.message}")
        elif event.event_type == EVENT_ASSISTANT_RESPONSE:
            self.task_desc_lbl.configure(text=event.message)
            self.add_log_entry(f"JARVIS: {event.message}", theme.SUCCESS)
        elif event.event_type == EVENT_ERROR:
            self.add_log_entry(f"Error: {event.message}", theme.ERROR)
            self.task_desc_lbl.configure(text=f"Error: {event.message}")

    def _on_close(self):
        if self.listening_active:
            self.controller.stop()
        self.destroy()
