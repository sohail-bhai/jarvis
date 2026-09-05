"""Tests for the control plane: tasks, permissions, approvals, emergency stop."""

import shutil
import tempfile
import time
import unittest
from pathlib import Path

from assistant.control.models import (
    ApprovalStatus,
    HelperStatus,
    PermissionStatus,
    StepStatus,
    TaskStatus,
)
from assistant.control.service import ControlPlane
from assistant.control.store import ControlStore


class ControlPlaneTestCase(unittest.TestCase):
    """Each test gets its own database so nothing leaks between them."""

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="vave-test-")
        self.store = ControlStore(Path(self.tempdir) / "control.db")
        self.plane = ControlPlane(store=self.store)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tempdir, ignore_errors=True)


class TaskLifecycleTests(ControlPlaneTestCase):
    def test_task_starts_pending_and_records_creation(self):
        task = self.plane.create_task("Continue my Hackwave project",
                                      steps=["Finding files", "Researching"])

        self.assertEqual(TaskStatus.PENDING, task.status)
        messages = [event.message for event in self.plane.list_events()]
        self.assertIn("Started working on: Continue my Hackwave project", messages)

    def test_starting_a_step_moves_the_task_to_running(self):
        task = self.plane.create_task("Do the thing", steps=["One", "Two"])
        self.plane.start_step(task.id, 0)

        self.assertEqual(TaskStatus.RUNNING, self.plane.get_task(task.id).status)

    def test_only_one_step_is_active_at_a_time(self):
        task = self.plane.create_task("Do the thing", steps=["One", "Two", "Three"])
        self.plane.start_step(task.id, 0)
        self.plane.start_step(task.id, 1)

        steps = self.store.list_steps(task.id)
        active = [step for step in steps if step.status == StepStatus.ACTIVE]
        self.assertEqual(1, len(active))
        self.assertEqual("Two", active[0].label)
        # The step we moved off is closed out rather than left dangling.
        self.assertEqual(StepStatus.DONE, steps[0].status)

    def test_progress_reflects_completed_steps(self):
        task = self.plane.create_task("Do the thing", steps=["One", "Two", "Three", "Four"])
        self.plane.start_step(task.id, 0)
        self.plane.finish_step(task.id, 0)

        self.assertEqual(0.25, self.plane.task_detail(task.id)["progress"])

    def test_completing_a_task_closes_outstanding_steps(self):
        task = self.plane.create_task("Do the thing", steps=["One", "Two"])
        self.plane.complete_task(task.id, "All done.")

        self.assertEqual(TaskStatus.COMPLETED, self.plane.get_task(task.id).status)
        self.assertTrue(all(step.status == StepStatus.DONE
                            for step in self.store.list_steps(task.id)))

    def test_failure_is_recorded_honestly(self):
        task = self.plane.create_task("Do the thing", steps=["One"])
        self.plane.fail_task(task.id, "Couldn't reach the server.")

        stored = self.plane.get_task(task.id)
        self.assertEqual(TaskStatus.FAILED, stored.status)
        self.assertEqual("Couldn't reach the server.", stored.summary)

    def test_checkpoint_survives_and_supports_resuming(self):
        task = self.plane.create_task("Long job", steps=["One", "Two"])
        self.plane.save_checkpoint(task.id, {"position": 1, "note": "half done"})

        self.assertEqual({"position": 1, "note": "half done"},
                         self.plane.get_task(task.id).checkpoint)

    def test_task_survives_a_restart(self):
        task = self.plane.create_task("Persisted goal", steps=["One"])
        self.store.close()

        reopened = ControlStore(Path(self.tempdir) / "control.db")
        try:
            self.assertEqual("Persisted goal", reopened.get_task(task.id).goal)
        finally:
            reopened.close()
            self.store = reopened  # so tearDown closes something valid


class HelperSelectionTests(ControlPlaneTestCase):
    def test_helper_is_chosen_by_capability_not_by_name(self):
        self.plane.register_helper("Research helper", ["research", "web"])
        self.plane.register_helper("Coding helper", ["files", "git"])

        self.assertEqual("Coding helper", self.plane.find_helper_for("git").name)

    def test_missing_capability_returns_nothing(self):
        self.plane.register_helper("Coding helper", ["files"])
        self.assertIsNone(self.plane.find_helper_for("train-model"))

    def test_quarantined_helper_is_never_selected(self):
        helper = self.plane.register_helper("Flaky helper", ["research"])
        self.plane.quarantine_helper(helper.id, "It kept failing.")

        self.assertIsNone(self.plane.find_helper_for("research"))
        self.assertEqual(HelperStatus.QUARANTINED,
                         self.store.get_helper(helper.id).status)

    def test_task_records_the_helper_it_picked(self):
        helper = self.plane.register_helper("Research helper", ["research"])
        task = self.plane.create_task("Look this up", capability="research")

        self.assertEqual(helper.id, task.helper_id)


