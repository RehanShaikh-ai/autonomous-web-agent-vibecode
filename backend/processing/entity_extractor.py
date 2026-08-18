"""Entity extraction module for extracting prices, model numbers, stock status, and specs."""

import logging
import re
from typing import Any, ClassVar

from backend.processing.exceptions import EntityExtractionError


logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extracts structured entities, metrics, and key-value properties from cleaned Markdown."""

    # Currency and price detection regex patterns
    PRICE_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        re.compile(
            r"(?:price|sale\s*price|current\s*price|our\s*price|now|cost)"
            r"[:\s]*([$€£₹¥]\s*\d{1,6}(?:,\d{3})*(?:\.\d{2})?)",
            re.IGNORECASE,
        ),
        re.compile(r"([$€£₹¥]\s*\d{1,6}(?:,\d{3})*(?:\.\d{2})?)", re.IGNORECASE),
        re.compile(r"(\d{1,6}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|INR|JPY))", re.IGNORECASE),
    ]

    # Availability / Stock status patterns
    STOCK_PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        (
            re.compile(
                r"\b(in\s*stock|available\s*now|in-stock|ready\s*to\s*ship)\b", re.IGNORECASE
            ),
            "In Stock",
        ),
        (
            re.compile(r"\b(out\s*of\s*stock|currently\s*unavailable|sold\s*out)\b", re.IGNORECASE),
            "Out of Stock",
        ),
        (
            re.compile(r"\b(pre[- ]?order|backordered|back[- ]?order)\b", re.IGNORECASE),
            "Pre-order",
        ),
        (
            re.compile(r"\b(only\s*\d+\s*left\s*(?:in\s*stock)?)\b", re.IGNORECASE),
            "Limited Stock",
        ),
    ]

    # ASIN / SKU / Model Number patterns
    ASIN_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b(B0[0-9A-Z]{8})\b")
    SKU_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?:sku|item\s*(?:#|number)|model\s*(?:#|number|no))[:\s]*([a-zA-Z0-9_-]{4,20})",
        re.IGNORECASE,
    )
    RATING_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(\d(?:\.\d)?)\s*(?:out\s*of\s*5|\/\s*5|\s*stars)", re.IGNORECASE
    )

    def __init__(self) -> None:
        """Initializes the EntityExtractor."""
        logger.debug("EntityExtractor initialized.")

    def extract_entities(
        self,
        markdown_text: str,
        target_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Extracts structured entities and attributes from Markdown text.

        Args:
            markdown_text: Cleaned Markdown content.
            target_keys: Optional specific key names requested (e.g. ['price', 'sku']).

        Returns:
            Dictionary containing extracted key-value pairs.

        Raises:
            EntityExtractionError: If entity extraction encounters an internal failure.
        """
        if not markdown_text or not markdown_text.strip():
            logger.debug("Empty markdown text provided for entity extraction.")
            return {}

        try:
            entities = self._extract_all_entities(markdown_text)

            if target_keys:
                entities = self._filter_by_target_keys(entities, target_keys)
                logger.debug("Extracted %d targeted entities from text.", len(entities))
            else:
                logger.debug("Extracted %d general entities from text.", len(entities))

            return entities

        except Exception as e:
            logger.error("Entity extraction error: %s", str(e), exc_info=True)
            raise EntityExtractionError(f"Failed to extract entities: {e}") from e

    def _extract_all_entities(self, markdown_text: str) -> dict[str, Any]:
        """Runs all extractors and merges results into a single entity dict.

        Args:
            markdown_text: Cleaned Markdown content.

        Returns:
            Dictionary of all extracted entities.
        """
        entities: dict[str, Any] = {}

        price = self._extract_price(markdown_text)
        if price:
            entities["price"] = price

        availability = self._extract_availability(markdown_text)
        if availability:
            entities["availability"] = availability

        model_number = self._extract_model_or_sku(markdown_text)
        if model_number:
            entities["model_number"] = model_number

        rating = self._extract_rating(markdown_text)
        if rating:
            entities["rating"] = rating

        # Key-Value pairs from markdown tables/lists (don't overwrite richer extractions)
        for k, v in self._extract_key_value_pairs(markdown_text).items():
            if k not in entities:
                entities[k] = v

        return entities

    def _filter_by_target_keys(
        self, entities: dict[str, Any], target_keys: list[str]
    ) -> dict[str, Any]:
        """Filters extracted entities to only those matching the requested target keys.

        Args:
            entities: Full extracted entity dictionary.
            target_keys: Caller-specified keys to retain.

        Returns:
            Filtered entity dictionary containing only matched keys.
        """
        filtered: dict[str, Any] = {}
        norm_targets = [k.lower().strip().replace(" ", "_") for k in target_keys]

        for k, v in entities.items():
            norm_k = k.lower().replace(" ", "_").strip()
            for target in norm_targets:
                if target in norm_k or norm_k in target:
                    filtered[k] = v
                    break

        # Ensure requested keys that weren't found default gracefully
        for target in target_keys:
            norm_target = target.lower().replace(" ", "_")
            matched = any(norm_target in k.lower().replace(" ", "_") for k in filtered)
            if not matched and target in entities:
                filtered[target] = entities[target]

        return filtered

    def _extract_price(self, text: str) -> str | None:
        """Finds product pricing from markdown text."""
        for pattern in self.PRICE_PATTERNS:
            match = pattern.search(text)
            if match:
                price_str = match.group(1).strip()
                return re.sub(r"\s+", "", price_str)
        return None

    def _extract_availability(self, text: str) -> str | None:
        """Finds availability or stock status from markdown text."""
        for pattern, status in self.STOCK_PATTERNS:
            if pattern.search(text):
                return status
        return None

    def _extract_model_or_sku(self, text: str) -> str | None:
        """Finds Amazon ASIN, retailer SKU, or model number."""
        asin_match = self.ASIN_PATTERN.search(text)
        if asin_match:
            return asin_match.group(1).strip()

        sku_match = self.SKU_PATTERN.search(text)
        if sku_match:
            return sku_match.group(1).strip()
        return None

    def _extract_rating(self, text: str) -> str | None:
        """Finds star rating from markdown text."""
        match = self.RATING_PATTERN.search(text)
        if match:
            return f"{match.group(1)} / 5"
        return None

    def _extract_key_value_pairs(self, text: str) -> dict[str, str]:
        """Extracts structured key-value pairs from Markdown lines and tables."""
        kv_pairs: dict[str, str] = {}

        # 1. Colon-separated lines: "* Key: Value" or "Key: Value"
        colon_pattern = re.compile(
            r"^(?:\*\s*|-\s*|#+\s*)?([a-zA-Z0-9\s_-]{2,30}):\s*([^\n\r|]{1,100})$",
            re.MULTILINE,
        )
        for match in colon_pattern.finditer(text):
            raw_key = match.group(1).strip()
            raw_val = match.group(2).strip()
            norm_key = raw_key.lower().replace(" ", "_")
            if norm_key and raw_val and norm_key not in ["http", "https"]:
                kv_pairs[norm_key] = raw_val

        # 2. Markdown Table rows: "| Key | Value |"
        table_row_pattern = re.compile(
            r"^[ \t]*\|\s*([a-zA-Z0-9][a-zA-Z0-9\s_-]{1,29})\s*\|\s*([^|\n\r]{1,100})\s*\|[ \t]*$",
            re.MULTILINE,
        )
        for match in table_row_pattern.finditer(text):
            k = match.group(1).strip()
            v = match.group(2).strip()
            if k.lower() not in ["---", "key", "property", "attribute", "feature"] and v != "---":
                norm_key = k.lower().replace(" ", "_")
                kv_pairs[norm_key] = v

        return kv_pairs
