from pathlib import Path
from datetime import datetime

from assistant.speech import speak, listen
from assistant.config import get_setting

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTES_FILE = PROJECT_ROOT / "data" / "notes.txt"

def add_note():
    speak("What should I write?")

    note = listen(
        timeout=10,
        max_phrase_time=int(get_setting("notes_max_phrase_time", 60)),
        pause_seconds=float(get_setting("notes_pause_seconds", 3.0))
    )

    if not note:
        speak("No note was added.")
        return

    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")

    with open(NOTES_FILE, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {note}\n")

    speak("Note saved.")

def read_notes():
    if not NOTES_FILE.exists() or NOTES_FILE.read_text(encoding="utf-8").strip() == "":
        speak("You have no notes.")
        return

    speak("Reading your notes.")

    with open(NOTES_FILE, "r", encoding="utf-8") as file:
        notes = file.readlines()

    for note in notes[-5:]:
        speak(note.strip())

def clear_notes():
    NOTES_FILE.write_text("", encoding="utf-8")
    speak("All notes cleared.")
