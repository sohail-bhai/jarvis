"""The screens behind the sidebar.

Each page is a CTkFrame the shell swaps into the content area. Pages stay
deliberately light: they describe what JARVIS can do in plain language and
never claim an integration works when it does not.
"""

import os
import threading
from pathlib import Path

from gui import integrations, theme
from gui.widgets.cards import (
    ApprovalCard,
    EnvironmentCard,
    StatusIndicator,
    TaskProgress,
    card,
    section_title,
    tone_color,
)


class Page:
    """Base page: owns a frame and a title."""

    title = ""
    subtitle = ""

    def __init__(self, ctk, parent, app):
        self.ctk = ctk
        self.app = app
        self.frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.frame.grid_columnconfigure(0, weight=1)
        self.build()

    def build(self):
        raise NotImplementedError

    def on_show(self):
        """Called each time the page becomes visible."""

    def _heading(self, row, text, subtitle=None):
        label = self.ctk.CTkLabel(self.frame, text=text, font=theme.font(22, "bold"),
                                  text_color=theme.TEXT, anchor="w")
        label.grid(row=row, column=0, sticky="ew", pady=(0, 2))
        if subtitle:
            sub = self.ctk.CTkLabel(self.frame, text=subtitle, font=theme.font(12),
                                    text_color=theme.TEXT_MUTED, anchor="w")
            sub.grid(row=row + 1, column=0, sticky="ew", pady=(0, theme.PAD))
        return row + 2


def empty_state(ctk, parent, message, hint=None):
    """A calm placeholder instead of an empty box."""
    holder = card(ctk, parent)
    holder.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(holder, text=message, font=theme.font(13),
                 text_color=theme.TEXT_MUTED, anchor="w", justify="left",
                 wraplength=560).grid(row=0, column=0, sticky="ew",
                                      padx=theme.PAD, pady=(theme.PAD, 2))
    if hint:
        ctk.CTkLabel(holder, text=hint, font=theme.font(12),
                     text_color=theme.TEXT_FAINT, anchor="w", justify="left",
                     wraplength=560).grid(row=1, column=0, sticky="ew",
                                          padx=theme.PAD, pady=(0, theme.PAD))
    return holder


