"""Run tasks through the real agent loop with the tools stubbed, and print the chain.

The question this answers is not "does the model pick the right tool first" -
for anything real the right first move is usually `focus_window` - but "does it
reach the goal by composing the atomic actions". So the loop runs against canned
tool results: nothing is clicked, typed or closed, yet the model sees plausible
output and carries on exactly as it would live.

Only the tool implementations are replaced. Narrowing, temperature, model
choice, the repeat-detection break and the stopped-short push are all the real
code, so a number from here means something about the assistant rather than
about the probe.

    ./venv/Scripts/python.exe scripts/probe_task_chain.py [model]
"""

import os
import sys

for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assistant.ai_brain as ai_brain
import assistant.system_tasks as system_tasks

# What the atomic tools would have returned. Deliberately plain and truthful in
# shape: the element list looks like a real get_clickable_elements reply,
# because a model that only works against tidy fake data proves nothing.
STUBS = {
    "list_windows": (
        "Untitled - Notepad\n"
        "Brave  <- currently in focus\n"
        "report.txt - File Explorer\n"
        "VAVE"
    ),
    "focus_window": "Brought '{title}' into focus.",
    "get_clickable_elements": (
        "Active window: 'Untitled - Notepad'\n"
        "File (MenuItem) at (18, 40)\n"
        "Edit (MenuItem) at (58, 40)\n"
        "View (MenuItem) at (98, 40)\n"
        "Text Editor (Edit) at (400, 300)\n"
        "Close (Button) at (1890, 12)"
    ),
    "read_screen": "hello world\nthis is the second line",
    "press_key": "Pressed {key}.",
    "type_text": "Typed {text} characters.",
    "click_at": "Clicked at ({x}, {y}).",
    "double_click_at": "Double-clicked at ({x}, {y}).",
    "right_click_at": (
        "Right-clicked at ({x}, {y}). A context menu opened with: "
        "Open, Edit, Rename, Delete, Properties"
    ),
    "scroll": "Scrolled.",
    "wait": "Waited 1 second.",
    "close_window": "Closed the window.",
    "open_app": "Opened {app_name}.",
}

TASKS = [
    ("save the document that is open in notepad", "press_key"),
    ("select all the text in notepad and delete it", "press_key"),
    ("copy everything on this screen", "press_key"),
    ("undo what I just did", "press_key"),
    ("make the notepad window go away", "close_window"),
    ("rename the file report.txt to final.txt", "right_click_at"),
    ("open the run dialog and launch calculator", "press_key"),
    ("type hello world into notepad and save it", "press_key"),
]

MAX_STEPS = 6


def stub_result(name, kwargs):
    """A believable reply for a tool, without touching the machine."""
    template = STUBS.get(name)
    if template is None:
        return f"{name} finished."
    safe = dict(kwargs)
    if name == "type_text":
        safe["text"] = len(str(safe.get("text", "")))
    try:
        return template.format(**safe)
    except (KeyError, IndexError):
        return template


def make_registry(chain):
    """Stand-ins for every tool, recording the call and returning canned output.

    `type_text` presses a chord handed to it as text, so the stub asks the real
    `_shortcut_sequence` what would happen and records that instead - the
    coercion is the tool's own behaviour, not a concession by the probe.
    """
    registry = {}

    def make(name):
        def stub(**kwargs):
            chords = (system_tasks._shortcut_sequence(kwargs.get("text", ""))
                      if name == "type_text" else [])
            if chords:
                for chord in chords:
                    chain.append(
                        f"press_key(key={chord!r})  [coerced from type_text]")
                return " ".join(f"Pressed {c}." for c in chords)
            shown = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
            chain.append(f"{name}({shown})")
            return stub_result(name, kwargs)

        # guard.call and coerce_args both read __name__, so the stub has to
        # answer to the tool's real name or every call is tiered as unknown.
        stub.__name__ = name
        return stub

    for name in ai_brain.AVAILABLE_FUNCTIONS:
        registry[name] = make(name)
    return registry


def run_task(task, model):
    """The tool names the model called, in order, over a stubbed run."""
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

    if reply is None:
        chain.append("<no reply from the model>")
    elif reply.strip():
        chain.append(f"<said: {reply.strip()[:90]}>")
    return chain


def main(model):
    reached = 0

    for task, required in TASKS:
        chain = run_task(task, model)
        called = {step.split("(")[0] for step in chain}
        ok = required in called
        reached += ok
        print(f"  {'ok  ' if ok else 'MISS'} {task}")
        for step in chain:
            print(f"         {step}")
        if not chain:
            print("         (nothing at all)")
        if not ok:
            print(f"         never called {required}")
        print()

    print(f"  {reached}/{len(TASKS)} tasks reached the action they needed")


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else None
    if model:
        # Measure one model per run. Overriding the selector rather than
        # writing `llm_model` keeps the user's config untouched, and works for
        # the fast model too - which as a config pin would be indistinguishable
        # from "no pin" and would escalate anyway.
        ai_brain.select_model = lambda instruction="", _m=model: _m
    print(f"model: {model or 'auto (escalating)'}, "
          f"tools stubbed, max {MAX_STEPS} steps\n")
    main(model)
