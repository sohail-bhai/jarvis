from enum import Enum


class AssistantState(str, Enum):
    IDLE = "idle"
    CALIBRATING = "calibrating"
    LISTENING = "listening"
    RECOGNIZING = "recognizing"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
    STOPPED = "stopped"
