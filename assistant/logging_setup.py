import logging
from logging.handlers import RotatingFileHandler
import sys
import threading
from pathlib import Path
from assistant import events

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

class EventBusHandler(logging.Handler):
    def __init__(self, bus):
        super().__init__()
        self._bus = bus
        self._local = threading.local()

    def emit(self, record):
        if getattr(self._local, "busy", False):
            return
        self._local.busy = True
        try:
            msg = self.format(record)
            exc = self.format_exc(record) if getattr(record, 'exc_info', None) else None
            self._bus.emit(events.EVENT_LOG, msg, level=record.levelname, logger=record.name, exc=exc)
        except Exception:
            pass
        finally:
            self._local.busy = False

_configured = False
_event_handler = None

def configure_logging(event_bus=None, *, level=None, console=True, bridge_level=logging.WARNING) -> None:
    global _configured
    if _configured:
        if event_bus:
            attach_event_bus(event_bus, bridge_level)
        return
        
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    
    for pkg in ("assistant", "gui"):
        logger = logging.getLogger(pkg)
        logger.setLevel(logging.DEBUG)
        
    for noisy in ("comtypes", "chromadb", "urllib3", "PIL", "edge_tts", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
        
    file_handler = RotatingFileHandler(
        LOG_DIR / "vave.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
        delay=True
    )
    file_handler.setLevel(level or logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)-28s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))
    root.addHandler(file_handler)
    
    if console:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)-28s %(message)s", datefmt="%H:%M:%S"))
        root.addHandler(console_handler)
        
    transcript_logger = logging.getLogger("assistant.transcript")
    transcript_logger.propagate = False
    th = logging.StreamHandler(sys.stdout)
    th.setFormatter(logging.Formatter("%(message)s"))
    transcript_logger.addHandler(th)
    
    _configured = True
    
    if event_bus:
        attach_event_bus(event_bus, bridge_level)

def attach_event_bus(event_bus, level=logging.WARNING) -> None:
    global _event_handler
    if _event_handler:
        detach_event_bus()
    _event_handler = EventBusHandler(event_bus)
    _event_handler.setLevel(level)
    _event_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(_event_handler)

def detach_event_bus() -> None:
    global _event_handler
    if _event_handler:
        logging.getLogger().removeHandler(_event_handler)
        _event_handler = None

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
