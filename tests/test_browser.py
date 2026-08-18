"""Unit and integration tests for the browser module (Member B scope).

Tests cover configuration validation, custom exceptions, multi-tab management,
atomic action executors (navigate, click, input, scroll, wait), error recovery,
screenshot capturing, and BrowserResult schema conformance.
"""

from pathlib import Path

import pytest
from playwright.async_api import async_playwright

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
from backend.browser.interceptor import BLOCKED_URL_PATTERNS, OVERLAY_SUPPRESSION_CSS
from backend.browser.tab_manager import TabManager
from shared.schemas import BrowserAction, BrowserResult, PlanStep


def test_browser_config_defaults() -> None:
    """Test default values of BrowserConfig model."""
    config = BrowserConfig()
    assert config.headless is True
    assert config.viewport_width == 1280
    assert config.viewport_height == 800
    assert config.timeout_ms == 30000
    assert config.screenshot_dir == "artifacts/screenshots"
    assert config.block_ads is True
    assert config.get_viewport() == {"width": 1280, "height": 800}


def test_browser_config_custom() -> None:
    """Test custom configuration options in BrowserConfig."""
    config = BrowserConfig(
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
        timeout_ms=15000,
        screenshot_dir="custom_artifacts/shots",
        block_ads=False,
    )
    assert config.headless is False
    assert config.viewport_width == 1920
    assert config.viewport_height == 1080
    assert config.timeout_ms == 15000
    assert config.screenshot_dir == "custom_artifacts/shots"
    assert config.block_ads is False
    assert config.get_viewport() == {"width": 1920, "height": 1080}


def test_custom_exceptions() -> None:
    """Test domain exceptions and message formatting."""
    base_err = BrowserError("Base error", details="some detail")
    assert "Base error" in str(base_err)
    assert "some detail" in str(base_err)

    action_err = BrowserActionError(action="click", message="Failed to click")
    assert action_err.action == "click"
    assert "Failed to click" in str(action_err)

    sel_err = SelectorNotFoundError(action="click", selector="#missing-btn")
    assert sel_err.selector == "#missing-btn"
    assert "Target selector '#missing-btn' was not found" in str(sel_err)

    nav_err = NavigationTimeoutError(url="https://slow.example.com", timeout_ms=5000)
    assert nav_err.url == "https://slow.example.com"
    assert nav_err.timeout_ms == 5000
    assert "5000ms" in str(nav_err)

    tab_err = TabManagementError(tab_id="tab_999", message="Tab not found")
    assert tab_err.tab_id == "tab_999"
    assert "Tab 'tab_999' error" in str(tab_err)


def test_interceptor_constants() -> None:
    """Test that ad-blocking and CSS overlay constants are properly populated."""
    assert len(BLOCKED_URL_PATTERNS) > 0
    assert "doubleclick.net" in BLOCKED_URL_PATTERNS
    assert "display: none !important" in OVERLAY_SUPPRESSION_CSS


