"""Driving a real browser: the way JARVIS uses the web like a person."""

from assistant.browser.actions import (
    browse,
    browser_ask_site,
    browser_click,
    browser_elements,
    browser_fill_form,
    browser_new_tab,
    browser_press,
    browser_read,
    browser_screenshot,
    browser_switch_tab,
    browser_tabs,
    browser_type,
    browser_wait_for,
    browser_wait_for_login,
    remember_about_site,
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
    "browser_click", "browser_elements", "browser_fill_form", "browser_new_tab",
    "browser_press", "browser_read", "browser_screenshot", "browser_switch_tab",
    "browser_tabs", "browser_type", "browser_wait_for", "browser_wait_for_login",
    "remember_about_site", "get_session", "reset_session", "set_session",
]
