"""Core processing pipeline for Stage 3: DOM cleaning, Markdown conversion, entity extraction."""

import logging

from backend.processing.dom_cleaner import DOMCleaner
from backend.processing.entity_extractor import EntityExtractor
from backend.processing.exceptions import ProcessingError
from backend.processing.markdown_converter import MarkdownConverter
from shared.schemas import ProcessedPage


logger = logging.getLogger(__name__)


class PageProcessor:
    """Unified coordinator for sanitizing web DOMs and generating ProcessedPage payloads."""

    def __init__(
        self,
        dom_cleaner: DOMCleaner | None = None,
        markdown_converter: MarkdownConverter | None = None,
        entity_extractor: EntityExtractor | None = None,
    ) -> None:
        """Initializes the PageProcessor pipeline.

        Args:
            dom_cleaner: Optional custom DOMCleaner instance.
            markdown_converter: Optional custom MarkdownConverter instance.
            entity_extractor: Optional custom EntityExtractor instance.
        """
        self.dom_cleaner = dom_cleaner or DOMCleaner()
        self.markdown_converter = markdown_converter or MarkdownConverter()
        self.entity_extractor = entity_extractor or EntityExtractor()
        logger.debug("PageProcessor initialized.")

    def process(
        self,
        raw_html: str,
        step_id: int,
        domain: str,
        extraction_keys: list[str] | None = None,
    ) -> ProcessedPage:
        """Runs the complete DOM sanitization, Markdown rendering, and entity extraction pipeline.

        Args:
            raw_html: Raw HTML captured by the browser module (Member B).
            step_id: Index ID of the plan step being executed.
            domain: Domain name of the target webpage (e.g., 'amazon.com').
            extraction_keys: Optional list of target properties to extract.

        Returns:
            A populated, schema-compliant ProcessedPage instance.

        Raises:
            ProcessingError: If processing fails at any stage of the pipeline.
        """
        logger.info(
            "Starting DOM and content processing for step %d (domain: %s, raw size: %d bytes).",
            step_id,
            domain,
            len(raw_html or ""),
        )

        try:
            # 1. Clean DOM and strip non-content / ad tags
            sanitized_html = self.dom_cleaner.clean_html(raw_html)

            # 2. Convert sanitized semantic HTML to Markdown
            cleaned_markdown = self.markdown_converter.convert(sanitized_html)

            # 3. Extract key entities and properties
            entities = self.entity_extractor.extract_entities(
                cleaned_markdown, target_keys=extraction_keys
            )

            # 4. Construct validated ProcessedPage conforming to shared/schemas.py
            processed_page = ProcessedPage(
                step_id=step_id,
                source_domain=domain or "unknown.com",
                cleaned_markdown=cleaned_markdown,
                entities=entities,
            )

            logger.info(
                "Completed processing for step %d. Extracted %d entities. Markdown length: %d chars.",  # noqa: E501
                step_id,
                len(entities),
                len(cleaned_markdown),
            )
            return processed_page

        except Exception as e:
            logger.error(
                "Processing pipeline failure for step %d: %s", step_id, str(e), exc_info=True
            )
            raise ProcessingError(f"Failed to process page for step {step_id}: {e}") from e


# Singleton instance for high performance and standard calls
_DEFAULT_PROCESSOR = PageProcessor()


def process_raw_html(
    raw_html: str,
    step_id: int,
    domain: str,
    extraction_keys: list[str] | None = None,
) -> ProcessedPage:
    """Convenience function executed by the Orchestrator (Member A) to process browser results.

    Args:
        raw_html: Raw HTML DOM text from browser execution.
        step_id: Order of execution index (1-indexed).
        domain: Main domain identifying the source page.
        extraction_keys: Optional list of target properties to extract.

    Returns:
        A validated ProcessedPage object containing sanitized Markdown and extracted entities.
    """
    return _DEFAULT_PROCESSOR.process(
        raw_html=raw_html,
        step_id=step_id,
        domain=domain,
        extraction_keys=extraction_keys,
    )
