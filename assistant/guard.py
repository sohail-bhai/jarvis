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

# A tool nobody has classified is not a tool to trust. Everything that drives
# the machine - the keyboard, the mouse, a form on a page - used to fall
# through to "safe" simply by not being on a list, which let a single text
# message press ctrl+a and type over whatever had focus with no confirmation.
UNCLASSIFIED_TIER = "sensitive"

# Tools that send something out of the machine, or hand something to another
# system. A web page that has just been read must not be able to trigger one
# of these without the user seeing it first.
REACHES_OUTWARD = frozenset({
    "send_email", "draft_gmail_message", "send_telegram_update",
    "web_api_call", "upload_google_drive_file", "git_auto_commit_and_push",
    "gitlab_merge", "gitlab_propose_fix", "browser_fill_form",
    "create_google_doc", "create_google_slides",
    "create_google_calendar_event", "schedule_meeting", "write_clipboard",
})

def tier_of(tool_name: str) -> str:
    """The risk tier of one tool. Unknown tools are not safe by default."""
    for tier in ("destructive", "sensitive", "safe"):
        if tool_name in _REGISTRY[tier]:
            return tier
    return UNCLASSIFIED_TIER


def register(tier: str):
    def decorator(func):
        if tier in _REGISTRY:
            _REGISTRY[tier].add(func.__name__)
        return func
    return decorator


def register_name(tier: str, tool_name: str) -> None:
    """Classify a tool by the name the model calls it by.

    Some tools are lambdas or are exposed under a different name than the
    function's own, and `func.__name__` then classifies "<lambda>" instead of
    the tool - which quietly left them unclassified.
    """
    if tier in _REGISTRY:
        _REGISTRY[tier].add(tool_name)

def _evaluate_policy(tool_name: str, args: dict, origin: str) -> bool:
    if _kill_switch:
        logger.warning(f"Kill switch active. Denying {tool_name}.")
        return False
        
    policy = config.get_setting("safety", {})
    origin_policy = policy.get(origin, {})
    
    if origin_policy.get("mode") == "deny_all":
        return False
        
    tier = tier_of(tool_name)

    # Content from a web page or the screen is data, not instruction. Once a
    # task has read some, the tools that could act on what it says get a
    # confirmation even where policy would have allowed them outright.
    #
    # Only the ones that reach past the page count. Asking before every click
    # inside the site the user sent VAVE to would make the browser unusable
    # and train the user to approve without reading, which is worse than the
    # risk it guards. So: the shell, the keyboard, the filesystem, and
    # anything that sends data outwards.
    if call_context.is_tainted() and (tier == "destructive"
                                      or tool_name in REACHES_OUTWARD):
        source = call_context.taint_source() or "a web page or the screen"
        return confirm.ask(
            f"{tool_name} was chosen after reading {source}, which VAVE does "
            f"not control. Arguments: {audit.redact(args)}. Run it?",
            origin)

        
    if origin_policy.get(f"allow_{tier}", False):
        return True
        
    if origin_policy.get(f"confirm_{tier}", False):
        # The arguments are the whole question. "Proceed with write_file?" is
        # not something anyone can answer.
        msg = (f"{origin} wants to run {tool_name} ({tier}) "
               f"with {audit.redact(args)}. Proceed?")
        return confirm.ask(msg, origin)
        
    return False

def coerce_args(func: Callable, kwargs: dict) -> dict:
    import inspect
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return kwargs

    has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    coerced = dict(kwargs) if has_var_keyword else {}

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

def call(func: Callable, _tool_name: str = None, **kwargs) -> Any:
    # The caller knows the name the model used; `func.__name__` is "<lambda>"
    # for some of them, which would look up the wrong policy.
    tool_name = _tool_name or func.__name__
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
