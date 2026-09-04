import re
import webbrowser
import urllib.parse

from assistant.speech import speak, listen
from assistant.config import get_setting, update_setting
from assistant.system_tasks import (
    open_app,
    tell_time,
    tell_date,
    tell_battery,
    take_screenshot,
    set_volume,
    change_volume_by,
    mute_volume,
    lock_laptop,
    shutdown_laptop,
    restart_laptop,
)
from assistant.notes import add_note, read_notes, clear_notes
from assistant.ai_brain import ask_ai
from assistant.dev_tools import git_auto_commit_and_push, deep_test_project, scrape_project_ideas, scaffold_code

def extract_number(command):
    match = re.search(r"\d+", command)
    if match:
        return int(match.group())
    return None

def change_user_name(command):
    """
    Example:
    change my name to sohail
    set my name to sohail
    """
    phrases = ["change my name to", "set my name to", "my name is"]

    for phrase in phrases:
        if phrase in command:
            new_name = command.split(phrase, 1)[1].strip().title()

            if new_name:
                update_setting("user_name", new_name)
                speak(f"Okay, I will call you {new_name}.")
                return True

    return False

def change_assistant_name(command):
    """
    Example:
    change assistant name to friday
    set your name to friday
    """
    phrases = ["change assistant name to", "set assistant name to", "change your name to", "set your name to"]

    for phrase in phrases:
        if phrase in command:
            new_name = command.split(phrase, 1)[1].strip().title()

            if new_name:
                update_setting("assistant_name", new_name)
                speak(f"Okay, my name is now {new_name}.")
                return True

    return False

def handle_settings_command(command):
    if change_user_name(command):
        return True

    if change_assistant_name(command):
        return True

    if "what is my name" in command:
        speak(f"Your name is {get_setting('user_name', 'Sir')}.")
        return True

    if "what is your name" in command:
        speak(f"My name is {get_setting('assistant_name', 'Jarvis')}.")
        return True

    return False

def handle_model_switch_command(command):
    """
    Hardcoded model switcher to bypass the LLM.
    Example: 'switch to high performance', 'switch to normal mode', or 'switch model qwen2.5:3b'
    """
    if "switch to high performance" in command:
        update_setting("llm_model", "qwen3.5:9b")
        speak("Hardcoded override successful. AI brain is now using high performance model (qwen3.5:9b).")
        return True
        
    if "switch to normal mode" in command:
        update_setting("llm_model", "qwen2.5:3b")
        speak("Hardcoded override successful. AI brain is now using normal mode model (qwen2.5:3b).")
        return True

    if "switch model" in command or "change model" in command:
        # try to extract the model name
        command_parts = command.replace("change model to", "switch model").split("switch model")
        if len(command_parts) > 1:
            new_model = command_parts[1].strip()
            if new_model:
                update_setting("llm_model", new_model)
                speak(f"Hardcoded override successful. AI brain is now using model: {new_model}")
                return True
    return False

def handle_volume_command(command):
    """
    Volume commands:
    - volume down            -> decrease by default step
    - volume down 20         -> decrease by 20
    - volume up              -> increase by default step
    - volume up 20           -> increase by 20
    - volume 40              -> set volume to 40
    - set volume to 40       -> set volume to 40
    - mute volume            -> mute/unmute
    """

    if "volume" not in command and "mute" not in command:
        return False

    if "mute" in command:
        mute_volume()
        return True

    amount = extract_number(command)
    default_step = int(get_setting("default_volume_step", 5))

    if "down" in command or "decrease" in command or "lower" in command:
        change_volume_by(-(amount if amount is not None else default_step))
        return True

    if "up" in command or "increase" in command or "raise" in command:
        change_volume_by(amount if amount is not None else default_step)
        return True

    if amount is not None:
        set_volume(amount)
        return True

    return False

def open_website(command):
    websites = get_setting("websites", {})

    for site_name, url in websites.items():
        if f"open {site_name}" in command:
            speak(f"Opening {site_name}")
            webbrowser.open(url)
            return True

    return False

def handle_app_command(command):
    """
    Handles opening common desktop applications:
    notepad, chrome, calculator, vscode, file explorer, cmd.
    """
    app_aliases = {
        "notepad": "notepad",
        "google chrome": "chrome",
        "chrome": "chrome",
        "calculator": "calculator",
        "calc": "calculator",
        "vs code": "vscode",
        "vscode": "vscode",
        "file explorer": "file_explorer",
        "explorer": "file_explorer",
        "command prompt": "cmd",
        "terminal": "cmd",
        "cmd": "cmd",
    }
    for alias, app_name in app_aliases.items():
        if f"open {alias}" in command:
            open_app(app_name)
            return True
    return False