class HomePage(Page):
    title = "Home"

    SUGGESTIONS = [
        "Find my files",
        "What's on my schedule?",
        "Research something",
        "Check my emails",
        "What am I looking at?",
    ]

    def build(self):
        ctk = self.ctk
        row = 0

        greeting = self.app.user_name
        row = self._heading(row, f"Hello, {greeting}.",
                            "Tell JARVIS what you want to do, in your own words.")

        # --- command box -------------------------------------------------
        box = card(ctk, self.frame)
        box.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD))
        box.grid_columnconfigure(0, weight=1)
        row += 1

        self.entry = ctk.CTkEntry(
            box, placeholder_text="How can I help you today?",
            height=46, font=theme.font(14), border_width=0,
            fg_color="transparent", text_color=theme.TEXT)
        self.entry.grid(row=0, column=0, sticky="ew",
                        padx=(theme.PAD, theme.PAD_SM), pady=theme.PAD_SM)
        self.entry.bind("<Return>", lambda _event: self._submit())

        self.send_button = ctk.CTkButton(
            box, text="Ask", width=76, height=36, font=theme.font(13, "bold"),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            corner_radius=theme.RADIUS_SM, command=self._submit)
        self.send_button.grid(row=0, column=1, sticky="e",
                              padx=(0, theme.PAD_SM), pady=theme.PAD_SM)

        self.voice_button = ctk.CTkButton(
            box, text="🎙 Talk", width=86, height=36, font=theme.font(13),
            fg_color=theme.SURFACE, text_color=theme.TEXT,
            hover_color=theme.SURFACE_ALT, border_width=1,
            border_color=theme.BORDER_STRONG, corner_radius=theme.RADIUS_SM,
            command=self.app.toggle_listening)
        self.voice_button.grid(row=0, column=2, sticky="e",
                               padx=(0, theme.PAD), pady=theme.PAD_SM)

        # --- suggestions --------------------------------------------------
        chips = ctk.CTkFrame(self.frame, fg_color="transparent")
        chips.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD_LG))
        row += 1
        for index, suggestion in enumerate(self.SUGGESTIONS):
            ctk.CTkButton(
                chips, text=suggestion, height=30, font=theme.font(12),
                fg_color=theme.SURFACE, text_color=theme.TEXT_MUTED,
                hover_color=theme.SURFACE_ALT, border_width=1,
                border_color=theme.BORDER, corner_radius=15,
                command=lambda s=suggestion: self._fill(s),
            ).grid(row=0, column=index, padx=(0, theme.PAD_SM), sticky="w")

        # --- current task ---------------------------------------------------
        section_title(ctk, self.frame, "CURRENT TASK").grid(
            row=row, column=0, sticky="ew", pady=(0, theme.PAD_SM))
        row += 1

        self.task_progress = TaskProgress(ctk, self.frame)
        self.task_progress.frame.grid(row=row, column=0, sticky="ew",
                                      pady=(0, theme.PAD_LG))
        row += 1

        # --- approvals ------------------------------------------------------
        self.approval = ApprovalCard(ctk, self.frame, self.app.resolve_approval)
        self.approval_row = row
        row += 1

        # --- environments ---------------------------------------------------
        section_title(ctk, self.frame, "YOUR ENVIRONMENTS").grid(
            row=row, column=0, sticky="ew", pady=(0, theme.PAD_SM))
        row += 1

        grid = ctk.CTkFrame(self.frame, fg_color="transparent")
        grid.grid(row=row, column=0, sticky="ew")
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="env")

        self.env_cards = {}
        specs = [
            ("computer", "🖥", "My Computer"),
            ("phone", "📱", "My Phone"),
            ("google", "◈", "Google"),
            ("internet", "🌐", "Internet"),
        ]
        for index, (key, icon, name) in enumerate(specs):
            env = EnvironmentCard(ctk, grid, icon, name, "Checking…", "offline")
            env.frame.grid(row=0, column=index, sticky="ew",
                           padx=(0 if index == 0 else theme.PAD_SM, 0))
            self.env_cards[key] = env

    def _fill(self, text):
        self.entry.delete(0, "end")
        self.entry.insert(0, text)
        self.entry.focus_set()

    def _submit(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.app.submit_goal(text)

    def show_approval(self, request_id, message):
        self.approval.show(request_id, message)
        self.approval.frame.grid(row=self.approval_row, column=0, sticky="ew",
                                 pady=(0, theme.PAD_LG))

    def hide_approval(self):
        self.approval.frame.grid_forget()

    def set_input_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.entry.configure(state=state)
        self.send_button.configure(state=state)

    def set_voice_active(self, active):
        self.voice_button.configure(text="■ Stop" if active else "🎙 Talk")

    def on_show(self):
        self.app.refresh_environments()

    def update_environments(self, statuses):
        for key, status in statuses.items():
            if key in self.env_cards:
                tone = "online" if status["connected"] else "offline"
                self.env_cards[key].set_status(status["label"], tone)


class DevicesPage(Page):
    title = "My Devices"

    def build(self):
        ctk = self.ctk
        row = self._heading(0, "My Devices",
                            "The machines JARVIS can work on for you.")

        self.container = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.container.grid(row=row, column=0, sticky="ew")
        self.container.grid_columnconfigure(0, weight=1)

    def on_show(self):
        for child in self.container.winfo_children():
            child.destroy()

        computer = integrations.computer_status()
        phone = integrations.phone_status()

        self._device_card(0, "🖥", "This Computer", computer,
                          ["Open apps and websites", "Read the screen",
                           "Manage files and notes", "Control volume"])
        self._device_card(1, "📱", "My Phone", phone,
                          ["Send commands to this computer",
                           "Receive updates from JARVIS"])

    def _device_card(self, index, icon, name, status, abilities):
        ctk = self.ctk
        holder = card(ctk, self.container)
        holder.grid(row=index, column=0, sticky="ew", pady=(0, theme.PAD_SM))
        holder.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(holder, text=icon, font=theme.font(22)).grid(
            row=0, column=0, rowspan=2, padx=(theme.PAD, theme.PAD),
            pady=theme.PAD)

        ctk.CTkLabel(holder, text=name, font=theme.font(14, "bold"),
                     text_color=theme.TEXT, anchor="w").grid(
            row=0, column=1, sticky="w", pady=(theme.PAD, 0))

        indicator = StatusIndicator(ctk, holder, status["detail"],
                                    "online" if status["connected"] else "offline")
        indicator.frame.grid(row=1, column=1, sticky="w", pady=(0, theme.PAD_SM))

        listing = ctk.CTkFrame(holder, fg_color="transparent")
        listing.grid(row=2, column=1, sticky="ew", padx=(0, theme.PAD),
                     pady=(0, theme.PAD))
        for position, ability in enumerate(abilities):
            ctk.CTkLabel(listing, text=f"·  {ability}", font=theme.font(12),
                         text_color=theme.TEXT_MUTED, anchor="w").grid(
                row=position, column=0, sticky="w")


class FilesPage(Page):
    title = "My Files"

    # Skip noise that would drown out real results.
    SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv",
                 ".cache", "site-packages", ".local/share/Trash"}
    MAX_RESULTS = 40

    def build(self):
        ctk = self.ctk
        row = self._heading(0, "My Files",
                            "Search what's on this computer. "
                            "Connect Google to search Drive too.")

        search_box = card(ctk, self.frame)
        search_box.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD))
        search_box.grid_columnconfigure(0, weight=1)
        row += 1

        self.entry = ctk.CTkEntry(
            search_box, placeholder_text="Find a file by name…",
            height=42, font=theme.font(13), border_width=0,
            fg_color="transparent", text_color=theme.TEXT)
        self.entry.grid(row=0, column=0, sticky="ew",
                        padx=(theme.PAD, theme.PAD_SM), pady=theme.PAD_SM)
        self.entry.bind("<Return>", lambda _event: self.search())

        self.button = ctk.CTkButton(
            search_box, text="Search", width=84, height=34,
            font=theme.font(13, "bold"), fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER, corner_radius=theme.RADIUS_SM,
            command=self.search)
        self.button.grid(row=0, column=1, sticky="e",
                         padx=(0, theme.PAD), pady=theme.PAD_SM)

        self.results = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.results.grid(row=row, column=0, sticky="ew")
        self.results.grid_columnconfigure(0, weight=1)

        self._show_message("Search your computer by typing a name above.")

    def _show_message(self, message, hint=None):
        for child in self.results.winfo_children():
            child.destroy()
        empty_state(self.ctk, self.results, message, hint).grid(
            row=0, column=0, sticky="ew")

    def search(self):
        query = self.entry.get().strip()
        if not query:
            return

        self.button.configure(state="disabled", text="…")
        self._show_message(f"Looking through your files for “{query}”…")
        self.app.log(f"Looking through your files for “{query}”")

        thread = threading.Thread(target=self._search_worker, args=(query,),
                                  name="JarvisFileSearch", daemon=True)
        thread.start()

    def _search_worker(self, query):
        """Runs off the main thread; results are handed back with `after`."""
        matches = []
        needle = query.lower()
        home = Path.home()

        try:
            for root, dirs, files in os.walk(home, topdown=True):
                dirs[:] = [d for d in dirs
                           if not d.startswith(".") and d not in self.SKIP_DIRS]
                for name in files:
                    if needle in name.lower():
                        try:
                            path = Path(root) / name
                            matches.append((name, path, path.stat().st_mtime))
                        except OSError:
                            continue
                        if len(matches) >= self.MAX_RESULTS:
                            raise StopIteration
        except StopIteration:
            pass
        except Exception:
            pass

        matches.sort(key=lambda item: item[2], reverse=True)
        self.frame.after(0, lambda: self._render(query, matches))

    def _render(self, query, matches):
        import datetime

        self.button.configure(state="normal", text="Search")

        if not matches:
            self._show_message(
                f"No files on this computer match “{query}”.",
                "Google Drive isn't connected yet, so Drive wasn't searched.")
            self.app.log(f"No files matched “{query}”", tone="muted")
            return

        for child in self.results.winfo_children():
            child.destroy()

        self.app.log(f"Found {len(matches)} matching file"
                     f"{'s' if len(matches) != 1 else ''}", tone="success")

        for index, (name, path, modified) in enumerate(matches):
            holder = card(self.ctk, self.results)
            holder.grid(row=index, column=0, sticky="ew", pady=(0, theme.PAD_SM))
            holder.grid_columnconfigure(0, weight=1)

            self.ctk.CTkLabel(holder, text=name, font=theme.font(13, "bold"),
                              text_color=theme.TEXT, anchor="w").grid(
                row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD_SM, 0))

            try:
                location = str(path.parent.relative_to(Path.home()))
            except ValueError:
                location = str(path.parent)
            stamp = datetime.datetime.fromtimestamp(modified).strftime("%d %b %Y")

            self.ctk.CTkLabel(
                holder, text=f"This computer / {location} · {stamp}",
                font=theme.font(11), text_color=theme.TEXT_MUTED, anchor="w").grid(
                row=1, column=0, sticky="ew", padx=theme.PAD, pady=(0, theme.PAD_SM))

            self.ctk.CTkButton(
                holder, text="Open", width=68, height=30, font=theme.font(12),
                fg_color=theme.SURFACE, text_color=theme.TEXT,
                hover_color=theme.SURFACE_ALT, border_width=1,
                border_color=theme.BORDER_STRONG, corner_radius=theme.RADIUS_SM,
                command=lambda p=path: self.app.open_path(p)).grid(
                row=0, column=1, rowspan=2, padx=(0, theme.PAD))


