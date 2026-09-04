"""Tests for driving the browser.

The session is stood in for, so these run with no Chromium, no network and no
model. What they check is the loop JARVIS actually relies on: act, look at
what the page became, decide again.
"""

import unittest

from assistant.browser import actions
from assistant.browser.session import BrowserUnavailable, set_session, reset_session


class FakePage:
    """A page with text and a few things on it that can be clicked."""

    def __init__(self, url, title, text, elements):
        self.url = url
        self.title = title
        self.text = text
        self.elements = elements


class FakeSession:
    """Stands in for BrowserSession, recording what was asked of it."""

    def __init__(self, pages, start_url):
        self.pages = pages
        self.current = start_url
        self.typed = []
        self.clicked = []
        self.pressed = []
        self.waited = []
        self.screenshots = 0

    @property
    def page(self):
        return self.pages[self.current]

    def describe(self):
        return {"url": self.page.url, "title": self.page.title}

    def read_text(self, limit=3000):
        return self.page.text[:limit]

    def elements(self, refresh=True):
        return [{"index": index + 1, "role": role, "label": label}
                for index, (role, label, _) in enumerate(self.page.elements)]

    def find(self, target):
        for index, (role, label, _) in enumerate(self.page.elements):
            if str(target) == str(index + 1) or str(target).lower() in label.lower():
                return {"index": index + 1, "role": role, "label": label}
        raise LookupError(f"Nothing on this page looks like '{target}'.")

    def goto(self, url):
        self.current = url
        return self.describe()

    def click(self, target):
        match = self.find(target)
        self.clicked.append(match["label"])
        destination = self.page.elements[match["index"] - 1][2]
        if destination:
            self.current = destination
        return {"clicked": match["label"], **self.describe()}

    def type_text(self, target, text, submit=False):
        match = self.find(target)
        self.typed.append((match["label"], text, submit))
        if submit:
            self.page.text += f" ANSWER: best tacos are on 5th Street."
        return {"typed_into": match["label"], "submitted": submit}

    def press(self, key):
        self.pressed.append(key)
        return self.describe()

    def wait_for_text(self, text, timeout_ms=None):
        self.waited.append(text)
        return True

    def screenshot(self, path=None):
        self.screenshots += 1
        return "/tmp/shot.png"


class BrowserTestCase(unittest.TestCase):
    def setUp(self):
        self.pages = {
            "https://example.com": FakePage(
                "https://example.com", "Example Domain",
                "Example Domain. This domain is for use in examples.",
                [("link", "More information", "https://example.com/docs")]),
            "https://example.com/docs": FakePage(
                "https://example.com/docs", "Docs",
                "Documentation lives here.", []),
            "https://chat.example.com": FakePage(
                "https://chat.example.com", "Chat",
                "Ask me anything.",
                [("textbox", "Message the assistant", None)]),
        }
        self.session = FakeSession(self.pages, "https://example.com")
        set_session(self.session)

    def tearDown(self):
        set_session(None)
        reset_session()


class LookingTests(BrowserTestCase):
    def test_opening_a_page_reports_what_is_on_it(self):
        result = actions.browse("https://example.com")

        self.assertIn("Example Domain", result)
        self.assertIn("[1] link: More information", result)

    def test_the_element_list_is_numbered_for_the_model(self):
        self.assertIn("[1] link: More information", actions.browser_elements())

    def test_reading_does_not_change_the_page(self):
        actions.browser_read()

        self.assertEqual([], self.session.clicked)

    def test_a_page_with_nothing_clickable_says_so(self):
        actions.browse("https://example.com/docs")

        self.assertIn("No clickable elements", actions.browser_elements())


class ActingTests(BrowserTestCase):
    def test_clicking_by_visible_text_follows_the_link(self):
        result = actions.browser_click("More information")

        self.assertIn("Docs", result)
        self.assertEqual(["More information"], self.session.clicked)

    def test_clicking_by_number_works_too(self):
        actions.browser_click(1)

        self.assertEqual(["More information"], self.session.clicked)

    def test_clicking_something_absent_hands_back_the_real_options(self):
        result = actions.browser_click("Buy now")

        self.assertIn("Nothing on this page looks like 'Buy now'", result)
        self.assertIn("[1] link: More information", result)

    def test_typing_can_submit(self):
        actions.browse("https://chat.example.com")

        actions.browser_type(1, "where should I eat?", submit=True)

        self.assertEqual([("Message the assistant", "where should I eat?", True)],
                         self.session.typed)

    def test_submit_accepts_the_strings_a_model_sends(self):
        actions.browse("https://chat.example.com")

        actions.browser_type(1, "hello", submit="true")

        self.assertTrue(self.session.typed[0][2])

    def test_waiting_for_text_is_reported(self):
        actions.browser_wait_for("done", seconds=5)

        self.assertEqual(["done"], self.session.waited)

    def test_a_screenshot_names_the_file(self):
        self.assertIn("/tmp/shot.png", actions.browser_screenshot())


class AskingASiteTests(BrowserTestCase):
    def test_a_question_is_typed_sent_and_the_answer_returned(self):
        result = actions.browser_ask_site("https://chat.example.com",
                                          "best places for food nearby?",
                                          answer_appears_within=0)

        self.assertEqual([("Message the assistant",
                           "best places for food nearby?", True)], self.session.typed)
        self.assertIn("best tacos", result)

    def test_a_site_with_no_input_says_so_instead_of_guessing(self):
        result = actions.browser_ask_site("https://example.com/docs", "hello",
                                          answer_appears_within=0)

        self.assertIn("could not find a box to type into", result)


class FailureTests(BrowserTestCase):
    def test_a_missing_browser_is_explained_not_raised(self):
        class Broken:
            def goto(self, url):
                raise BrowserUnavailable("Playwright is not installed.")

        set_session(Broken())

        self.assertIn("browser is not available", actions.browse("https://example.com"))

    def test_an_unexpected_failure_is_reported_to_the_model(self):
        class Broken:
            def describe(self):
                raise RuntimeError("tab crashed")

        set_session(Broken())

        self.assertIn("tab crashed", actions.browser_read())


if __name__ == "__main__":
    unittest.main()
