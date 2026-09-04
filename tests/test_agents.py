"""Tests for the agent registry, health monitoring and the kill switch.

Health here is observed rather than assumed: an agent is only marked gone once
it has reported and then stopped, and stopping one must remove its access as
well as its work.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from assistant.control.adapters import (
    AdapterRegistry,
    AgentUnavailable,
    HttpAdapter,
    NativeAdapter,
)
from assistant.control.executor import TaskExecutor
from assistant.control.models import (
    Decision,
    DeviceStatus,
    Helper,
    HelperStatus,
    PermissionStatus,
    TaskStatus,
    now,
)
from assistant.control.service import (
    AGENT_STALE_SECONDS,
    DEVICE_STALE_SECONDS,
    ControlPlane,
)
from assistant.control.store import ControlStore


class AgentTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="jarvis-agent-test-")
        self.store = ControlStore(Path(self.tempdir) / "control.db")
        self.plane = ControlPlane(store=self.store)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tempdir, ignore_errors=True)


class RegistryTests(AgentTestCase):
    def test_an_agent_records_its_version_and_endpoint(self):
        agent = self.plane.register_helper(
            "Research agent", ["research"], framework="http",
            version="1.4.0", endpoint="http://localhost:9000/run",
            metadata={"owner": "phase-2"})

        stored = self.plane.get_helper(agent.id)
        self.assertEqual("1.4.0", stored.version)
        self.assertEqual("http://localhost:9000/run", stored.endpoint)
        self.assertEqual({"owner": "phase-2"}, stored.metadata)

    def test_registering_is_announced_on_the_timeline(self):
        self.plane.register_helper("Research agent", ["research"], version="1.4.0")

        messages = [event.message for event in self.plane.list_events()]
        self.assertIn("Research agent is available (1.4.0).", messages)

    def test_a_disabled_agent_is_never_selected(self):
        agent = self.plane.register_helper("Research agent", ["research"])

        self.plane.set_helper_enabled(agent.id, False)

        self.assertIsNone(self.plane.find_helper_for("research"))

    def test_a_disabled_agent_can_be_switched_back_on(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        self.plane.set_helper_enabled(agent.id, False)

        self.plane.set_helper_enabled(agent.id, True)

        self.assertEqual(agent.id, self.plane.find_helper_for("research").id)

    def test_disabling_keeps_the_agent_and_its_history(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        self.plane.heartbeat(agent.id, latency_ms=120, ok=True)

        self.plane.set_helper_enabled(agent.id, False)

        stored = self.plane.get_helper(agent.id)
        self.assertEqual(1, stored.success_count)
        self.assertFalse(stored.enabled)


class HealthTests(AgentTestCase):
    def test_a_heartbeat_records_success_and_latency(self):
        agent = self.plane.register_helper("Research agent", ["research"])

        self.plane.heartbeat(agent.id, latency_ms=200, ok=True)
        self.plane.heartbeat(agent.id, latency_ms=400, ok=True)

        stored = self.plane.get_helper(agent.id)
        self.assertEqual(2, stored.success_count)
        self.assertEqual(400, stored.p95_latency_ms)

    def test_failures_show_up_as_an_error_rate(self):
        agent = self.plane.register_helper("Research agent", ["research"])

        self.plane.heartbeat(agent.id, ok=True)
        self.plane.heartbeat(agent.id, ok=False)
        self.plane.heartbeat(agent.id, ok=False)

        self.assertEqual(0.667, self.plane.get_helper(agent.id).error_rate)

    def test_an_agent_that_goes_quiet_is_marked_offline(self):
        agent = self.plane.register_helper("Research agent", ["research"])

        self.plane.sweep(at=now() + AGENT_STALE_SECONDS + 1)

        self.assertEqual(HelperStatus.OFFLINE, self.plane.get_helper(agent.id).status)

    def test_going_offline_is_recorded_once(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        later = now() + AGENT_STALE_SECONDS + 1

        self.plane.sweep(at=later)
        self.plane.sweep(at=later)

        offline = [event for event in self.plane.list_events()
                   if event.message == "Research agent stopped responding."]
        self.assertEqual(1, len(offline))

    def test_an_agent_that_never_reported_is_not_assumed_dead(self):
        agent = Helper(name="Quiet agent", capabilities=["research"])
        self.store.save_helper(agent)

        self.plane.sweep(at=now() + AGENT_STALE_SECONDS * 10)

        self.assertEqual(HelperStatus.IDLE, self.plane.get_helper(agent.id).status)

    def test_a_returning_agent_becomes_available_again(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        self.plane.sweep(at=now() + AGENT_STALE_SECONDS + 1)

        self.plane.heartbeat(agent.id)

        self.assertEqual(HelperStatus.IDLE, self.plane.get_helper(agent.id).status)
        self.assertIsNotNone(self.plane.find_helper_for("research"))

    def test_an_offline_agent_is_not_selected(self):
        self.plane.register_helper("Research agent", ["research"])

        self.plane.sweep(at=now() + AGENT_STALE_SECONDS + 1)

        self.assertIsNone(self.plane.find_helper_for("research"))

    def test_health_reports_one_row_per_agent(self):
        self.plane.register_helper("Research agent", ["research"], version="1.0.0")
        self.plane.register_helper("Browser agent", ["browser"])

        rows = self.plane.agent_health()

        self.assertEqual({"Browser agent", "Research agent"},
                         {row["name"] for row in rows})
        self.assertIn("p95_latency_ms", rows[0])

    def test_the_status_summary_counts_unhealthy_agents(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        self.plane.kill_helper(agent.id)

        self.assertEqual(1, self.plane.status()["agents_quarantined"])


class DeviceTests(AgentTestCase):
    def test_a_device_advertises_what_it_can_do(self):
        device = self.plane.register_device("Rav's phone", kind="phone",
                                            capabilities=["notify", "approve"])

        self.assertTrue(self.store.get_device(device.id).can("approve"))

    def test_a_quiet_device_goes_offline(self):
        device = self.plane.register_device("Rav's phone", kind="phone")

        self.plane.sweep(at=now() + DEVICE_STALE_SECONDS + 1)

        self.assertEqual(DeviceStatus.OFFLINE, self.store.get_device(device.id).status)

    def test_a_heartbeat_brings_a_device_back(self):
        device = self.plane.register_device("Rav's phone", kind="phone")
        self.plane.sweep(at=now() + DEVICE_STALE_SECONDS + 1)

        self.plane.device_heartbeat(device.id, capabilities=["notify"])

        stored = self.store.get_device(device.id)
        self.assertEqual(DeviceStatus.ONLINE, stored.status)
        self.assertEqual(["notify"], stored.capabilities)

    def test_this_computer_is_never_swept_offline(self):
        self.plane.sweep(at=now() + DEVICE_STALE_SECONDS * 100)

        local = self.store.get_device(self.plane.local_device.id)
        self.assertEqual(DeviceStatus.ONLINE, local.status)


class KillSwitchTests(AgentTestCase):
    def test_killing_an_agent_quarantines_and_disables_it(self):
        agent = self.plane.register_helper("Rogue agent", ["research"])

        self.plane.kill_helper(agent.id, reason="It kept clicking Buy.")

        stored = self.plane.get_helper(agent.id)
        self.assertEqual(HelperStatus.QUARANTINED, stored.status)
        self.assertFalse(stored.enabled)

    def test_a_killed_agent_is_never_given_work_again(self):
        agent = self.plane.register_helper("Rogue agent", ["research"])

        self.plane.kill_helper(agent.id)

        self.assertIsNone(self.plane.find_helper_for("research"))

    def test_killing_an_agent_revokes_its_access(self):
        agent = self.plane.register_helper("Rogue agent", ["research"])
        task = self.plane.create_task("Look something up")
        self.plane.request_capability("browser.navigate", agent_id=agent.id,
                                      task_id=task.id)

        self.plane.kill_helper(agent.id)

        permission = self.plane.list_permissions(active_only=False)[0]
        self.assertEqual(PermissionStatus.REVOKED, permission.status)

    def test_another_agents_access_survives(self):
        rogue = self.plane.register_helper("Rogue agent", ["research"])
        good = self.plane.register_helper("Good agent", ["research"])
        self.plane.request_capability("browser.navigate", agent_id=rogue.id)
        self.plane.request_capability("web.search", agent_id=good.id)

        self.plane.kill_helper(rogue.id)

        active = [permission.actions[0]
                  for permission in self.plane.list_permissions(active_only=True)]
        self.assertEqual(["web.search"], active)

    def test_killing_an_agent_stops_the_task_it_was_working_on(self):
        agent = self.plane.register_helper("Rogue agent", ["research"])
        task = self.plane.create_task("Look something up", capability="research")
        agent.current_task_id = task.id
        self.store.save_helper(agent)

        self.plane.kill_helper(agent.id)

        self.assertEqual(TaskStatus.CANCELLED, self.plane.get_task(task.id).status)

    def test_the_timeline_records_why(self):
        agent = self.plane.register_helper("Rogue agent", ["research"])

        self.plane.kill_helper(agent.id, reason="It kept clicking Buy.")

        messages = [event.message for event in self.plane.list_events()]
        self.assertIn("Stopped Rogue agent and removed its access. "
                      "It kept clicking Buy.", messages)

    def test_killing_an_unknown_agent_reports_nothing(self):
        self.assertIsNone(self.plane.kill_helper("no-such-agent"))


class AdapterTests(unittest.TestCase):
    def test_the_native_adapter_runs_the_injected_runner(self):
        adapter = NativeAdapter(runner=lambda instruction, context: f"did {instruction}")

        self.assertEqual("did tidy", adapter.run_step("tidy"))

    def test_the_http_adapter_posts_the_step_and_reads_the_output(self):
        sent = {}

        def transport(url, payload, timeout):
            sent.update({"url": url, "payload": payload})
            return {"output": "Found 3 results."}

        adapter = HttpAdapter(transport=transport)
        agent = Helper(name="Remote", framework="http",
                       endpoint="http://localhost:9000/run")

        result = adapter.run_step("Search the web", context="none", agent=agent)

        self.assertEqual("Found 3 results.", result)
        self.assertEqual("http://localhost:9000/run", sent["url"])
        self.assertEqual("Search the web", sent["payload"]["instruction"])

    def test_an_agent_without_an_endpoint_is_unavailable(self):
        adapter = HttpAdapter(transport=lambda *args: {"output": "x"})

        with self.assertRaises(AgentUnavailable):
            adapter.run_step("Do it", agent=Helper(name="Remote", framework="http"))

    def test_a_transport_failure_is_reported_as_unavailable(self):
        def transport(url, payload, timeout):
            raise OSError("connection refused")

        adapter = HttpAdapter(transport=transport)
        agent = Helper(name="Remote", framework="http", endpoint="http://x/run")

        with self.assertRaises(AgentUnavailable):
            adapter.run_step("Do it", agent=agent)

    def test_an_error_from_the_agent_is_reported(self):
        adapter = HttpAdapter(transport=lambda *args: {"error": "model unavailable"})
        agent = Helper(name="Remote", framework="http", endpoint="http://x/run")

        with self.assertRaises(AgentUnavailable) as caught:
            adapter.run_step("Do it", agent=agent)
        self.assertIn("model unavailable", str(caught.exception))

    def test_the_registry_picks_the_adapter_for_the_framework(self):
        registry = AdapterRegistry(default=NativeAdapter(runner=lambda i, c: "local"))

        native = registry.for_agent(Helper(name="Local", framework="native"))
        remote = registry.for_agent(Helper(name="Remote", framework="http"))

        self.assertIsInstance(remote, HttpAdapter)
        self.assertEqual("local", native.run_step("x"))

    def test_an_unknown_framework_falls_back_to_running_it_locally(self):
        registry = AdapterRegistry(default=NativeAdapter(runner=lambda i, c: "local"))

        adapter = registry.for_agent(Helper(name="Mystery", framework="langgraph"))

        self.assertEqual("local", adapter.run_step("x"))


class ExecutorHealthTests(AgentTestCase):
    def test_finishing_a_step_records_the_agent_as_healthy(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        task = self.plane.create_task("Look it up", steps=["Searching"],
                                      capability="research")
        executor = TaskExecutor(plane=self.plane,
                                runner=lambda instruction, context: "Found it.")

        executor.run(task.id)

        stored = self.plane.get_helper(agent.id)
        self.assertEqual(1, stored.success_count)
        self.assertEqual(0, stored.error_count)

    def test_a_failing_step_counts_against_the_agent(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        task = self.plane.create_task("Look it up", steps=["Searching"],
                                      capability="research")

        def runner(instruction, context):
            raise RuntimeError("no model")

        TaskExecutor(plane=self.plane, runner=runner).run(task.id)

        self.assertEqual(1, self.plane.get_helper(agent.id).error_count)

    def test_a_remote_agent_is_driven_through_its_adapter(self):
        agent = self.plane.register_helper("Remote agent", ["research"],
                                           framework="http",
                                           endpoint="http://localhost:9000/run")
        task = self.plane.create_task("Look it up", steps=["Searching"],
                                      capability="research")
        registry = AdapterRegistry(default=NativeAdapter(runner=lambda i, c: "local"))
        registry.register(HttpAdapter(transport=lambda *args: {"output": "remote"}))

        TaskExecutor(plane=self.plane, adapters=registry).run(task.id)

        self.assertEqual("remote", self.store.list_steps(task.id)[0].detail)


if __name__ == "__main__":
    unittest.main()
