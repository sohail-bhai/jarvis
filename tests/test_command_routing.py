"""Tests for command routing and the atomic desktop toolkit.

Two things are pinned down here. First, that ending the session is a decision
about the whole utterance: "stop overwatch" and "exit fullscreen" are ordinary
instructions, and treating the bare word "stop" as a shutdown used to kill the
assistant mid-task. Second, that the atomic tools a task gets chained from -
key combinations, waiting, window handling - behave predictably, since every
goal without a purpose-built tool is carried out by composing these.

The keyboard and window tests drive no real input; they check the translation
and clamping that happens before the OS is touched.
"""

import unittest


class QuitRoutingTests(unittest.TestCase):
    """Only an utterance aimed at the assistant itself should end the session."""

    @staticmethod
    def _is_quit(command):
        from assistant.commands import is_quit_command
        return is_quit_command(command)

    def test_instructions_containing_stop_are_not_shutdowns(self):
        # Each of these used to end the session, because the router matched the
        # bare substrings "stop", "exit" and "quit" anywhere in the sentence.
        for command in (
            "stop overwatch",
            "stop the music",
            "stop watching my screen",
            "stop the download",
            "exit fullscreen",
            "exit the game",
            "quit the game",
            "quit photoshop",
            "close the browser",
            "close notepad",
        ):
            with self.subTest(command=command):
                self.assertFalse(
                    self._is_quit(command),
                    f"{command!r} is an instruction, not a request to shut down",
                )

    def test_utterances_aimed_at_the_assistant_do_shut_down(self):
        for command in (
            "goodbye",
            "goodbye jarvis",
            "bye",
            "exit",
            "quit",
            "stop",
            "shut down",
            "quit vave",
            "stop yourself",
            "please exit",
            "goodbye.",
        ):
            with self.subTest(command=command):
                self.assertTrue(
                    self._is_quit(command),
                    f"{command!r} asks the assistant to shut down",
                )

    def test_blank_input_is_not_a_shutdown(self):
        for command in ("", "   ", None):
            with self.subTest(command=command):
                self.assertFalse(self._is_quit(command))


class KeyCombinationTests(unittest.TestCase):
    """Shortcuts are how a task saves, copies, or closes something."""

    @staticmethod
    def _normalise(raw):
        from assistant.system_tasks import _normalise_keys
        return _normalise_keys(raw)

    def test_combinations_are_split_into_keys(self):
        self.assertEqual(self._normalise("ctrl+s"), ["ctrl", "s"])
        self.assertEqual(self._normalise("ctrl+shift+esc"), ["ctrl", "shift", "esc"])
        self.assertEqual(self._normalise("alt+f4"), ["alt", "f4"])

    def test_spelling_a_model_might_use_is_accepted(self):
        # A language model will say "Control + S" or "control-s" as readily as
        # "ctrl+s", and pyautogui only understands the last of those.
        for raw in ("Ctrl + S", "control-s", "CONTROL+S", ["ctrl", "s"]):
            with self.subTest(raw=raw):
                self.assertEqual(self._normalise(raw), ["ctrl", "s"])

    def test_aliases_map_onto_platform_key_names(self):
        self.assertEqual(self._normalise("windows+r"), ["win", "r"])
        self.assertEqual(self._normalise("escape"), ["esc"])
        self.assertEqual(self._normalise("return"), ["enter"])

    def test_single_key_stays_single(self):
        self.assertEqual(self._normalise("enter"), ["enter"])

    def test_empty_input_yields_no_keys(self):
        self.assertEqual(self._normalise(""), [])
        self.assertEqual(self._normalise("  "), [])


class WaitTests(unittest.TestCase):
    """Waiting lets the interface settle, but must never stall the assistant."""

    def test_wait_is_clamped_to_a_sane_ceiling(self):
        from assistant.system_tasks import wait
        self.assertIn("30", wait(9999))

    def test_negative_and_unparsable_waits_do_not_raise(self):
        from assistant.system_tasks import wait
        self.assertIn("0", wait(-5))
        self.assertIn("1", wait("not a number"))


