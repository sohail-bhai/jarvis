"""Running a real task from the desktop app.

The Web page used to show a mock-up of browser progress. This connects it to
the control plane: what you type becomes a real task, the steps are real
steps, and the progress card follows what actually happened rather than a
script. No tkinter here, so it can be tested without a display.

The plane may be on this machine or on another one. When `vave_server` is set
in `config.json` the work is created and run over there, which is what lets a
laptop drive the computer that has the files, the tools and the model. Either
way the progress card is fed by the same events, so nothing below this line
cares where the work happened.
"""

import logging

from assistant.control.executor import get_executor
from assistant.control.models import EventType
from assistant.control.service import get_control_plane
from assistant.remote import RemoteError, get_remote_plane

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

    Returns the task, or None when VAVE is stopped.
    """
    if plane is None:
        remote = get_remote_plane()
        if remote is not None:
            return _start_remote_task(remote, goal, on_progress)

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


def _start_remote_task(remote, goal, on_progress):
    """Create and run the task on the computer that owns the work.

    The other machine plans the steps and works them, so nothing is planned or
    executed here - this only asks, and then watches.

    The watching starts before the asking. The first step can begin before the
    reply arrives over the network, and a progress card that misses the first
    step looks stuck.
    """
    held = []
    task_id = [None]

    def handle(event):
        if event.type not in PROGRESS_EVENTS:
            return
        # Until the reply names the task, keep anything that might be ours.
        if task_id[0] is None:
            held.append(event)
        elif event.task_id == task_id[0]:
            _report(event, on_progress)

    unsubscribe = remote.subscribe(handle) if on_progress is not None else None

    try:
        payload = remote.create_task(goal, autoplan=True, run=True)
    except RemoteError as error:
        if unsubscribe:
            unsubscribe()
        logger.info("Not starting web task on %s: %s", remote.host, error)
        if on_progress is not None:
            on_progress({"text": str(error), "done": False, "active": False,
                         "failed": True, "needs_you": False, "finished": True})
        return None

    task = _RemoteTask(payload)

    if unsubscribe is not None:
        task_id[0] = task.id
        for event in held:
            if event.task_id == task.id:
                _report(event, on_progress)
        held.clear()

        # Stop listening once this task is over, the same as the local path.
        def finish_when_done(event):
            if event.task_id == task.id and event.type in (
                    EventType.TASK_COMPLETED, EventType.TASK_FAILED,
                    EventType.TASK_CANCELLED):
                unsubscribe()
                stop_watching()

        stop_watching = remote.subscribe(finish_when_done)

    return task


def _report(event, on_progress):
    try:
        on_progress(describe(event))
    except Exception:
        logger.exception("Progress callback failed")


class _RemoteTask:
    """Just enough of a task for a caller that only needs its id and goal."""

    def __init__(self, payload):
        self.id = payload.get("id", "")
        self.goal = payload.get("goal", "")
        self.status = payload.get("status", "pending")
        self.steps = payload.get("steps", [])


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
