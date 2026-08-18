"""Multi-tab orchestration and lifecycle management for Playwright browser sessions.

This module provides the TabManager class to safely create, switch, track,
and close multiple browser tabs within an active BrowserContext.
"""

import logging
import uuid
from typing import Dict, List, Optional, Tuple

from playwright.async_api import BrowserContext, Page

from backend.browser.exceptions import TabManagementError

logger = logging.getLogger(__name__)


class TabManager:
    """Manages multiple browser tabs (pages) within a Playwright BrowserContext."""

    def __init__(self, context: BrowserContext) -> None:
        """Initialize the TabManager with an active BrowserContext.

        Args:
            context: The Playwright BrowserContext owning the pages.
        """
        self._context: BrowserContext = context
        self._tabs: Dict[str, Page] = {}
        self._active_tab_id: Optional[str] = None

    @property
    def active_tab_id(self) -> Optional[str]:
        """Return the ID of the currently active tab."""
        return self._active_tab_id

    def tab_count(self) -> int:
        """Return the number of open tabs currently tracked.

        Returns:
            Count of open tabs.
        """
        return len(self._tabs)

    def list_tabs(self) -> List[str]:
        """Return a list of all currently open tab identifiers.

        Returns:
            List of tab ID strings.
        """
        return list(self._tabs.keys())

    def get_active_page(self) -> Page:
        """Get the active Playwright Page instance.

        Returns:
            The currently active Page.

        Raises:
            TabManagementError: If no tabs are currently open or active.
        """
        if not self._active_tab_id or self._active_tab_id not in self._tabs:
            raise TabManagementError(
                tab_id="none",
                message="No active tab is currently available.",
            )
        return self._tabs[self._active_tab_id]

    def get_tab(self, tab_id: str) -> Page:
        """Retrieve a specific Page instance by its tab ID.

        Args:
            tab_id: The identifier of the desired tab.

        Returns:
            The matching Playwright Page.

        Raises:
            TabManagementError: If the specified tab_id does not exist.
        """
        if tab_id not in self._tabs:
            raise TabManagementError(
                tab_id=tab_id,
                message=f"Tab '{tab_id}' does not exist in open tabs: {list(self._tabs.keys())}",
            )
        return self._tabs[tab_id]

    async def open_tab(self, url: Optional[str] = None) -> Tuple[str, Page]:
        """Open a new browser tab and set it as the active tab.

        Args:
            url: Optional URL to immediately navigate the new tab to.

        Returns:
            A tuple of (tab_id, page).
        """
        tab_id = f"tab_{uuid.uuid4().hex[:6]}"
        logger.info("Opening new browser tab: %s", tab_id)

        page = await self._context.new_page()
        self._tabs[tab_id] = page
        self._active_tab_id = tab_id

        if url:
            logger.debug("Navigating new tab %s to '%s'", tab_id, url)
            await page.goto(url, wait_until="domcontentloaded")

        return tab_id, page

    def register_page(self, page: Page, tab_id: Optional[str] = None) -> str:
        """Register an existing Page instance into the TabManager.

        Args:
            page: The Playwright Page to register.
            tab_id: Optional identifier; generated if not provided.

        Returns:
            The assigned tab identifier.
        """
        assigned_id = tab_id or f"tab_{uuid.uuid4().hex[:6]}"
        self._tabs[assigned_id] = page
        self._active_tab_id = assigned_id
        logger.debug("Registered external page as tab %s", assigned_id)
        return assigned_id

    async def switch_tab(self, tab_id: str) -> Page:
        """Switch focus to the specified tab and bring it to the front.

        Args:
            tab_id: The identifier of the tab to focus.

        Returns:
            The focused Playwright Page.

        Raises:
            TabManagementError: If the tab_id does not exist.
        """
        page = self.get_tab(tab_id)
        logger.info("Switching active tab to: %s", tab_id)
        await page.bring_to_front()
        self._active_tab_id = tab_id
        return page

    async def close_tab(self, tab_id: str) -> None:
        """Close a specific tab and update the active tab pointer.

        Args:
            tab_id: The identifier of the tab to close.

        Raises:
            TabManagementError: If the tab_id is not open.
        """
        page = self.get_tab(tab_id)
        logger.info("Closing tab: %s", tab_id)
        try:
            await page.close()
        except Exception as e:
            logger.warning("Error closing page for tab %s: %s", tab_id, str(e))
        finally:
            del self._tabs[tab_id]

            if self._active_tab_id == tab_id:
                if self._tabs:
                    self._active_tab_id = next(iter(self._tabs))
                    logger.debug("Switched active tab to remaining tab: %s", self._active_tab_id)
                else:
                    self._active_tab_id = None
                    logger.debug("All tabs closed; active tab is now None.")

    async def close_all(self) -> None:
        """Close all open tabs managed by this instance."""
        logger.info("Closing all %d open tabs.", len(self._tabs))
        for tab_id in list(self._tabs.keys()):
            await self.close_tab(tab_id)
        self._tabs.clear()
        self._active_tab_id = None
