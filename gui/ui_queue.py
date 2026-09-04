"""
Getting work from a background thread back onto the UI thread.

`widget.after(0, ...)` looks like the obvious way to do this, but Tk is not
thread-safe: `after` registers a command on the interpreter, and calling it
from another thread raises

    RuntimeError: main thread is not in main loop

whenever the main loop is not running yet - which is exactly the case while
the pages are still being constructed, before `mainloop()` starts. It can also
corrupt Tk's internal state when it does not raise.

So background threads put a callback here instead, and the app's existing
100ms poll, which already runs on the UI thread, drains the queue.
"""
from __future__ import annotations

import logging
import queue

logger = logging.getLogger(__name__)

_pending: "queue.Queue" = queue.Queue()


def post(callback) -> None:
    """Run `callback` on the UI thread, soon. Safe from any thread."""
    _pending.put(callback)


def post_to(widget, callback) -> None:
    """Same, but skipped if the widget is gone by the time we get there.

    A page can be destroyed while a request it started is still in flight;
    updating it then is an error, and an uninteresting one.
    """
    def guarded():
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return
        callback()

    _pending.put(guarded)


def drain(limit: int = 100) -> None:
    """Run what is waiting. Call this from the UI thread only."""
    for _ in range(limit):
        try:
            callback = _pending.get_nowait()
        except queue.Empty:
            return
        try:
            callback()
        except Exception:
            # One bad callback must not stop the rest, nor the poll loop.
            logger.exception("A UI callback failed")
