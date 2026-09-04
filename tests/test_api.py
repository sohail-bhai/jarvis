"""Tests for the HTTP and WebSocket boundary.

These use a control plane backed by a temporary database, so the API is
exercised end to end without touching the real one.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from assistant.api import create_app
from assistant.control.service import ControlPlane
from assistant.control.store import ControlStore


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="jarvis-api-test-")
        self.store = ControlStore(Path(self.tempdir) / "control.db")
        self.plane = ControlPlane(store=self.store)
        self.client = TestClient(create_app(control=self.plane))

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tempdir, ignore_errors=True)


class SystemTests(ApiTestCase):
    def test_root_points_at_the_documentation(self):
        response = self.client.get("/")
        self.assertEqual(200, response.status_code)
        self.assertEqual("/docs", response.json()["documentation"])

    def test_health_reports_ok(self):
        response = self.client.get("/health")
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["ok"])

    def test_status_summarises_the_control_plane(self):
        body = self.client.get("/api/status").json()
        for key in ("devices", "helpers", "active_tasks",
                    "pending_approvals", "temporary_access"):
            self.assertIn(key, body)

    def test_local_device_is_registered_automatically(self):
        devices = self.client.get("/api/devices").json()
        self.assertEqual(1, len(devices))
        self.assertEqual("computer", devices[0]["kind"])


class TaskApiTests(ApiTestCase):
    def test_creating_a_task_returns_its_steps(self):
        response = self.client.post("/api/tasks", json={
            "goal": "Continue my Hackwave project",
            "steps": ["Finding relevant files", "Researching on the web"],
        })

        self.assertEqual(201, response.status_code)
        body = response.json()
        self.assertEqual("Continue my Hackwave project", body["goal"])
        self.assertEqual(2, len(body["steps"]))
        self.assertEqual(0.0, body["progress"])

    def test_a_goal_is_required(self):
        self.assertEqual(422, self.client.post("/api/tasks", json={"goal": ""}).status_code)

    def test_unknown_task_is_a_404(self):
        self.assertEqual(404, self.client.get("/api/tasks/nope").status_code)

    def test_walking_the_steps_updates_progress(self):
        task_id = self.client.post("/api/tasks", json={
            "goal": "Do the thing", "steps": ["One", "Two"],
        }).json()["id"]

        self.client.post(f"/api/tasks/{task_id}/steps/start", json={"position": 0})
        self.client.post(f"/api/tasks/{task_id}/steps/finish",
                         json={"position": 0, "detail": "Found 3 documents"})

        body = self.client.get(f"/api/tasks/{task_id}").json()
        self.assertEqual(0.5, body["progress"])
        self.assertEqual("running", body["status"])

    def test_cancelling_a_task(self):
        task_id = self.client.post("/api/tasks", json={
            "goal": "Do the thing", "steps": ["One"],
        }).json()["id"]

        body = self.client.post(f"/api/tasks/{task_id}/cancel").json()
        self.assertEqual("cancelled", body["status"])

    def test_active_only_filters_finished_tasks(self):
        task_id = self.client.post("/api/tasks", json={"goal": "Finished one"}).json()["id"]
        self.client.post("/api/tasks", json={"goal": "Still going"})
        self.client.post(f"/api/tasks/{task_id}/complete")

        active = self.client.get("/api/tasks", params={"active_only": True}).json()
        self.assertEqual(["Still going"], [task["goal"] for task in active])


class HelperApiTests(ApiTestCase):
    def test_registering_a_helper_advertises_its_capabilities(self):
        response = self.client.post("/api/helpers", json={
            "name": "Research helper", "capabilities": ["research", "web"],
        })

        self.assertEqual(201, response.status_code)
        self.assertEqual(["research", "web"], response.json()["capabilities"])

    def test_a_task_is_matched_to_a_capable_helper(self):
        self.client.post("/api/helpers", json={
            "name": "Research helper", "capabilities": ["research"]})

        body = self.client.post("/api/tasks", json={
            "goal": "Look this up", "capability": "research"}).json()

        self.assertTrue(body["helper_id"])


class ApprovalApiTests(ApiTestCase):
    def _pending_approval(self):
        task = self.plane.create_task("Merge my changes", steps=["One"])
        return self.plane.request_approval(
            "Merge changes", "I'm ready to merge your project changes.",
            reason="You asked me to finish the project",
            impact="14 files will change", task_id=task.id), task

    def test_pending_approvals_are_listed(self):
        approval, _task = self._pending_approval()

        body = self.client.get("/api/approvals").json()
        self.assertEqual([approval.id], [item["id"] for item in body])

    def test_approving_resumes_the_task(self):
        approval, task = self._pending_approval()

        response = self.client.post(f"/api/approvals/{approval.id}",
                                    json={"approved": True})

        self.assertEqual(200, response.status_code)
        self.assertEqual("approved", response.json()["status"])
        self.assertEqual("running", self.client.get(f"/api/tasks/{task.id}").json()["status"])

    def test_declining_cancels_the_task(self):
        approval, task = self._pending_approval()

        self.client.post(f"/api/approvals/{approval.id}", json={"approved": False})

        self.assertEqual("cancelled",
                         self.client.get(f"/api/tasks/{task.id}").json()["status"])

    def test_deciding_twice_is_a_404(self):
        approval, _task = self._pending_approval()
        self.client.post(f"/api/approvals/{approval.id}", json={"approved": True})

        response = self.client.post(f"/api/approvals/{approval.id}",
                                    json={"approved": True})
        self.assertEqual(404, response.status_code)


class SecurityApiTests(ApiTestCase):
    def test_granting_access_reports_time_remaining(self):
        response = self.client.post("/api/permissions", json={
            "resource": "Hackwave project", "actions": ["read", "write"],
            "seconds": 1800,
        })

        self.assertEqual(201, response.status_code)
        body = response.json()
        self.assertEqual("active", body["status"])
        self.assertGreater(body["seconds_remaining"], 1700)

    def test_permission_length_is_capped(self):
        response = self.client.post("/api/permissions", json={
            "resource": "Everything", "actions": ["read"], "seconds": 999999,
        })
        self.assertEqual(422, response.status_code)

    def test_revoking_access(self):
        permission_id = self.client.post("/api/permissions", json={
            "resource": "Hackwave project", "actions": ["read"],
        }).json()["id"]

        self.client.delete(f"/api/permissions/{permission_id}")

        self.assertFalse(self.plane.check("Hackwave project", "read"))

    def test_emergency_stop_halts_work_and_blocks_new_tasks(self):
        self.client.post("/api/tasks", json={"goal": "Something", "steps": ["One"]})

        result = self.client.post("/api/emergency-stop").json()
        self.assertTrue(result["stopped"])
        self.assertEqual(1, result["tasks_cancelled"])

        blocked = self.client.post("/api/tasks", json={"goal": "New work"})
        self.assertEqual(409, blocked.status_code)

    def test_resume_allows_work_again(self):
        self.client.post("/api/emergency-stop")
        self.client.post("/api/resume")

        self.assertEqual(201, self.client.post("/api/tasks",
                                               json={"goal": "New work"}).status_code)


class ActivityApiTests(ApiTestCase):
    def test_activity_is_returned_newest_first(self):
        self.plane.record("First thing")
        self.plane.record("Second thing")

        messages = [event["message"] for event in self.client.get("/api/activity").json()]
        self.assertEqual("Second thing", messages[0])

    def test_websocket_sends_history_then_live_events(self):
        self.plane.record("Earlier thing")

        with self.client.websocket_connect("/ws/activity") as websocket:
            self.assertEqual("Earlier thing", websocket.receive_json()["message"])

            self.plane.record("Live thing")
            self.assertEqual("Live thing", websocket.receive_json()["message"])

    def test_websocket_unsubscribes_on_disconnect(self):
        with self.client.websocket_connect("/ws/activity") as websocket:
            websocket.receive_json  # connection established

        # The subscriber list must not grow once the client has gone away.
        self.assertEqual([], self.plane._subscribers)


if __name__ == "__main__":
    unittest.main()
