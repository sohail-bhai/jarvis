import logging
from typing import Callable, Any
from functools import wraps

from assistant import config
from assistant import call_context
from assistant import confirm
from assistant import events
from assistant import audit

logger = logging.getLogger(__name__)

class ToolDenied(Exception):
    pass

_bus = None
_kill_switch = False

def configure(event_bus: events.EventBus) -> None:
    global _bus
    _bus = event_bus

def set_kill_switch(active: bool) -> None:
    global _kill_switch
    _kill_switch = active

_REGISTRY = {
    "safe": set(),
    "sensitive": set(),
    "destructive": set()
}

def register(tier: str):
    def decorator(func):
        if tier in _REGISTRY:
            _REGISTRY[tier].add(func.__name__)
        return func
    return decorator

def _evaluate_policy(tool_name: str, args: dict, origin: str) -> bool:
    if _kill_switch:
        logger.warning(f"Kill switch active. Denying {tool_name}.")
        return False
        
    policy = config.get_setting("safety", {})
    origin_policy = policy.get(origin, {})
    
    if origin_policy.get("mode") == "deny_all":
        return False
        
    tier = "safe"
    if tool_name in _REGISTRY["destructive"]:
        tier = "destructive"
    elif tool_name in _REGISTRY["sensitive"]:
        tier = "sensitive"
        
    if origin_policy.get(f"allow_{tier}", False):
        return True
        
    if origin_policy.get(f"confirm_{tier}", False):
        msg = f"Origin '{origin}' wants to run {tool_name}. Proceed?"
        return confirm.ask(msg, origin)
        
    return False

def coerce_args(func: Callable, kwargs: dict) -> dict:
    import inspect
    sig = inspect.signature(func)
    coerced = {}
    for name, param in sig.parameters.items():
        if name in kwargs:
            val = kwargs[name]
            if param.annotation == int and isinstance(val, str):
                try:
                    val = int(val)
                except ValueError:
                    pass
            elif param.annotation == bool and isinstance(val, str):
                val = val.lower() in ("true", "1", "yes")
            coerced[name] = val
    return coerced

def call(func: Callable, **kwargs) -> Any:
    tool_name = func.__name__
    origin = call_context.get_origin()
    
    record = {
        "event": "tool_call_attempt",
        "tool": tool_name,
        "origin": origin,
        "args": audit.redact(kwargs)
    }
    audit_id = audit.append(record)
    
    if _bus:
        _bus.emit(events.EVENT_TOOL_CALL, f"Evaluating {tool_name}", tool=tool_name, origin=origin)
        
    allowed = _evaluate_policy(tool_name, kwargs, origin)
    
    if not allowed:
        audit.append({
            "event": "tool_call_denied",
            "audit_id": audit_id,
            "tool": tool_name
        })
        logger.warning(f"Guard denied {tool_name} for origin {origin}")
        raise ToolDenied(f"Execution of {tool_name} was denied by safety policy.")
        
    audit.append({
        "event": "tool_call_approved",
        "audit_id": audit_id,
        "tool": tool_name
    })
    
    logger.info(f"Guard approved {tool_name} for origin {origin}")
    try:
        result = func(**kwargs)
        audit.append({
            "event": "tool_call_success",
            "audit_id": audit_id,
            "tool": tool_name
        })
        return result
    except Exception as e:
        audit.append({
            "event": "tool_call_error",
            "audit_id": audit_id,
            "tool": tool_name,
            "error": str(e)
        })
        raise
