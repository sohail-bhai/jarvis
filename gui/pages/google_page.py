"""
Google workspace integration screen.
Unified view for Drive, Gmail, Calendar, Docs and Slides.

Everything on this page comes from the Google gateway. When Google is not
connected the gateway answers with examples, and the page says so at the top
rather than dressing them up as the user's own mail and files.
"""
from __future__ import annotations

import datetime
import threading
import webbrowser

import customtkinter as ctk

from assistant.workspace import auth as workspace_auth
from assistant.workspace.gateway import gateway
from gui import theme
from gui.store import store

TABS = ["Overview", "Drive", "Gmail", "Calendar", "Docs"]


def _readable_size(raw) -> str:
    try:
        size = int(raw)
    except (TypeError, ValueError):
        return ""
    if size <= 0:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return ""


def _readable_date(raw) -> str:
    if not raw:
        return ""
    try:
        moment = datetime.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return str(raw)
    return moment.astimezone().strftime("%d %b, %H:%M")


def _icon_for(mime: str) -> str:
    if "presentation" in mime:
        return "📊"
    if "spreadsheet" in mime:
        return "📈"
    if "pdf" in mime:
        return "📑"
    if "folder" in mime:
        return "📁"
    return "📄"


class GooglePage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.CARD_BORDER,
        )
        self.active_tab = "Overview"
        self.tab_buttons = {}
        # What the gateway last told us. None means "not asked yet", which is
        # not the same as "not connected".
        self.status = None

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text="Google",
            font=theme.font(20, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        self.conn_badge = ctk.CTkLabel(
            title_row,
            text="● Checking",
            font=theme.font(11, "bold"),
            text_color=theme.TEXT_SECONDARY,
            fg_color=theme.MAIN_BG,
            corner_radius=10,
            padx=10,
            pady=4,
        )
        self.conn_badge.pack(side="left", padx=12)

        self.connect_button = ctk.CTkButton(
            title_row,
            text="Connect Google",
            font=theme.font(11, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color="#FFFFFF",
            corner_radius=8,
            height=28,
            width=130,
            command=self._connect,
        )
        self.connect_button.pack(side="right")

        ctk.CTkLabel(
            header,
            text="JARVIS connects to your Google ecosystem so you never have to juggle tabs.",
            font=theme.font(12),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # A demo state has to be visible before any data is read.
        self.notice = ctk.CTkLabel(
            self,
            text="",
            font=theme.font(11),
            text_color=theme.TEXT_PRIMARY,
            fg_color=theme.WARNING_LIGHT,
            corner_radius=10,
            anchor="w",
            justify="left",
            wraplength=760,
            padx=12,
            pady=8,
        )

        # 2. Tabs Row
        tabs_row = ctk.CTkFrame(self, fg_color="transparent")
        tabs_row.pack(fill="x", padx=16, pady=(0, 14))

        for name in TABS:
            btn = ctk.CTkButton(
                tabs_row,
                text=name,
                font=theme.font(11, "bold" if name == "Overview" else "normal"),
                fg_color=theme.SIDEBAR_BG if name == "Overview" else theme.CARD_BG,
                hover_color=theme.SIDEBAR_HOVER if name == "Overview" else theme.CARD_HOVER,
                text_color="#FFFFFF" if name == "Overview" else theme.TEXT_SECONDARY,
                border_width=0 if name == "Overview" else 1,
                border_color=theme.CARD_BORDER,
                corner_radius=12,
                height=28,
                command=lambda chosen=name: self._switch_tab(chosen),
            )
            btn.pack(side="left", padx=3)
            self.tab_buttons[name] = btn

        # 3. Tab Content Container
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_container.pack(fill="x", padx=16, pady=(0, 20))

        self._render_tab_content()
        self._refresh_status()

    # -- connection state ---------------------------------------------------

    def _refresh_status(self):
        """Ask the gateway where we stand, off the main thread."""
        def work():
            status = gateway.get_status()
            self.after(0, lambda: self._apply_status(status))

        threading.Thread(target=work, daemon=True, name="google-status").start()

    def _apply_status(self, status):
        if not self.winfo_exists():
            return

        self.status = status
        connected = status.get("connected", False)

        account = status.get("account") or ""
        self.conn_badge.configure(
            text=f"● {account}" if connected and account
            else "● Connected" if connected else "● Not connected",
            text_color=theme.SUCCESS if connected else theme.TEXT_SECONDARY,
            fg_color=theme.SUCCESS_LIGHT if connected else theme.MAIN_BG,
        )

        if connected:
            self.notice.pack_forget()
            self.connect_button.configure(text="Disconnect", command=self._disconnect,
                                          fg_color=theme.MAIN_BG,
                                          hover_color=theme.CARD_BORDER,
                                          text_color=theme.TEXT_PRIMARY)
        else:
            self.notice.configure(
                text="Demo mode. Google isn't connected, so everything below is an "
                     f"example rather than your own mail, files or calendar. "
                     f"{status.get('detail', '')}")
            self.notice.pack(fill="x", padx=16, pady=(0, 12), before=self.tab_container)
            self.connect_button.configure(text="Connect Google", command=self._connect,
                                          fg_color=theme.ACCENT,
                                          hover_color=theme.ACCENT_HOVER,
                                          text_color="#FFFFFF")

        self._render_tab_content()

    def _connect(self):
        """Open Google's consent screen. It has to happen on this computer."""
        state = workspace_auth.connection_state()
        if state["state"] == workspace_auth.NOT_CONFIGURED:
            store.add_system_log(state["detail"], "failed")
            self.notice.configure(text=state["detail"])
            return

        self.connect_button.configure(state="disabled", text="Signing in...")
        store.add_system_log("Opened Google sign-in in your browser", "working")

        def work():
            result = workspace_auth.authorize()
            self.after(0, lambda: self._finish_connect(result))

        threading.Thread(target=work, daemon=True, name="google-oauth").start()

    def _finish_connect(self, result):
        if not self.winfo_exists():
            return
        self.connect_button.configure(state="normal")
        connected = result["state"] == workspace_auth.LIVE
        store.add_system_log(
            "Connected your Google account" if connected
            else f"Google sign-in did not finish. {result['detail']}",
            "completed" if connected else "failed")
        self._refresh_status()

    def _disconnect(self):
        workspace_auth.disconnect()
        store.add_system_log("Disconnected your Google account", "completed")
        self._refresh_status()

    # -- tabs ---------------------------------------------------------------

    def _switch_tab(self, tab_name: str):
        self.active_tab = tab_name
        for name, btn in self.tab_buttons.items():
            if name == tab_name:
                btn.configure(
                    fg_color=theme.SIDEBAR_BG,
                    text_color="#FFFFFF",
                    border_width=0,
                    font=theme.font(11, "bold"),
                )
            else:
                btn.configure(
                    fg_color=theme.CARD_BG,
                    text_color=theme.TEXT_SECONDARY,
                    border_width=1,
                    font=theme.font(11, "normal"),
                )
        self._render_tab_content()

    def _render_tab_content(self):
        for child in self.tab_container.winfo_children():
            child.destroy()

        if self.active_tab == "Overview":
            self._render_overview()
        elif self.active_tab == "Drive":
            self._render_drive()
        elif self.active_tab == "Gmail":
            self._render_gmail()
        elif self.active_tab == "Calendar":
            self._render_calendar()
        elif self.active_tab == "Docs":
            self._render_docs()

    def _loading(self, message="Asking Google..."):
        label = ctk.CTkLabel(
            self.tab_container,
            text=message,
            font=theme.font(12),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        label.pack(anchor="w", pady=12)
        return label

    def _load(self, capability, on_ready, **kwargs):
        """Fetch from the gateway in a thread, then draw on the main thread."""
        placeholder = self._loading()
        tab_at_request = self.active_tab

        def work():
            try:
                items = gateway.execute_capability(capability, **kwargs)
            except Exception as error:                # pragma: no cover - defensive
                items = error

            def draw():
                # The user may have moved on while Google was answering.
                if not self.winfo_exists() or self.active_tab != tab_at_request:
                    return
                if placeholder.winfo_exists():
                    placeholder.destroy()
                if isinstance(items, Exception):
                    ctk.CTkLabel(
                        self.tab_container,
                        text=f"Google could not answer: {items}",
                        font=theme.font(12),
                        text_color=theme.DANGER,
                        anchor="w",
                        wraplength=700,
                        justify="left",
                    ).pack(anchor="w", pady=12)
                    return
                on_ready(items)

            self.after(0, draw)

        threading.Thread(target=work, daemon=True, name="google-fetch").start()

    # -- Overview -----------------------------------------------------------

    def _render_overview(self):
        grid = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 16))
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="g_ov")

        services = (self.status or {}).get("services", {})
        cards = [
            ("Google Drive", "📁", theme.INFO_LIGHT, theme.INFO_BORDER, "drive"),
            ("Gmail", "✉", theme.DANGER_LIGHT, theme.DANGER_BORDER, "gmail"),
            ("Calendar", "📅", theme.SUCCESS_LIGHT, theme.SUCCESS_BORDER, "calendar"),
            ("Docs & Slides", "📄", theme.WARNING_LIGHT, theme.WARNING_BORDER, "docs"),
        ]

        for idx, (title, icon, bg, border, key) in enumerate(cards):
            card = ctk.CTkFrame(
                grid,
                fg_color=bg,
                border_width=1,
                border_color=border,
                corner_radius=12,
                height=84,
            )
            card.grid(row=0, column=idx, padx=4, sticky="nsew")
            card.pack_propagate(False)

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=12, pady=12)

            ctk.CTkLabel(content, text=icon, font=theme.font(18)).pack(anchor="w")
            ctk.CTkLabel(content, text=title, font=theme.font(11, "bold"),
                         text_color=theme.TEXT_PRIMARY).pack(anchor="w", pady=(2, 0))
            # No invented counts: JARVIS has not read these accounts yet.
            ctk.CTkLabel(content,
                         text=services.get(key, {}).get("status", "unknown").title(),
                         font=theme.font(10),
                         text_color=theme.TEXT_MUTED).pack(anchor="w")

        actions_card = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG,
                                    corner_radius=14, border_width=1,
                                    border_color=theme.CARD_BORDER)
        actions_card.pack(fill="x", pady=8)

        ctk.CTkLabel(actions_card, text="Quick Google Actions with JARVIS",
                     font=theme.font(13, "bold"),
                     text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))

        prompts = [
            ("Check today's schedule", "📅", "Calendar"),
            ("Read my unread emails", "✉", "Gmail"),
            ("Find a file in Drive", "🔍", "Drive"),
            ("Write a document or deck", "📄", "Docs"),
        ]
        for prompt, icon, target in prompts:
            ctk.CTkButton(
                actions_card,
                text=f"  {icon}   {prompt}",
                font=theme.font(12),
                fg_color=theme.MAIN_BG,
                hover_color=theme.CARD_BORDER,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
                corner_radius=8,
                height=32,
                command=lambda chosen=target: self._switch_tab(chosen),
            ).pack(fill="x", padx=16, pady=3)

        ctk.CTkFrame(actions_card, height=10, fg_color="transparent").pack()

    # -- Drive --------------------------------------------------------------

    def _render_drive(self):
        search_row = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG,
                                  corner_radius=12, border_width=1,
                                  border_color=theme.CARD_BORDER)
        search_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(search_row, text="Search", font=theme.font(11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(12, 4))

        entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search your Google Drive...",
            placeholder_text_color=theme.TEXT_MUTED,
            border_width=0,
            fg_color="transparent",
        )
        entry.pack(side="left", fill="x", expand=True, pady=8)

        self.drive_results = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.drive_results.pack(fill="x")

        def run_search(_event=None):
            query = entry.get().strip()
            for child in self.drive_results.winfo_children():
                child.destroy()
            if query:
                self._load("google.drive.search", self._show_drive_files,
                           query=query, limit=20)
            else:
                self._load("google.drive.list", self._show_drive_files, limit=20)

        entry.bind("<Return>", run_search)
        ctk.CTkButton(
            search_row,
            text="Search",
            font=theme.font(11, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color="#FFFFFF",
            corner_radius=8,
            width=80,
            height=26,
            command=run_search,
        ).pack(side="right", padx=8)

        self._load("google.drive.list", self._show_drive_files, limit=20)

    def _show_drive_files(self, files):
        parent = getattr(self, "drive_results", self.tab_container)
        if not parent.winfo_exists():
            return
        if not files:
            ctk.CTkLabel(parent, text="No files matched.", font=theme.font(12),
                         text_color=theme.TEXT_MUTED).pack(anchor="w", pady=12)
            return

        for item in files:
            card = ctk.CTkFrame(parent, fg_color=theme.CARD_BG, corner_radius=12,
                                border_width=1, border_color=theme.CARD_BORDER)
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            ctk.CTkLabel(row, text=_icon_for(item.get("mimeType", "")),
                         font=theme.font(18)).pack(side="left", padx=(0, 10))

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(col, text=item.get("name", "Untitled"),
                         font=theme.font(12, "bold"),
                         text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")

            detail = " · ".join(part for part in (
                _readable_date(item.get("modifiedTime")),
                _readable_size(item.get("size")),
            ) if part)
            ctk.CTkLabel(col, text=detail or "In your Drive", font=theme.font(10),
                         text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

            link = item.get("webViewLink", "")
            ctk.CTkButton(
                row,
                text="Open" if link else "No link",
                font=theme.font(11, "bold"),
                fg_color=theme.ACCENT if link else theme.MAIN_BG,
                hover_color=theme.ACCENT_HOVER if link else theme.CARD_BORDER,
                text_color="#FFFFFF" if link else theme.TEXT_MUTED,
                corner_radius=8,
                height=26,
                state="normal" if link else "disabled",
                command=lambda url=link, name=item.get("name", ""): self._open_link(url, name),
            ).pack(side="right", padx=4)

    def _open_link(self, url, name):
        if not url:
            return
        webbrowser.open(url)
        store.add_system_log(f"Opened {name} in your browser", "completed")

    # -- Gmail --------------------------------------------------------------

    def _render_gmail(self):
        self._load("google.gmail.search", self._show_emails,
                   query="is:unread", max_results=10)

    def _show_emails(self, emails):
        if not self.tab_container.winfo_exists():
            return
        if not emails:
            ctk.CTkLabel(self.tab_container, text="No unread mail.",
                         font=theme.font(12),
                         text_color=theme.TEXT_MUTED).pack(anchor="w", pady=12)
            return

        for email in emails:
            unread = email.get("unread", False)
            card = ctk.CTkFrame(
                self.tab_container,
                fg_color=theme.INFO_LIGHT if unread else theme.CARD_BG,
                corner_radius=12,
                border_width=1,
                border_color=theme.INFO_BORDER if unread else theme.CARD_BORDER,
            )
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)

            sender_row = ctk.CTkFrame(col, fg_color="transparent")
            sender_row.pack(fill="x", anchor="w")

            if unread:
                ctk.CTkLabel(sender_row, text="●", font=theme.font(9, "bold"),
                             text_color=theme.INFO).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(sender_row, text=email.get("sender", "Unknown"),
                         font=theme.font(12, "bold"),
                         text_color=theme.TEXT_PRIMARY).pack(side="left")

            ctk.CTkLabel(col, text=email.get("subject", "(no subject)"),
                         font=theme.font(12), text_color=theme.TEXT_SECONDARY,
                         anchor="w").pack(anchor="w", pady=(2, 0))
            ctk.CTkLabel(col, text=email.get("snippet", ""), font=theme.font(10),
                         text_color=theme.TEXT_MUTED, anchor="w",
                         wraplength=520, justify="left").pack(anchor="w")

            ctk.CTkButton(
                row,
                text="Draft a reply",
                font=theme.font(11, "bold"),
                fg_color=theme.ACCENT,
                hover_color=theme.ACCENT_HOVER,
                text_color="#FFFFFF",
                corner_radius=8,
                height=26,
                command=lambda message=email: self._draft_reply(message),
            ).pack(side="right", padx=4)

    def _draft_reply(self, email):
        """Write a draft in Gmail. A draft sends nothing, so it needs no approval."""
        sender = email.get("sender", "")
        subject = email.get("subject", "")

        def work():
            result = gateway.execute_capability(
                "google.gmail.draft", to=sender,
                subject=f"Re: {subject}",
                body="")
            failed = isinstance(result, dict) and result.get("error")
            self.after(0, lambda: store.add_system_log(
                f"Could not draft a reply: {result['error']}" if failed
                else f"Drafted a reply to {sender} in Gmail",
                "failed" if failed else "completed"))

        store.add_system_log(f"Drafting a reply to {sender}", "working")
        threading.Thread(target=work, daemon=True, name="gmail-draft").start()

    # -- Calendar -----------------------------------------------------------

    def _render_calendar(self):
        ctk.CTkLabel(self.tab_container, text="What's coming up",
                     font=theme.font(13, "bold"),
                     text_color=theme.TEXT_PRIMARY).pack(anchor="w", pady=(4, 10))
        self._load("google.calendar.read", self._show_events, max_results=10)

    def _show_events(self, events):
        if not self.tab_container.winfo_exists():
            return
        if not events:
            ctk.CTkLabel(self.tab_container, text="Nothing on your calendar.",
                         font=theme.font(12),
                         text_color=theme.TEXT_MUTED).pack(anchor="w", pady=12)
            return

        for event in events:
            card = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG,
                                corner_radius=12, border_width=1,
                                border_color=theme.CARD_BORDER)
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=12)

            start = event.get("start", {})
            when = start.get("dateTime") or start.get("date") or ""

            time_box = ctk.CTkFrame(row, fg_color=theme.MAIN_BG, corner_radius=8,
                                    width=110, height=36)
            time_box.pack(side="left", padx=(0, 12))
            time_box.pack_propagate(False)
            ctk.CTkLabel(time_box, text=_readable_date(when) or "Sometime",
                         font=theme.font(11, "bold"),
                         text_color=theme.TEXT_PRIMARY).pack(expand=True)

            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(col, text=event.get("summary", "Untitled event"),
                         font=theme.font(12, "bold"),
                         text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=event.get("description", ""), font=theme.font(10),
                         text_color=theme.TEXT_MUTED, anchor="w", wraplength=520,
                         justify="left").pack(anchor="w")

    # -- Docs, Sheets and Slides -------------------------------------------

    def _render_docs(self):
        card = ctk.CTkFrame(self.tab_container, fg_color=theme.CARD_BG,
                            corner_radius=14, border_width=1,
                            border_color=theme.CARD_BORDER)
        card.pack(fill="x", pady=4)

        ctk.CTkLabel(card, text="Make something in Google",
                     font=theme.font(13, "bold"),
                     text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(card,
                     text="JARVIS writes the document or deck in your Drive. "
                          "Nothing is shared with anyone by creating it.",
                     font=theme.font(11), text_color=theme.TEXT_SECONDARY,
                     anchor="w").pack(anchor="w", padx=16)

        entry = ctk.CTkEntry(
            card,
            placeholder_text="What should it be called?",
            placeholder_text_color=theme.TEXT_MUTED,
            fg_color=theme.MAIN_BG,
            border_color=theme.CARD_BORDER,
            height=32,
        )
        entry.pack(fill="x", padx=16, pady=10)

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            buttons,
            text="Create a document",
            font=theme.font(11, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color="#FFFFFF",
            corner_radius=8,
            height=30,
            command=lambda: self._create("google.docs.create", entry.get().strip(),
                                         "document"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="Create a presentation",
            font=theme.font(11, "bold"),
            fg_color=theme.MAIN_BG,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT_PRIMARY,
            border_width=1,
            border_color=theme.CARD_BORDER,
            corner_radius=8,
            height=30,
            command=lambda: self._create("google.slides.create", entry.get().strip(),
                                         "presentation"),
        ).pack(side="left")

        self.docs_result = ctk.CTkLabel(
            card, text="", font=theme.font(11), text_color=theme.TEXT_SECONDARY,
            anchor="w", wraplength=700, justify="left")
        self.docs_result.pack(anchor="w", padx=16, pady=(0, 14))

    def _create(self, capability, title, kind):
        if not title:
            self.docs_result.configure(text=f"Give the {kind} a name first.")
            return

        self.docs_result.configure(text=f"Creating the {kind}...")
        store.add_system_log(f"Creating the {kind} \"{title}\"", "working")

        def work():
            result = gateway.execute_capability(capability, title=title)

            def done():
                if not self.winfo_exists() or not self.docs_result.winfo_exists():
                    return
                error = result.get("error") if isinstance(result, dict) else None
                if error:
                    self.docs_result.configure(text=f"Google refused: {error}")
                    store.add_system_log(f"Could not create the {kind}", "failed")
                    return

                live = gateway.is_connected()
                link = result.get("webViewLink", "")
                self.docs_result.configure(
                    text=f"Created \"{title}\"." + (f"  {link}" if link else "")
                    if live else
                    f"Demo mode: described \"{title}\" but did not create it in "
                    "Google. Connect Google to make it real.")
                store.add_system_log(
                    f"Created the {kind} \"{title}\"" if live
                    else f"Demo mode: did not really create \"{title}\"",
                    "completed")

            self.after(0, done)

        threading.Thread(target=work, daemon=True, name="google-create").start()