class GooglePage(Page):
    title = "Google"

    TABS = ["Overview", "Drive", "Gmail", "Calendar"]

    def build(self):
        ctk = self.ctk
        row = self._heading(0, "Google",
                            "Your Drive, mail and calendar, through JARVIS.")

        self.tab_bar = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.tab_bar.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD))
        row += 1

        self._tab_buttons = {}
        for index, name in enumerate(self.TABS):
            button = ctk.CTkButton(
                self.tab_bar, text=name, height=30, width=88,
                font=theme.font(12), corner_radius=theme.RADIUS_SM,
                fg_color="transparent", text_color=theme.TEXT_MUTED,
                hover_color=theme.SURFACE_ALT,
                command=lambda n=name: self.select_tab(n))
            button.grid(row=0, column=index, padx=(0, theme.PAD_XS))
            self._tab_buttons[name] = button

        self.body = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.body.grid(row=row, column=0, sticky="ew")
        self.body.grid_columnconfigure(0, weight=1)

        self._active_tab = "Overview"

    def on_show(self):
        self.select_tab(self._active_tab)

    def select_tab(self, name):
        self._active_tab = name
        for tab_name, button in self._tab_buttons.items():
            active = tab_name == name
            button.configure(
                fg_color=theme.ACCENT_SOFT if active else "transparent",
                text_color=theme.ACCENT if active else theme.TEXT_MUTED,
                font=theme.font(12, "bold" if active else "normal"))

        for child in self.body.winfo_children():
            child.destroy()

        google = integrations.google_status()
        mail = integrations.gmail_status()

        if name == "Overview":
            self._status_row(0, "Drive, Calendar & Docs", google)
            self._status_row(1, "Mail", mail)
            return

        if name == "Gmail":
            if mail["connected"]:
                empty_state(self.ctk, self.body,
                            "Mail is connected.",
                            "Ask JARVIS to “check my emails” and the "
                            "results appear in the System Log.").grid(
                    row=0, column=0, sticky="ew")
            else:
                empty_state(self.ctk, self.body, mail["label"],
                            mail["detail"]).grid(row=0, column=0, sticky="ew")
            return

        # Drive and Calendar both ride on the Google OAuth connection.
        if google["connected"]:
            hint = ("Ask JARVIS for your schedule to see events here."
                    if name == "Calendar"
                    else "Drive browsing isn't built yet. Nothing is being shown.")
            empty_state(self.ctk, self.body, f"{name} is connected.", hint).grid(
                row=0, column=0, sticky="ew")
        else:
            empty_state(self.ctk, self.body,
                        f"{name} isn't connected yet.",
                        google["detail"] + "  Nothing is shown until it is.").grid(
                row=0, column=0, sticky="ew")

    def _status_row(self, index, name, status):
        holder = card(self.ctk, self.body)
        holder.grid(row=index, column=0, sticky="ew", pady=(0, theme.PAD_SM))
        holder.grid_columnconfigure(0, weight=1)

        self.ctk.CTkLabel(holder, text=name, font=theme.font(13, "bold"),
                          text_color=theme.TEXT, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD_SM, 0))
        self.ctk.CTkLabel(holder, text=status["detail"], font=theme.font(12),
                          text_color=theme.TEXT_MUTED, anchor="w",
                          wraplength=440, justify="left").grid(
            row=1, column=0, sticky="ew", padx=theme.PAD, pady=(0, theme.PAD_SM))

        self.ctk.CTkLabel(
            holder, text=status["label"], font=theme.font(12, "bold"),
            text_color=tone_color("connected" if status["connected"] else "offline"),
        ).grid(row=0, column=1, rowspan=2, padx=theme.PAD)


