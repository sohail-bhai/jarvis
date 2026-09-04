import logging
logger = logging.getLogger(__name__)

import io
import threading
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
    EventBus,
    set_global_event_bus
)
from assistant import logging_setup
from assistant.smoke_test import run_smoke_tests
from assistant.speech import is_speech_enabled, set_speech_enabled
from gui import theme
from gui.widgets.command_panel import CommandPanel
from gui.widgets.history_panel import HistoryPanel
from gui.widgets.overwatch_card import OverwatchCard
from gui.widgets.status_panel import StatusPanel


class JarvisDashboardApp(ctk.CTk):
    def __init__(self):
        theme.configure_theme(ctk)
        super().__init__()

        self.title("JARVIS Desktop Assistant")
        self.geometry("1000x650")
        self.minsize(850, 550)
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
        self.smoke_thread = None
        self.listening_active = False
        self.stopping_requested = False

        self._build_layout()
        self._set_listening_controls(active=False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_events)

    def _build_layout(self):
        self.grid_columnconfigure(0, minsize=240, weight=0) # Left Nav
        self.grid_columnconfigure(1, weight=1) # Center Orb
        self.grid_columnconfigure(2, minsize=280, weight=0) # Right Panel
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------
        # LEFT SIDEBAR
        # ---------------------------------------------------------
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=theme.BACKGROUND, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.sidebar.grid_propagate(False)

        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(10, 30), padx=15)
        
        # A mock hexagon icon
        logo_icon = ctk.CTkLabel(logo_frame, text="⬡", font=theme.font(28), text_color=theme.ACCENT)
        logo_icon.pack(side="left")
        
        logo_text = ctk.CTkLabel(logo_frame, text=" J A R V I S", font=theme.font(16, "bold"), text_color=theme.TEXT)
        logo_text.pack(side="left", padx=5)

        # Nav Menu Container (Looks like a rounded card)
        nav_card = ctk.CTkFrame(self.sidebar, fg_color=theme.SURFACE, corner_radius=15, border_width=1, border_color=theme.BORDER)
        nav_card.pack(fill="x", padx=10)

        def make_nav_button(parent, icon, title, subtitle, is_active=False):
            btn_frame = ctk.CTkFrame(parent, fg_color=theme.SURFACE_ALT if is_active else "transparent", corner_radius=10)
            btn_frame.pack(fill="x", padx=10, pady=5)
            
            # Icon
            lbl_icon = ctk.CTkLabel(btn_frame, text=icon, font=theme.font(20), text_color=theme.ACCENT if is_active else theme.TEXT_MUTED)
            lbl_icon.grid(row=0, column=0, rowspan=2, padx=(10, 15), pady=10)
            
            # Title
            lbl_title = ctk.CTkLabel(btn_frame, text=title, font=theme.font(12, "bold"), text_color=theme.TEXT)
            lbl_title.grid(row=0, column=1, sticky="w", pady=(8, 0))
            
            # Subtitle
            lbl_sub = ctk.CTkLabel(btn_frame, text=subtitle, font=theme.font(10), text_color=theme.TEXT_MUTED)
            lbl_sub.grid(row=1, column=1, sticky="w", pady=(0, 8))
            
            # If active, add a small left border indicator
            if is_active:
                indicator = ctk.CTkFrame(btn_frame, width=4, fg_color=theme.ACCENT, corner_radius=2)
                indicator.place(relx=0, rely=0.1, relheight=0.8)

        make_nav_button(nav_card, "🎙", "VOICE MODE", "Start a voice conversation", True)
        make_nav_button(nav_card, "💬", "CHAT", "Text based interaction")
        make_nav_button(nav_card, "💻", "CONTROL PC", "System control center")
        make_nav_button(nav_card, "🏠", "SMART HOME", "Manage your devices")
        make_nav_button(nav_card, "☁", "CLOUD DRIVE", "Access your files")
        make_nav_button(nav_card, "🎵", "MEDIA", "Music & video control")
        make_nav_button(nav_card, "⚙", "SETTINGS", "Preferences & tools")

        # Start/Stop overlay buttons (since we replaced the original ones)
        self.start_button = ctk.CTkButton(self.sidebar, text="START LISTENING", fg_color=theme.ACCENT_MUTED, hover_color=theme.ACCENT, command=self.start_listening)
        self.start_button.pack(fill="x", padx=10, pady=(20, 5))
        
        self.stop_button = ctk.CTkButton(self.sidebar, text="STOP LISTENING", fg_color=theme.SURFACE, hover_color=theme.BORDER, command=self.stop_listening)
        self.stop_button.pack(fill="x", padx=10)

        # Status at bottom
        self.sidebar_status = ctk.CTkLabel(self.sidebar, text="● JARVIS ONLINE\nAll systems operational", font=theme.font(11), text_color=theme.SUCCESS, justify="left")
        self.sidebar_status.pack(side="bottom", anchor="w", padx=15, pady=20)

        # ---------------------------------------------------------
        # CENTER AREA (ORB & WAVEFORM)
        # ---------------------------------------------------------
        self.main_area = ctk.CTkFrame(self, fg_color=theme.BACKGROUND, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        
        # Center container
        center_container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        center_container.place(relx=0.5, rely=0.45, anchor="center")

        from gui.widgets.hud_elements import GlowingOrb, AudioWaveform
        self.orb = GlowingOrb(center_container, size=350)
        self.orb.pack(pady=10)

        self.status_label = ctk.CTkLabel(center_container, text="Awaiting Command...", font=theme.font(24), text_color=theme.TEXT)
        self.status_label.pack()

        self.sub_status = ctk.CTkLabel(center_container, text="System is idle.", font=theme.font(14), text_color=theme.TEXT_MUTED)
        self.sub_status.pack(pady=(5, 20))

        self.waveform = AudioWaveform(center_container, width=300, height=40)
        self.waveform.pack()

        # We need the CommandPanel at the bottom
        bottom_container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        bottom_container.pack(side="bottom", fill="x", pady=20)
        
        self.command_panel = CommandPanel(ctk, bottom_container, self.submit_text_command)
        self.command_panel.frame.pack(fill="x", padx=50)

        class DummyStatus:
            def set_state(self, *args): pass
            def set_status(self, *args): pass
        self.status_panel = DummyStatus()
        self.command_card = {"value": self.sub_status} # Route recognized text to sub_status
        self.response_card = {"value": self.sub_status} # Route responses to sub_status


        # ---------------------------------------------------------
        # RIGHT SIDEBAR (LIVE PANELS)
        # ---------------------------------------------------------
        self.right_sidebar = ctk.CTkFrame(self, width=320, fg_color=theme.BACKGROUND, corner_radius=0)
        self.right_sidebar.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        self.right_sidebar.grid_propagate(False)

        # Overwatch Card
        self.overwatch_card = OverwatchCard(ctk, self.right_sidebar)
        self.overwatch_card.frame.pack(fill="x", pady=(10, 20))
        
        # Confirmation Card
        self.confirm_frame = ctk.CTkFrame(self.right_sidebar, fg_color=theme.SURFACE, border_color=theme.WARNING, border_width=1, corner_radius=8)
        self.confirm_label = ctk.CTkLabel(self.confirm_frame, text="Confirmation Required", font=theme.font(14, "bold"), text_color=theme.WARNING, wraplength=280)
        self.confirm_label.pack(pady=(10, 5), padx=10)
        
        btn_frame = ctk.CTkFrame(self.confirm_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 10))
        
        self.btn_yes = ctk.CTkButton(btn_frame, text="Yes", width=60, fg_color=theme.SUCCESS, hover_color=theme.SUCCESS, command=lambda: self.resolve_confirm(True))
        self.btn_yes.pack(side="left", padx=5)
        self.btn_no = ctk.CTkButton(btn_frame, text="No", width=60, fg_color=theme.ERROR, hover_color=theme.ERROR, command=lambda: self.resolve_confirm(False))
        self.btn_no.pack(side="left", padx=5)
        
        self.pending_confirmation_id = None
        
        # History Panel
        self.history_panel = HistoryPanel(ctk, self.right_sidebar, max_lines=5000)
        self.history_panel.frame.pack(fill="both", expand=True, pady=10)


    def _create_info_card(self, parent, title, initial_text):
        frame = ctk.CTkFrame(
            parent,
            fg_color=theme.SURFACE,
            border_color=theme.BORDER,
            border_width=1,
            corner_radius=8,
        )
        frame.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            frame,
            text=title,
            font=theme.font(14, "bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        label.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 4))

        value = ctk.CTkLabel(
            frame,
            text=initial_text,
            font=theme.font(20, "bold"),
            text_color=theme.TEXT,
            anchor="w",
            wraplength=330,
        )
        value.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))

        return {"frame": frame, "value": value}

    def start_listening(self):
        if self._listener_running():
            self._set_status("Already listening")
            return

        self.listening_active = True
        self.stopping_requested = False
        self._set_status("Starting...")
        self.status_label.configure(text="STARTING...")
        self._set_listening_controls(active=True)

        self.listener_thread = threading.Thread(
            target=self._run_voice_loop,
            name="JarvisVoiceLoop",
            daemon=True,
        )
        self.listener_thread.start()

    def _run_voice_loop(self):
        try:
            self.controller.run_forever(greet=True)
        except Exception as error:
            logger.info("GUI listener thread error:", error)
            traceback.print_exc()
            self.event_bus.emit(
                EVENT_ERROR,
                "Voice listener stopped because an error occurred.",
                error=str(error),
            )
        finally:
            self.event_bus.emit(EVENT_STATUS, "Voice listener stopped.")

    def stop_listening(self):
        if not self._listener_running():
            self._set_status("Listener is not running")
            self._set_listening_controls(active=False)
            return

        self.stopping_requested = True
        self._set_status("Stopping...")
        self.controller.stop()
        self.stop_button.configure(state="disabled")
        self.after(250, self._check_listener_stopped)

    def submit_text_command(self, command_text):
        if self._listener_running():
            self._set_status("Stop listening before sending text commands")
            return

        if self.text_thread is not None and self.text_thread.is_alive():
            self._set_status("Text command already processing")
            return

        self.command_panel.clear()
        self.command_panel.set_enabled(False)
        self.sub_status.configure(text=command_text)
        self._set_status("Processing...")

        self.text_thread = threading.Thread(
            target=self._run_text_command,
            args=(command_text,),
            name="JarvisTextCommand",
            daemon=True,
        )
        self.text_thread.start()
        self.after(150, self._check_text_finished)

    def _run_text_command(self, command_text):
        try:
            self.controller.handle_text_command(command_text)
        except Exception as error:
            logger.info("GUI text command error:", error)
            traceback.print_exc()
            self.event_bus.emit(
                EVENT_ERROR,
                "Text command failed.",
                error=str(error),
            )

    def run_smoke_test(self):
        if self._listener_running():
            self._set_status("Stop listening before running smoke tests")
            return

        if self.smoke_thread is not None and self.smoke_thread.is_alive():
            self._set_status("Smoke test already running")
            return

        self.smoke_button.configure(state="disabled")
        self._set_status("Running smoke test...")

        self.smoke_thread = threading.Thread(
            target=self._run_smoke_test_worker,
            name="JarvisSmokeTest",
            daemon=True,
        )
        self.smoke_thread.start()
        self.after(200, self._check_smoke_finished)

    def _run_smoke_test_worker(self):
        output = io.StringIO()

        try:
            with redirect_stdout(output):
                passed = run_smoke_tests()

            summary = "Smoke test passed." if passed else "Smoke test failed."
            logger.info(output.getvalue(), end="")
            self.event_bus.emit(EVENT_ASSISTANT_RESPONSE, summary, text=summary)
            self.event_bus.emit(EVENT_STATUS, summary)
        except Exception as error:
            logger.info("GUI smoke test error:", error)
            traceback.print_exc()
            self.event_bus.emit(
                EVENT_ERROR,
                "Smoke test failed unexpectedly.",
                error=str(error),
            )

    def _poll_events(self):
        for event in self.event_bus.poll(max_events=100):
            self._handle_event(event)

        self.after(50, self._poll_events)

    def _handle_event(self, event):
        if event.event_type == EVENT_STATE_CHANGED:
            state = event.payload.get("state", event.message)
            self.status_label.configure(text=state.upper() + "...")
            
            if state == "listening":
                self.waveform.set_listening(True)
            else:
                self.waveform.set_listening(False)

            if state == "stopped":
                self._set_listening_controls(active=False)

        elif event.event_type == EVENT_STATUS:
            self._set_status(event.message)

        elif event.event_type == EVENT_RECOGNIZED_TEXT:
            text = event.payload.get("text", event.message)
            self.sub_status.configure(text=text or "No command")

        elif event.event_type == EVENT_ASSISTANT_RESPONSE:
            text = event.payload.get("text", event.message)
            self.sub_status.configure(text=text or "No response")

        elif event.event_type == EVENT_ERROR:
            message = event.message or "An error occurred."
            self._set_status(message, is_error=True)
            self.sub_status.configure(text=message, text_color=theme.ERROR)
            error_detail = event.payload.get("error")

            if error_detail:
                logger.info("GUI event error detail:", error_detail)

        elif event.event_type == EVENT_LOG:
            self.history_panel.add_entry(event.payload.get("level", "INFO"), event.message)
            
        elif event.event_type == EVENT_AUDIT:
            self.history_panel.add_entry("AUDIT", event.message)
            
        elif event.event_type == EVENT_TOOL_CALL:
            self.history_panel.add_entry("TOOL", event.message)
            
        elif event.event_type == EVENT_OVERWATCH_CANDIDATE:
            self.history_panel.add_entry("OW_CANDIDATE", event.message)
            
        elif event.event_type == EVENT_OVERWATCH_ACTION:
            self.history_panel.add_entry("OW_ACTION", event.message)
            
        elif event.event_type == EVENT_OVERWATCH_STATE:
            self.overwatch_card.update_state(event.message)
            self.history_panel.add_entry("OW_STATE", event.message)
            
        elif event.event_type == EVENT_CONFIRMATION_REQUEST:
            self.pending_confirmation_id = event.payload.get("request_id")
            self.confirm_label.configure(text=f"Confirm: {event.message}")
            self.confirm_frame.pack(fill="x", pady=(0, 20), before=self.history_panel.frame)
            self.history_panel.add_entry("WARNING", f"Confirmation requested: {event.message}")


    def _check_listener_stopped(self):
        if self._listener_running():
            self.after(250, self._check_listener_stopped)
            return

        self.listening_active = False
        self.stopping_requested = False
        self._set_listening_controls(active=False)
        self._set_status("Ready")

    def _check_text_finished(self):
        if self.text_thread is not None and self.text_thread.is_alive():
            self.after(150, self._check_text_finished)
            return

        self.command_panel.set_enabled(True)

    def _check_smoke_finished(self):
        if self.smoke_thread is not None and self.smoke_thread.is_alive():
            self.after(200, self._check_smoke_finished)
            return

        self.smoke_button.configure(state="normal")

    def _listener_running(self):
        return self.listener_thread is not None and self.listener_thread.is_alive()

    def _set_listening_controls(self, active):
        self.start_button.configure(state="disabled" if active else "normal")
        self.stop_button.configure(state="normal" if active else "disabled")
        self.waveform.set_listening(active)

    def _set_status(self, message, is_error=False):
        color = theme.ERROR if is_error else theme.TEXT_MUTED
        self.status_label.configure(text=message)
        self.sidebar_status.configure(text=f"● JARVIS ONLINE\n{message}", text_color=theme.SUCCESS if not is_error else theme.ERROR)

    def _on_close(self):
        if self._listener_running():
            self.controller.stop()

        self.destroy()

    def resolve_confirm(self, approved):
        if self.pending_confirmation_id:
            from assistant import confirm
            confirm.resolve(self.pending_confirmation_id, approved)
            self.confirm_frame.pack_forget()
            self.pending_confirmation_id = None
            self.history_panel.add_entry("USER", f"Confirmed: {approved}")