def google_search(command):
    query = ""

    if "search google for" in command:
        query = command.replace("search google for", "", 1).strip()
    elif "google search" in command:
        query = command.replace("google search", "", 1).strip()
    elif command.startswith("search "):
        query = command.replace("search", "", 1).strip()

    if query:
        speak(f"Searching Google for {query}")
        encoded_query = urllib.parse.quote_plus(query)
        webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
        return True

    return False

def youtube_search(command):
    query = ""

    if "youtube search" in command:
        query = command.replace("youtube search", "", 1).strip()
    elif "search youtube for" in command:
        query = command.replace("search youtube for", "", 1).strip()
    elif "search on youtube" in command:
        query = command.replace("search on youtube", "", 1).strip()

    if query:
        speak(f"Searching YouTube for {query}")
        encoded_query = urllib.parse.quote_plus(query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
        return True

    return False

def confirm_action(question):
    speak(question)
    speak("Say yes to confirm or no to cancel.")

    answer = listen()

    if "yes" in answer or "confirm" in answer or "sure" in answer:
        return True

    speak("Cancelled.")
    return False

def check_routines(command):
    """
    Checks if the command matches a predefined routine in config.json.
    If it does, it executes the list of commands sequentially.
    """
    routines = get_setting("routines", {})
    
    for routine_name, commands_list in routines.items():
        if routine_name in command:
            speak(f"Running routine: {routine_name.title()}")
            for cmd in commands_list:
                call_context.set_origin("routine")
                if not execute_command(cmd, auto_confirm=True):
                    return False
            return True
            
    return False

def execute_command(command, auto_confirm=False):
    """
    Main command router for JARVIS Version 1.2.
    """

    if any(word in command for word in ["stop", "exit", "quit", "goodbye"]):
        speak(f"Goodbye {get_setting('user_name', 'Sir')}.")
        return False

    if handle_model_switch_command(command):
        return True

    if handle_settings_command(command):
        return True
        
    if check_routines(command):
        return True

    if handle_volume_command(command):
        return True

    if open_website(command):
        return True

    if handle_app_command(command):
        return True

    if youtube_search(command):
        return True

    if google_search(command):
        return True

    # Developer Mode Commands
    if "commit my changes" in command or "commit my code" in command or "push my code" in command:
        push_code = "push" in command
        git_auto_commit_and_push(push=push_code)
        return True
    
    if "deep test the project" in command or "run deep test" in command or "test my code" in command:
        # Use default args or parse them if needed
        deep_test_project()
        return True
        
    if "scrape for ideas" in command or "project ideas" in command or "find templates" in command:
        scrape_project_ideas()
        return True
        
    if "scaffold" in command:
        # Give it directly to the LLM Brain to trigger scaffold_code
        ask_ai(command, auto_confirm=True)
        return True

    # Calendar Commands
    if "my schedule" in command or "read my calendar" in command or "upcoming events" in command:
        from assistant.calendar_sync import get_upcoming_events
        response = get_upcoming_events()
        speak(response)
        return True
        
    if "schedule a meeting" in command or "schedule an event" in command:
        ask_ai(command, auto_confirm=True)
        return True

    # Email Commands
    if "send an email" in command or "write an email" in command:
        ask_ai(command, auto_confirm=True)
        return True
        
    
    # Swarm & Deep Research Commands
    if "deep research" in command or "research this deeply" in command:
        ask_ai(command, auto_confirm=True)
        return True
        
    if "spawn agents" in command or "delegate" in command or "swarm" in command:
        ask_ai(command, auto_confirm=True)
        return True

    # Document RAG Commands
    if "ingest document" in command or "read textbook" in command or "read pdf" in command:
        ask_ai(command, auto_confirm=True)
        return True
        
    if "ask document" in command or "search knowledge base" in command:
        ask_ai(command, auto_confirm=True)
        return True

    # Briefing Command
    if "brief me" in command or "morning briefing" in command or "what is my briefing" in command:
        from assistant.system_tasks import provide_morning_briefing
        provide_morning_briefing()
        return True

    if "time" in command:
        tell_time()
    elif "date" in command:
        tell_date()
    elif "battery" in command:
        tell_battery()

    elif "screenshot" in command or "screen shot" in command:
        take_screenshot()
    elif "lock laptop" in command or "lock computer" in command or "lock screen" in command:
        lock_laptop()

    elif "shutdown" in command or "shut down" in command:
        try: guard.call(shutdown_laptop)
        except guard.ToolDenied: pass

    elif "restart" in command or "reboot" in command:
        try: guard.call(restart_laptop)
        except guard.ToolDenied: pass

    elif "take a note" in command or "take note" in command or "write a note" in command or "add note" in command:
        add_note()
    elif "read notes" in command or "read my notes" in command:
        read_notes()
    elif "clear notes" in command or "delete notes" in command:
        try: guard.call(clear_notes)
        except guard.ToolDenied: pass

    else:
        # Route unrecognized commands to the local LLM brain
        ask_ai(command, auto_confirm=auto_confirm)

    return True
