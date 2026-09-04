"""The browser, as tools a model can call.

Each function answers in plain text, because that text goes straight back into
the model's context. The pattern is always the same: do one thing, then say
what the page looks like now, so the next decision is made from what is
actually on screen rather than from what was expected.
"""

import logging

from assistant.browser.session import BrowserUnavailable, get_session

logger = logging.getLogger(__name__)

# How much of a page to hand back after an action. Enough to decide with,
# small enough to leave room for the rest of the conversation.
GLANCE_CHARS = 900
READ_CHARS = 3000


def _session():
    return get_session()


def _page_summary(chars=GLANCE_CHARS):
    session = _session()
    where = session.describe()
    return (f"Page: {where['title']} ({where['url']})\n"
            f"{session.read_text(limit=chars)}")


def _element_list():
    elements = _session().elements()
    if not elements:
        return "No clickable elements found on this page."
    lines = [f"[{item['index']}] {item['role']}: {item['label']}" for item in elements]
    return "Things you can click or type into:\n" + "\n".join(lines)


def _guarded(action, *args, **kwargs):
    """Turn browser failures into something the model can react to."""
    try:
        return action(*args, **kwargs)
    except BrowserUnavailable as error:
        return f"The browser is not available: {error}"
    except LookupError as error:
        return f"{error}\n\n{_element_list()}"
    except Exception as error:
        logger.exception("Browser action failed")
        return f"That didn't work: {error}"


# -- the tools --------------------------------------------------------------

def browse(url):
    """Open a web page and report what is on it."""
    def run():
        _session().goto(url)
        return f"{_page_summary()}\n\n{_element_list()}"
    return _guarded(run)


def browser_read(full=False):
    """Read the current page again, without touching anything."""
    return _guarded(lambda: _page_summary(READ_CHARS if full else GLANCE_CHARS))


def browser_elements():
    """List what can be clicked or typed into, numbered."""
    return _guarded(_element_list)


def browser_click(target):
    """Click something by its number or its visible text."""
    def run():
        result = _session().click(target)
        return (f"Clicked '{result['clicked']}'. Now on: {result['title']}\n\n"
                f"{_page_summary()}\n\n{_element_list()}")
    return _guarded(run)


def browser_type(target, text, submit=False):
    """Type into a box. `submit=True` presses Enter afterwards."""
    def run():
        result = _session().type_text(target, text, submit=_as_bool(submit))
        note = "and pressed Enter" if result["submitted"] else "without submitting"
        return (f"Typed into '{result['typed_into']}' {note}.\n\n"
                f"{_page_summary()}")
    return _guarded(run)


def browser_press(key):
    """Press a key, such as Enter or Escape."""
    def run():
        _session().press(key)
        return f"Pressed {key}.\n\n{_page_summary()}"
    return _guarded(run)


def browser_wait_for(text, seconds=30):
    """Wait until some text appears - how you know a slow answer arrived."""
    def run():
        _session().wait_for_text(text, timeout_ms=int(float(seconds) * 1000))
        return f"'{text}' appeared.\n\n{_page_summary(READ_CHARS)}"
    return _guarded(run)


def browser_screenshot():
    """Save a picture of the page, for when reading the text is not enough."""
    return _guarded(lambda: f"Saved a screenshot to {_session().screenshot()}")


def browser_ask_site(url, prompt, answer_appears_within=90):
    """Ask a question on a site that has a chat box, and bring the answer back.

    This is the ChatGPT-style flow in one call: open the site, find the box a
    person would type into, send the question, wait for the reply to finish,
    and return what it said. It works on any site with a single obvious input,
    which is why it is not named after one of them.
    """
    def run():
        session = _session()
        session.goto(url)

        box = _find_input(session)
        if box is None:
            return (f"Opened {url} but could not find a box to type into. "
                    f"{_element_list()}")

        before = session.read_text(limit=READ_CHARS)
        session.type_text(box["index"], prompt, submit=True)

        # The answer arrives after the page does - a chat writes it a word at
        # a time, a search engine fills the results in afterwards. So wait for
        # real content that has stopped changing, not for "loaded".
        waiter = getattr(session, "wait_for_content", None)
        if callable(waiter):
            waiter(min_words=40, timeout_ms=int(answer_appears_within) * 1000)
        else:
            _wait_for_change(session, before, int(answer_appears_within))

        after = session.read_text(limit=READ_CHARS)
        answer = _new_text(before, after)
        return (f"Asked on {session.describe()['url']}:\n{prompt}\n\n"
                f"The page now says:\n{answer or after}")
    return _guarded(run)


# -- helpers ----------------------------------------------------------------

def _as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "yes", "1", "submit")


def _find_input(session):
    """The box a person would type a question into."""
    elements = session.elements()
    typeable = [item for item in elements
                if item["role"] in ("textbox", "input", "true", "textarea")]
    if not typeable:
        typeable = [item for item in elements
                    if any(word in item["label"].lower()
                           for word in ("ask", "message", "search", "prompt", "type"))]
    return typeable[0] if typeable else None


def _wait_for_change(session, before, seconds):
    """Poll until the page stops looking like it did before we asked."""
    import time

    deadline = time.monotonic() + seconds
    stable_since = None
    latest = before

    while time.monotonic() < deadline:
        time.sleep(1.0)
        current = session.read_text(limit=READ_CHARS)
        if current == latest and current != before:
            # Unchanged for a beat, and different from before: it finished.
            if stable_since and time.monotonic() - stable_since > 1.5:
                return True
            stable_since = stable_since or time.monotonic()
        else:
            stable_since = None
        latest = current
    return False


def _new_text(before, after):
    """Roughly, what the page gained - which is usually the answer."""
    if before and after.startswith(before[:200]):
        return after[len(before):].strip()
    return after.strip() if after != before else ""
