"""Tests for driving the browser.

The session is stood in for, so these run with no Chromium, no network and no
model. What they check is the loop VAVE actually relies on: act, look at
what the page became, decide again.
"""

import unittest

import shutil
import tempfile
from pathlib import Path

from assistant.browser import actions
from assistant.browser.session import BrowserUnavailable, set_session, reset_session
from assistant.site_memory import SiteMemory, set_site_memory


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
        self.filled = []
        self.login_page = False
        self.sign_in_calls = 0
        self.open_tabs = [start_url]

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

    def fill_form(self, fields):
        labels = []
        for target, value in fields.items():
            match = self.find(target)
            self.filled.append((match["label"], value))
            labels.append(match["label"])
        return labels

    def looks_like_login(self):
        return self.login_page

    def wait_until_signed_in(self, timeout_ms=None, poll_ms=None):
        self.sign_in_calls += 1
        self.login_page = False
        return True

    def tabs(self):
        return [{"index": index + 1, "title": self.pages[url].title, "url": url}
                for index, url in enumerate(self.open_tabs)]

    def new_tab(self, url=None):
        self.open_tabs.append(url or self.current)
        if url:
            self.current = url
        return self.describe()

    def switch_tab(self, index):
        position = int(index) - 1
        if not 0 <= position < len(self.open_tabs):
            raise LookupError(f"There is no tab {index}.")
        self.current = self.open_tabs[position]
        return self.describe()


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

        self.notes_dir = tempfile.mkdtemp(prefix="vave-browser-notes-")
        self.notes = SiteMemory(Path(self.notes_dir) / "site_notes.json")
        set_site_memory(self.notes)

    def tearDown(self):
        set_session(None)
        reset_session()
        set_site_memory(None)
        shutil.rmtree(self.notes_dir, ignore_errors=True)


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


class SiteMemoryTests(BrowserTestCase):
    def test_what_was_learned_before_comes_back_with_the_page(self):
        actions.remember_about_site("https://example.com", "the docs link is [1]")

        result = actions.browse("https://example.com")

        self.assertIn("What you learned about example.com before", result)
        self.assertIn("the docs link is [1]", result)

    def test_a_site_with_no_notes_just_shows_the_page(self):
        result = actions.browse("https://example.com")

        self.assertNotIn("What you learned", result)

    def test_a_note_is_confirmed_back_to_the_model(self):
        result = actions.remember_about_site("https://example.com", "needs a login")

        self.assertIn("Noted for https://example.com", result)
        self.assertEqual(["needs a login"], self.notes.recall("https://example.com"))


class SignInTests(BrowserTestCase):
    def test_a_login_page_is_pointed_out_rather_than_guessed_at(self):
        self.session.login_page = True

        result = actions.browse("https://example.com")

        self.assertIn("asking for a sign-in", result)
        self.assertIn("Do not try to type a password", result)

    def test_waiting_hands_the_window_to_the_person(self):
        self.session.login_page = True

        result = actions.browser_wait_for_login(seconds=1)

        self.assertEqual(1, self.session.sign_in_calls)
        self.assertIn("Signed in", result)

    def test_waiting_on_a_page_that_is_not_a_login_says_so(self):
        result = actions.browser_wait_for_login(seconds=1)

        self.assertIn("not asking for a sign-in", result)
        self.assertEqual(0, self.session.sign_in_calls)


class FormAndTabTests(BrowserTestCase):
    def test_a_form_is_filled_in_one_call(self):
        actions.browse("https://chat.example.com")

        result = actions.browser_fill_form({"Message the assistant": "hello"})

        self.assertEqual([("Message the assistant", "hello")], self.session.filled)
        self.assertIn("Filled: Message the assistant", result)

    def test_fields_sent_as_json_text_are_understood(self):
        actions.browse("https://chat.example.com")

        actions.browser_fill_form('{"Message the assistant": "typed as json"}')

        self.assertEqual([("Message the assistant", "typed as json")],
                         self.session.filled)

    def test_something_that_is_not_an_object_is_explained(self):
        self.assertIn("Send the fields as an object",
                      actions.browser_fill_form("just a string"))

    def test_a_side_trip_can_open_and_return(self):
        actions.browser_new_tab("https://example.com/docs")

        listed = actions.browser_tabs()
        back = actions.browser_switch_tab(1)

        self.assertIn("[2] Docs", listed)
        self.assertIn("Example Domain", back)

    def test_switching_to_a_tab_that_is_not_there_says_so(self):
        self.assertIn("There is no tab 9", actions.browser_switch_tab(9))


if __name__ == "__main__":
    unittest.main()
