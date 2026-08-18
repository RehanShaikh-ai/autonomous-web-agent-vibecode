"""High-level BrowserEngine orchestrating Playwright automation and step execution.

This module is the core engine owned by Member B (Browser Specialist). It coordinates
browser lifecycle, tab management, atomic action dispatch, screenshot capture, and
returns structured BrowserResult payloads conforming to shared/schemas.py.
"""

import logging
from pathlib import Path
from types import TracebackType
from typing import List, Optional, Type

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from backend.browser.actions import (
    execute_click,
    execute_input,
    execute_navigate,
    execute_scroll,
    execute_wait,
)
from backend.browser.config import BrowserConfig
from backend.browser.exceptions import (
    BrowserActionError,
    BrowserError,
    NavigationTimeoutError,
    TabManagementError,
)
from backend.browser.interceptor import setup_route_interception
from backend.browser.tab_manager import TabManager
from shared.schemas import BrowserAction, BrowserResult, PlanStep

logger = logging.getLogger(__name__)


class BrowserEngine:
    """Core browser automation engine for executing structured PlanSteps via Playwright."""

    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        """Initialize the BrowserEngine with configuration.

        Args:
            config: Optional BrowserConfig instance; defaults will be used if omitted.
        """
        self.config: BrowserConfig = config or BrowserConfig()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._tab_manager: Optional[TabManager] = None
        self._is_started: bool = False

    @property
    def tab_manager(self) -> TabManager:
        """Return the active TabManager instance.

        Returns:
            The TabManager managing browser pages.

        Raises:
            BrowserError: If the browser engine is not started.
        """
        if not self._tab_manager:
            raise BrowserError("BrowserEngine has not been started. Call start() first.")
        return self._tab_manager

    @property
    def is_running(self) -> bool:
        """Check if the browser engine is actively running.

        Returns:
            True if started and browser is active, False otherwise.
        """
        return self._is_started and self._browser is not None

    async def start(self) -> None:
        """Start the Playwright driver, launch browser instance, and open initial tab."""
        if self._is_started:
            logger.warning("BrowserEngine is already running.")
            return

        logger.info("Starting BrowserEngine (headless=%s)", self.config.headless)

        self._playwright = await async_playwright().start()

        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]

        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
            args=launch_args,
        )

        self._context = await self._browser.new_context(
            viewport=self.config.get_viewport(),
            user_agent=self.config.user_agent,
            locale=self.config.locale,
            timezone_id=self.config.timezone_id,
            ignore_https_errors=self.config.ignore_https_errors,
            bypass_csp=self.config.bypass_csp,
        )

        if self.config.block_ads:
            await setup_route_interception(self._context)

        self._tab_manager = TabManager(self._context)
        # Open default initial tab
        await self._tab_manager.open_tab()

        self._is_started = True
        logger.info("BrowserEngine initialized successfully with 1 active tab.")

    async def close(self) -> None:
        """Gracefully close all tabs, browser context, and stop Playwright."""
        if not self._is_started:
            return

        logger.info("Shutting down BrowserEngine...")

        if self._tab_manager:
            try:
                await self._tab_manager.close_all()
            except Exception as e:
                logger.warning("Error closing tabs: %s", str(e))
            self._tab_manager = None

        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                logger.warning("Error closing browser context: %s", str(e))
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning("Error closing browser: %s", str(e))
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning("Error stopping Playwright: %s", str(e))
            self._playwright = None

        self._is_started = False
        logger.info("BrowserEngine shutdown complete.")

    async def __aenter__(self) -> "BrowserEngine":
        """Async context manager entry.

        Returns:
            The started BrowserEngine instance.
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if raised in context.
            exc_val: Exception value if raised in context.
            exc_tb: Exception traceback if raised in context.
        """
        await self.close()

    async def _capture_screenshot(self, page: Page, goal_id: str, step_id: int) -> Optional[str]:
        """Capture and save viewport screenshot, returning relative path.

        Args:
            page: Active Playwright Page.
            goal_id: Identifier for current goal transaction.
            step_id: Index of the active plan step.

        Returns:
            Relative file path string of saved screenshot, or None on failure.
        """
        try:
            target_dir = Path(self.config.screenshot_dir)
            target_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{goal_id}_step{step_id}.png"
            full_path = target_dir / filename

            await page.screenshot(path=str(full_path), full_page=False)

            # Return forward-slash relative path
            rel_path = f"/{self.config.screenshot_dir.strip('/')}/{filename}"
            logger.debug("Screenshot saved: %s", rel_path)
            return rel_path
        except Exception as e:
            logger.warning("Screenshot capture failed for step %d: %s", step_id, str(e))
            return None

    async def _dispatch_action(self, page: Page, step: PlanStep) -> None:
        """Dispatch PlanStep to appropriate atomic action executor.

        Args:
            page: Active Playwright Page.
            step: PlanStep to execute.

        Raises:
            BrowserActionError: If required step parameters are missing or action is unsupported.
        """
        if step.action == BrowserAction.NAVIGATE:
            if not step.url:
                raise BrowserActionError(
                    action="navigate",
                    message="PlanStep with action 'navigate' requires a non-empty 'url'.",
                )
            await execute_navigate(
                page=page,
                url=step.url,
                timeout_ms=self.config.timeout_ms,
                block_ads=self.config.block_ads,
            )
        elif step.action == BrowserAction.CLICK:
            if not step.selector:
                raise BrowserActionError(
                    action="click",
                    message="PlanStep with action 'click' requires a valid 'selector'.",
                )
            await execute_click(
                page=page, selector=step.selector, timeout_ms=self.config.timeout_ms
            )
        elif step.action == BrowserAction.INPUT:
            if not step.selector:
                raise BrowserActionError(
                    action="input",
                    message="PlanStep with action 'input' requires a valid 'selector'.",
                )
            await execute_input(
                page=page,
                selector=step.selector,
                input_value=step.input_value or "",
                timeout_ms=self.config.timeout_ms,
            )
        elif step.action == BrowserAction.SCROLL:
            await execute_scroll(
                page=page,
                direction="down",
                selector=step.selector,
                timeout_ms=self.config.timeout_ms,
            )
        elif step.action == BrowserAction.WAIT:
            wait_timeout = self.config.timeout_ms if step.selector else 1000
            await execute_wait(page=page, selector=step.selector, timeout_ms=wait_timeout)
        else:
            raise BrowserActionError(
                action=str(step.action),
                message=f"Unsupported browser action: {step.action}",
            )

    async def execute_step(self, step: PlanStep, goal_id: Optional[str] = None) -> BrowserResult:
        """Execute a single PlanStep and produce a structured BrowserResult.

        Args:
            step: The atomic PlanStep to execute.
            goal_id: Optional tracking transaction ID.

        Returns:
            BrowserResult populated with raw HTML, status, final URL, and screenshot.
        """
        if not self._is_started:
            await self.start()

        gid = goal_id or "session"
        logger.info("Executing step %d [%s]: %s", step.step_id, step.action.value, step.description)

        try:
            page = self.tab_manager.get_active_page()
        except TabManagementError as e:
            logger.error("Failed to retrieve active page: %s", str(e))
            return BrowserResult(
                step_id=step.step_id,
                status="failed",
                final_url="",
                raw_html="",
                screenshot_path=None,
                error_message=str(e),
            )

        try:
            await self._dispatch_action(page, step)

            # Capture outputs post execution
            final_url = page.url or (step.url or "")
            raw_html = await page.content()
            screenshot_path = await self._capture_screenshot(page, gid, step.step_id)

            logger.info("Step %d executed successfully on %s", step.step_id, final_url)
            return BrowserResult(
                step_id=step.step_id,
                status="success",
                final_url=final_url,
                raw_html=raw_html,
                screenshot_path=screenshot_path,
                error_message=None,
            )

        except (NavigationTimeoutError, PlaywrightTimeoutError) as e:
            logger.warning("Step %d timed out: %s", step.step_id, str(e))
            return await self._handle_error_result(page, step, gid, "timeout", str(e))

        except (BrowserError, Exception) as e:
            logger.error("Step %d execution failed: %s", step.step_id, str(e), exc_info=True)
            return await self._handle_error_result(page, step, gid, "failed", str(e))

    async def _handle_error_result(
        self,
        page: Page,
        step: PlanStep,
        goal_id: str,
        status: str,
        error_message: str,
    ) -> BrowserResult:
        """Construct a failure or timeout BrowserResult.

        Args:
            page: Active Playwright Page.
            step: The failed PlanStep.
            goal_id: Tracking transaction ID.
            status: Status string ('failed' or 'timeout').
            error_message: Description of the error.

        Returns:
            Populated BrowserResult.
        """
        current_url = getattr(page, "url", "") or (step.url or "")
        raw_html = ""
        try:
            raw_html = await page.content()
        except Exception:
            pass
        screenshot_path = await self._capture_screenshot(page, goal_id, step.step_id)

        return BrowserResult(
            step_id=step.step_id,
            status=status,
            final_url=current_url,
            raw_html=raw_html,
            screenshot_path=screenshot_path,
            error_message=error_message,
        )

    async def execute_steps(
        self, steps: List[PlanStep], goal_id: Optional[str] = None
    ) -> List[BrowserResult]:
        """Execute a sequence of PlanSteps in order.

        Args:
            steps: List of PlanStep objects to execute sequentially.
            goal_id: Optional tracking transaction ID.

        Returns:
            List of BrowserResult objects corresponding to each step.
        """
        results: List[BrowserResult] = []
        for step in steps:
            result = await self.execute_step(step, goal_id=goal_id)
            results.append(result)
            if result.status != "success":
                logger.warning(
                    "Step %d returned status '%s'; halting sequential execution.",
                    step.step_id,
                    result.status,
                )
                break
        return results