@pytest.mark.asyncio
async def test_tab_manager_lifecycle(tmp_path: Path) -> None:
    """Test TabManager tab creation, switching, listing, and closing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        tab_mgr = TabManager(context)

        assert tab_mgr.tab_count() == 0
        assert tab_mgr.active_tab_id is None

        # Open first tab
        tab1_id, page1 = await tab_mgr.open_tab()
        assert tab_mgr.tab_count() == 1
        assert tab_mgr.active_tab_id == tab1_id
        assert tab_mgr.get_active_page() == page1
        assert tab_mgr.list_tabs() == [tab1_id]

        # Open second tab
        tab2_id, page2 = await tab_mgr.open_tab()
        assert tab_mgr.tab_count() == 2
        assert tab_mgr.active_tab_id == tab2_id
        assert tab_mgr.get_active_page() == page2

        # Switch back to first tab
        switched_page = await tab_mgr.switch_tab(tab1_id)
        assert tab_mgr.active_tab_id == tab1_id
        assert switched_page == page1

        # Switch to invalid tab raises error
        with pytest.raises(TabManagementError):
            await tab_mgr.switch_tab("non_existent_tab")

        # Close first tab
        await tab_mgr.close_tab(tab1_id)
        assert tab_mgr.tab_count() == 1
        assert tab_mgr.active_tab_id == tab2_id

        # Close all tabs
        await tab_mgr.close_all()
        assert tab_mgr.tab_count() == 0
        assert tab_mgr.active_tab_id is None

        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_actions_on_local_html(tmp_path: Path) -> None:
    """Test execute_navigate, click, input, scroll, and wait actions on local HTML."""
    html_file = tmp_path / "test_page.html"
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Heading for Browser Test</h1>
        <input type="text" id="username" placeholder="Enter username" />
        <button id="submit-btn" onclick="document.getElementById('result').innerText='Clicked!'">
            Submit
        </button>
        <div id="result">Initial</div>
        <div style="height: 2000px;">Tall spacer for scroll</div>
        <div id="footer">Footer Content</div>
    </body>
    </html>
    """
    html_file.write_text(html_content, encoding="utf-8")
    file_url = html_file.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Test Navigation
        final_url = await execute_navigate(page, file_url, timeout_ms=10000)
        assert "test_page.html" in final_url
        assert await page.title() == "Test Page"

        # 2. Test Input
        await execute_input(page, selector="#username", input_value="TestAgentUser")
        input_val = await page.input_value("#username")
        assert input_val == "TestAgentUser"

        # 3. Test Click
        await execute_click(page, selector="#submit-btn")
        result_text = await page.inner_text("#result")
        assert result_text == "Clicked!"

        # 4. Test Scroll
        await execute_scroll(page, direction="down", amount=500)
        await execute_scroll(page, direction="bottom")
        await execute_scroll(page, direction="top")

        # 5. Test Wait
        await execute_wait(page, selector="#footer", timeout_ms=5000)
        await execute_wait(page, timeout_ms=100)

        # 6. Test Selector Not Found Error
        with pytest.raises(SelectorNotFoundError):
            await execute_click(page, selector="#non-existent-button", timeout_ms=500)

        with pytest.raises(SelectorNotFoundError):
            await execute_input(
                page, selector="#non-existent-input", input_value="test", timeout_ms=500
            )

        # 7. Test Empty navigation URL error
        with pytest.raises(BrowserActionError):
            await execute_navigate(page, url="", timeout_ms=500)

        # 8. Test Empty selector click error
        with pytest.raises(BrowserActionError):
            await execute_click(page, selector="", timeout_ms=500)

        # 9. Test Empty selector input error
        with pytest.raises(BrowserActionError):
            await execute_input(page, selector="", input_value="test", timeout_ms=500)

        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_browser_engine_lifecycle_and_step_execution(tmp_path: Path) -> None:
    """Test BrowserEngine end-to-end step execution and schema output."""
    html_file = tmp_path / "engine_test.html"
    btn_onclick = "document.body.innerHTML += '<p id=done>Search Complete</p>'"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Engine Test</title></head>
    <body>
        <h1>Browser Specialist Engine</h1>
        <input id="search-box" type="text" />
        <button id="search-btn" onclick="{btn_onclick}">
            Search
        </button>
    </body>
    </html>
    """
    html_file.write_text(html_content, encoding="utf-8")
    file_url = html_file.as_uri()

    screenshot_dir = tmp_path / "screenshots"
    config = BrowserConfig(
        headless=True,
        timeout_ms=10000,
        screenshot_dir=str(screenshot_dir),
    )

    async with BrowserEngine(config=config) as engine:
        assert engine.is_running is True
        assert engine.tab_manager.tab_count() == 1

        # Step 1: Navigate
        step1 = PlanStep(
            step_id=1,
            action=BrowserAction.NAVIGATE,
            url=file_url,
            description="Navigate to engine test page",
        )
        res1 = await engine.execute_step(step1, goal_id="goal_test1")
        assert isinstance(res1, BrowserResult)
        assert res1.step_id == 1
        assert res1.status == "success"
        assert "engine_test.html" in res1.final_url
        assert "Browser Specialist Engine" in res1.raw_html
        assert res1.screenshot_path is not None
        assert res1.error_message is None

        # Step 2: Input
        step2 = PlanStep(
            step_id=2,
            action=BrowserAction.INPUT,
            selector="#search-box",
            input_value="Playwright Specialist",
            description="Type query into search input",
        )
        res2 = await engine.execute_step(step2, goal_id="goal_test1")
        assert res2.step_id == 2
        assert res2.status == "success"

        # Step 3: Click
        step3 = PlanStep(
            step_id=3,
            action=BrowserAction.CLICK,
            selector="#search-btn",
            description="Click search button",
        )
        res3 = await engine.execute_step(step3, goal_id="goal_test1")
        assert res3.step_id == 3
        assert res3.status == "success"
        assert "Search Complete" in res3.raw_html

        # Step 4: Scroll
        step4 = PlanStep(
            step_id=4,
            action=BrowserAction.SCROLL,
            description="Scroll the viewport",
        )
        res4 = await engine.execute_step(step4, goal_id="goal_test1")
        assert res4.step_id == 4
        assert res4.status == "success"

        # Step 5: Wait
        step5 = PlanStep(
            step_id=5,
            action=BrowserAction.WAIT,
            selector="#done",
            description="Wait for search completed element",
        )
        res5 = await engine.execute_step(step5, goal_id="goal_test1")
        assert res5.step_id == 5
        assert res5.status == "success"

        # Step 6: Failure handling (missing selector)
        step_fail = PlanStep(
            step_id=6,
            action=BrowserAction.CLICK,
            selector="#missing-element-xyz",
            description="Click non-existent element",
        )
        res_fail = await engine.execute_step(step_fail, goal_id="goal_test1")
        assert res_fail.step_id == 6
        assert res_fail.status == "failed"
        assert res_fail.error_message is not None


@pytest.mark.asyncio
async def test_browser_engine_execute_steps_sequence(tmp_path: Path) -> None:
    """Test sequential execution via execute_steps method."""
    html_file = tmp_path / "sequence_test.html"
    html_file.write_text("<html><body><h1>Step Sequence Test</h1></body></html>", encoding="utf-8")
    file_url = html_file.as_uri()

    config = BrowserConfig(
        headless=True,
        timeout_ms=10000,
        screenshot_dir=str(tmp_path / "seq_shots"),
    )

    steps = [
        PlanStep(
            step_id=1,
            action=BrowserAction.NAVIGATE,
            url=file_url,
            description="Nav to seq test",
        ),
        PlanStep(
            step_id=2,
            action=BrowserAction.WAIT,
            description="Wait brief interval",
        ),
    ]

    async with BrowserEngine(config=config) as engine:
        results = await engine.execute_steps(steps, goal_id="goal_seq")
        assert len(results) == 2
        assert all(r.status == "success" for r in results)
        assert results[0].step_id == 1
        assert results[1].step_id == 2


def test_engine_not_started_tab_manager() -> None:
    """Test that accessing tab_manager before starting raises BrowserError."""
    engine = BrowserEngine()
    with pytest.raises(BrowserError):
        _ = engine.tab_manager
