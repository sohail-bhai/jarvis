"""Tests for two things that only bite once the assistant is really in use.

Short-term memory used to be trimmed by counting messages. Ten messages is
nothing until three of them are 2000-character tool results, at which point
the request itself competes with the tool schemas for the context window.

Phone commands used to get a thread each. Two texts sent together meant two
agent loops driving the same mouse and keyboard, and the polling loop blocked
for the whole of every answer, so the inbox backed up behind long tasks.
"""

import queue
import unittest
from unittest import mock


class HistoryTrimTests(unittest.TestCase):
    @staticmethod
    def _trim(history, **kwargs):
        from assistant.ai_brain import trim_history
        return trim_history(history, **kwargs)

    def test_the_system_prompt_is_always_kept(self):
        history = [{"role": "system", "content": "rules"}]
        history += [{"role": "user", "content": "x" * 5000} for _ in range(6)]

        kept = self._trim(history)

        self.assertEqual(kept[0], history[0])

    def test_long_tool_results_shorten_the_history(self):
        history = [{"role": "system", "content": "rules"}]
        history += [{"role": "tool", "content": "x" * 3000} for _ in range(8)]

        kept = self._trim(history, max_messages=10, max_chars=12000)

        # Ten of these would be 30,000 characters; the budget is what decides.
        body = sum(len(message["content"]) for message in kept[1:])
        self.assertLessEqual(body, 12000 + 3000)
        self.assertLess(len(kept), 9)

    def test_short_turns_are_kept_up_to_the_message_limit(self):
        history = [{"role": "system", "content": "rules"}]
        history += [{"role": "user", "content": "hi"} for _ in range(30)]

        kept = self._trim(history, max_messages=10, max_chars=12000)

        self.assertEqual(len(kept), 11)

    def test_the_newest_turn_survives_even_when_it_is_huge(self):
        history = [{"role": "system", "content": "rules"},
                   {"role": "user", "content": "old"},
                   {"role": "user", "content": "y" * 40000}]

        kept = self._trim(history, max_messages=10, max_chars=12000)

        self.assertEqual(kept[-1]["content"], "y" * 40000)


class TelegramQueueTests(unittest.TestCase):
    """Commands from the phone run one at a time, in the order they arrived."""

    def setUp(self):
        from assistant import telegram_sync

        self.telegram_sync = telegram_sync
        telegram_sync._command_queue = queue.Queue()

    def test_commands_are_queued_rather_than_each_given_a_thread(self):
        first = self.telegram_sync._enqueue_command("open notepad")
        second = self.telegram_sync._enqueue_command("lock the laptop")

        self.assertEqual((first, second), (1, 2))
        self.assertEqual(self.telegram_sync._command_queue.qsize(), 2)

    def test_the_worker_runs_them_in_order_and_one_at_a_time(self):
        ran = []
        running = []

        def fake_execute(command, auto_confirm=False):
            # Anything overlapping would show up here as a second entry.
            running.append(command)
            self.assertEqual(len(running), 1)
            ran.append(command)
            running.pop()

        self.telegram_sync._enqueue_command("first")
        self.telegram_sync._enqueue_command("second")

        with mock.patch.object(self.telegram_sync, "execute_command",
                               fake_execute), \
             mock.patch.object(self.telegram_sync, "_telegram_active", True):
            worker = self.telegram_sync._command_worker
            # Drain what is queued, then stop the loop.
            with mock.patch.object(self.telegram_sync, "speak", lambda *a: None):
                import threading

                thread = threading.Thread(target=worker, daemon=True)
                thread.start()
                self.telegram_sync._command_queue.join()
                self.telegram_sync._telegram_active = False
                thread.join(timeout=3)

        self.assertEqual(ran, ["first", "second"])

    def test_a_failing_command_does_not_stop_the_queue(self):
        ran = []

        def fake_execute(command, auto_confirm=False):
            ran.append(command)
            if command == "boom":
                raise RuntimeError("tool exploded")

        self.telegram_sync._enqueue_command("boom")
        self.telegram_sync._enqueue_command("after")

        with mock.patch.object(self.telegram_sync, "execute_command",
                               fake_execute), \
             mock.patch.object(self.telegram_sync, "speak", lambda *a: None), \
             mock.patch.object(self.telegram_sync, "_telegram_active", True):
            import threading

            thread = threading.Thread(target=self.telegram_sync._command_worker,
                                      daemon=True)
            thread.start()
            self.telegram_sync._command_queue.join()
            self.telegram_sync._telegram_active = False
            thread.join(timeout=3)

        self.assertEqual(ran, ["boom", "after"])


class BrowserUnavailableTests(unittest.TestCase):
    """A missing browser must not send the model clicking around the desktop."""

    def test_the_failure_names_the_fix_and_forbids_the_desktop_route(self):
        from assistant.browser.actions import _guarded
        from assistant.browser.session import BrowserUnavailable

        def explode():
            raise BrowserUnavailable(
                "Playwright is not installed. Run: pip install playwright")

        message = _guarded(explode)

        self.assertIn("pip install playwright", message)
        self.assertIn("Do not try to reach this website by clicking", message)


if __name__ == "__main__":
    unittest.main()
