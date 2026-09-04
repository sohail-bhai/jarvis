"""Guards for mistakes the GUI cannot catch at import time.

The dashboard once referenced EVENT_* names it never imported. Because the
event poller rescheduled itself only after handling a batch, the resulting
NameError killed the poll loop and froze the whole UI. These tests parse the
GUI source instead of importing it, so they run without tkinter installed.
"""

import ast
import unittest
from pathlib import Path

import assistant.events as events

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUI_APP = PROJECT_ROOT / "gui" / "app.py"


def _module_tree(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class EventNameTests(unittest.TestCase):
    """Every EVENT_* the GUI mentions must exist and be imported."""

    def setUp(self):
        self.tree = _module_tree(GUI_APP)

    def _referenced_event_names(self):
        return {
            node.id
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Name) and node.id.startswith("EVENT_")
        }

    def _imported_names(self):
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported.add(alias.asname or alias.name)
        return imported

    def test_referenced_event_names_exist_in_events_module(self):
        for name in self._referenced_event_names():
            self.assertTrue(
                hasattr(events, name),
                f"gui/app.py uses {name}, which assistant.events does not define.",
            )

    def test_referenced_event_names_are_imported(self):
        missing = self._referenced_event_names() - self._imported_names()
        self.assertEqual(
            set(), missing,
            f"gui/app.py uses these event names without importing them: {sorted(missing)}",
        )


class EventPollerTests(unittest.TestCase):
    """The poll loop must always reschedule, even when an event blows up."""

    def test_poll_events_reschedules_in_a_finally_block(self):
        tree = _module_tree(GUI_APP)
        poller = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_poll_events"
        )

        tries = [node for node in poller.body if isinstance(node, ast.Try)]
        self.assertTrue(
            tries and any(block.finalbody for block in tries),
            "_poll_events must reschedule itself from a finally block so a "
            "failing event cannot stop the UI from updating.",
        )


class RedactionTests(unittest.TestCase):
    """The System Log must never render a credential."""

    def test_secrets_are_removed(self):
        from gui.widgets.system_log import redact

        secrets = [
            "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig12345678",
            "api_key=AIzaSyD-1234567890abcdefghijklmnopqrs",
            "password: hunter2trustno1",
            "ghp_16CharsAndMoreHere1234567890abcd",
        ]
        for secret in secrets:
            with self.subTest(secret=secret):
                self.assertNotIn(secret, redact(secret))

    def test_ordinary_messages_are_untouched(self):
        from gui.widgets.system_log import redact

        message = "Found 3 matching documents"
        self.assertEqual(message, redact(message))


if __name__ == "__main__":
    unittest.main()
