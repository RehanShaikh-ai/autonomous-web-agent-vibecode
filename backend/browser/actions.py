"""Atomic browser action executors using Playwright.

This module provides dedicated async execution routines for navigation, clicking,
text input, scrolling, and waiting within active browser pages.
"""

import logging
from typing import Optional

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from backend.browser.exceptions import (
    BrowserActionError,
    NavigationTimeoutError,
    SelectorNotFoundError,
)
from backend.browser.interceptor import inject_ad_block_css

logger = logging.getLogger(__name__)


async def execute_navigate(
    page: Page,
    url: str,
    timeout_ms: int = 30000,
    block_ads: bool = True,
) -> str:
    """Navigate page to the specified URL and return final loaded URL.

    Args:
        page: The Playwright Page instance.
        url: The web address to load.
        timeout_ms: Maximum navigation timeout in milliseconds.
        block_ads: Whether to inject ad-block and overlay suppression CSS.

    Returns:
        The final URL of the page after any HTTP or JS redirects.

    Raises:
        NavigationTimeoutError: If page loading exceeds timeout_ms.
        BrowserActionError: If navigation fails due to DNS or network errors.
    """
    if not url:
        raise BrowserActionError(
            action="navigate",
            message="Target URL cannot be empty.",
        )

    # Ensure URL protocol scheme is present
    target_url = url if url.startswith(("http://", "https://", "file://")) else f"https://{url}"
    logger.info("Navigating to '%s' (timeout: %dms)", target_url, timeout_ms)

    try:
        try:
            await page.goto(target_url, timeout=timeout_ms, wait_until="load")
        except PlaywrightTimeoutError:
            # Fallback check: if load timed out, attempt domcontentloaded wait
            logger.warning(
                "Full load event timed out for %s; falling back to domcontentloaded check.",
                target_url,
            )
            await page.wait_for_load_state("domcontentloaded", timeout=5000)

        if block_ads:
            await inject_ad_block_css(page)

        final_url = page.url
        logger.info("Navigation complete. Final URL: %s", final_url)
        return final_url

    except PlaywrightTimeoutError as e:
        logger.error("Navigation timed out for %s: %s", target_url, str(e))
        raise NavigationTimeoutError(url=target_url, timeout_ms=timeout_ms, details=str(e)) from e
    except PlaywrightError as e:
        logger.error("Navigation error on %s: %s", target_url, str(e))
        raise BrowserActionError(
            action="navigate",
            message=f"Failed to navigate to '{target_url}'",
            details=str(e),
        ) from e


async def execute_click(
    page: Page,
    selector: str,
    timeout_ms: int = 30000,
) -> None:
    """Locate an element by selector and click it.

    Args:
        page: The Playwright Page instance.
        selector: CSS or XPath selector of the target element.
        timeout_ms: Maximum wait timeout in milliseconds.

    Raises:
        SelectorNotFoundError: If the selector cannot be found in DOM.
        BrowserActionError: If clicking the element fails.
    """
    if not selector:
        raise BrowserActionError(
            action="click",
            message="Target selector must be specified for click action.",
        )

    logger.info("Executing click on selector '%s' (timeout: %dms)", selector, timeout_ms)

    try:
        # Wait for element to become visible and attached
        locator = page.locator(selector).first
        await locator.wait_for(state="visible", timeout=timeout_ms)
        await locator.scroll_into_view_if_needed(timeout=timeout_ms)
        await locator.click(timeout=timeout_ms)

        # Allow brief interval for asynchronous event handlers to process
        await page.wait_for_timeout(300)
        logger.debug("Successfully clicked selector '%s'", selector)

    except PlaywrightTimeoutError as e:
        logger.warning("Click target selector '%s' timed out: %s", selector, str(e))
        raise SelectorNotFoundError(action="click", selector=selector, details=str(e)) from e
    except PlaywrightError as e:
        logger.error("Failed to click selector '%s': %s", selector, str(e))
        raise BrowserActionError(
            action="click",
            message=f"Click failed on selector '{selector}'",
            details=str(e),
        ) from e


