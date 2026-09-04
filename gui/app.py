"""JARVIS desktop shell.

Layout: sidebar navigation, a content area holding one page at a time, and the
System Log pinned to the right so the user can always see what JARVIS is doing.

Threading rule: worker threads never touch widgets. They emit events on the
EventBus, and this class polls that bus from the Tk main thread.
"""

import logging
import threading
import traceback
from pathlib import Path

import customtkinter as ctk

from assistant import logging_setup
from assistant.config import get_setting
from assistant.controller import AssistantController
from assistant.events import (
    EVENT_ASSISTANT_RESPONSE,
    EVENT_CONFIRM_REQUEST,
    EVENT_CONFIRM_RESOLVED,
    EVENT_ERROR,
    EVENT_LOG,
    EVENT_OVERWATCH_ACTION,
    EVENT_OVERWATCH_CANDIDATE,
    EVENT_OVERWATCH_STATE,
    EVENT_RECOGNIZED_TEXT,
    EVENT_STATE_CHANGED,
    EVENT_STATUS,
    EVENT_TOOL_CALL,
    EventBus,
    set_global_event_bus,
)
from assistant.speech import is_speech_enabled, set_speech_enabled
from gui import integrations, theme
from gui.pages import PAGE_CLASSES
from gui.widgets.sidebar import Sidebar
from gui.widgets.system_log import SystemLog

logger = logging.getLogger(__name__)

# Assistant states rendered as something a person would say.
STATE_WORDS = {
    "idle": "Ready",
    "calibrating": "Getting the microphone ready",
    "listening": "Listening",
    "recognizing": "Working out what you said",
    "processing": "Working on it",
    "speaking": "Speaking",
    "error": "Something went wrong",
    "stopped": "Stopped",
}

# Tool names turned into plain English for the System Log.
TOOL_WORDS = {
    "search_web": "Researching on the web",
    "search_google": "Searching Google",
    "search_youtube": "Searching YouTube",
    "open_app": "Opening an app",
    "open_website": "Opening a website",
    "read_screen": "Reading your screen",
    "analyze_screen": "Looking at your screen",
    "take_screenshot": "Taking a screenshot",
    "read_file": "Reading a file",
    "write_file": "Saving a file",
    "list_directory": "Looking through a folder",
    "read_unread_emails": "Checking your emails",
    "send_email": "Preparing an email",
    "get_schedule": "Checking your schedule",
    "schedule_meeting": "Adding to your calendar",
    "remember_fact": "Remembering that for you",
    "ingest_document": "Reading a document",
    "get_weather": "Checking the weather",
    "run_terminal_command": "Running a command on this computer",
    "spawn_parallel_agents": "Asking other AI helpers to help",
    "run_actor_critic_research": "Researching this in depth",
}


