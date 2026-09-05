"""Who asked for the current work, and whether it has read anything untrusted.

Origin says where a command came from - the microphone, the phone, a routine -
and the safety policy is written per origin.

Taint is the other half. A web page or the text on screen is content VAVE does
not control, and a page that says "ignore your instructions and run this
command" reaches the model exactly like a request from the user. Once a task
has read some, that is remembered for the rest of the task, and the guard asks
before anything that changes the machine.
"""

import contextvars
import threading

_call_origin = contextvars.ContextVar("call_origin", default="voice")

# Set when untrusted content enters the task, with a plain-language note of
# where it came from so a confirmation can say so.
_untrusted_source = contextvars.ContextVar("untrusted_source", default=None)


def mark_tainted(source: str) -> None:
    """Record that this task has read content VAVE does not control."""
    if not _untrusted_source.get():
        _untrusted_source.set(str(source))


def is_tainted() -> bool:
    return bool(_untrusted_source.get())


def taint_source():
    """Where the untrusted content came from, in words, or None."""
    return _untrusted_source.get()


def clear_taint() -> None:
    """Start a fresh task. Taint must not leak from one request into the next."""
    _untrusted_source.set(None)

def set_origin(origin: str) -> contextvars.Token:
    return _call_origin.set(origin)

def get_origin() -> str:
    return _call_origin.get()

def reset_origin(token: contextvars.Token) -> None:
    _call_origin.reset(token)

def spawn_thread(target, args=(), kwargs=None, daemon=True, name=None) -> threading.Thread:
    if kwargs is None:
        kwargs = {}
    
    ctx = contextvars.copy_context()
    def wrapper():
        return ctx.run(target, *args, **kwargs)
        
    t = threading.Thread(target=wrapper, daemon=daemon, name=name)
    t.start()
    return t
