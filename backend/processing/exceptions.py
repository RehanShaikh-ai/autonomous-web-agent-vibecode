"""Custom exception definitions for the processing and verification pipeline (Member C)."""


class ProcessingError(Exception):
    """Base exception for all processing and verification module operations."""


class DOMCleaningError(ProcessingError):
    """Exception raised when HTML sanitization or DOM traversal fails."""


class MarkdownConversionError(ProcessingError):
    """Exception raised when converting HTML to Markdown fails."""


class EntityExtractionError(ProcessingError):
    """Exception raised when entity extraction encounters an unrecoverable error."""


class VerificationError(ProcessingError):
    """Exception raised when cross-source verification or scoring fails."""
