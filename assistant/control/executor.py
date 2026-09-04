"""Executes control plane tasks by running their steps through the AI brain.

The control plane records what should happen; this is the piece that makes it
happen. It walks a task's steps in order, hands each one to the JARVIS agent
loop, and writes the outcome back so every client - desktop, mobile or the
activity stream - sees real progress rather than a plan nobody is working on.

The runner is injectable, so the coordination logic here is testable without a
local model, and so a future remote helper can be plugged in without touching
the control plane.
"""

import logging
import threading
import time

from assistant.control.models import StepStatus, TaskStatus
from assistant.control.service import get_control_plane

logger = logging.getLogger(__name__)

# How long a step may wait on a user decision before we give up on it.
DEFAULT_APPROVAL_TIMEOUT = 15 * 60

# How often we look for a decision or a stop while waiting.
POLL_SECONDS = 0.1

# Steps carry their predecessors' outcomes forward, but not without limit.
MAX_CONTEXT_CHARS = 2000


class TaskExecutor:
    """Runs tasks step by step and keeps the control plane honest about it."""

    def __init__(self, plane=None, runner=None,
                 approval_timeout=DEFAULT_APPROVAL_TIMEOUT):
        self.plane = plane or get_control_plane()
        self._runner = runner
        self.approval_timeout = approval_timeout
        self._threads = {}
        self._lock = threading.RLock()

    # -- running ------------------------------------------------------------

    def submit(self, task_id):
        """Start a task in the background. Returns the task, or None if unknown."""
        task = self.plane.get_task(task_id)
        if task is None:
            return None

        with self._lock:
            existing = self._threads.get(task_id)
            if existing is not None and existing.is_alive():
                return task

            thread = threading.Thread(target=self._run_quietly, args=(task_id,),
                                      name=f"task-{task_id[:8]}", daemon=True)
            self._threads[task_id] = thread

        thread.start()
        return task

    def start(self, goal, steps=None, capability=None):
        """Create a task and immediately begin working it."""
        task = self.plane.create_task(goal, steps=steps, capability=capability)
        self.submit(task.id)
        return task

    def wait(self, task_id, timeout=60):
        """Block until a submitted task's thread finishes. Returns the task."""
        with self._lock:
            thread = self._threads.get(task_id)
        if thread is not None:
            thread.join(timeout)
        return self.plane.get_task(task_id)

    def _run_quietly(self, task_id):
        try:
            self.run(task_id)
        except Exception:
            # A background thread must not die silently, and it must not take
            # the process with it either.
            logger.exception("Task %s crashed", task_id)
            self.plane.fail_task(task_id, "Something went wrong while working on this.")

    def run(self, task_id):
        """Work a task to completion on the calling thread.

        Every exit path is recorded: completion with a summary, an honest
        failure with the real reason, or cancellation when the user or an
        emergency stop says so.
        """
        task = self.plane.get_task(task_id)
        if task is None:
            return None
        if task.status.is_terminal:
            return task

        if self.plane.is_stopped:
            return self.plane.cancel_task(task_id, "JARVIS is stopped.")

        steps = self.plane.store.list_steps(task_id)
        if not steps:
            # A goal with no plan is still work: treat the goal as the step.
            return self._run_single(task)

        outcomes = []
        for step in steps:
            if step.status in (StepStatus.DONE, StepStatus.SKIPPED):
                continue

            halted = self._halt_reason(task_id)
            if halted:
                return self.plane.cancel_task(task_id, halted)

            if not self._wait_for_approvals(task_id):
                return self.plane.get_task(task_id)

            self.plane.start_step(task_id, step.position)
            try:
                outcome = self._call_runner(step.label, self._context(outcomes))
            except Exception as error:
                logger.exception("Step %s of task %s failed", step.position, task_id)
                self.plane.finish_step(task_id, step.position,
                                       detail=f"Couldn't do this: {error}", failed=True)
                return self.plane.fail_task(
                    task_id, f"Stopped at '{step.label}'. {error}")

            outcomes.append((step.label, outcome))
            self.plane.finish_step(task_id, step.position, detail=outcome)
            self.plane.save_checkpoint(task_id, {
                "completed_through": step.position,
                "outcomes": [{"step": label, "outcome": text}
                             for label, text in outcomes],
            })

        return self.plane.complete_task(task_id, outcomes[-1][1] if outcomes else "Done.")

    def _run_single(self, task):
        """Work a task whose goal was never broken into steps."""
        try:
            outcome = self._call_runner(task.goal, "")
        except Exception as error:
            logger.exception("Task %s failed", task.id)
            return self.plane.fail_task(task.id, str(error))
        return self.plane.complete_task(task.id, outcome)

    # -- collaborators ------------------------------------------------------

    def _call_runner(self, instruction, context):
        if self._runner is not None:
            return self._runner(instruction, context)

        # Imported here so the control plane and the API stay importable
        # without the assistant's heavier runtime dependencies.
        from assistant import ai_brain

        return ai_brain.run_task_step(instruction, context=context)

    def _context(self, outcomes):
        """What earlier steps produced, trimmed so the model's context survives."""
        if not outcomes:
            return ""
        text = "\n".join(f"- {label}: {outcome}" for label, outcome in outcomes)
        if len(text) > MAX_CONTEXT_CHARS:
            text = "..." + text[-MAX_CONTEXT_CHARS:]
        return text

    # -- interruptions ------------------------------------------------------

    def _halt_reason(self, task_id):
        """Why this task should stop now, or an empty string to keep going."""
        if self.plane.is_stopped:
            return "JARVIS is stopped."

        task = self.plane.get_task(task_id)
        if task is None:
            return "This task no longer exists."
        if task.status == TaskStatus.CANCELLED:
            return "You stopped this."
        if task.status.is_terminal:
            return "This task already finished."
        return ""

    def _wait_for_approvals(self, task_id):
        """Hold while the user decides. False means the task must not continue.

        The control plane already moved the task to `waiting_approval` when the
        approval was requested, so this only has to respect that decision.
        """
        deadline = time.monotonic() + self.approval_timeout

        while True:
            task = self.plane.get_task(task_id)
            if task is None or task.status.is_terminal:
                return False
            if self.plane.is_stopped:
                self.plane.cancel_task(task_id, "JARVIS is stopped.")
                return False
            if task.status != TaskStatus.WAITING_APPROVAL:
                return True

            if time.monotonic() >= deadline:
                self.plane.cancel_task(
                    task_id, "Nobody answered the approval request, so this stopped.")
                return False

            time.sleep(POLL_SECONDS)


_executor = None
_executor_lock = threading.Lock()


def get_executor(plane=None, runner=None):
    """Shared executor used by the desktop app and the API."""
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = TaskExecutor(plane=plane, runner=runner)
        return _executor


def reset_executor():
    """Drop the shared executor. Used by tests."""
    global _executor
    with _executor_lock:
        _executor = None
