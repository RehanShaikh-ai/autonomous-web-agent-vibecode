"""Domain-specific exceptions for the browser execution module.

This module defines custom error types raised during browser automation,
element interaction, page navigation, and multi-tab orchestration.
"""

from typing import Optional


class BrowserError(Exception):
    """Base exception for all browser module errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize the browser error.

        Args:
            message: Human-readable error description.
            details: Optional technical diagnostic details.
        """
        super().__init__(message)
        self.message: str = message
        self.details: Optional[str] = details

    def __str__(self) -> str:
        """Return formatted string representation of the error."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class BrowserActionError(BrowserError):
    """Exception raised when an atomic browser action fails to complete."""

    def __init__(self, action: str, message: str, details: Optional[str] = None) -> None:
        """Initialize the action error.

        Args:
            action: Name of the failed action (e.g., 'click', 'input').
            message: Human-readable error description.
            details: Optional technical diagnostic details.
        """
        super().__init__(f"Action '{action}' failed: {message}", details)
        self.action: str = action


class SelectorNotFoundError(BrowserActionError):
    """Exception raised when a required DOM selector cannot be found on the page."""

    def __init__(self, action: str, selector: str, details: Optional[str] = None) -> None:
        """Initialize selector not found error.

        Args:
            action: The action attempting to locate the selector.
            selector: The CSS or XPath selector string.
            details: Optional technical diagnostic details.
        """
        super().__init__(
            action=action,
            message=f"Target selector '{selector}' was not found in active DOM",
            details=details,
        )
        self.selector: str = selector


class NavigationTimeoutError(BrowserActionError):
    """Exception raised when a navigation or page load exceeds configured timeout."""

    def __init__(self, url: str, timeout_ms: int, details: Optional[str] = None) -> None:
        """Initialize navigation timeout error.

        Args:
            url: The destination URL that timed out.
            timeout_ms: Timeout threshold in milliseconds.
            details: Optional technical diagnostic details.
        """
        super().__init__(
            action="navigate",
            message=f"Navigation to '{url}' timed out after {timeout_ms}ms",
            details=details,
        )
        self.url: str = url
        self.timeout_ms: int = timeout_ms


class TabManagementError(BrowserError):
    """Exception raised for invalid tab operations."""

    def __init__(self, tab_id: str, message: str) -> None:
        """Initialize tab management error.

        Args:
            tab_id: Identifier of the problematic tab.
            message: Description of the failure.
        """
        super().__init__(f"Tab '{tab_id}' error: {message}")
        self.tab_id: str = tab_id
