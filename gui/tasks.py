"""Running a real task from the desktop app.

The Web page used to show a mock-up of browser progress. This connects it to
the control plane: what you type becomes a real task, the steps are real
steps, and the progress card follows what actually happened rather than a
script. No tkinter here, so it can be tested without a display.
"""

import logging

from assistant.control.executor import get_executor
from assistant.control.models import EventType
from assistant.control.service import get_control_plane

logger = logging.getLogger(__name__)

# Events worth showing on the progress card. Everything else stays in the log.
PROGRESS_EVENTS = {
    EventType.STEP_STARTED,
    EventType.STEP_FINISHED,
    EventType.TASK_COMPLETED,
    EventType.TASK_FAILED,
    EventType.TASK_CANCELLED,
    EventType.APPROVAL_REQUESTED,
}


def start_web_task(goal, on_progress=None, plane=None, executor=None):
    """Turn what the user typed into a task and start working it.

    `on_progress(event)` is called from a worker thread for each step, so the
    caller is responsible for hopping back onto the UI thread.

    Returns the task, or None when JARVIS is stopped.
    """
    plane = plane or get_control_plane()
    runner = executor or get_executor(plane=plane)

    try:
        steps = runner.planner.plan(goal)
    except Exception:
        logger.exception("Could not plan %r", goal)
        steps = None

    try:
        task = plane.create_task(goal, steps=steps)
    except RuntimeError as error:
        # Raised while an emergency stop is latched.
        logger.info("Not starting web task: %s", error)
        return None

    if on_progress is not None:
        _follow(plane, task.id, on_progress)

    runner.submit(task.id)
    return task


def _follow(plane, task_id, on_progress):
    """Report this task's steps until it finishes, then stop listening."""
    unsubscribe = None

    def handle(event):
        if event.task_id != task_id or event.type not in PROGRESS_EVENTS:
            return

        try:
            on_progress(describe(event))
        except Exception:
            logger.exception("Progress callback failed")

        if event.type in (EventType.TASK_COMPLETED, EventType.TASK_FAILED,
                          EventType.TASK_CANCELLED) and unsubscribe:
            unsubscribe()

    unsubscribe = plane.subscribe(handle)
    return unsubscribe


def describe(event):
    """One event, in the shape the progress card draws."""
    finished = event.type in (EventType.STEP_FINISHED, EventType.TASK_COMPLETED)
    failed = (event.type == EventType.TASK_FAILED or event.result == "failed")

    return {
        "text": event.message,
        "done": finished and not failed,
        "active": event.type == EventType.STEP_STARTED,
        "failed": failed,
        "needs_you": event.type == EventType.APPROVAL_REQUESTED,
        "finished": event.type in (EventType.TASK_COMPLETED, EventType.TASK_FAILED,
                                   EventType.TASK_CANCELLED),
    }
