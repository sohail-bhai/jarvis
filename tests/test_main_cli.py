import unittest
import sys
import types
from unittest.mock import Mock, patch

import assistant
import main


class MainCliTests(unittest.TestCase):
    def test_server_mode_forwards_host_and_port_to_api(self):
        api_main = Mock(return_value=0)
        api_package = types.ModuleType("assistant.api")
        api_app = types.ModuleType("assistant.api.app")
        api_app.main = api_main

        with patch.dict(sys.modules, {
            "assistant.api": api_package,
            "assistant.api.app": api_app,
        }):
            assistant.api = api_package
            result = main.main(["--server", "--host", "0.0.0.0", "--port", "9876"])

        self.assertEqual(0, result)
        api_main.assert_called_once_with(["--host", "0.0.0.0", "--port", "9876"])

    def test_host_and_port_do_not_start_server_without_server_flag(self):
        with patch("main.AssistantController") as controller:
            instance = controller.return_value
            instance.handle_text_command.return_value = True

            result = main.main(["--text", "time", "--host", "0.0.0.0", "--port", "9876",
                                "--no-speech"])

        self.assertEqual(0, result)
        instance.handle_text_command.assert_called_once_with("time")


if __name__ == "__main__":
    unittest.main()
