"""The catalog of things an agent can ask to do.

Agents never receive open access to Gmail, the filesystem or the cloud. They
ask for one named capability at a time, and every capability carries a default
risk level, which is what decides whether the user is interrupted.

The names are namespaced and stable: clients, policies and the Phase 2
integrations all key off these exact strings, so add to this catalog rather
than inventing names at the call site.
"""

from assistant.control.models import RiskLevel, matches_pattern

# capability -> (risk, what it means in plain language)
CATALOG = {
    # -- Google Workspace -------------------------------------------------
    "google.gmail.read": (RiskLevel.MEDIUM, "Read your email"),
    "google.gmail.send": (RiskLevel.HIGH, "Send email as you"),
    "google.drive.read": (RiskLevel.MEDIUM, "Read your Drive files"),
    "google.drive.write": (RiskLevel.HIGH, "Create or change Drive files"),
    "google.drive.delete": (RiskLevel.CRITICAL, "Delete Drive files"),
    "google.calendar.read": (RiskLevel.MEDIUM, "Read your calendar"),
    "google.calendar.write": (RiskLevel.HIGH, "Create or change events"),

    # -- Browser ----------------------------------------------------------
    "browser.navigate": (RiskLevel.LOW, "Open web pages"),
    "browser.read": (RiskLevel.LOW, "Read what is on a page"),
    "browser.download": (RiskLevel.MEDIUM, "Download files"),
    "browser.upload": (RiskLevel.HIGH, "Upload your files to a website"),
    "browser.purchase": (RiskLevel.CRITICAL, "Buy something"),

    # -- This computer ----------------------------------------------------
    "filesystem.read": (RiskLevel.MEDIUM, "Read files on this computer"),
    "filesystem.write": (RiskLevel.HIGH, "Write files on this computer"),
    "filesystem.delete": (RiskLevel.CRITICAL, "Delete files on this computer"),
    "system.screen.read": (RiskLevel.MEDIUM, "See what is on screen"),
    "system.input.control": (RiskLevel.HIGH, "Control the mouse and keyboard"),
    "system.shell.run": (RiskLevel.CRITICAL, "Run terminal commands"),
    "system.power": (RiskLevel.HIGH, "Lock, restart or shut down"),
    "system.settings.write": (RiskLevel.MEDIUM, "Change JARVIS settings"),
    "system.notify": (RiskLevel.LOW, "Send you a message"),

    # -- Cloud (Phase 2 builds on these names) ----------------------------
    "gcp.logging.read": (RiskLevel.MEDIUM, "Read cloud logs"),
    "gcp.storage.read": (RiskLevel.MEDIUM, "Read cloud storage"),
    "gcp.storage.write": (RiskLevel.HIGH, "Write to cloud storage"),
    "gcp.cloud_run.deploy": (RiskLevel.CRITICAL, "Deploy to production"),
    "gcp.iam.write": (RiskLevel.CRITICAL, "Change who has access"),

    # -- Knowledge --------------------------------------------------------
    "memory.read": (RiskLevel.LOW, "Read what JARVIS remembers"),
    "memory.write": (RiskLevel.MEDIUM, "Remember something new"),
    "web.search": (RiskLevel.LOW, "Search the web"),
}

# The tools in ai_brain map onto the same capability names, so the voice path
# and an agent asking over the API are judged by one set of rules.
TOOL_CAPABILITIES = {
    "run_terminal_command": "system.shell.run",
    "write_file": "filesystem.write",
    "read_file": "filesystem.read",
    "list_directory": "filesystem.read",
    "shutdown_laptop": "system.power",
    "restart_laptop": "system.power",
    "lock_laptop": "system.power",
    "send_email": "google.gmail.send",
    "read_unread_emails": "google.gmail.read",
    "get_schedule": "google.calendar.read",
    "schedule_meeting": "google.calendar.write",
    "read_screen": "system.screen.read",
    "analyze_screen": "system.screen.read",
    "get_clickable_elements": "system.screen.read",
    "take_screenshot": "system.screen.read",
    "click_at": "system.input.control",
    "type_text": "system.input.control",
    "press_key": "system.input.control",
    "scroll": "system.input.control",
    "drag_and_drop": "system.input.control",
    "find_and_click_text": "system.input.control",
    "open_website": "browser.navigate",
    "search_google": "web.search",
    "search_youtube": "web.search",
    "search_web": "web.search",
    "update_setting": "system.settings.write",
    "remember_fact": "memory.write",
    "ingest_document": "memory.write",
    "send_telegram_update": "system.notify",

    # Google Workspace gateway (assistant/workspace/).
    "search_google_drive": "google.drive.read",
    "read_google_drive_file": "google.drive.read",
    "upload_google_drive_file": "google.drive.write",
    "create_google_doc": "google.drive.write",
    "summarize_gmail_inbox": "google.gmail.read",
    "draft_gmail_message": "google.gmail.send",
    "create_google_calendar_event": "google.calendar.write",

    # Local tools that touch something a person would want a say over.
    "git_auto_commit_and_push": "system.shell.run",
    "scaffold_code": "filesystem.write",
    "deep_test_project": "system.shell.run",
    "read_clipboard": "system.screen.read",
    "write_clipboard": "system.input.control",
    "clear_notes": "filesystem.write",
    "add_note": "filesystem.write",
    "read_notes": "filesystem.read",
    "ask_document": "memory.read",
    "start_overwatch": "system.input.control",
    "stop_overwatch": "system.notify",
    "disable_voice_input": "system.settings.write",
    "enable_voice_input": "system.settings.write",
    "disable_speech_output": "system.settings.write",
    "enable_speech_output": "system.settings.write",
    "provide_morning_briefing": "google.calendar.read",
    "scrape_project_ideas": "web.search",
    "spawn_parallel_agents": "web.search",
    "run_actor_critic_research": "web.search",
}

# Anything not in the catalog is treated as this risky, because an unknown
# capability is exactly the case where guessing low would be wrong.
UNKNOWN_RISK = RiskLevel.CRITICAL


def is_known(capability):
    return capability in CATALOG


def risk_for(capability):
    """The risk level of a capability. Unknown names are treated as critical."""
    entry = CATALOG.get(capability)
    return entry[0] if entry else UNKNOWN_RISK


def describe(capability):
    """Plain language for the approval screen, never the raw name alone."""
    entry = CATALOG.get(capability)
    return entry[1] if entry else f"Do something JARVIS does not recognise ({capability})"


def capability_for_tool(tool_name):
    """The capability a JARVIS tool needs, or '' when it needs none."""
    return TOOL_CAPABILITIES.get(tool_name, "")


def namespace(capability):
    """`google.gmail.send` -> `google.gmail`, for grouping in a UI."""
    return capability.rsplit(".", 1)[0] if "." in capability else capability


def catalog(prefix=""):
    """The catalog as plain dicts, optionally filtered by a pattern."""
    return [
        {"capability": name, "risk": risk.value, "description": description,
         "namespace": namespace(name)}
        for name, (risk, description) in sorted(CATALOG.items())
        if not prefix or matches_pattern(prefix, name)
    ]
