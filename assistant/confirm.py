import queue
import threading
import uuid
import logging
from assistant import events
from assistant import speech

logger = logging.getLogger(__name__)

class ConfirmationBroker:
    def __init__(self):
        self._pending = {}
        self._lock = threading.Lock()
        self._bus = None
        
    def configure(self, bus: events.EventBus):
        self._bus = bus
        
    def request_confirmation(self, message: str, origin: str) -> bool:
        if origin == "voice":
            return self._ask_voice(message)
            
        return self._ask_async_channel(message, origin)
        
    def _ask_voice(self, message: str) -> bool:
        speech.speak(message)
        response = speech.listen()
        if not response:
            return False
            
        lower = response.lower()
        if any(w in lower for w in ["yes", "yeah", "do it", "sure", "proceed"]):
            return True
        return False
        
    def _ask_async_channel(self, message: str, origin: str) -> bool:
        if not self._bus:
            logger.warning("ConfirmationBroker has no EventBus. Denying.")
            return False
            
        req_id = uuid.uuid4().hex
        q = queue.Queue(maxsize=1)
        
        with self._lock:
            self._pending[req_id] = q
            
        self._bus.emit(
            events.EVENT_CONFIRM_REQUEST, 
            message, 
            req_id=req_id, 
            origin=origin
        )
        
        try:
            result = q.get(timeout=60.0)
            return result
        except queue.Empty:
            logger.warning(f"Confirmation {req_id} timed out.")
            return False
        finally:
            with self._lock:
                self._pending.pop(req_id, None)
                
    def resolve(self, req_id: str, approved: bool) -> bool:
        with self._lock:
            q = self._pending.get(req_id)
            
        if q:
            try:
                q.put_nowait(approved)
                return True
            except queue.Full:
                pass
        return False
        
_broker = ConfirmationBroker()

def configure(event_bus: events.EventBus) -> None:
    _broker.configure(event_bus)

def ask(message: str, origin: str) -> bool:
    return _broker.request_confirmation(message, origin)

def resolve(req_id: str, approved: bool) -> bool:
    return _broker.resolve(req_id, approved)
