"""Tests for the desktop app's bridge into the control plane.

The Web page used to draw a scripted animation. These check it now follows a
real task: real steps, real failures, and it stops listening when the work is
over.
"""

import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from assistant.control.executor import TaskExecutor
from assistant.control.service import ControlPlane
from assistant.control.store import ControlStore
from gui.tasks import describe, start_web_task
from assistant.control.models import ActivityEvent, EventType


class FixedPlanner:
    def __init__(self, steps):
        self.steps = steps

    def plan(self, goal):
        return list(self.steps)


class WebTaskTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="jarvis-gui-task-")
        self.store = ControlStore(Path(self.tempdir) / "control.db")
        self.plane = ControlPlane(store=self.store)
        self.ran = []
        self.executor = TaskExecutor(
            plane=self.plane,
            runner=lambda instruction, context: self._run(instruction),
            planner=FixedPlanner([{"label": "Opening the website", "depends_on": []},
                                  {"label": "Reading the results", "depends_on": [0]}]),
            max_attempts=1, backoff=0)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _run(self, instruction):
        self.ran.append(instruction)
        return f"Did: {instruction}"

    def start(self, goal="find the best places for food nearby", **kwargs):
        seen = []
        task = start_web_task(goal, on_progress=seen.append, plane=self.plane,
                              executor=self.executor, **kwargs)
        if task is not None:
            self.executor.wait(task.id, timeout=5)
        return task, seen

    def test_what_you_type_becomes_a_real_task_with_real_steps(self):
        task, _ = self.start()

        self.assertEqual(["Opening the website", "Reading the results"], self.ran)
        self.assertEqual("completed", self.plane.get_task(task.id).status.value)

    def test_progress_follows_the_actual_steps(self):
        _, seen = self.start()

        texts = [item["text"] for item in seen]
        self.assertIn("Opening the website", texts)
        self.assertIn("Did: Opening the website", texts)

    def test_a_started_step_is_marked_active_and_a_finished_one_is_not(self):
        _, seen = self.start()

        started = next(item for item in seen if item["text"] == "Opening the website")
        finished = next(item for item in seen if item["text"] == "Did: Opening the website")
        self.assertTrue(started["active"])
        self.assertTrue(finished["done"])

    def test_the_last_update_says_the_task_is_over(self):
        _, seen = self.start()

        self.assertTrue(seen[-1]["finished"])

    def test_a_failure_is_shown_as_a_failure_not_a_tick(self):
        self.executor = TaskExecutor(
            plane=self.plane,
            runner=lambda instruction, context: (_ for _ in ()).throw(
                RuntimeError("the site never loaded")),
            planner=FixedPlanner([{"label": "Opening the website", "depends_on": []}]),
            max_attempts=1, backoff=0)

        _, seen = self.start()

        self.assertTrue(any(item["failed"] for item in seen))

    def test_nothing_starts_while_jarvis_is_stopped(self):
        self.plane.emergency_stop()

        task, seen = self.start()

        self.assertIsNone(task)
        self.assertEqual([], self.ran)

    def test_it_stops_listening_once_the_task_is_over(self):
        before = len(self.plane._subscribers)

        self.start()

        self.assertEqual(before, len(self.plane._subscribers))

    def test_an_approval_is_flagged_as_needing_you(self):
        event = ActivityEvent(type=EventType.APPROVAL_REQUESTED,
                              message="Waiting for your approval: Can I merge?")

        self.assertTrue(describe(event)["needs_you"])

    def test_a_broken_progress_callback_never_stops_the_work(self):
        def explode(step):
            raise RuntimeError("the UI is gone")

        task = start_web_task("find food", on_progress=explode, plane=self.plane,
                              executor=self.executor)
        self.executor.wait(task.id, timeout=5)

        self.assertEqual("completed", self.plane.get_task(task.id).status.value)


if __name__ == "__main__":
    unittest.main()