class WebPage(Page):
    title = "Web"

    def build(self):
        ctk = self.ctk
        row = self._heading(0, "Web", "Ask JARVIS to look something up for you.")

        box = card(ctk, self.frame)
        box.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD))
        box.grid_columnconfigure(0, weight=1)
        row += 1

        self.entry = ctk.CTkEntry(
            box, placeholder_text="What should I find or do online?",
            height=42, font=theme.font(13), border_width=0,
            fg_color="transparent", text_color=theme.TEXT)
        self.entry.grid(row=0, column=0, sticky="ew",
                        padx=(theme.PAD, theme.PAD_SM), pady=theme.PAD_SM)
        self.entry.bind("<Return>", lambda _event: self._submit())

        self.button = ctk.CTkButton(
            box, text="Go", width=68, height=34, font=theme.font(13, "bold"),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            corner_radius=theme.RADIUS_SM, command=self._submit)
        self.button.grid(row=0, column=1, sticky="e",
                         padx=(0, theme.PAD), pady=theme.PAD_SM)

        self.status_holder = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.status_holder.grid(row=row, column=0, sticky="ew")
        self.status_holder.grid_columnconfigure(0, weight=1)

    def on_show(self):
        for child in self.status_holder.winfo_children():
            child.destroy()

        internet = integrations.internet_status()
        browser = integrations.browser_automation_status()

        if internet["connected"]:
            empty_state(self.ctk, self.status_holder,
                        "JARVIS can search and read the web.",
                        "Multi-step browser tasks: " + browser["detail"]).grid(
                row=0, column=0, sticky="ew")
        else:
            empty_state(self.ctk, self.status_holder,
                        "You're offline.",
                        "JARVIS can't search the web right now.").grid(
                row=0, column=0, sticky="ew")

    def _submit(self):
        query = self.entry.get().strip()
        if not query:
            return
        self.entry.delete(0, "end")
        self.app.submit_goal(f"search the web for {query}")


