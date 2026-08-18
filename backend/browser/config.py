"""Configuration settings and options for the Playwright browser module.

This module provides Pydantic models for setting browser launching flags,
viewport dimensions, timeouts, and ad-blocking behaviors.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class BrowserConfig(BaseModel):
    """Configuration model for controlling Playwright browser instances."""

    headless: bool = Field(
        default=True,
        description="Whether to run browser in headless mode without a visible GUI window.",
    )
    viewport_width: int = Field(
        default=1280,
        description="Default viewport width in pixels.",
    )
    viewport_height: int = Field(
        default=800,
        description="Default viewport height in pixels.",
    )
    timeout_ms: int = Field(
        default=30000,
        description="Default timeout in milliseconds for operations and page loading.",
    )
    screenshot_dir: str = Field(
        default="artifacts/screenshots",
        description="Relative directory path where screenshots are saved.",
    )
    user_agent: Optional[str] = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        description="Custom User-Agent string to avoid automated bot blocking.",
    )
    block_ads: bool = Field(
        default=True,
        description="Whether to block third-party ad networks and intrusive overlays.",
    )
    bypass_csp: bool = Field(
        default=True,
        description="Whether to bypass Content Security Policy to allow script/style injection.",
    )
    ignore_https_errors: bool = Field(
        default=True,
        description="Whether to ignore SSL/TLS certificate validation errors.",
    )
    locale: str = Field(
        default="en-US",
        description="Locale setting for browser emulation.",
    )
    timezone_id: str = Field(
        default="America/New_York",
        description="Timezone identifier for browser context.",
    )

    def get_viewport(self) -> Dict[str, int]:
        """Return viewport dimensions as a dictionary compatible with Playwright.

        Returns:
            Dictionary containing 'width' and 'height' keys.
        """
        return {"width": self.viewport_width, "height": self.viewport_height}