async def execute_input(
    page: Page,
    selector: str,
    input_value: str,
    timeout_ms: int = 30000,
) -> None:
    """Locate an input field, clear existing text, and fill with input_value.

    Args:
        page: The Playwright Page instance.
        selector: CSS or XPath selector of the input field.
        input_value: Text content to insert.
        timeout_ms: Maximum wait timeout in milliseconds.

    Raises:
        SelectorNotFoundError: If the input element cannot be located.
        BrowserActionError: If filling the input field fails.
    """
    if not selector:
        raise BrowserActionError(
            action="input",
            message="Target selector must be specified for input action.",
        )

    val = input_value or ""
    logger.info("Filling input '%s' with value '%s'", selector, val)

    try:
        locator = page.locator(selector).first
        await locator.wait_for(state="visible", timeout=timeout_ms)
        await locator.scroll_into_view_if_needed(timeout=timeout_ms)
        await locator.fill(val, timeout=timeout_ms)
        logger.debug("Successfully filled input '%s'", selector)

    except PlaywrightTimeoutError as e:
        logger.warning("Input target selector '%s' timed out: %s", selector, str(e))
        raise SelectorNotFoundError(action="input", selector=selector, details=str(e)) from e
    except PlaywrightError as e:
        logger.error("Failed to fill input '%s': %s", selector, str(e))
        raise BrowserActionError(
            action="input",
            message=f"Input action failed on selector '{selector}'",
            details=str(e),
        ) from e


async def execute_scroll(
    page: Page,
    direction: str = "down",
    amount: Optional[int] = None,
    selector: Optional[str] = None,
    timeout_ms: int = 30000,
) -> None:
    """Scroll the page or a target container element.

    Args:
        page: The Playwright Page instance.
        direction: Scroll direction ('down', 'up', 'top', 'bottom').
        amount: Optional explicit pixel delta. If None, defaults to viewport fraction.
        selector: Optional container selector to scroll instead of main window.
        timeout_ms: Maximum wait timeout in milliseconds.

    Raises:
        BrowserActionError: If scrolling operation fails.
    """
    logger.info("Scrolling %s (amount: %s, selector: %s)", direction, str(amount), str(selector))

    try:
        if selector:
            locator = page.locator(selector).first
            await locator.wait_for(state="visible", timeout=timeout_ms)
            scroll_delta = amount if amount is not None else 500
            if direction in ("up", "top"):
                scroll_delta = -abs(scroll_delta)
            await locator.evaluate(
                "(element, delta) => element.scrollBy({top: delta, behavior: 'smooth'})",
                scroll_delta,
            )
        else:
            if direction == "top":
                await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
            elif direction == "bottom":
                await page.evaluate(
                    "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})"
                )
            else:
                scroll_delta = amount if amount is not None else 600
                if direction == "up":
                    scroll_delta = -abs(scroll_delta)
                await page.evaluate(
                    "(delta) => window.scrollBy({top: delta, behavior: 'smooth'})",
                    scroll_delta,
                )

        # Allow lazy loaded content to render post-scroll
        await page.wait_for_timeout(400)
        logger.debug("Scroll execution finished.")

    except PlaywrightError as e:
        logger.error("Scroll action failed: %s", str(e))
        raise BrowserActionError(
            action="scroll",
            message="Scroll action execution failed",
            details=str(e),
        ) from e


async def execute_wait(
    page: Page,
    selector: Optional[str] = None,
    timeout_ms: int = 1000,
) -> None:
    """Pause execution or wait for a specific DOM selector to appear.

    Args:
        page: The Playwright Page instance.
        selector: Optional selector to wait for visibility.
        timeout_ms: Wait duration or timeout in milliseconds.

    Raises:
        SelectorNotFoundError: If waiting for selector exceeds timeout_ms.
        BrowserActionError: If wait operation encounters an error.
    """
    if selector:
        logger.info("Waiting for selector '%s' (timeout: %dms)", selector, timeout_ms)
        try:
            locator = page.locator(selector).first
            await locator.wait_for(state="visible", timeout=timeout_ms)
        except PlaywrightTimeoutError as e:
            logger.warning("Wait for selector '%s' timed out: %s", selector, str(e))
            raise SelectorNotFoundError(action="wait", selector=selector, details=str(e)) from e
        except PlaywrightError as e:
            raise BrowserActionError(
                action="wait",
                message=f"Wait failed on selector '{selector}'",
                details=str(e),
            ) from e
    else:
        logger.debug("Executing time delay wait: %dms", timeout_ms)
        await page.wait_for_timeout(timeout_ms)
