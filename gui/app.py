"""
VAVE Desktop Assistant Frontend Application.
Production-quality CustomTkinter desktop interface designed for normal, non-technical users.
"""
from __future__ import annotations

import logging
import threading
import traceback
import sys

import customtkinter as ctk

from assistant.controller import AssistantController
from assistant.events import (
    EVENT_ASSISTANT_RESPONSE,
    EVENT_ERROR,
    EVENT_RECOGNIZED_TEXT,
    EVENT_STATE_CHANGED,
    EVENT_STATUS,
    EventBus,
    set_global_event_bus,
)
from assistant import logging_setup
from gui import theme, ui_queue
from gui.store import store
from gui.widgets.topnav import TopNav
from gui.widgets.system_log import SystemLogPanel
from gui.widgets.drawer import DetailDrawer
from gui.widgets.command_palette import CommandPalette
from gui.widgets.notifications_modal import NotificationsModal
from gui.widgets.approval_modal import ApprovalModal

from gui.pages.home_page import HomePage
from gui.pages.devices_page import DevicesPage
from gui.pages.files_page import FilesPage
from gui.pages.google_page import GooglePage
from gui.pages.web_page import WebPage
from gui.pages.activity_page import ActivityPage
from gui.pages.settings_page import SettingsPage

logger = logging.getLogger(__name__)


