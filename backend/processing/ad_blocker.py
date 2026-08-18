"""Ad blocking, cookie banner, and promo overlay removal module."""

import logging
import re
from re import Pattern
from typing import ClassVar


logger = logging.getLogger(__name__)


class AdBlocker:
    """Detects and strips advertisements, tracking elements, cookie consent modals, and overlays."""

    # Common ad-related class and ID keywords
    AD_IDENTIFIER_PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r"\b(ad|ads|advert|advertisement|advertising|advertorial)\b", re.IGNORECASE),
        re.compile(r"[-_](ad|ads|banner|sponsor|sponsored)[-_]", re.IGNORECASE),
        re.compile(r"(google[-_]?ads|adsense|adsbygoogle|dfp[-_]?tag)", re.IGNORECASE),
        re.compile(r"(taboola|outbrain|criteo|amazon[-_]?adsystem)", re.IGNORECASE),
        re.compile(r"(cookie[-_]?(banner|consent|modal|notice|policy|bar))", re.IGNORECASE),
        re.compile(r"(newsletter[-_]?(popup|modal|subscribe|signup))", re.IGNORECASE),
        re.compile(r"(promo[-_]?(banner|popup|bar|overlay))", re.IGNORECASE),
        re.compile(r"(sponsored[-_]?(content|product|item|listing|result))", re.IGNORECASE),
    ]

    # Tag names commonly dedicated to ads/tracking
    AD_TAG_NAMES: ClassVar[list[str]] = [
        "ins",
        "amp-ad",
        "amp-embed",
    ]

    def __init__(self) -> None:
        """Initializes the AdBlocker component."""
        logger.debug("AdBlocker initialized.")

    def is_ad_identifier(self, identifier_str: str) -> bool:
        """Checks if a class name, ID, or attribute string matches ad/tracking patterns.

        Args:
            identifier_str: Attribute string (e.g. class, id, role) to test.

        Returns:
            True if the identifier matches known advertising or promotional patterns.
        """
        if not identifier_str:
            return False

        return any(pattern.search(identifier_str) for pattern in self.AD_IDENTIFIER_PATTERNS)

    def strip_ad_tags(self, html_content: str) -> str:
        """Strips dedicated advertising tag elements from raw HTML markup.

        Args:
            html_content: Raw HTML text.

        Returns:
            Cleaned HTML text with ad tags and identified ad containers removed.
        """
        if not html_content:
            return ""

        cleaned = html_content

        # 1. Remove dedicated ad tags (<ins class="adsbygoogle">, <amp-ad>, etc.)
        for tag in self.AD_TAG_NAMES:
            tag_regex = re.compile(
                rf"<{tag}\b[^>]*>.*?</{tag}>|<{tag}\b[^>]*/>",
                re.IGNORECASE | re.DOTALL,
            )
            cleaned = tag_regex.sub("", cleaned)

        # 2. Remove script / iframe ad widgets directly matched by source URLs
        ad_src_pattern = re.compile(
            r"<(?:iframe|script)\b[^>]*"
            r"(?:googleads|doubleclick|criteo|outbrain|taboola|amazon-adsystem)"
            r"[^>]*>.*?</(?:iframe|script)>",
            re.IGNORECASE | re.DOTALL,
        )
        cleaned = ad_src_pattern.sub("", cleaned)

        # 3. Strip identifiable ad / cookie / promo blocks with regex on common element wrappers
        # Match <div class="...ad...">...</div> or <section id="...promo...">...</section>
        for pattern in self.AD_IDENTIFIER_PATTERNS:
            container_pattern = re.compile(
                rf"<(div|section|aside|banner)\b[^>]*(?:class|id)=['\"][^'\"]*?"
                rf"{pattern.pattern}[^'\"]*?['\"][^>]*>.*?</\1>",
                re.IGNORECASE | re.DOTALL,
            )
            cleaned = container_pattern.sub("", cleaned)

        logger.debug(
            "AdBlocker finished. Content size reduced from %d to %d bytes.",
            len(html_content),
            len(cleaned),
        )
        return cleaned
