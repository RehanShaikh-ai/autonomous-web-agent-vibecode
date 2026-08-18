"""Module Owned by Member B: Browser Specialist.

This module provides Playwright-based browser control, multi-tab orchestration,
atomic action executors (navigate, click, input, scroll, wait), ad/tracker suppression,
viewport screenshots, and DOM capture.
"""

from backend.browser.actions import (
    execute_click,
    execute_input,
    execute_navigate,
    execute_scroll,
    execute_wait,
)
from backend.browser.config import BrowserConfig
from backend.browser.engine import BrowserEngine
from backend.browser.exceptions import (
    BrowserActionError,
    BrowserError,
    NavigationTimeoutError,
    SelectorNotFoundError,
    TabManagementError,
)
from backend.browser.tab_manager import TabManager

__all__ = [
    "BrowserEngine",
    "BrowserConfig",
    "TabManager",
    "BrowserError",
    "BrowserActionError",
    "SelectorNotFoundError",
    "NavigationTimeoutError",
    "TabManagementError",
    "execute_navigate",
    "execute_click",
    "execute_input",
    "execute_scroll",
    "execute_wait",
]
