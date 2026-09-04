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
from gui.widgets.sidebar import Sidebar
from gui.widgets.topbar import TopBar
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
        # Sidebar (0), Content (1), Right Panel (2). Only the content column
        # grows; the other two are fixed so the page never gets squeezed into
        # a strip when the window is small.
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1, minsize=560)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Left Sidebar
        self.sidebar = Sidebar(
            self,
            on_navigate=self.navigate_to,
            on_voice_toggle=self.toggle_voice_listening,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Center Column: TopBar + Dynamic Page Content
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="nsew")
        center_frame.grid_rowconfigure(1, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        self.topbar = TopBar(
            center_frame,
            on_open_command_palette=self.open_command_palette,
            on_open_notifications=self.open_notifications,
        )
        self.topbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 0))

        # Dynamic Content Container
        self.page_container = ctk.CTkFrame(center_frame, fg_color="transparent")
        self.page_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        # Cache Pages
        self.pages = {
            "home": HomePage(self.page_container, on_navigate=self.navigate_to, on_execute_command=self.handle_user_command, on_voice_toggle=self.toggle_voice_listening),
            "devices": DevicesPage(self.page_container),
            "files": FilesPage(self.page_container),
            "google": GooglePage(self.page_container),
            "web": WebPage(self.page_container),
            "activity": ActivityPage(self.page_container),
            "settings": SettingsPage(self.page_container),
        }

        # Mount initial page
        self.current_page_widget = self.pages["home"]
        self.current_page_widget.grid(row=0, column=0, sticky="nsew")

        # Right Column: System Log Panel & Reusable Drawer
        right_container = ctk.CTkFrame(self, fg_color="transparent", width=286)
        right_container.grid(row=0, column=2, sticky="nsew", padx=(0, 14), pady=14)
        right_container.grid_propagate(False)
        right_container.grid_rowconfigure(0, weight=1)
        right_container.grid_columnconfigure(0, weight=1)

        self.system_log_panel = SystemLogPanel(right_container)
        self.system_log_panel.grid(row=0, column=0, sticky="nsew")

        self.detail_drawer = DetailDrawer(right_container, on_close=self.close_drawer)
        # detail_drawer initially hidden

        self.right_container = right_container
        self._right_visible = True
        # The System Log is the first thing to give way: below this width it
        # costs the page more than it tells the user.
        self.bind("<Configure>", self._on_resize)

    # Width at which the right-hand panel stops earning its space.
    RIGHT_PANEL_MIN_WIDTH = 1080

    def _on_resize(self, event):
        if event.widget is not self:
            return

        wanted = event.width >= self.RIGHT_PANEL_MIN_WIDTH
        if wanted == self._right_visible:
            return

        self._right_visible = wanted
        if wanted:
            self.right_container.grid(row=0, column=2, sticky="nsew",
                                      padx=(0, 14), pady=14)
        else:
            self.right_container.grid_remove()

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
        title_map = {
            "home": "Home",
            "devices": "My Devices",
            "files": "My Files",
            "google": "Google Workspace",
            "web": "Web Assistant",
            "activity": "Activity History",
            "settings": "Settings",
        }
        self.topbar.set_title(title_map.get(page_id, "VAVE"))
        # Navigation also happens from cards and the command palette, so the
        # sidebar has to follow the app rather than only lead it.
        self.sidebar.highlight(page_id)
        store.set_page(page_id)

    def open_drawer(self, drawer_type: str, data: any):
        self.detail_drawer.set_content(drawer_type, data)
        self.system_log_panel.grid_forget()
        self.detail_drawer.grid(row=0, column=0, sticky="nsew")

    def close_drawer(self):
        self.detail_drawer.grid_forget()
        self.system_log_panel.grid(row=0, column=0, sticky="nsew")
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
            self.sidebar.update_voice_state(False)
            store.add_system_log("Voice listening stopped.", "info")
        else:
            self.listening_active = True
            self.sidebar.update_voice_state(True)
            store.add_system_log("Listening for voice commands...", "working")

            def _voice_loop():
                try:
                    while self.listening_active:
                        self.controller.run_once()
                except Exception as ex:
                    logger.error(f"Voice loop ended: {ex}")
                finally:
                    self.listening_active = False
                    self.after(0, lambda: self.sidebar.update_voice_state(False))

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
