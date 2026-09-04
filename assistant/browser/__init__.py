"""Driving a real browser: the way JARVIS uses the web like a person."""

from assistant.browser.actions import (
    browse,
    browser_ask_site,
    browser_click,
    browser_elements,
    browser_press,
    browser_read,
    browser_screenshot,
    browser_type,
    browser_wait_for,
)
from assistant.browser.session import (
    BrowserSession,
    BrowserUnavailable,
    get_session,
    reset_session,
    set_session,
)

__all__ = [
    "BrowserSession", "BrowserUnavailable", "browse", "browser_ask_site",
    "browser_click", "browser_elements", "browser_press", "browser_read",
    "browser_screenshot", "browser_type", "browser_wait_for",
    "get_session", "reset_session", "set_session",
]