class PermissionTests(ControlPlaneTestCase):
    def test_granted_action_is_allowed_and_others_are_not(self):
        self.plane.grant("Hackwave project", ["read", "write"], seconds=600)

        self.assertTrue(self.plane.check("Hackwave project", "read"))
        self.assertFalse(self.plane.check("Hackwave project", "delete"))

    def test_access_to_a_different_resource_is_denied(self):
        self.plane.grant("Hackwave project", ["read"], seconds=600)
        self.assertFalse(self.plane.check("Private notes", "read"))

    def test_expired_permission_stops_allowing_access(self):
        permission = self.plane.grant("Temp thing", ["read"], seconds=1)
        # Move expiry into the past rather than sleeping.
        permission.expires_at = time.time() - 1
        self.store.save_permission(permission)

        self.assertFalse(self.plane.check("Temp thing", "read"))
        self.plane.expire_permissions()
        self.assertEqual(PermissionStatus.EXPIRED,
                         self.store.get_permission(permission.id).status)

    def test_revoked_permission_stops_allowing_access(self):
        permission = self.plane.grant("Hackwave project", ["read"], seconds=600)
        self.plane.revoke(permission.id)

        self.assertFalse(self.plane.check("Hackwave project", "read"))

    def test_finishing_a_task_releases_its_access(self):
        task = self.plane.create_task("Do the thing", steps=["One"])
        self.plane.grant("Hackwave project", ["read", "write"], task_id=task.id)
        self.plane.complete_task(task.id, "Done.")

        self.assertFalse(self.plane.check("Hackwave project", "read", task.id))


class ApprovalTests(ControlPlaneTestCase):
    def test_requesting_approval_parks_the_task(self):
        task = self.plane.create_task("Merge my changes", steps=["One"])
        self.plane.request_approval("Merge changes", "Ready to merge?", task_id=task.id)

        self.assertEqual(TaskStatus.WAITING_APPROVAL, self.plane.get_task(task.id).status)

    def test_approving_resumes_the_task(self):
        task = self.plane.create_task("Merge my changes", steps=["One"])
        approval = self.plane.request_approval("Merge changes", "Ready?", task_id=task.id)
        self.plane.resolve_approval(approval.id, True)

        self.assertEqual(TaskStatus.RUNNING, self.plane.get_task(task.id).status)
        self.assertEqual(ApprovalStatus.APPROVED,
                         self.store.get_approval(approval.id).status)

    def test_declining_cancels_the_task(self):
        task = self.plane.create_task("Merge my changes", steps=["One"])
        approval = self.plane.request_approval("Merge changes", "Ready?", task_id=task.id)
        self.plane.resolve_approval(approval.id, False)

        self.assertEqual(TaskStatus.CANCELLED, self.plane.get_task(task.id).status)

    def test_an_approval_cannot_be_decided_twice(self):
        approval = self.plane.request_approval("Send email", "Send it?")
        self.plane.resolve_approval(approval.id, True)

        self.assertIsNone(self.plane.resolve_approval(approval.id, False))


class EmergencyStopTests(ControlPlaneTestCase):
    def test_emergency_stop_cancels_work_and_revokes_access(self):
        task = self.plane.create_task("Do the thing", steps=["One"])
        self.plane.start_step(task.id, 0)
        self.plane.grant("Hackwave project", ["read", "write"], task_id=task.id)
        self.plane.request_approval("Send email", "Send it?", task_id=task.id)

        result = self.plane.emergency_stop()

        self.assertTrue(result["stopped"])
        self.assertEqual(TaskStatus.CANCELLED, self.plane.get_task(task.id).status)
        self.assertFalse(self.plane.check("Hackwave project", "read"))
        self.assertEqual([], self.plane.list_approvals(pending_only=True))

    def test_no_new_work_is_accepted_while_stopped(self):
        self.plane.emergency_stop()
        with self.assertRaises(RuntimeError):
            self.plane.create_task("Something new")

    def test_resume_allows_work_again(self):
        self.plane.emergency_stop()
        self.plane.resume()

        self.assertFalse(self.plane.is_stopped)
        self.assertIsNotNone(self.plane.create_task("Something new"))

    def test_emergency_stop_does_not_delete_history(self):
        task = self.plane.create_task("Do the thing", steps=["One"])
        before = len(self.plane.list_events())

        self.plane.emergency_stop()

        self.assertIsNotNone(self.plane.get_task(task.id))
        self.assertGreater(len(self.plane.list_events()), before)


class ActivityTests(ControlPlaneTestCase):
    def test_subscribers_receive_events_as_they_happen(self):
        received = []
        self.plane.subscribe(received.append)

        self.plane.record("Found 3 matching documents")

        self.assertEqual(["Found 3 matching documents"],
                         [event.message for event in received])

    def test_a_broken_subscriber_does_not_stop_the_work(self):
        def explode(_event):
            raise RuntimeError("listener is broken")

        received = []
        self.plane.subscribe(explode)
        self.plane.subscribe(received.append)

        self.plane.record("Still recorded")

        self.assertEqual(1, len(received))

    def test_unsubscribe_stops_delivery(self):
        received = []
        unsubscribe = self.plane.subscribe(received.append)
        unsubscribe()

        self.plane.record("Not delivered")

        self.assertEqual([], received)

    def test_events_can_be_filtered_by_task(self):
        first = self.plane.create_task("First goal")
        second = self.plane.create_task("Second goal")

        messages = [event.message for event in self.plane.list_events(task_id=first.id)]
        self.assertIn("Started working on: First goal", messages)
        self.assertNotIn("Started working on: Second goal", messages)

        del second


if __name__ == "__main__":
    unittest.main()
