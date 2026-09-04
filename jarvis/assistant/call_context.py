import contextvars
import threading

_call_origin = contextvars.ContextVar("call_origin", default="voice")

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
