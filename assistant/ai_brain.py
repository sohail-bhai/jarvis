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

def open_website(url: str):
    return webbrowser.open(url)

def search_google(query: str):
    return webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}")

def search_youtube(query: str):
    return webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}")

# Mapping of tool names to actual Python functions
AVAILABLE_FUNCTIONS = {
    "search_google_drive": search_google_drive,
    "read_google_drive_file": read_google_drive_file,
    "upload_google_drive_file": upload_google_drive_file,
    "summarize_gmail_inbox": summarize_gmail_inbox,
    "draft_gmail_message": draft_gmail_message,
    "create_google_calendar_event": create_google_calendar_event,
    "create_google_doc": create_google_doc,
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
    "type_text": system_tasks.type_text,
    "press_key": system_tasks.press_key,
    "find_and_click_text": system_tasks.find_and_click_text,
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
    "send_telegram_update": system_tasks.send_telegram_update
}

# The JSON schema describing our tools to the LLM
LLM_TOOLS = [
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
            "description": "Deactivates Overwatch Mode. JARVIS will stop constantly scanning the screen in the background."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "disable_speech_output",
            "description": "Mutes JARVIS's Text-to-Speech voice so he stops speaking out loud. He will only reply via text. Use this if the user wants quiet time."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enable_speech_output",
            "description": "Unmutes JARVIS's Text-to-Speech voice so he can speak out loud again."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "disable_voice_input",
            "description": "Temporarily turns off JARVIS's microphone, stopping him from listening to the user's voice or wake words. Useful if the user wants quiet time or wants to type instead."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enable_voice_input",
            "description": "Turns the microphone and wake word detection back on so JARVIS can hear the user again."
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
            "name": "find_and_click_text",
            "description": "Scans the screen for specific text and clicks it. Use this to click buttons like 'Save', 'Submit', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_text": {"type": "string", "description": "The exact text to look for and click"}
                },
                "required": ["target_text"]
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
            "description": "Dynamically change JARVIS settings (like voice speed/volume).",
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
            "description": "Reads all visible text and document content from the active window and screen. Use this when the user asks you to read, find, or inspect text, lines, documents, or content in an open application like Notepad, Word, browser, or screen.",
            "parameters": {
                "type": "object",
                "properties": {}
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
    }
]

# Short-term Memory (Conversation History)
def get_system_prompt():
    return (
        "You are JARVIS, a highly intelligent AI desktop assistant. "
        "Your personality is a friendly buddy who has the user's back. You make funny jokes and use casual, conversational language instead of being a robotic servant. "
        "Keep your text answers brief and to the point (no markdown).\n\n"
        "CRITICAL RULE: NEVER ask for permission to use tools. When the user asks you to do something, IMMEDIATELY output the JSON tool call to execute it! Do NOT ask 'shall I proceed?' or 'should I pull the trigger?'. Just DO IT.\n\n"
        "CRITICAL AUTONOMY RULE: If the user asks you to do a computer task that you don't have a direct 'app' tool for, BE RESOURCEFUL. "
        "You have a vast array of atomic tools like `get_clickable_elements`, `scroll`, `read_clipboard`, `run_terminal_command`, `read_file`, `list_directory`, `click_at`, `type_text`, `read_screen`, and `press_key`. "
        "You can chain these together to achieve ANYTHING! For example, to open an unknown app, you can use `press_key('win')`, wait a second, use `type_text('app_name')`, and then `press_key('enter')`. "
        "To click a button you don't know the coordinates for, use `get_clickable_elements` to retrieve the exact X/Y of every button on screen, then `click_at` the correct one. "
        "To read text, lines, or content from an open window or document (such as Notepad, Word, editor, or screen), use the `read_screen` tool directly.\n\n"
        "CRITICAL MULTI-STEP SEQUENCING: When a request requires multiple actions, execute the FIRST step first (e.g. open an application before trying to read from it or type into it). Do not announce in text what you will do without emitting the tool call.\n\n"
        "You have configurable settings that you can change using the update_setting tool. The main settings are:\n"
        "- 'voice_rate': Reading speed (default 170. Higher is faster).\n"
        "- 'voice_volume': Audio volume (default 1.0. Range 0.0 to 1.0).\n\n"
        "CRITICAL RULE: Always use the provided tools to accomplish the user's tasks, chaining them if necessary."
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
    Queries the local Ollama instance using the /api/chat endpoint with the full message history.
    """
    url = "http://localhost:11434/api/chat"
    
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
        with urllib.request.urlopen(req, timeout=180) as response:
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
                should_continue=None, authorize=None, resolve_secrets=None):
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

        message = query_local_llm_chat(current_messages, model=model_name)

        if not message:
            return None

        # Append Assistant's response to history
        conversation.append(message)

        # Check if the LLM decided to call a tool
        if "tool_calls" in message and message["tool_calls"]:
            current_tool_calls_repr = str(message["tool_calls"])
            if current_tool_calls_repr == previous_tool_calls_repr:
                logger.info("[JARVIS] Caught LLM in an infinite loop! Breaking out.")
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
                    logger.info(f"[JARVIS Executing] {func_name}({args_dict})")

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
                        auto_confirm=auto_confirm)

    if reply is None:
        speak("I'm sorry, I couldn't reach my local brain. Please ensure Ollama is running.")
        conversation_history.pop()  # Remove failed prompt
        return None

    if reply:
        speak(reply)
    return reply


def run_task_step(instruction, context="", auto_confirm=True,
                  should_continue=None, authorize=None, resolve_secrets=None):
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

    reply = _agent_loop(conversation,
                        extra_messages=[_memory_message(instruction)],
                        auto_confirm=auto_confirm,
                        should_continue=should_continue, authorize=authorize,
                        resolve_secrets=resolve_secrets)

    if reply is None:
        raise RuntimeError("Could not reach the local model. Is Ollama running?")

    return reply.strip() or "Done."


# Register guards
for t in ["run_terminal_command", "shutdown_laptop", "restart_laptop", "clear_notes", "write_file", "disable_voice_input", "disable_speech_output"]:
    if t in AVAILABLE_FUNCTIONS:
        guard.register("destructive")(AVAILABLE_FUNCTIONS[t])
for t in ["update_setting", "take_screenshot", "read_file", "send_email", "git_auto_commit_and_push", "spawn_parallel_agents", "run_actor_critic_research", "send_telegram_update", "upload_google_drive_file", "draft_gmail_message", "create_google_calendar_event", "create_google_doc"]:
    if t in AVAILABLE_FUNCTIONS:
        guard.register("sensitive")(AVAILABLE_FUNCTIONS[t])
