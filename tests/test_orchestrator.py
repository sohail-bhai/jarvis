"""Tests for planning, the step graph, cancellation and capability enforcement.

These cover what the orchestrator promises: independent work runs at the same
time, dependent work waits, a running step can be stopped, and a tool whose
capability was never granted is refused at the moment it is called.
"""

import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from assistant.control.executor import CancelToken, Cancelled, TaskExecutor
from assistant.control.models import Decision, StepStatus, TaskStatus
from assistant.control.planner import Planner
from assistant.control.service import ControlPlane
from assistant.control.store import ControlStore


class PlannerTests(unittest.TestCase):
    def plan(self, reply, goal="Prepare my project for deployment"):
        return Planner(ask=lambda prompt: reply).plan(goal)

    def test_a_plan_becomes_steps_with_dependencies(self):
        steps = self.plan('[{"label": "Analysing the repository", "depends_on": []},'
                          ' {"label": "Running the tests", "depends_on": [0]}]')

        self.assertEqual(["Analysing the repository", "Running the tests"],
                         [step["label"] for step in steps])
        self.assertEqual([0], steps[1]["depends_on"])

    def test_json_wrapped_in_prose_is_still_read(self):
        steps = self.plan('Sure! Here you go:\n```json\n'
                          '[{"label": "Reading the notes", "depends_on": []}]\n```')

        self.assertEqual(["Reading the notes"], [step["label"] for step in steps])

    def test_a_dependency_may_only_point_backwards(self):
        steps = self.plan('[{"label": "First", "depends_on": [3]},'
                          ' {"label": "Second", "depends_on": [0, 7]}]')

        self.assertEqual([], steps[0]["depends_on"])
        self.assertEqual([0], steps[1]["depends_on"])

    def test_an_unreadable_answer_falls_back_to_the_goal(self):
        steps = self.plan("I am not going to answer in JSON today")

        self.assertEqual([{"label": "Prepare my project for deployment",
                           "depends_on": []}], steps)

    def test_a_model_failure_falls_back_to_the_goal(self):
        def explode(prompt):
            raise RuntimeError("Ollama is not running")

        steps = Planner(ask=explode).plan("Tidy my notes")

        self.assertEqual(["Tidy my notes"], [step["label"] for step in steps])

    def test_the_plan_is_capped(self):
        many = ",".join(f'{{"label": "Step {index}", "depends_on": []}}'
                        for index in range(20))
        steps = Planner(ask=lambda prompt: f"[{many}]", max_steps=4).plan("Do lots")

        self.assertEqual(4, len(steps))

    def test_empty_labels_are_dropped(self):
        steps = self.plan('[{"label": "", "depends_on": []},'
                          ' {"label": "Real work", "depends_on": []}]')

        self.assertEqual(["Real work"], [step["label"] for step in steps])


class OrchestratorTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="vave-orchestrator-test-")
        self.store = ControlStore(Path(self.tempdir) / "control.db")
        self.plane = ControlPlane(store=self.store)
        self.calls = []
        self.lock = threading.Lock()

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def runner(self, result="Done."):
        def run(instruction, context):
            with self.lock:
                self.calls.append(instruction)
            return result
        return run

    def executor(self, runner=None, **kwargs):
        kwargs.setdefault("max_attempts", 1)
        return TaskExecutor(plane=self.plane, runner=runner or self.runner(),
                            approval_timeout=5, **kwargs)


class StepGraphTests(OrchestratorTestCase):
    def test_a_plain_list_of_steps_still_runs_in_order(self):
        task = self.plane.create_task("Two parts", steps=["First", "Second"])

        self.executor(max_parallel=3).run(task.id)

        self.assertEqual(["First", "Second"], self.calls)

    def test_independent_steps_run_together(self):
        started = threading.Barrier(2, timeout=5)

        def run(instruction, context):
            started.wait()          # both must be running for this to pass
            with self.lock:
                self.calls.append(instruction)
            return "Done."

        task = self.plane.create_task("Two parts", steps=[
            {"label": "Search the web", "depends_on": []},
            {"label": "Read my notes", "depends_on": []},
        ])

        self.executor(runner=run, max_parallel=2).run(task.id)

        self.assertEqual({"Search the web", "Read my notes"}, set(self.calls))
        self.assertEqual(TaskStatus.COMPLETED, self.plane.get_task(task.id).status)

    def test_a_dependent_step_waits_for_what_it_needs(self):
        task = self.plane.create_task("Three parts", steps=[
            {"label": "Fetch the data", "depends_on": []},
            {"label": "Fetch the template", "depends_on": []},
            {"label": "Write the report", "depends_on": [0, 1]},
        ])

        self.executor(max_parallel=3).run(task.id)

        self.assertEqual("Write the report", self.calls[-1])

    def test_parallelism_is_bounded(self):
        running = []
        peak = []

        def run(instruction, context):
            with self.lock:
                running.append(instruction)
                peak.append(len(running))
            try:
                return "Done."
            finally:
                with self.lock:
                    running.remove(instruction)

        task = self.plane.create_task("Four parts", steps=[
            {"label": f"Part {index}", "depends_on": []} for index in range(4)])

        self.executor(runner=run, max_parallel=2).run(task.id)

        self.assertLessEqual(max(peak), 2)

    def test_a_step_whose_dependency_failed_never_runs(self):
        def run(instruction, context):
            with self.lock:
                self.calls.append(instruction)
            if instruction == "Fetch the data":
                raise RuntimeError("no network")
            return "Done."

        task = self.plane.create_task("Two parts", steps=[
            {"label": "Fetch the data", "depends_on": []},
            {"label": "Write the report", "depends_on": [0]},
        ])

        self.executor(runner=run).run(task.id)

        self.assertEqual(["Fetch the data"], self.calls)
        self.assertEqual(TaskStatus.FAILED, self.plane.get_task(task.id).status)

    def test_a_step_may_name_the_agent_that_should_do_it(self):
        agent = self.plane.register_helper("Research agent", ["research"])
        task = self.plane.create_task("One part", steps=[
            {"label": "Searching", "depends_on": [], "agent_id": agent.id}])

        self.executor().run(task.id)

        self.assertEqual(1, self.plane.get_helper(agent.id).success_count)

    def test_planning_produces_a_task_that_runs(self):
        planner = Planner(ask=lambda prompt:
                          '[{"label": "Reading the notes", "depends_on": []},'
                          ' {"label": "Writing the summary", "depends_on": [0]}]')
        executor = self.executor(planner=planner)

        task = executor.start("Summarise my notes")
        executor.wait(task.id, timeout=5)

        self.assertEqual(["Reading the notes", "Writing the summary"], self.calls)
        self.assertEqual(TaskStatus.COMPLETED, self.plane.get_task(task.id).status)


