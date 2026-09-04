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
from assistant.api.auth import ApiSecurity
from assistant.control.executor import TaskExecutor
from assistant.control.service import ControlPlane
from assistant.control.store import ControlStore


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="jarvis-api-test-")
        self.store = ControlStore(Path(self.tempdir) / "control.db")
        self.plane = ControlPlane(store=self.store)
        # A runner that needs no local model, so the API is tested on its own.
        self.executed = []
        self.executor = TaskExecutor(plane=self.plane, runner=self._runner)
        # These tests are about the endpoints; authentication has its own
        # module, so this app is deliberately open.
        self.security = ApiSecurity(self.store, require_auth=False,
                                    rate_limit_per_minute=10000)
        self.client = TestClient(create_app(control=self.plane,
                                            executor=self.executor,
                                            security=self.security))

    def _runner(self, instruction, context):
        self.executed.append(instruction)
        return f"Handled: {instruction}"

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


class TaskExecutionTests(ApiTestCase):
    def test_running_a_task_works_its_steps(self):
        created = self.client.post("/api/tasks", json={
            "goal": "Tidy my notes", "steps": ["Reading notes"]}).json()

        response = self.client.post(f"/api/tasks/{created['id']}/run")
        self.executor.wait(created["id"], timeout=5)

        self.assertEqual(202, response.status_code)
        self.assertEqual(["Reading notes"], self.executed)
        detail = self.client.get(f"/api/tasks/{created['id']}").json()
        self.assertEqual("completed", detail["status"])

    def test_a_task_can_be_created_and_run_in_one_call(self):
        created = self.client.post("/api/tasks", json={
            "goal": "Tidy my notes", "steps": ["Reading notes"], "run": True}).json()
        self.executor.wait(created["id"], timeout=5)

        self.assertEqual(["Reading notes"], self.executed)

    def test_creating_without_run_does_not_start_work(self):
        self.client.post("/api/tasks", json={
            "goal": "Tidy my notes", "steps": ["Reading notes"]})

        self.assertEqual([], self.executed)

    def test_running_an_unknown_task_is_a_404(self):
        response = self.client.post("/api/tasks/no-such-task/run")
        self.assertEqual(404, response.status_code)

    def test_running_a_finished_task_is_refused(self):
        created = self.client.post("/api/tasks", json={"goal": "Tidy my notes"}).json()
        self.client.post(f"/api/tasks/{created['id']}/complete")

        response = self.client.post(f"/api/tasks/{created['id']}/run")
        self.assertEqual(409, response.status_code)

    def test_running_is_refused_while_stopped(self):
        created = self.client.post("/api/tasks", json={
            "goal": "Tidy my notes", "steps": ["Reading notes"]}).json()
        self.client.post("/api/emergency-stop")

        response = self.client.post(f"/api/tasks/{created['id']}/run")

        self.assertEqual(409, response.status_code)
        self.assertEqual([], self.executed)


class CapabilityTests(ApiTestCase):
    def test_the_catalog_lists_capabilities_with_their_risk(self):
        body = self.client.get("/api/capabilities").json()

        entry = next(item for item in body
                     if item["capability"] == "gcp.cloud_run.deploy")
        self.assertEqual("critical", entry["risk"])

    def test_the_catalog_can_be_filtered(self):
        body = self.client.get("/api/capabilities", params={"prefix": "browser.*"}).json()

        self.assertTrue(all(item["capability"].startswith("browser.")
                            for item in body))

    def test_a_low_risk_request_is_granted(self):
        body = self.client.post("/api/capabilities/request",
                                json={"capability": "browser.navigate"}).json()

        self.assertEqual("granted", body["status"])
        self.assertIsNotNone(body["permission"])

    def test_a_high_risk_request_comes_back_waiting(self):
        body = self.client.post("/api/capabilities/request",
                                json={"capability": "google.gmail.send"}).json()

        self.assertEqual("waiting", body["status"])
        self.assertEqual("google.gmail.send", body["approval"]["capability"])

    def test_approving_over_the_api_releases_the_access(self):
        request = self.client.post("/api/capabilities/request",
                                   json={"capability": "google.gmail.send"}).json()

        self.client.post(f"/api/approvals/{request['approval']['id']}",
                         json={"approved": True})

        granted = [permission["actions"]
                   for permission in self.client.get("/api/permissions").json()]
        self.assertIn(["google.gmail.send"], granted)

    def test_requesting_is_refused_while_stopped(self):
        self.client.post("/api/emergency-stop")

        response = self.client.post("/api/capabilities/request",
                                    json={"capability": "browser.navigate"})

        self.assertEqual(409, response.status_code)

    def test_a_policy_rule_changes_the_answer(self):
        self.client.post("/api/policies", json={"capability": "browser.navigate",
                                                 "decision": "deny",
                                                 "reason": "Not today."})

        body = self.client.post("/api/capabilities/request",
                                json={"capability": "browser.navigate"}).json()

        self.assertEqual("denied", body["status"])
        self.assertEqual("Not today.", body["judgement"]["reason"])

    def test_policy_rules_are_listed_and_removable(self):
        rule = self.client.post("/api/policies",
                                json={"capability": "google.*",
                                      "decision": "require_approval"}).json()

        self.assertEqual(1, len(self.client.get("/api/policies").json()))
        self.assertEqual(200, self.client.delete(f"/api/policies/{rule['id']}").status_code)
        self.assertEqual([], self.client.get("/api/policies").json())

    def test_an_unknown_decision_is_rejected(self):
        response = self.client.post("/api/policies",
                                    json={"capability": "google.*",
                                          "decision": "maybe"})

        self.assertEqual(422, response.status_code)

    def test_removing_an_unknown_rule_is_a_404(self):
        self.assertEqual(404, self.client.delete("/api/policies/nope").status_code)


if __name__ == "__main__":
    unittest.main()
