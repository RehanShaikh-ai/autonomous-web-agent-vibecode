<<<<<<< HEAD
# Module Owned by Member C: Processing and Verification Specialist
# Responsibilities: Ad-blocking logic, DOM cleaning, MarkItDown markdown rendering, entity extraction, source verification, confidence calculations.
=======
"""Processing and Verification Package (Owned by Member C).

Responsibilities:
- Ad-blocking and tracking overlay removal
- DOM cleaning and HTML sanitization
- MarkItDown and semantic Markdown conversion
- Entity extraction (prices, availability, model numbers, SKUs)
- Source verification and mathematical confidence scoring
"""

from backend.processing.ad_blocker import AdBlocker
from backend.processing.cleaner import PageProcessor, process_raw_html
from backend.processing.dom_cleaner import DOMCleaner
from backend.processing.entity_extractor import EntityExtractor
from backend.processing.exceptions import (
    DOMCleaningError,
    EntityExtractionError,
    MarkdownConversionError,
    ProcessingError,
    VerificationError,
)
from backend.processing.markdown_converter import MarkdownConverter
from backend.processing.verifier import VerificationEngine, verify_cross_source


__all__ = [
    "AdBlocker",
    "DOMCleaner",
    "DOMCleaningError",
    "EntityExtractionError",
    "EntityExtractor",
    "MarkdownConversionError",
    "MarkdownConverter",
    "PageProcessor",
    "ProcessingError",
    "VerificationEngine",
    "VerificationError",
    "process_raw_html",
    "verify_cross_source",
]
>>>>>>> 4d8d5e7 (feat(process): complete processing & verification pipeline)