class JarvisDashboardApp(ctk.CTk):
    def __init__(self):
        theme.configure_theme(ctk)
        super().__init__()

        self.title("VAVE — Your AI, Everywhere")
        self.geometry("1240x760")
        # Window managers do not have to honour the geometry above, so the
        # layout has to survive a much narrower window than the one we ask for.
        self.minsize(880, 600)
        self.configure(fg_color=theme.MAIN_BG)

        # 1. Event Bus & Assistant Controller
        self.event_bus = EventBus(maxsize=2000)
        set_global_event_bus(self.event_bus)
        logging_setup.configure_logging(event_bus=self.event_bus)

        # Initialize safe optional backend modules
        try:
            from assistant import audit, guard, confirm, overwatch
            from pathlib import Path
            audit.configure(Path("logs/audit.jsonl"), max_bytes=5_000_000, backup_count=20)
            guard.configure(event_bus=self.event_bus)
            confirm.configure(event_bus=self.event_bus)
            overwatch.configure(event_bus=self.event_bus)
        except Exception as e:
            logger.warning(f"Optional assistant subsystem initialization note: {e}")

        self.controller = AssistantController(
            event_bus=self.event_bus,
            speech_enabled=True,
        )

        self.listener_thread = None
        self.listening_active = False

        # 2. Build Core Window Layout
        self._build_layout()

        # 3. Register Store Subscriptions
        store.subscribe(self._on_store_event)

        # 4. Global Keyboard Shortcuts
        self.bind("<Command-k>", lambda e: self.open_command_palette())
        self.bind("<Control-k>", lambda e: self.open_command_palette())

        # 5. Clean Window Close Handling
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 6. Event Bus Polling
        self.after(100, self._poll_events)

    def _build_layout(self):
        """One column under one bar.

        The rail and the permanent right-hand panel are gone: between them they
        cost 520px of a window this app is rarely given, and everything they
        held is either in the nav or on the page that needs it.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.topnav = TopNav(
            self,
            on_navigate=self.navigate_to,
            on_open_command_palette=self.open_command_palette,
            on_open_notifications=self.open_notifications,
        )
        self.topnav.grid(row=0, column=0, sticky="ew")
        # Older code talks to a sidebar and a topbar; both jobs belong to one
        # widget now, so point the old names at it rather than chase callers.
        self.sidebar = self.topnav
        self.topbar = self.topnav

        self.page_container = ctk.CTkFrame(self, fg_color="transparent")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "home": HomePage(self.page_container, on_navigate=self.navigate_to,
                             on_execute_command=self.handle_user_command,
                             on_voice_toggle=self.toggle_voice_listening),
            "devices": DevicesPage(self.page_container),
            "files": FilesPage(self.page_container),
            "google": GooglePage(self.page_container),
            "web": WebPage(self.page_container),
            "activity": ActivityPage(self.page_container),
            "settings": SettingsPage(self.page_container),
        }

        self.current_page_widget = self.pages["home"]
        self.current_page_widget.grid(row=0, column=0, sticky="nsew")

        # The drawer slides in over the page instead of living beside it.
        self.detail_drawer = DetailDrawer(self, on_close=self.close_drawer)

    def navigate_to(self, page_id: str):
        if page_id not in self.pages:
            return

        # Hide current page
        if self.current_page_widget:
            self.current_page_widget.grid_forget()

        # Mount new page
        self.current_page_widget = self.pages[page_id]
        self.current_page_widget.grid(row=0, column=0, sticky="nsew")

        # Update TopBar title
        # Navigation also happens from cards and the command palette, so the
        # nav has to follow the app rather than only lead it.
        self.topnav.highlight(page_id)
        store.set_page(page_id)

    def open_drawer(self, drawer_type: str, data: any):
        self.detail_drawer.set_content(drawer_type, data)
        self.detail_drawer.place(relx=1.0, rely=0, relheight=1, anchor="ne",
                                 width=390)
        self.detail_drawer.lift()

    def close_drawer(self):
        self.detail_drawer.place_forget()
        store.close_drawer()

    def open_command_palette(self):
        CommandPalette(self, on_execute=self.handle_user_command)

    def open_notifications(self):
        NotificationsModal(self, on_navigate=self.navigate_to)

    def handle_user_command(self, command_text: str):
        cmd_clean = command_text.strip()
        if not cmd_clean:
            return

        cmd_lower = cmd_clean.lower()
        store.add_system_log(f"User: \"{cmd_clean}\"", "info")

        # Check for core project / presentation demo flow
        if any(w in cmd_lower for w in ["continue my project", "hackwave", "continue project", "prepare project"]):
            store.run_hackwave_demo()
            return

        # Check for file finding
        if any(w in cmd_lower for w in ["find my presentation", "find presentation", "find files"]):
            store.add_system_log("Searching your computer and Google Drive...", "working")
            self.after(800, lambda: store.add_system_log("Found 'Hackwave_Final.pptx' on your computer", "completed"))
            self.after(1200, lambda: self.navigate_to("files"))
            return

        # Check for email checking
        if any(w in cmd_lower for w in ["check my emails", "emails", "summarize my emails"]):
            store.add_system_log("Reading unread emails from Google Workspace...", "working")
            self.after(900, lambda: store.add_system_log("Summarized 2 unread emails from Hackathon team", "completed"))
            self.after(1100, lambda: self.navigate_to("google"))
            return

        # Check for web research
        if any(w in cmd_lower for w in ["research", "search web", "look up"]):
            store.add_system_log(f"Starting web research: '{cmd_clean}'", "working")
            self.after(1000, lambda: store.add_system_log("Found 4 relevant documentation sources", "completed"))
            self.after(1200, lambda: self.navigate_to("web"))
            return

        # Pass through to the real AssistantController in a background thread
        def _exec():
            try:
                self.controller.handle_text_command(cmd_clean)
            except Exception as ex:
                logger.error(f"Error handling command: {ex}")
                self.event_bus.emit(EVENT_ERROR, f"Could not complete '{cmd_clean}'.")

        t = threading.Thread(target=_exec, daemon=True)
        t.start()

    def toggle_voice_listening(self):
        if self.listening_active:
            self.listening_active = False
            self.topnav.update_voice_state(False)
            store.add_system_log("Voice listening stopped.", "info")
        else:
            self.listening_active = True
            self.topnav.update_voice_state(True)
            store.add_system_log("Listening for voice commands...", "working")

            def _voice_loop():
                try:
                    while self.listening_active:
                        self.controller.run_once()
                except Exception as ex:
                    logger.error(f"Voice loop ended: {ex}")
                finally:
                    self.listening_active = False
                    self.after(0, lambda: self.topnav.update_voice_state(False))

            self.listener_thread = threading.Thread(target=_voice_loop, daemon=True)
            self.listener_thread.start()

    def _on_store_event(self, event: str, data: any):
        if event == "drawer_opened":
            self.open_drawer(data.get("type", "generic"), data.get("data", {}))
        elif event == "drawer_closed":
            self.close_drawer()
        elif event == "approval_requested":
            ApprovalModal(self, data)

    def _poll_events(self):
        """Poll the event bus from the main UI thread."""
        # Work handed back by background threads. Tk is not thread-safe, so
        # they queue callbacks rather than touching widgets themselves.
        ui_queue.drain()

        try:
            while not self.event_bus.empty():
                evt = self.event_bus.get_nowait()
                if not evt:
                    break

                if evt.event_type == EVENT_RECOGNIZED_TEXT:
                    text = evt.payload.get("text", "")
                    if text:
                        store.add_system_log(f"Heard: \"{text}\"", "info")

                elif evt.event_type == EVENT_ASSISTANT_RESPONSE:
                    resp = evt.payload.get("text", "")
                    if resp:
                        store.add_system_log(resp, "completed")

                elif evt.event_type == EVENT_ERROR:
                    err = evt.payload.get("error", "An unexpected error occurred.")
                    store.add_system_log(f"Notice: {err}", "waiting")

        except Exception as e:
            logger.debug(f"Event polling note: {e}")

        finally:
            # Reschedule from a finally block: one failing event must never
            # stop the loop and freeze the whole UI.
            self.after(100, self._poll_events)

    def _on_close(self):
        self.listening_active = False
        self.destroy()
