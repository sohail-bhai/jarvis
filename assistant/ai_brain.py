import logging
logger = logging.getLogger(__name__)

import json
import urllib.request
import urllib.error
import traceback
from assistant import guard
from assistant.speech import speak
from assistant.config import get_setting, update_setting
import assistant.system_tasks as system_tasks
import assistant.notes as notes
import assistant.memory as memory
import assistant.email_tasks as email_tasks
import assistant.dev_tools as dev_tools
import assistant.calendar_sync as calendar_sync
import assistant.browser as browser
import assistant.gitlab_agent as gitlab_agent
import assistant.web_api as web_api
import assistant.site_memory as site_memory
import assistant.files as shared_files
import assistant.workspace as workspace
import webbrowser
import urllib.parse

def search_google_drive(query: str, limit: int = 5) -> str:
    return str(workspace.search_drive(query, limit=int(limit)))

def read_google_drive_file(file_id: str) -> str:
    return str(workspace.read_drive_file(file_id))

def upload_google_drive_file(name: str, content: str) -> str:
    return str(workspace.upload_drive_file(name, content))

def summarize_gmail_inbox(limit: int = 5) -> str:
    return workspace.summarize_emails(limit=int(limit))

def draft_gmail_message(to: str, subject: str, body: str) -> str:
    return str(workspace.draft_email(to, subject, body))

def create_google_calendar_event(summary: str, start_time_iso: str = None, duration_minutes: int = 60, description: str = None) -> str:
    return str(workspace.create_calendar_event(summary, start_time_iso, int(duration_minutes), description))

def create_google_doc(title: str, content: str = "") -> str:
    return str(workspace.create_google_doc(title, content))

def create_google_slides(title: str, slides=None) -> str:
    return str(workspace.create_google_slides(title, slides))

def open_website(url: str):
    success = webbrowser.open(url)
    return "Website opened in browser. To interact with it use: browse(url) then browser_elements() then browser_click(index)." if success else "Failed to open website."

def search_google(query: str):
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"Google search opened. Now call browse('{url}') to read the results and browser_click(index) to open a result."

def search_youtube(query: str):
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"YouTube search opened. Now call browse('{url}') to read the page, browser_elements() to list videos, then browser_click(index) to play one."

# Mapping of tool names to actual Python functions
AVAILABLE_FUNCTIONS = {
    "search_google_drive": search_google_drive,
    "read_google_drive_file": read_google_drive_file,
    "upload_google_drive_file": upload_google_drive_file,
    "summarize_gmail_inbox": summarize_gmail_inbox,
    "draft_gmail_message": draft_gmail_message,
    "create_google_calendar_event": create_google_calendar_event,
    "create_google_doc": create_google_doc,
    "create_google_slides": create_google_slides,
    "open_app": system_tasks.open_app,
    "close_app": system_tasks.close_app,
    "tell_time": system_tasks.tell_time,
    "tell_date": system_tasks.tell_date,
    "tell_battery": system_tasks.tell_battery,
    "take_screenshot": system_tasks.take_screenshot,
    "set_volume": system_tasks.set_volume,
    "mute_volume": system_tasks.mute_volume,
    "lock_laptop": system_tasks.lock_laptop,
    "shutdown_laptop": system_tasks.shutdown_laptop,
    "restart_laptop": system_tasks.restart_laptop,
    "add_note": notes.add_note,
    "read_notes": notes.read_notes,
    "clear_notes": notes.clear_notes,
    "open_website": open_website,
    "search_google": search_google,
    "search_youtube": search_youtube,
    "click_at": system_tasks.click_at,
    "double_click_at": system_tasks.double_click_at,
    "right_click_at": system_tasks.right_click_at,
    "move_mouse": system_tasks.move_mouse,
    "type_text": system_tasks.type_text,
    "press_key": system_tasks.press_key,
    "press_hotkey": system_tasks.press_hotkey,
    "wait": system_tasks.wait,
    "list_windows": system_tasks.list_windows,
    "focus_window": system_tasks.focus_window,
    "close_window": system_tasks.close_window,
    "remember_fact": memory.remember_fact,
    "search_web": system_tasks.search_web,
    "read_unread_emails": email_tasks.read_unread_emails,
    "get_weather": system_tasks.get_weather,
    "update_setting": update_setting,
    "read_screen": system_tasks.read_screen,
    "analyze_screen": system_tasks.analyze_screen,
    "propose_new_feature": system_tasks.propose_new_feature,
    "git_auto_commit_and_push": dev_tools.git_auto_commit_and_push,
    "scaffold_code": dev_tools.scaffold_code,
    "scrape_project_ideas": dev_tools.scrape_project_ideas,
    "deep_test_project": dev_tools.deep_test_project,
    "get_schedule": calendar_sync.get_upcoming_events,
    "schedule_meeting": calendar_sync.schedule_event,
    "provide_morning_briefing": system_tasks.provide_morning_briefing,
    "send_email": email_tasks.send_email,
    "ingest_document": memory.ingest_document,
    "ask_document": lambda **kwargs: ask_document(**kwargs),
    "scroll": system_tasks.scroll,
    "drag_and_drop": system_tasks.drag_and_drop,
    "read_clipboard": system_tasks.read_clipboard,
    "write_clipboard": system_tasks.write_clipboard,
    "run_terminal_command": system_tasks.run_terminal_command,
    "list_directory": system_tasks.list_directory,
    "read_file": system_tasks.read_file,
    "write_file": system_tasks.write_file,
    "get_clickable_elements": system_tasks.get_clickable_elements,
    "spawn_parallel_agents": __import__('assistant.swarm', fromlist=['']).spawn_parallel_agents,
    "run_actor_critic_research": __import__('assistant.swarm', fromlist=['']).run_actor_critic_research,
    "disable_voice_input": system_tasks.disable_voice_input,
    "enable_voice_input": system_tasks.enable_voice_input,
    "disable_speech_output": system_tasks.disable_speech_output,
    "enable_speech_output": system_tasks.enable_speech_output,
    "start_overwatch": __import__('assistant.overwatch', fromlist=['']).start_overwatch,
    "stop_overwatch": __import__('assistant.overwatch', fromlist=['']).stop_overwatch,
    "send_telegram_update": system_tasks.send_telegram_update,
    "write_to_screen_line": system_tasks.write_to_screen_line,

    # Driving a real browser, the way a person uses the web.
    "browse": browser.browse,
    "browser_read": browser.browser_read,
    "browser_elements": browser.browser_elements,
    "browser_click": browser.browser_click,
    "browser_type": browser.browser_type,
    "browser_press": browser.browser_press,
    "browser_wait_for": browser.browser_wait_for,
    "browser_screenshot": browser.browser_screenshot,
    "browser_ask_site": browser.browser_ask_site,
    "browser_fill_form": browser.browser_fill_form,
    "browser_tabs": browser.browser_tabs,
    "browser_new_tab": browser.browser_new_tab,
    "browser_switch_tab": browser.browser_switch_tab,
    "browser_wait_for_login": browser.browser_wait_for_login,
    "remember_about_site": browser.remember_about_site,

    # Any service with an API, without a module per service.
    "web_api_get": web_api.web_api_get,
    "web_api_call": web_api.web_api_call,

    # The folders shared with the phone, reachable by the agent too.
    "list_shared_files": shared_files.list_shared_files,
    "find_shared_file": shared_files.find_shared_file,
    "shared_folders": shared_files.shared_folders,

    # GitLab, through its API rather than by clicking.
    "gitlab_list_issues": gitlab_agent.gitlab_list_issues,
    "gitlab_read_issue": gitlab_agent.gitlab_read_issue,
    "gitlab_find_file": gitlab_agent.gitlab_find_file,
    "gitlab_read_file": gitlab_agent.gitlab_read_file,
    "gitlab_propose_fix": gitlab_agent.gitlab_propose_fix,
    "gitlab_merge": gitlab_agent.gitlab_merge,

}

