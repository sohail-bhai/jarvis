import unittest

from assistant.text_utils import normalize_command_text


class TextUtilsTests(unittest.TestCase):
    def test_collapses_repeated_full_command(self):
        command = "open notepad open notepad open notepad"
        self.assertEqual(normalize_command_text(command), "open notepad")

    def test_keeps_normal_repeated_words(self):
        self.assertEqual(normalize_command_text("very very good"), "very very good")

    def test_normalizes_spacing_and_case(self):
        self.assertEqual(normalize_command_text("  TIME   "), "time")


if __name__ == "__main__":
    unittest.main()
