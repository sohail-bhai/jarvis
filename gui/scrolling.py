"""
Wheel scrolling that matches the rest of the desktop.

CustomTkinter scrolls an X11 wheel notch by a single text unit, so a long page
takes dozens of notches to cross and the window feels stuck. One notch moves a
few lines here, which is what every other application on the machine does.
Windows and macOS already scroll by a sensible amount, so they are left alone.
"""
from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)

LINES_PER_NOTCH = 4


def tune(scrollable, lines: int = LINES_PER_NOTCH) -> None:
    """Give one wheel notch a usable step on a CTkScrollableFrame."""
    if not sys.platform.startswith("linux"):
        return

    canvas = getattr(scrollable, "_parent_canvas", None)
    if canvas is None:
        return

    def on_wheel(event):
        # Nothing to scroll: let the event through so a parent can use it.
        if canvas.yview() == (0.0, 1.0):
            return None
        canvas.yview_scroll(-lines if event.num == 4 else lines, "units")
        # Stops CustomTkinter's own bind_all handler from scrolling again.
        return "break"

    try:
        canvas.bind("<Button-4>", on_wheel, add="+")
        canvas.bind("<Button-5>", on_wheel, add="+")
    except Exception:
        logger.debug("Could not tune scrolling", exc_info=True)