def _tool(name, description, properties, required=None):
    """Shorthand for one entry in the schema the model is given."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties,
                           "required": required or []},
        },
    }


# Browsing and GitLab. These are written out with the same shape as the rest,
# just built by a helper because there are a lot of them.
WEB_TOOLS = [
    _tool("browse", "Open a web page in the real browser and read what is on it. "
          "Use this whenever the user names a website or asks you to look something "
          "up on a specific site.",
          {"url": {"type": "string", "description": "The address to open."}},
          ["url"]),
    _tool("browser_read", "Read the page that is currently open again, without "
          "clicking anything. Use `full` when you need the whole page.",
          {"full": {"type": "boolean", "description": "Read the long version."}}),
    _tool("browser_elements", "List everything on the current page that can be "
          "clicked or typed into, numbered. Use this when you are not sure what to "
          "click next.", {}),
    _tool("browser_click", "Click something on the page, by its number from "
          "browser_elements or by the words shown on it.",
          {"target": {"type": "string", "description": "A number, or the visible text."}},
          ["target"]),
    _tool("browser_type", "Type into a box on the page. Set submit to true to press "
          "Enter afterwards, which is how you send a search or a chat message.",
          {"target": {"type": "string", "description": "A number, or the box's label."},
           "text": {"type": "string", "description": "What to type."},
           "submit": {"type": "boolean", "description": "Press Enter after typing."}},
          ["target", "text"]),
    _tool("browser_press", "Press a single key, such as Enter or Escape.",
          {"key": {"type": "string"}}, ["key"]),
    _tool("browser_wait_for", "Wait until some text appears on the page. Use this "
          "when a site is still loading or still writing an answer.",
          {"text": {"type": "string"}, "seconds": {"type": "number"}}, ["text"]),
    _tool("browser_screenshot", "Save a picture of the page, for when the text is "
          "not enough to tell what is going on.", {}),
    _tool("browser_ask_site", "Open a site that has a chat or search box, ask it "
          "one question, wait for the answer, and bring the answer back. Use this "
          "for 'ask ChatGPT ...', 'ask Perplexity ...' and the like.",
          {"url": {"type": "string", "description": "e.g. https://chatgpt.com"},
           "prompt": {"type": "string", "description": "The question to ask."},
           "answer_appears_within": {"type": "number",
                                     "description": "Seconds to wait. Default 90."}},
          ["url", "prompt"]),

    _tool("browser_fill_form", "Fill several boxes on the page at once. Send an "
          "object of label or number to value.",
          {"fields": {"type": "object", "description": '{"Email": "me@x.com"}'}},
          ["fields"]),
    _tool("browser_tabs", "List the open browser tabs.", {}),
    _tool("browser_new_tab", "Open another tab, so a side trip does not lose the "
          "page you were on.", {"url": {"type": "string"}}),
    _tool("browser_switch_tab", "Go back to a tab by its number.",
          {"index": {"type": "number"}}, ["index"]),
    _tool("browser_wait_for_login", "When a site asks for a sign-in, call this and "
          "wait. The user signs in themselves in the window. NEVER type a password.",
          {"seconds": {"type": "number", "description": "How long to wait. Default 180."}}),
    _tool("remember_about_site", "Write down something you worked out about a site "
          "- where a page lives, which element is the search box, that it needs a "
          "login - so the next visit is faster.",
          {"url": {"type": "string"}, "note": {"type": "string"}},
          ["url", "note"]),

    _tool("web_api_get", "Read from any service's API. Use this instead of the "
          "browser whenever the service has an API - the answer is exact and it "
          "either worked or it did not. Name a stored credential with auth_secret; "
          "you never handle the value.",
          {"url": {"type": "string", "description": "Full https:// address."},
           "params": {"type": "object", "description": "Query parameters."},
           "auth_secret": {"type": "string",
                           "description": "Name of a stored credential, e.g. github_token."},
           "auth_style": {"type": "string",
                          "description": "bearer, token, private-token, x-api-key or basic."}},
          ["url"]),
    _tool("web_api_call", "Change something through a service's API: POST, PUT, "
          "PATCH or DELETE. Same credential handling as web_api_get.",
          {"method": {"type": "string"}, "url": {"type": "string"},
           "body": {"type": "object", "description": "JSON body to send."},
           "params": {"type": "object"},
           "auth_secret": {"type": "string"}, "auth_style": {"type": "string"}},
          ["method", "url"]),

    _tool("shared_folders", "Say which folders on this computer are reachable "
          "from the user's phone.", {}),
    _tool("list_shared_files", "List what is in a shared folder on this computer.",
          {"path": {"type": "string", "description": "Folder. Empty means the first share."}}),
    _tool("find_shared_file", "Find a file by name in the shared folders, for "
          "'where did I put my ...' questions.",
          {"query": {"type": "string"}}, ["query"]),

    _tool("gitlab_list_issues", "List issues on a GitLab project, so you can pick "
          "one to work on. The project looks like 'group/repository'.",
          {"project": {"type": "string"}, "state": {"type": "string"},
           "limit": {"type": "number"}}, ["project"]),
    _tool("gitlab_read_issue", "Read one GitLab issue in full, with its comments, "
          "to understand what is actually being asked for.",
          {"project": {"type": "string"}, "issue_iid": {"type": "number"}},
          ["project", "issue_iid"]),
    _tool("gitlab_find_file", "Search a GitLab repository for the file an issue is "
          "about, before trying to change anything.",
          {"project": {"type": "string"}, "query": {"type": "string"}},
          ["project", "query"]),
    _tool("gitlab_read_file", "Read a file from a GitLab repository, so your fix is "
          "written against the real code rather than a guess.",
          {"project": {"type": "string"}, "path": {"type": "string"},
           "ref": {"type": "string", "description": "Branch. Defaults to the main one."}},
          ["project", "path"]),
    _tool("gitlab_propose_fix", "Put a fix on its own branch and open a merge "
          "request. Send the complete new contents of the file, not a patch. This "
          "does not merge anything.",
          {"project": {"type": "string"}, "issue_iid": {"type": "number"},
           "path": {"type": "string"},
           "new_content": {"type": "string",
                           "description": "The whole file, after your fix."},
           "summary": {"type": "string", "description": "One line on what changed."}},
          ["project", "issue_iid", "path", "new_content"]),
    _tool("gitlab_merge", "Merge a merge request. Only do this when the user has "
          "asked for it - it changes the real repository.",
          {"project": {"type": "string"}, "merge_request_iid": {"type": "number"}},
          ["project", "merge_request_iid"]),
]


# Handing a small model every tool at once is expensive: the whole schema is
# re-read on every turn, and on a CPU that is the difference between a step
# taking half a minute and taking two. So each request gets the tools it
# plausibly needs, chosen by what the user actually asked for.
TOOL_GROUPS = {
    "web": (
        ("http", "https", "www.", ".com", ".org", ".io", "website", "site",
         "web", "browser", "browse", "open ", "search", "google it", "look up",
         "chatgpt", "perplexity", "online", "internet", "page", "click", "login",
         "log in", "sign in", "form", "tab"),
        ("browse", "browser_read", "browser_elements", "browser_click",
         "browser_type", "browser_press", "browser_wait_for", "browser_screenshot",
         "browser_ask_site", "browser_fill_form", "browser_tabs", "browser_new_tab",
         "browser_switch_tab", "browser_wait_for_login", "remember_about_site",
         "web_api_get", "web_api_call", "search_web"),
    ),
    "gitlab": (
        ("gitlab", "issue", "merge request", "repository", "repo", "branch",
         "commit", "pipeline", "mr "),
        ("gitlab_list_issues", "gitlab_read_issue", "gitlab_find_file",
         "gitlab_read_file", "gitlab_propose_fix", "gitlab_merge",
         "web_api_get", "web_api_call"),
    ),
    "google": (
        ("email", "mail", "gmail", "inbox", "drive", "calendar", "meeting",
         "schedule", "document", "doc", "sheet", "spreadsheet", "slides",
         "presentation", "deck"),
        ("read_unread_emails", "send_email", "summarize_gmail_inbox",
         "draft_gmail_message", "search_google_drive", "read_google_drive_file",
         "upload_google_drive_file", "create_google_doc", "create_google_slides",
         "get_schedule", "schedule_meeting", "create_google_calendar_event"),
    ),
    "computer": (
        ("open ", "app", "volume", "screenshot", "screen", "click", "type",
         "battery", "lock", "shutdown", "restart", "file", "folder", "terminal",
         "command", "clipboard", "window"),
        ("open_app", "close_app", "set_volume", "mute_volume", "take_screenshot",
         "read_screen", "analyze_screen", "get_clickable_elements", "click_at",
         "double_click_at", "right_click_at", "move_mouse", "type_text",
         "press_key", "press_hotkey", "wait", "list_windows", "focus_window",
         "close_window", "find_and_click_text", "scroll", "drag_and_drop",
         "lock_laptop", "run_terminal_command",
         "list_directory", "read_file", "write_file", "read_clipboard",
         "write_clipboard", "tell_battery"),
    ),
    "notes": (
        ("note", "remember", "remind", "memory", "wrote down", "document",
         "pdf", "textbook"),
        ("add_note", "read_notes", "clear_notes", "remember_fact",
         "ingest_document", "ask_document"),
    ),
    "files": (
        ("file", "folder", "document", "pdf", "photo", "picture", "download",
         "upload", "send me", "where did i put", "shared", "phone"),
        ("shared_folders", "list_shared_files", "find_shared_file", "read_file",
         "write_file", "list_directory"),
    ),
}

# When nothing in the request points anywhere, these are what a person most
# often means.
DEFAULT_TOOL_NAMES = (
    "browse", "browser_ask_site", "web_api_get", "search_web", "tell_time",
    "tell_date", "tell_battery", "open_app", "add_note", "remember_fact",
    "read_screen", "send_telegram_update",
)

# A ceiling, because two matching groups should not undo the point of this.
MAX_TOOLS_PER_CALL = 22


def select_tools(instruction, tools=None):
    """The tools worth offering for this request, rather than all of them."""
    catalogue = tools if tools is not None else LLM_TOOLS
    text = str(instruction or "").lower()

    # Score each group by how much of the request points at it, so "fix the
    # login issue in gitlab repo x" leads with GitLab rather than with the
    # browser tools that "login" happens to match too.
    scored = []
    for group, (triggers, names) in TOOL_GROUPS.items():
        hits = sum(1 for trigger in triggers if trigger in text)
        if hits:
            scored.append((hits, group, names))

    wanted = []
    for _, _, names in sorted(scored, key=lambda item: item[0], reverse=True):
        wanted.extend(names)

    if not wanted:
        wanted = list(DEFAULT_TOOL_NAMES)

    chosen, seen = [], set()
    for name in wanted:
        if name in seen:
            continue
        schema = next((item for item in catalogue
                       if item["function"]["name"] == name), None)
        if schema is not None:
            chosen.append(schema)
            seen.add(name)
        if len(chosen) >= MAX_TOOLS_PER_CALL:
            break

    return chosen or catalogue


# The JSON schema describing our tools to the LLM
LLM_TOOLS = WEB_TOOLS + [
    {
        "type": "function",
        "function": {
            "name": "search_google_drive",
            "description": "Searches Google Drive for files, presentations, spreadsheets, or documents matching the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term or filename to look for in Google Drive."},
                    "limit": {"type": "integer", "description": "Maximum number of files to return (default 5)."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_google_drive_file",
            "description": "Retrieves the content or text excerpt of a specific file in Google Drive by its file ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "The Google Drive file ID to read."}
                },
                "required": ["file_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "upload_google_drive_file",
            "description": "Uploads a new file or document to Google Drive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The filename including extension (e.g. 'Project_Notes.txt')."},
                    "content": {"type": "string", "description": "The text content of the file."}
                },
                "required": ["name", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_gmail_inbox",
            "description": "Retrieves recent unread emails from Gmail and returns a clean executive summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of recent unread emails to inspect (default 5)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_gmail_message",
            "description": "Creates an email draft in Gmail without sending it immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address."},
                    "subject": {"type": "string", "description": "Email subject line."},
                    "body": {"type": "string", "description": "Body text of the draft email."}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_google_calendar_event",
            "description": "Schedules a new meeting or event on Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Title or summary of the meeting/event."},
                    "start_time_iso": {"type": "string", "description": "ISO 8601 start timestamp (e.g. '2026-09-04T18:00:00Z'). Defaults to 1 hour from now if omitted."},
                    "duration_minutes": {"type": "integer", "description": "Duration in minutes (default 60)."},
                    "description": {"type": "string", "description": "Optional notes or meeting agenda."}
                },
                "required": ["summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_google_doc",
            "description": "Creates a new Google Document with a title and optional initial content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the Google Document."},
                    "content": {"type": "string", "description": "Initial text content to insert into the document."}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_google_slides",
            "description": "Creates a Google Slides presentation from a title and an outline of slides.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the presentation."},
                    "slides": {
                        "type": "array",
                        "description": "One entry per slide: a title string, or an object with a title and bullets.",
                        "items": {"type": "string"}
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Closes or terminates a running desktop application by name (e.g. 'notepad', 'chrome', 'netflix', 'spotify', 'calculator').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to close."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram_update",
            "description": "Sends a message directly to the user's Telegram app. Useful for sending updates, reports, or asking questions when the user is away from their computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_text": {
                        "type": "string",
                        "description": "The message to send to the user on Telegram."
                    }
                },
                "required": ["message_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_overwatch",
            "description": "Start the AI Overwatch mode, which visually monitors the screen in a background thread and automatically clicks UI elements matching given rules.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rules": {
                        "type": "array",
                        "description": "List of rule objects. E.g. [{\"target_text\": \"submit\", \"auto_click\": true, \"require_focus\": false, \"pattern\": \"exact\"}]",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target_text": {"type": "string"},
                                "auto_click": {"type": "boolean"},
                                "require_focus": {"type": "boolean"},
                                "pattern": {"type": "string", "enum": ["exact", "contains"]}
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_overwatch",
            "description": "Deactivates Overwatch Mode. VAVE will stop constantly scanning the screen in the background."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "disable_speech_output",
            "description": "Mutes VAVE's Text-to-Speech voice so he stops speaking out loud. He will only reply via text. Use this if the user wants quiet time."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enable_speech_output",
            "description": "Unmutes VAVE's Text-to-Speech voice so he can speak out loud again."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "disable_voice_input",
            "description": "Temporarily turns off VAVE's microphone, stopping him from listening to the user's voice or wake words. Useful if the user wants quiet time or wants to type instead."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enable_voice_input",
            "description": "Turns the microphone and wake word detection back on so VAVE can hear the user again."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_parallel_agents",
            "description": "Dynamically spawns multiple sub-agents to execute tasks in parallel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_list": {
                        "type": "string",
                        "description": "A string representation of a Python list of dicts. Example: \"[ {'role': 'Coder', 'task': 'write a python script'}, {'role': 'Researcher', 'task': 'find python docs'} ]\""
                    }
                },
                "required": ["task_list"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_actor_critic_research",
            "description": "Triggers the Deep Web Researcher Swarm. It spawns an Actor agent to browse and research, and a Critic agent to review the draft, refining it iteratively.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The complex topic to research deeply."}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scrolls the mouse wheel up (positive) or down (negative).",
            "parameters": {
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "description": "Number of clicks to scroll (e.g. 500 or -500)"}
                },
                "required": ["clicks"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "drag_and_drop",
            "description": "Drags the mouse from a start coordinate to an end coordinate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_x": {"type": "integer"},
                    "start_y": {"type": "integer"},
                    "end_x": {"type": "integer"},
                    "end_y": {"type": "integer"}
                },
                "required": ["start_x", "start_y", "end_x", "end_y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_clipboard",
            "description": "Reads text from the system clipboard."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_clipboard",
            "description": "Writes text to the system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to write to clipboard"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": "Executes a background terminal/shell command and returns the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to run (e.g. 'ping google.com', 'npm install')"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists files and folders in a given directory path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to list (default is '.')"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the contents of a local text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes text content to a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clickable_elements",
            "description": "Scans the current active window and returns a list of clickable elements with their text and (x, y) coordinates."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ingest_document",
            "description": "Reads a PDF or text file and saves it to the vector knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to the document file"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_document",
            "description": "Searches the vector knowledge base to answer a question based on ingested documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to ask about the documents"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Sends an email to a recipient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_address": {"type": "string", "description": "The recipient's email address"},
                    "subject": {"type": "string", "description": "The subject of the email"},
                    "body": {"type": "string", "description": "The main text body of the email"}
                },
                "required": ["to_address", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "provide_morning_briefing",
            "description": "Synthesizes the user's weather, schedule, and unread emails into a concise briefing."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": "Retrieves upcoming events from the user's Google Calendar."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedules an event on Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "The title of the meeting"},
                    "time_str": {"type": "string", "description": "The start time in ISO 8601 format, e.g. 2024-05-15T10:00:00-07:00"}
                },
                "required": ["summary", "time_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Opens a desktop application on the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the app (e.g., chrome, notepad, calculator, vscode)"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tell_time",
            "description": "Speaks the current local time.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tell_battery",
            "description": "Checks and speaks the current battery percentage and power status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Sets the system volume to a specific level (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume level from 0 to 100"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Searches Google for a given query in the web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": "Searches YouTube for a given query in the web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Types text automatically using the keyboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to type"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Presses a specific keyboard key (e.g., 'enter', 'tab', 'esc', 'space').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The key to press"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_at",
            "description": "Clicks at specific screen coordinates (x, y). Use get_clickable_elements first to find exact coordinates of buttons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "The X screen coordinate"},
                    "y": {"type": "integer", "description": "The Y screen coordinate"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Captures a screenshot of the user's primary display and saves it.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Opens a website URL in the user's default browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The website URL or name to open"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Saves a fact, user preference, or piece of context to permanent memory so you can recall it in the future.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The explicit fact to remember (e.g. 'The user's favorite color is blue')"}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the internet for information, news, or answers and returns a summary of the top results. Use this when you need real-time or factual knowledge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query (e.g., 'who won the super bowl 2024')"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_unread_emails",
            "description": "Reads the user's latest unread emails from Gmail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of emails to read (default 5)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Gets the live weather and temperature for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_setting",
            "description": "Dynamically change VAVE settings (like voice speed/volume).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The setting key, e.g. 'voice_rate' (speed) or 'voice_volume'."},
                    "value": {"type": "number", "description": "The new value (e.g. 150 for rate, or 0.5 for volume)."}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_screen",
            "description": "Reads all visible text or a specific line from the active window or screen (such as Notepad, Word, browser, code editor). Use this when the user asks to read, inspect, or get content or lines from an open application or screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "line_number": {
                        "type": "integer",
                        "description": "Optional 1-indexed line number to read (e.g. 2 for 2nd line, 10 for 10th line). If omitted, reads all text."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_to_screen_line",
            "description": "Writes, adds, or appends text onto a specific line in an open document or editor window (such as Notepad, Word, or code editor).",
            "parameters": {
                "type": "object",
                "properties": {
                    "line_number": {
                        "type": "integer",
                        "description": "The 1-indexed line number to write or append text to."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to write or add onto the line."
                    }
                },
                "required": ["line_number", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_screen",
            "description": "Uses a local Vision AI to look at a screenshot and answer a question about the screen. Use this when the user asks 'what am I looking at', 'describe the image', or asks about visual layout (not just text).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The question to ask the Vision AI about the screen (e.g. 'What is on the screen?', 'What game is the user playing?')"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_new_feature",
            "description": "Adds a missing feature or tool to the project's developer roadmap (plan.md). Call this when the user asks you to do something you cannot currently do.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_name": {"type": "string", "description": "Short name for the feature"},
                    "description": {"type": "string", "description": "Brief description of what the user wanted you to do"}
                },
                "required": ["feature_name", "description"]
            }
        }
    },
    {"type": "function", "function": {"name": "tell_date", "description": "Speaks the current date.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "mute_volume", "description": "Mutes the system volume.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "lock_laptop", "description": "Locks the computer.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "shutdown_laptop", "description": "Shuts down the computer.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "restart_laptop", "description": "Restarts the computer.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "read_notes", "description": "Reads all saved notes.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "clear_notes", "description": "Clears all saved notes.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "add_note", "description": "Saves a new note.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "The note text"}}, "required": ["text"]}}}
]

# Short-term Memory (Conversation History)
def get_system_prompt():
    return (
        "You are VAVE, a highly intelligent AI desktop assistant. "
        "Your personality is a friendly buddy who has the user's back. You make funny jokes and use casual, conversational language instead of being a robotic servant. "
        "Keep your text answers brief and to the point (no markdown).\n\n"
        "CRITICAL RULE: NEVER ask for permission to use tools. When the user asks you to do something, IMMEDIATELY output the JSON tool call to execute it! Do NOT ask 'shall I proceed?'. Just DO IT.\n\n"
        "NATIVE APPS (Notepad, File Explorer, VS Code, etc): Use `open_app`, `read_screen`, `type_text`, `press_key`, `scroll`, `run_terminal_command`. "
        "For clicking buttons inside native Windows apps, use `get_clickable_elements` then `click_at`.\n\n"
        "WEBSITES & BROWSERS: ALWAYS use the Playwright browser tools. NEVER use get_clickable_elements or click_at for web tasks — they do not work in browsers.\n"
        "The correct web flow is ALWAYS:\n"
        "  Step 1: Call `browse(url)` OR `search_youtube(query)` OR `search_google(query)` to open the page.\n"
        "  Step 2: Call `browser_elements()` to get a numbered list of everything clickable on the page.\n"
        "  Step 3: Call `browser_click(index)` with the number of the element you want.\n"
        "  Step 4: If needed, call `browser_type(index, text)` to type into a field.\n"
        "ANTI-HALLUCINATION RULE: Never claim 'the video is playing' or 'the task is done' without actually calling browser_click. If browser_elements shows nothing useful, call browse(url) again to reload.\n\n"
        "CRITICAL MULTI-STEP SEQUENCING: Execute actions one at a time. After each tool call, read the result and decide the next step. NEVER output just conversational text if there are remaining actions to take.\n\n"
        "CRITICAL READING RULE: When asked to read a specific line, call `read_screen(line_number=N)` immediately.\n\n"
        "CRITICAL RULE: Always use the provided tools to accomplish tasks, chaining them if necessary.\n\n"

        "USING THE WEB: You drive a real browser. Never say you cannot open a "
        "website - open it. The loop is always the same: `browse` the page, "
        "read what came back, then act on what is ACTUALLY there. Every action "
        "returns the page's numbered elements, so click and type by those "
        "numbers or by the words shown on screen. If something is missing, call "
        "`browser_elements` and look again rather than guessing a selector. "
        "When a site has one obvious box to type a question into - ChatGPT, "
        "Perplexity, a search engine - `browser_ask_site` does the whole "
        "round trip in one call and brings the answer back.\n\n"

        "SERVICES WITH AN API: prefer `web_api_get` and `web_api_call` over "
        "clicking whenever the service has an API - GitHub, Jira, Linear, "
        "Notion, Slack, a home server, anything. Name the credential with "
        "`auth_secret` (for example 'github_token') and VAVE resolves it; you "
        "never see or send the value itself. If the credential is missing, say "
        "which one to store rather than trying the browser instead.\n\n"
        "GOOGLE WORKSPACE: If the user asks you to create a Google Doc, Google Calendar event, or draft an email, you MUST use the provided workspace tools (`create_google_doc`, `create_google_calendar_event`, `draft_gmail_message`). NEVER pretend you did it. NEVER output a fake URL. You must emit the JSON tool call.\n\n"

        "SIGNING IN: you never type a password and never read one. If a page "
        "asks for a sign-in, call `browser_wait_for_login` and let the user do "
        "it in the window, then carry on where you left off.\n\n"

        "LEARNING A SITE: when you work out where something lives or how a "
        "site behaves, call `remember_about_site`. Those notes come back the "
        "next time you open that domain, so the second visit is faster.\n\n"

        "WORKING ON GITLAB: use the GitLab tools, not the browser, because they "
        "make a real commit instead of a click that might have missed. The "
        "order that works: `gitlab_list_issues` to see what is open, "
        "`gitlab_read_issue` to understand what is actually being asked, "
        "`gitlab_find_file` then `gitlab_read_file` to see the real code, then "
        "`gitlab_propose_fix` with the COMPLETE new contents of the file. Never "
        "send a diff or a snippet - send the whole file after your change. "
        "Proposing opens a merge request and stops there. Only call "
        "`gitlab_merge` when the user has explicitly asked you to merge."

    )

conversation_history = []

def init_history():
    global conversation_history
    if not conversation_history:
        conversation_history = [{"role": "system", "content": get_system_prompt()}]


def ask_document(question):
    from assistant.memory import query_document
    from assistant.speech import speak
    
    speak("Searching the knowledge base.")
    context = query_document(question)
    
    if "No relevant information" in context or "Error" in context:
        return context
        
    prompt = f"Based on the following document excerpts, answer the user's question.\n\n[Excerpts]:\n{context}\n\n[Question]: {question}\n\nAnswer:"
    
    response = query_local_llm_chat([{"role": "user", "content": prompt}], model=get_setting("llm_model", "qwen2.5:3b"))
    answer = response.get("content", "") if isinstance(response, dict) else str(response)
    
    return answer if answer else "Could not generate an answer."

def query_local_llm_chat(messages, model="qwen2.5:3b", tools=None):
    """
    Queries the local Ollama instance using the /api/chat endpoint, or Featherless AI if configured.
    """
    featherless_key = get_setting("featherless_api_key", "")
    
    if featherless_key:
        url = "https://api.featherless.ai/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {featherless_key}'
        }
        payload = {
            "model": get_setting("featherless_model", "meta-llama/Meta-Llama-3.1-8B-Instruct"),
            "messages": messages,
            "stream": False
        }
        if tools is not False:
            payload["tools"] = tools if tools is not None else LLM_TOOLS
            
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=int(get_setting("llm_timeout_seconds", 300))) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("choices", [{}])[0].get("message", {})
        except Exception as e:
            logger.info(f"[Featherless API Error] {e}")
            return None

    # Fallback to Local Ollama
    url = str(get_setting("ollama_url", "http://localhost:11434")).rstrip("/") + "/api/chat"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "60m",
        "options": {
            "num_ctx": 8192
        }
    }
    
    if tools is not False:
        payload["tools"] = tools if tools is not None else LLM_TOOLS
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req, timeout=int(get_setting("llm_timeout_seconds", 300))) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("message", {})
    except urllib.error.URLError as e:
        logger.info(f"[AI Brain Error] Could not connect to local LLM: {e}")
        return None
    except Exception as e:
        logger.info(f"[AI Brain Error] {e}")
        return None

# The task-execution loop tells the model it is working a single control plane
# step, so it finishes the step instead of chatting about it.
STEP_SYSTEM_NOTE = (
    "You are executing one step of a task the user already approved. "
    "Use your tools to actually carry the step out, then reply with one short "
    "sentence describing what you did and what you found. "
    "Do not ask questions and do not ask for permission."
)


class StepCancelled(Exception):
    """The control plane stopped this step part-way through."""


def _agent_loop(conversation, extra_messages=None, auto_confirm=False, max_steps=5,
                should_continue=None, authorize=None, resolve_secrets=None,
                tools=None):
    """Run the tool-calling loop over `conversation`, which is mutated in place.

    `extra_messages` are injected into the payload just before the latest user
    message without being stored in the caller's history, so retrieved memories
    never accumulate in short-term memory.

    `should_continue` is checked between model turns and before every tool
    call, so a long task can be stopped without waiting for it to finish.
    `authorize(tool_name)` returns `(allowed, reason)`; a refused tool is
    reported back to the model rather than run. `resolve_secrets` turns
    `secret://name` in the model's arguments into the real value at the moment
    the tool runs, so the credential is never in the model's context.

    Returns the model's final text, or None if the local brain is unreachable.
    """
    previous_tool_calls_repr = None

    def _keep_going():
        if should_continue is not None and not should_continue:
            raise StepCancelled("Stopped part-way.")

    for step in range(max_steps):
        _keep_going()
        model_name = get_setting("llm_model", "qwen2.5:3b")

        # Inject dynamic context into the payload without mutating history
        current_messages = list(conversation)
        for extra in (extra_messages or []):
            current_messages.insert(-1, extra)
        if auto_confirm:
            current_messages.insert(-1, {"role": "system", "content": "CRITICAL EXCEPTION: You are executing a Routine. IGNORE the rule about asking for permission. DO NOT ask 'Shall I proceed?'. Execute the tool immediately."})

        message = query_local_llm_chat(current_messages, model=model_name,
                                       tools=tools)

        if not message:
            return None

        # Append Assistant's response to history
        conversation.append(message)

        # Check if the LLM decided to call a tool
        if "tool_calls" in message and message["tool_calls"]:
            current_tool_calls_repr = str(message["tool_calls"])
            if current_tool_calls_repr == previous_tool_calls_repr:
                logger.info("[VAVE] Caught LLM in an infinite loop! Breaking out.")
                conversation.append({
                    "role": "system",
                    "content": "You are repeating the same tool call. It failed or wasn't helpful. Give up and tell the user."
                })
                continue
            previous_tool_calls_repr = current_tool_calls_repr

            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args_dict = tool_call["function"].get("arguments", {})

                _keep_going()

                if authorize is not None:
                    allowed, refusal = authorize(func_name)
                    if not allowed:
                        logger.info(f"Tool {func_name} not authorised: {refusal}")
                        conversation.append({
                            "role": "tool",
                            "content": f"Not allowed: {refusal}",
                            "name": func_name
                        })
                        continue

                if func_name in AVAILABLE_FUNCTIONS:
                    func_to_call = AVAILABLE_FUNCTIONS[func_name]
                    logger.info(f"[VAVE Executing] {func_name}({args_dict})")

                    try:
                        if resolve_secrets is not None:
                            args_dict = resolve_secrets(args_dict)
                        args_dict = guard.coerce_args(func_to_call, args_dict)
                        result = guard.call(func_to_call, **args_dict)
                        result_str = str(result) if result is not None else "Success"

                        if len(result_str) > 2000:
                            result_str = result_str[:2000] + "... [TRUNCATED DUE TO LENGTH]"

                        conversation.append({
                            "role": "tool",
                            "content": result_str,
                            "name": func_name
                        })

                    except guard.ToolDenied as e:
                        logger.info(f"Tool {func_name} denied: {e}")
                        conversation.append({
                            "role": "tool",
                            "content": f"Denied by safety guard: {e}",
                            "name": func_name
                        })
                    except Exception as e:
                        logger.info(f"Error executing tool {func_name}: {e}")
                        conversation.append({
                            "role": "tool",
                            "content": f"Failed: {e}",
                            "name": func_name
                        })
                else:
                    logger.info(f"LLM tried to call unknown tool: {func_name}")
                    conversation.append({
                        "role": "tool",
                        "content": f"Tool {func_name} does not exist.",
                        "name": func_name
                    })
            # After executing all tools in this step, loop continues to ask LLM what's next
            continue

        # No tool calls means the model answered in words. That ends the turn.
        return message.get("content", "")

    # The loop ran out of steps. Report what was said last rather than nothing.
    return ""


def _memory_message(query):
    """Relevant permanent memories, as a system message for one turn."""
    relevant_memories = memory.get_relevant_memories_text(query)
    return {
        "role": "system",
        "content": f"Here are relevant permanent memories related to the user's current request:\n{relevant_memories}"
    }


def ask_ai(command, auto_confirm=False):
    """
    Handles conversational requests by routing them to the local LLM.
    Supports tool calling and short-term memory.
    """
    global conversation_history
    init_history()

    clean_command = command.strip()

    if not clean_command:
        return

    # 1. Append user command to history
    conversation_history.append({"role": "user", "content": clean_command})

    # 2. Keep history from growing indefinitely (keep last 10 messages + system prompt)
    if len(conversation_history) > 11:
        conversation_history = [conversation_history[0]] + conversation_history[-10:]

    # 3. Retrieve relevant permanent memories based on current query (RAG)
    reply = _agent_loop(conversation_history,
                        extra_messages=[_memory_message(clean_command)],
                        tools=select_tools(clean_command),
                        auto_confirm=auto_confirm)

    if reply is None:
        speak("I'm sorry, I couldn't reach my local brain. Please ensure Ollama is running.")
        conversation_history.pop()  # Remove failed prompt
        return None

    if reply:
        speak(reply)
    return reply


def run_task_step(instruction, context="", auto_confirm=True,
                  should_continue=None, authorize=None, resolve_secrets=None,
                  max_steps=None):
    """Carry out one control plane step with the same tools as the voice loop.

    The control plane calls this. It runs in its own short conversation so a
    background task never disturbs what the user is talking about, and it
    returns the outcome as text instead of speaking it - the timeline and the
    mobile client are the audience here, not the speakers.

    Raises RuntimeError if the local model cannot be reached, so the control
    plane can record an honest failure instead of a silent success.
    """
    conversation = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "system", "content": STEP_SYSTEM_NOTE},
    ]
    if context:
        conversation.append({
            "role": "system",
            "content": f"Earlier steps of this task:\n{context}",
        })
    conversation.append({"role": "user", "content": instruction})

    # Offer the tools this step plausibly needs. On a small local model the
    # whole schema is re-read every turn, so this is the difference between a
    # step finishing and a step timing out.
    reply = _agent_loop(conversation,
                        tools=select_tools(f"{instruction} {context}"),
                        extra_messages=[_memory_message(instruction)],
                        auto_confirm=auto_confirm,
                        max_steps=max_steps or get_setting("agent_max_steps", 15),
                        should_continue=should_continue, authorize=authorize,
                        resolve_secrets=resolve_secrets)

    if reply is None:
        raise RuntimeError("Could not reach the local model. Is Ollama running?")

    return reply.strip() or "Done."


# Register guards
for t in ["run_terminal_command", "shutdown_laptop", "restart_laptop", "clear_notes", "write_file", "disable_voice_input", "disable_speech_output"]:
    if t in AVAILABLE_FUNCTIONS:
        guard.register("destructive")(AVAILABLE_FUNCTIONS[t])
for t in ["update_setting", "take_screenshot", "read_file", "send_email", "git_auto_commit_and_push", "spawn_parallel_agents", "run_actor_critic_research", "send_telegram_update", "upload_google_drive_file", "draft_gmail_message", "create_google_calendar_event", "create_google_doc", "create_google_slides"]:
    if t in AVAILABLE_FUNCTIONS:
        guard.register("sensitive")(AVAILABLE_FUNCTIONS[t])