class ActivityPage(Page):
    title = "Activity"

    def build(self):
        row = self._heading(0, "Activity", "What JARVIS has done recently.")
        self.container = self.ctk.CTkFrame(self.frame, fg_color="transparent")
        self.container.grid(row=row, column=0, sticky="ew")
        self.container.grid_columnconfigure(0, weight=1)

    def on_show(self):
        for child in self.container.winfo_children():
            child.destroy()

        entries = list(reversed(self.app.system_log.entries()))
        if not entries:
            empty_state(self.ctk, self.container,
                        "Nothing yet.",
                        "Ask JARVIS to do something and it will be listed here.").grid(
                row=0, column=0, sticky="ew")
            return

        holder = card(self.ctk, self.container)
        holder.grid(row=0, column=0, sticky="ew")
        holder.grid_columnconfigure(1, weight=1)

        for index, (stamp, message, tone) in enumerate(entries[:200]):
            self.ctk.CTkLabel(holder, text=stamp, font=theme.font(11),
                              text_color=theme.TEXT_FAINT, anchor="w").grid(
                row=index, column=0, sticky="nw",
                padx=(theme.PAD, theme.PAD), pady=4)
            self.ctk.CTkLabel(holder, text=message, font=theme.font(12),
                              text_color=theme.TEXT, anchor="w",
                              justify="left", wraplength=460).grid(
                row=index, column=1, sticky="ew", padx=(0, theme.PAD), pady=4)


