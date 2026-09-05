"""Run multi-step requests through the real agent loop with the tools stubbed.

The single question here is whether a request made of several actions is
carried through to its last one. "Open Netflix and open any profile" opened
Netflix and stopped, and the same shape of failure covered most compound
requests, so each task below names the actions the chain has to reach - not
just the first one.

Only the tool implementations are replaced. The model, the narrowing, the
checklist, the stall guard and the finish check are all the real code, so a
miss here is a miss in the assistant.

    python scripts/probe_chained_tasks.py [model]
"""

import os
import sys

for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assistant.ai_brain as ai_brain

# Believable tool output. The element lists are numbered the way the real
# browser tools number them, because a model that only copes with tidy data
# proves nothing about the live machine.
PAGE_AFTER_OPEN = (
    "Page: Netflix - Who's watching?\n"
    "[0] link 'Netflix'\n"
    "[1] button 'Rav'\n"
    "[2] button 'Sohail'\n"
    "[3] button 'Kids'\n"
    "[4] button 'Manage Profiles'"
)
PAGE_AFTER_CLICK = (
    "Page: Netflix - Home\n"
    "[0] link 'Home'\n"
    "[1] button 'Play Stranger Things'\n"
    "[2] input 'Search'"
)

STUBS = {
    "browse": "Opened {url}.\n" + PAGE_AFTER_OPEN,
    "browser_elements": PAGE_AFTER_OPEN,
    "browser_click": "Clicked element {index}.\n" + PAGE_AFTER_CLICK,
    "browser_type": "Typed into element {index}.\n" + PAGE_AFTER_CLICK,
    "browser_press": "Pressed {key}.\n" + PAGE_AFTER_CLICK,
    "browser_read": "Netflix home page. Rows: Continue Watching, Trending Now.",
    "search_youtube": "YouTube search opened.\n"
                      "[0] video 'lofi hip hop radio'\n[1] video 'chill beats'",
    "search_google": "Google results opened.\n[0] link 'First result'",
    "open_website": "Website opened in browser.",
    "open_app": "Opened {app_name}.",
    "list_windows": "Untitled - Notepad  <- currently in focus\nBrave\nVAVE",
    "focus_window": "Brought '{title}' into focus.",
    "get_clickable_elements": (
        "Active window: 'Untitled - Notepad'\n"
        "File (MenuItem) at (18, 40)\n"
        "Edit (MenuItem) at (58, 40)\n"
        "Text Editor (Edit) at (400, 300)"
    ),
    "read_screen": "hello world",
    "type_text": "Typed the text.",
    "press_key": "Pressed {key}.",
    "click_at": "Clicked at ({x}, {y}).",
    "wait": "Waited.",
    "set_volume": "Volume set to {level}.",
    "take_screenshot": "Screenshot saved.",
    "tell_battery": "Battery is at 78 percent.",
    "tell_time": "It is 4:12 PM.",
}

# (request, [tool names the chain must reach])
TASKS = [
    ("open netflix and open any profile",
     ["browse", "browser_click"]),
    ("open netflix and play stranger things",
     ["browse", "browser_click"]),
    ("open youtube and play lofi",
     ["browse|search_youtube", "browser_click"]),
    ("open notepad and type hello world",
     ["open_app", "type_text"]),
    ("open notepad, type hello and save it",
     ["open_app", "type_text", "press_key"]),
    ("take a screenshot and tell me the battery level",
     ["take_screenshot", "tell_battery"]),
    ("set the volume to 30 and open notepad",
     ["set_volume", "open_app"]),
    ("open netflix, pick a profile and search for comedy",
     ["browse", "browser_click", "browser_type"]),
    # Controls: neither of these should grow extra steps.
    ("open notepad", ["open_app"]),
    ("what time is it", ["tell_time"]),
]

MAX_STEPS = 8


def stub_result(name, kwargs):
    template = STUBS.get(name)
    if template is None:
        return f"{name} finished."
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def make_registry(chain):
    registry = {}

    def make(name):
        def stub(**kwargs):
            shown = ", ".join(f"{k}={v!r}" for k, v in list(kwargs.items())[:3])
            chain.append(f"{name}({shown})")
            return stub_result(name, kwargs)

        # guard.call and coerce_args read __name__, so a stub has to answer to
        # the real tool's name.
        stub.__name__ = name
        return stub

    for name in ai_brain.AVAILABLE_FUNCTIONS:
        registry[name] = make(name)
    return registry


def run_task(task):
    chain = []
    real_registry = ai_brain.AVAILABLE_FUNCTIONS
    ai_brain.AVAILABLE_FUNCTIONS = make_registry(chain)

    conversation = [{"role": "system", "content": ai_brain.get_system_prompt()},
                    {"role": "user", "content": task}]
    try:
        reply = ai_brain._agent_loop(conversation, max_steps=MAX_STEPS,
                                     tools=ai_brain.select_tools(task))
    except Exception as exc:
        chain.append(f"<crashed: {type(exc).__name__}: {exc}>")
        reply = None
    finally:
        ai_brain.AVAILABLE_FUNCTIONS = real_registry

    said = (reply or "").strip()
    return chain, said


def main():
    finished = 0

    for task, required in TASKS:
        chain, said = run_task(task)
        called = [step.split("(")[0] for step in chain]

        missing = [want for want in required
                   if not any(name in called for name in want.split("|"))]
        ok = not missing
        finished += ok

        print(f"  {'ok  ' if ok else 'MISS'} {task}")
        for step in chain:
            print(f"         {step}")
        if said:
            print(f"         <said: {said[:100]}>")
        if missing:
            print(f"         never reached: {', '.join(missing)}")
        print(flush=True)

    print(f"  {finished}/{len(TASKS)} requests carried through to the end")


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else None
    if model:
        ai_brain.select_model = lambda instruction="", _m=model: _m
    print(f"model: {model or 'auto'}, tools stubbed, max {MAX_STEPS} steps\n",
          flush=True)
    main()
