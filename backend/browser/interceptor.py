"""Ad-blocking, tracker filtering, and overlay suppression interceptors.

This module provides route filtering rules to abort intrusive ad and analytics requests,
as well as stylesheet injections to hide annoying cookie consent banners and overlays.
"""

import logging
from typing import List

from playwright.async_api import BrowserContext, Page, Route

logger = logging.getLogger(__name__)

# List of domain pattern substrings associated with advertising and tracking networks
BLOCKED_URL_PATTERNS: List[str] = [
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googlesyndication.com",
    "adnxs.com",
    "criteo.com",
    "scorecardresearch.com",
    "quantserve.com",
    "outbrain.com",
    "taboola.com",
    "amazon-adsystem.com",
    "hotjar.com",
    "clarity.ms",
    "adservice.google.",
]

# CSS rules to hide cookie banners, consent dialogs, and intrusive overlays
OVERLAY_SUPPRESSION_CSS: str = """
#onetrust-consent-sdk,
#onetrust-banner-sdk,
.cookie-banner,
.cookie-consent,
.cookie-notice,
[id*="cookie-consent"],
[class*="cookie-banner"],
[class*="consent-modal"],
.qc-cmp-ui-container,
#CybotCookiebotDialog,
#cmpbox,
.evidon-banner,
[id*="sp_message_container"],
.truste_box_overlay,
.truste_overlay {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}
"""


async def _handle_route(route: Route) -> None:
    """Intercept and filter network requests matching tracker patterns.

    Args:
        route: The Playwright Route object representing the intercepted request.
    """
    request_url = route.request.url.lower()
    for pattern in BLOCKED_URL_PATTERNS:
        if pattern in request_url:
            logger.debug("Blocking ad/tracker network request: %s", request_url)
            await route.abort()
            return
    await route.continue_()


async def setup_route_interception(context: BrowserContext) -> None:
    """Attach ad-blocking and tracker filtering route handlers to a BrowserContext.

    Args:
        context: The Playwright BrowserContext to protect.
    """
    logger.debug("Attaching ad-blocking network route filters to browser context.")
    await context.route("**/*", _handle_route)


async def inject_ad_block_css(page: Page) -> None:
    """Inject overlay suppression stylesheet into a page.

    Args:
        page: The Playwright Page instance.
    """
    try:
        await page.add_style_tag(content=OVERLAY_SUPPRESSION_CSS)
        logger.debug("Successfully injected overlay suppression CSS into page: %s", page.url)
    except Exception as e:
        logger.warning("Failed to inject overlay suppression CSS on %s: %s", page.url, str(e))
