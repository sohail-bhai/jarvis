import unittest
from unittest.mock import patch

from assistant.controller import AssistantController


class ControllerTextCommandTests(unittest.TestCase):
    def test_handle_text_command_dispatches_normalized_command_once(self):
        seen_commands = []

        def fake_execute_command(command):
            seen_commands.append(command)
            return True

        with patch("assistant.controller.execute_command", fake_execute_command):
            controller = AssistantController(
                configure_speech_hooks=False,
                speech_enabled=False,
            )
            result = controller.handle_text_command(
                "open notepad open notepad open notepad"
            )

        self.assertTrue(result)
        self.assertEqual(seen_commands, ["open notepad"])


if __name__ == "__main__":
    unittest.main()