class SettingsPage(Page):
    title = "Settings"

    def build(self):
        ctk = self.ctk
        row = self._heading(0, "Settings", "Preferences and connected services.")

        section_title(ctk, self.frame, "CONNECTED SERVICES").grid(
            row=row, column=0, sticky="ew", pady=(0, theme.PAD_SM))
        row += 1

        self.services = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.services.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD_LG))
        self.services.grid_columnconfigure(0, weight=1)
        row += 1

        section_title(ctk, self.frame, "VOICE").grid(
            row=row, column=0, sticky="ew", pady=(0, theme.PAD_SM))
        row += 1

        voice_card = card(ctk, self.frame)
        voice_card.grid(row=row, column=0, sticky="ew")
        voice_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(voice_card, text="Speak responses out loud",
                     font=theme.font(13), text_color=theme.TEXT, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=theme.PAD, pady=theme.PAD)

        self.speech_switch = ctk.CTkSwitch(
            voice_card, text="", progress_color=theme.ACCENT,
            command=self.app.toggle_speech)
        self.speech_switch.grid(row=0, column=1, padx=theme.PAD)

    def on_show(self):
        for child in self.services.winfo_children():
            child.destroy()

        for index, (name, status) in enumerate(integrations.all_integrations()):
            holder = card(self.ctk, self.services)
            holder.grid(row=index, column=0, sticky="ew", pady=(0, theme.PAD_XS))
            holder.grid_columnconfigure(0, weight=1)

            self.ctk.CTkLabel(holder, text=name, font=theme.font(13, "bold"),
                              text_color=theme.TEXT, anchor="w").grid(
                row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD_SM, 0))
            self.ctk.CTkLabel(holder, text=status["detail"], font=theme.font(11),
                              text_color=theme.TEXT_MUTED, anchor="w",
                              wraplength=420, justify="left").grid(
                row=1, column=0, sticky="ew", padx=theme.PAD, pady=(0, theme.PAD_SM))
            self.ctk.CTkLabel(
                holder, text=status["label"], font=theme.font(12, "bold"),
                text_color=tone_color("connected" if status["connected"] else "offline"),
            ).grid(row=0, column=1, rowspan=2, padx=theme.PAD)

        if self.app.speech_enabled():
            self.speech_switch.select()
        else:
            self.speech_switch.deselect()


PAGE_CLASSES = {
    "home": HomePage,
    "devices": DevicesPage,
    "files": FilesPage,
    "google": GooglePage,
    "web": WebPage,
    "activity": ActivityPage,
    "settings": SettingsPage,
}
