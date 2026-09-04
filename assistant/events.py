import queue
import time
from dataclasses import dataclass, field
from typing import Any

EVENT_STATE_CHANGED = "state_changed"
EVENT_STATUS = "status"
EVENT_RECOGNIZED_TEXT = "recognized_text"
EVENT_ASSISTANT_RESPONSE = "assistant_response"
EVENT_ERROR = "error"

EVENT_OVERWATCH_STATE = "overwatch_state"
EVENT_OVERWATCH_CANDIDATE = "overwatch_candidate"
EVENT_OVERWATCH_ACTION = "overwatch_action"
EVENT_CONFIRM_REQUEST = "confirm_request"
EVENT_CONFIRM_RESOLVED = "confirm_resolved"
EVENT_TOOL_CALL = "tool_call"
EVENT_LOG = "log"

@dataclass
class AssistantEvent:
    event_type: str
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class EventBus:
    """Thread-safe event queue that a GUI can poll from its main thread."""
    def __init__(self, maxsize=2000):
        self._events = queue.Queue(maxsize=maxsize)
        self.dropped_events = 0

    def emit(self, event_type, message="", **payload):
        event = AssistantEvent(
            event_type=event_type,
            message=message,
            payload=payload
        )
        try:
            self._events.put_nowait(event)
        except queue.Full:
            try:
                self._events.get_nowait()
            except queue.Empty:
                pass
            try:
                self._events.put_nowait(event)
            except queue.Full:
                pass
            self.dropped_events += 1
        return event

    def get_nowait(self):
        try:
            return self._events.get_nowait()
        except queue.Empty:
            return None

    def drain(self, max_events=None):
        events = []
        while max_events is None or len(events) < max_events:
            event = self.get_nowait()
            if event is None:
                break
            events.append(event)
        return events

    def poll(self, max_events=None):
        return self.drain(max_events=max_events)

    def empty(self):
        return self._events.empty()

_global_bus = None

def set_global_event_bus(bus: EventBus) -> None:
    global _global_bus
    _global_bus = bus

def get_global_event_bus() -> EventBus | None:
    return _global_bus

def emit_global(event_type, message="", **payload) -> None:
    if _global_bus:
        _global_bus.emit(event_type, message, **payload)