class ToolRegistryTests(unittest.TestCase):
    """The model can only use a tool it can both see and call."""

    def setUp(self):
        import assistant.ai_brain as ai_brain
        self.registry = ai_brain.AVAILABLE_FUNCTIONS
        self.schemas = {t["function"]["name"] for t in ai_brain.LLM_TOOLS}

    def test_atomic_desktop_tools_are_callable_and_described(self):
        # Without these a goal that has no purpose-built tool cannot be carried
        # out by composition, which is the whole fallback strategy.
        for name in (
            "get_clickable_elements", "read_screen", "list_windows",
            "focus_window", "close_window", "click_at", "double_click_at",
            "right_click_at", "move_mouse", "type_text", "press_key",
            "press_hotkey", "wait", "scroll", "drag_and_drop",
            "run_terminal_command",
        ):
            with self.subTest(tool=name):
                self.assertIn(name, self.registry, f"{name} is not callable")
                self.assertIn(name, self.schemas, f"{name} is invisible to the model")

    def test_every_described_tool_actually_exists(self):
        missing = sorted(self.schemas - set(self.registry))
        self.assertEqual(missing, [], f"described but not implemented: {missing}")


class ShortcutTypingTests(unittest.TestCase):
    """A shortcut handed to type_text must be pressed, not typed.

    Measured misuse: asked to select all and delete, the 3B model called
    type_text with "Ctrl+A\\nCtrl+Delete", which would have written those
    characters into the user's document.
    """

    @staticmethod
    def _sequence(raw):
        from assistant.system_tasks import _shortcut_sequence
        return _shortcut_sequence(raw)

    def test_a_lone_chord_is_recognised(self):
        for raw in ("ctrl+s", "Ctrl + A", "alt+f4", "CONTROL+S", "win+r",
                    "ctrl+shift+esc"):
            with self.subTest(raw=raw):
                self.assertEqual(self._sequence(raw), [raw.strip()])

    def test_several_chords_on_separate_lines_are_all_pressed(self):
        self.assertEqual(self._sequence("Ctrl+A\nCtrl+Delete"),
                         ["Ctrl+A", "Ctrl+Delete"])

    def test_real_text_is_still_typed(self):
        # Anything a person might actually want written must not be swallowed:
        # a false positive here silently loses the user's content.
        for raw in ("hello world", "2+2", "sales+marketing", "ctrl",
                    "Ctrl+A then type this", "my email is a+b@c.com",
                    "", "a+b+c+d+e", "press ctrl+s to save",
                    "The shortcut is Ctrl+S"):
            with self.subTest(raw=raw):
                self.assertEqual(self._sequence(raw), [])


class ToolSelectionTests(unittest.TestCase):
    """Narrowing decides what the model is even able to do."""

    @staticmethod
    def _names(instruction):
        import assistant.ai_brain as ai_brain
        return {t["function"]["name"]
                for t in ai_brain.select_tools(instruction)}

    def test_atomic_actions_are_offered_for_every_request(self):
        # The fallback strategy only exists if the fallback tools are sent.
        # "select all the text in notepad" matched no computer trigger at all,
        # so press_key was absent and the model settled for clear_notes.
        for instruction in (
            "select all the text in notepad and delete it",
            "undo what I just did",
            "summarise my unread email",
            "what is the capital of France",
            "",
        ):
            with self.subTest(instruction=instruction):
                names = self._names(instruction)
                for required in ("press_key", "type_text", "click_at",
                                 "get_clickable_elements", "focus_window",
                                 "list_windows", "close_window"):
                    self.assertIn(required, names)

    def test_triggers_match_whole_words(self):
        # "note" used to match inside "notepad", pulling in the notes tools and
        # letting clear_notes win; "doc" matched inside "document" and handed
        # the budget to Google Workspace.
        self.assertNotIn("clear_notes", self._names("close notepad"))
        self.assertNotIn("create_google_doc",
                         self._names("save the document open in notepad"))

    def test_request_specific_tools_still_lead(self):
        self.assertIn("summarize_gmail_inbox", self._names("summarise my inbox"))
        self.assertIn("browser_click", self._names("click the login button on example.com"))


if __name__ == "__main__":
    unittest.main()