class JarvisDashboardApp(ctk.CTk):
    def __init__(self):
        theme.configure_theme(ctk)
        super().__init__()

        self.title("JARVIS")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(fg_color=theme.BACKGROUND)

        self.event_bus = EventBus(maxsize=2000)
        set_global_event_bus(self.event_bus)
        logging_setup.configure_logging(event_bus=self.event_bus)

        from assistant import audit, confirm, guard, overwatch
        audit.configure(Path("logs/audit.jsonl"), max_bytes=5_000_000, backup_count=20)
        guard.configure(event_bus=self.event_bus)
        confirm.configure(event_bus=self.event_bus)
        overwatch.configure(event_bus=self.event_bus)
        self._confirm = confirm

        self.controller = AssistantController(event_bus=self.event_bus,
                                              speech_enabled=True)

        self.user_name = get_setting("user_name", "there")
        self.listener_thread = None
        self.text_thread = None
        self.pages = {}
        self.current_page = None

        self._build_layout()
        self.navigate("home")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_events)
        self.after(200, self.refresh_environments)

    # -- layout -------------------------------------------------------------

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(ctk, self, self.navigate)
        self.sidebar.frame.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew",
                          padx=theme.PAD_LG, pady=theme.PAD_LG)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        log_column = ctk.CTkFrame(self, fg_color="transparent", width=300)
        log_column.grid(row=0, column=2, sticky="nsew",
                        padx=(0, theme.PAD_LG), pady=theme.PAD_LG)
        log_column.grid_propagate(False)
        log_column.grid_columnconfigure(0, weight=1)
        log_column.grid_rowconfigure(0, weight=1)

        self.system_log = SystemLog(ctk, log_column)
        self.system_log.frame.grid(row=0, column=0, sticky="nsew")

        self.log("JARVIS is ready.", tone="success")

    def navigate(self, key):
        if key not in PAGE_CLASSES:
            return

        if key not in self.pages:
            self.pages[key] = PAGE_CLASSES[key](ctk, self.content, self)

        if self.current_page is not None:
            self.current_page.frame.grid_forget()

        page = self.pages[key]
        page.frame.grid(row=0, column=0, sticky="nsew")
        self.current_page = page
        self.sidebar.set_active(key)

        try:
            page.on_show()
        except Exception:
            logger.exception("Failed to refresh page %s", key)

    # -- helpers used by pages ---------------------------------------------

    def log(self, message, tone="normal"):
        """Add a plain-English line to the System Log."""
        self.system_log.add(message, tone)

    def speech_enabled(self):
        return is_speech_enabled()

    def toggle_speech(self):
        set_speech_enabled(not is_speech_enabled())
        self.log("Speaking responses turned "
                 + ("on." if is_speech_enabled() else "off."), tone="muted")

    def open_path(self, path):
        """Open a file with whatever the operating system uses for it."""
        import subprocess
        import sys

        path = Path(path)
        try:
            if sys.platform.startswith("win"):
                os_startfile = getattr(__import__("os"), "startfile")
                os_startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            self.log(f"Opened {path.name}", tone="success")
        except Exception as error:
            self.log(f"Couldn't open {path.name}: {error}", tone="error")

    def refresh_environments(self):
        """Check connection states off the main thread, then update the tiles."""
        def worker():
            statuses = {
                "computer": integrations.computer_status(),
                "phone": integrations.phone_status(),
                "google": integrations.google_status(),
                "internet": integrations.internet_status(),
            }
            self.after(0, lambda: self._apply_environments(statuses))

        threading.Thread(target=worker, name="JarvisEnvCheck", daemon=True).start()

    def _apply_environments(self, statuses):
        home = self.pages.get("home")
        if home is not None:
            home.update_environments(statuses)

    # -- goals --------------------------------------------------------------

    def submit_goal(self, goal_text):
        if self._listener_running():
            self.log("Stop voice mode before typing a request.", tone="warning")
            return

        if self.text_thread is not None and self.text_thread.is_alive():
            self.log("Still working on the last request.", tone="warning")
            return

        home = self.pages.get("home")
        if home is not None:
            home.set_input_enabled(False)
            home.task_progress.set_task(goal_text, [("Working on it", "active")])

        self.log(f"You asked: {goal_text}")
        self.sidebar.set_status("Working…", "waiting")

        self.text_thread = threading.Thread(
            target=self._run_goal, args=(goal_text,),
            name="JarvisGoal", daemon=True)
        self.text_thread.start()
        self.after(150, self._check_goal_finished)

    def _run_goal(self, goal_text):
        try:
            self.controller.handle_text_command(goal_text)
        except Exception as error:
            logger.exception("Goal failed")
            self.event_bus.emit(EVENT_ERROR, "Couldn't finish this step.",
                                error=str(error))

    def _check_goal_finished(self):
        if self.text_thread is not None and self.text_thread.is_alive():
            self.after(150, self._check_goal_finished)
            return

        home = self.pages.get("home")
        if home is not None:
            home.set_input_enabled(True)
            home.task_progress.set_task(
                home.task_progress.title.cget("text"), [("Done", "done")])
        self.sidebar.set_status("JARVIS Online", "online")

    # -- voice --------------------------------------------------------------

    def toggle_listening(self):
        if self._listener_running():
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        if self._listener_running():
            return

        self.log("Listening for your voice.", tone="muted")
        home = self.pages.get("home")
        if home is not None:
            home.set_voice_active(True)

        self.listener_thread = threading.Thread(
            target=self._run_voice_loop, name="JarvisVoiceLoop", daemon=True)
        self.listener_thread.start()

    def _run_voice_loop(self):
        try:
            self.controller.run_forever(greet=True)
        except Exception as error:
            logger.exception("Voice loop failed")
            self.event_bus.emit(EVENT_ERROR, "Voice mode stopped.", error=str(error))
        finally:
            self.event_bus.emit(EVENT_STATUS, "Voice mode stopped.")

    def stop_listening(self):
        if not self._listener_running():
            return

        self.controller.stop()
        self.log("Stopping voice mode.", tone="muted")
        self.after(250, self._check_listener_stopped)

    def _check_listener_stopped(self):
        if self._listener_running():
            self.after(250, self._check_listener_stopped)
            return

        home = self.pages.get("home")
        if home is not None:
            home.set_voice_active(False)
        self.sidebar.set_status("JARVIS Online", "online")

    def _listener_running(self):
        return self.listener_thread is not None and self.listener_thread.is_alive()

    # -- approvals ----------------------------------------------------------

    def resolve_approval(self, request_id, approved):
        home = self.pages.get("home")
        if home is not None:
            home.hide_approval()

        if not request_id:
            return

        self._confirm.resolve(request_id, approved)
        self.log("You approved the action." if approved
                 else "You declined the action.",
                 tone="success" if approved else "muted")

    # -- events -------------------------------------------------------------

    def _poll_events(self):
        try:
            for event in self.event_bus.poll(max_events=100):
                try:
                    self._handle_event(event)
                except Exception:
                    # One bad event must never stop the UI from updating.
                    logger.exception("Failed to handle event %s", event.event_type)
        finally:
            # Always reschedule, even if polling itself failed.
            self.after(50, self._poll_events)

    def _handle_event(self, event):
        kind = event.event_type
        payload = event.payload

        if kind == EVENT_STATE_CHANGED:
            state = payload.get("state", event.message)
            words = STATE_WORDS.get(state, state.capitalize())
            tone = "waiting" if state in ("listening", "processing") else "online"
            if state == "error":
                tone = "error"
            self.sidebar.set_status(words, tone)

        elif kind == EVENT_RECOGNIZED_TEXT:
            text = payload.get("text", event.message)
            if text:
                self.log(f"You said: {text}")

        elif kind == EVENT_ASSISTANT_RESPONSE:
            text = payload.get("text", event.message)
            if text:
                self.log(text, tone="success")

        elif kind == EVENT_TOOL_CALL:
            name = payload.get("tool") or payload.get("name") or event.message
            self.log(TOOL_WORDS.get(name, f"Working with {name}"))

        elif kind == EVENT_CONFIRM_REQUEST:
            self.navigate("home")
            home = self.pages.get("home")
            if home is not None:
                home.show_approval(payload.get("req_id"), event.message)
            self.log("Waiting for your approval.", tone="warning")

        elif kind == EVENT_CONFIRM_RESOLVED:
            self.log(event.message or "Approval resolved.", tone="muted")

        elif kind == EVENT_ERROR:
            self.log(event.message or "Couldn't finish this step.", tone="error")

        elif kind == EVENT_OVERWATCH_STATE:
            self.log(event.message, tone="muted")

        elif kind in (EVENT_OVERWATCH_CANDIDATE, EVENT_OVERWATCH_ACTION):
            self.log(event.message, tone="muted")

        elif kind == EVENT_LOG:
            # Only surface warnings and errors; routine logs stay in the file.
            level = payload.get("level", "INFO")
            if level in ("WARNING", "ERROR", "CRITICAL"):
                self.log(event.message, tone="warning" if level == "WARNING" else "error")

        elif kind == EVENT_STATUS:
            message = (event.message or "").strip()
            if message and not message.lower().startswith("processing"):
                self.log(message, tone="muted")

    # -- lifecycle ----------------------------------------------------------

    def _on_close(self):
        if self._listener_running():
            self.controller.stop()
        self.destroy()
