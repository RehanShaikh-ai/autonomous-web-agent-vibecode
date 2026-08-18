"""HTML DOM cleaning and sanitization module."""

import logging
import re
from typing import ClassVar

from backend.processing.ad_blocker import AdBlocker
from backend.processing.exceptions import DOMCleaningError


logger = logging.getLogger(__name__)


class DOMCleaner:
    """Sanitizes raw HTML DOM trees by removing scripts, styles, metadata, and boilerplate."""

    # Tags to strip entirely including their inner contents
    STRIP_WITH_CONTENT_TAGS: ClassVar[list[str]] = [
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "frame",
        "frameset",
        "object",
        "embed",
        "applet",
        "template",
        "audio",
        "video",
        "source",
        "track",
        "map",
        "link",
        "meta",
        "head",
        "header",
        "footer",
        "nav",
        "aside",
        "form",
        "dialog",
    ]

    # Regex for stripping HTML comments
    COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)

    # Regex for removing inline event handlers and excessive attributes
    EVENT_HANDLER_PATTERN = re.compile(
        r"\s+on[a-zA-Z]+\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)", re.IGNORECASE
    )
    STYLE_ATTR_PATTERN = re.compile(r"\s+style\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)", re.IGNORECASE)
    DATA_ATTR_PATTERN = re.compile(
        r"\s+data-[a-zA-Z0-9_-]+\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)", re.IGNORECASE
    )

    def __init__(self, ad_blocker: AdBlocker | None = None) -> None:
        """Initializes the DOMCleaner.

        Args:
            ad_blocker: Optional AdBlocker instance to preprocess ads.
        """
        self.ad_blocker = ad_blocker or AdBlocker()
        logger.debug("DOMCleaner initialized.")

    def clean_html(self, raw_html: str, strip_navigation: bool = True) -> str:
        """Sanitizes raw HTML string into clean, readable DOM structure.

        Args:
            raw_html: The raw HTML content from browser execution.
            strip_navigation: Whether to strip header, footer, and nav elements.

        Returns:
            Sanitized HTML text suitable for Markdown conversion and entity extraction.

        Raises:
            DOMCleaningError: If an unexpected error occurs during DOM sanitation.
        """
        if not raw_html or not raw_html.strip():
            logger.debug("Received empty HTML content to clean.")
            return ""

        try:
            # 1. Strip advertisements and tracking elements
            cleaned = self.ad_blocker.strip_ad_tags(raw_html)

            # 2. Strip HTML comments
            cleaned = self.COMMENT_PATTERN.sub("", cleaned)

            # 3. Strip tags and their inner contents
            tags_to_strip = list(self.STRIP_WITH_CONTENT_TAGS)
            if not strip_navigation:
                for nav_tag in ["header", "footer", "nav", "aside"]:
                    if nav_tag in tags_to_strip:
                        tags_to_strip.remove(nav_tag)

            for tag in tags_to_strip:
                tag_pattern = re.compile(
                    rf"<{tag}\b[^>]*>.*?</{tag}>|<{tag}\b[^>]*/>",
                    re.IGNORECASE | re.DOTALL,
                )
                cleaned = tag_pattern.sub("", cleaned)

            # 4. Remove inline event handlers, style attributes, and data attributes
            cleaned = self.EVENT_HANDLER_PATTERN.sub("", cleaned)
            cleaned = self.STYLE_ATTR_PATTERN.sub("", cleaned)
            cleaned = self.DATA_ATTR_PATTERN.sub("", cleaned)

            # 5. Collapse excessive whitespace and blank lines
            cleaned = re.sub(r"[ \t]+", " ", cleaned)
            cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
            cleaned = cleaned.strip()

            reduction_pct = (
                ((len(raw_html) - len(cleaned)) / len(raw_html) * 100) if raw_html else 0.0
            )
            logger.debug(
                "DOM cleaned. Size: %d -> %d chars (%.1f%% token reduction).",
                len(raw_html),
                len(cleaned),
                reduction_pct,
            )
            return cleaned

        except Exception as e:
            logger.error("DOM cleaning failed: %s", str(e), exc_info=True)
            raise DOMCleaningError(f"Failed to clean DOM: {e}") from e
