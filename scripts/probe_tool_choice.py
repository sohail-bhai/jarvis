"""Ask the model to pick a tool for a task, and report what it picked.

Nothing is executed: the chosen tool call is printed and thrown away. This
mirrors the real runtime path - same system prompt, same narrowed tool payload
from select_tools - so the answers reflect what the assistant would really do,
not what it would do if handed the whole catalogue.

    ./venv/Scripts/python.exe scripts/probe_tool_choice.py [model]
"""

import os
import sys

# ChromaDB pulls in OpenBLAS, which grabs a thread pool per core and fails to
# allocate on a loaded machine. One thread is plenty for a probe.
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assistant.ai_brain as ai_brain

# Tasks with no purpose-built tool. Each one has to be composed out of the
# atomic actions, which is the whole point: a goal phrased in plain language
# should still reach the keyboard and the mouse.
TASKS = [
    ("save the document that is open in notepad", "press_key"),
    ("select all the text in notepad and delete it", "press_key"),
    ("copy everything on this screen", "press_key"),
    ("undo what I just did", "press_key"),
    ("make the notepad window go away", "close_window"),
    ("switch to my brave browser window", "focus_window"),
    ("what windows do I have open", "list_windows"),
    ("rename the file report.txt on my desktop to final.txt", None),
    ("open the run dialog and launch calculator", None),
    ("what buttons can you see on my screen right now", "get_clickable_elements"),
]


def probe(model):
    prompt = ai_brain.get_system_prompt()
    hits = 0

    for task, expected in TASKS:
        tools = ai_brain.select_tools(task)
        reply = ai_brain.query_local_llm_chat(
            [{"role": "system", "content": prompt},
             {"role": "user", "content": task}],
            model=model,
            tools=tools,
        )

        if not isinstance(reply, dict):
            print(f"  ! {task}\n      request failed: {reply}")
            continue

        calls = reply.get("tool_calls") or []
        if calls:
            fn = calls[0].get("function", {})
            got = fn.get("name")
            detail = f"{got}({fn.get('arguments')})"
        else:
            got = None
            detail = f"no tool call, said: {(reply.get('content') or '').strip()[:70]!r}"

        ok = expected is None or got == expected
        hits += ok
        print(f"  {'ok  ' if ok else 'MISS'} {task}\n       -> {detail}"
              + ("" if ok else f"\n       expected {expected}"))

    scored = [t for t, e in TASKS if e is not None]
    print(f"\n  {hits}/{len(TASKS)} acceptable "
          f"({len(scored)} of them have a required tool)")


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:3b"
    print(f"model: {model}   tools offered per task: narrowed by select_tools\n")
    probe(model)