class CancellationTests(OrchestratorTestCase):
    def test_a_token_reports_when_it_is_cancelled(self):
        token = CancelToken()

        self.assertTrue(token)
        token.cancel()

        self.assertTrue(token.cancelled)
        with self.assertRaises(Cancelled):
            token.check()

    def test_stopping_a_task_interrupts_the_running_step(self):
        entered = threading.Event()
        released = threading.Event()

        def run(instruction, context):
            entered.set()
            released.wait(3)
            return "Done."

        task = self.plane.create_task("Two parts", steps=["First", "Second"])
        executor = self.executor(runner=run)
        executor.submit(task.id)
        entered.wait(3)

        executor.stop(task.id)
        released.set()
        executor.wait(task.id, timeout=5)

        self.assertEqual(TaskStatus.CANCELLED, self.plane.get_task(task.id).status)

    def test_a_cancelled_step_is_marked_rather_than_left_running(self):
        token_holder = {}

        def run(instruction, context):
            token = token_holder["token"]
            token.cancel()
            token.check()          # what a real step does between tool calls
            return "Done."

        task = self.plane.create_task("One part", steps=["First"])
        executor = self.executor(runner=run)

        original = executor._run_step

        def capture(task_id, step, outcomes, token):
            token_holder["token"] = token
            return original(task_id, step, outcomes, token)

        executor._run_step = capture
        executor.run(task.id)

        step = self.store.list_steps(task.id)[0]
        self.assertEqual(StepStatus.FAILED, step.status)
        self.assertEqual("Stopped part-way.", step.detail)

    def test_stopping_an_idle_task_still_cancels_it(self):
        task = self.plane.create_task("One part", steps=["First"])

        self.executor().stop(task.id)

        self.assertEqual(TaskStatus.CANCELLED, self.plane.get_task(task.id).status)


class CapabilityEnforcementTests(OrchestratorTestCase):
    def authorize(self, task_id="", agent=None):
        return self.executor()._authorizer(task_id, agent)

    def test_a_tool_with_no_capability_is_always_allowed(self):
        allowed, reason = self.authorize()("tell_time")

        self.assertTrue(allowed)
        self.assertEqual("", reason)

    def test_a_low_risk_tool_is_granted_on_demand(self):
        task = self.plane.create_task("Look it up")

        allowed, _ = self.authorize(task.id)("search_google")

        self.assertTrue(allowed)
        self.assertTrue(self.plane.has_capability("web.search", task_id=task.id))

    def test_a_high_risk_tool_is_refused_until_it_is_approved(self):
        task = self.plane.create_task("Send the invoice")

        allowed, reason = self.authorize(task.id)("send_email")

        self.assertFalse(allowed)
        self.assertIn("needs your approval", reason)

    def test_an_approved_capability_lets_the_tool_run(self):
        task = self.plane.create_task("Send the invoice")
        result = self.plane.request_capability("google.gmail.send", task_id=task.id)
        self.plane.resolve_approval(result["approval"]["id"], approved=True)

        allowed, _ = self.authorize(task.id)("send_email")

        self.assertTrue(allowed)

    def test_a_denied_capability_refuses_the_tool_with_the_reason(self):
        task = self.plane.create_task("Run something")
        self.plane.add_policy_rule("system.shell.run", Decision.DENY,
                                   reason="Not from a task.")

        allowed, reason = self.authorize(task.id)("run_terminal_command")

        self.assertFalse(allowed)
        self.assertIn("Not from a task.", reason)

    def test_an_already_granted_capability_is_not_requested_again(self):
        task = self.plane.create_task("Look it up")
        self.plane.request_capability("web.search", task_id=task.id)
        before = len(self.plane.list_permissions(active_only=True))

        self.authorize(task.id)("search_google")

        self.assertEqual(before, len(self.plane.list_permissions(active_only=True)))


if __name__ == "__main__":
    unittest.main()
