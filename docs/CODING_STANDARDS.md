# Coding & Development Standards

This document establishes the code quality, formatting, error-handling, and logging standards for the Autonomous Web Agent repository. Adherence to these standards is verified by automated tools and reviewed during pull requests.

---

## ⚡ Linting, Formatting, & Styling

To maintain readability and clean diffs, this repository uses **Ruff** for all linting and code formatting, superseding Black, Flake8, and isort.

* **Formatter Rules**: Line length is capped at **100 characters**. Imports must be sorted alphabetically, grouped by standard library, third-party, and internal modules.
* **Command Check**: To verify formatting and lint compliance locally, run:
  ```bash
  ruff check .
  ruff format --check .
  ```

---

## 🏷️ Type Hints

Type definitions are mandatory for all backend and frontend files.

* **Backend (Python)**: Every function declaration must have explicit parameters and return type annotations.
  * 👍 `def fetch_page(url: str, timeout_ms: int = 30000) -> BrowserResult:`
  * 👎 `def fetch_page(url, timeout_ms=30000):`
  * Avoid `Any` type. If a type is complex or dynamic, define a specific `TypeVar` or use Pydantic schemas. If a field can be null, wrap it explicitly in `Optional[...]`.
* **Frontend (TypeScript)**: Do not use `any`. Define interfaces for all API response payloads and component props.

---

## 📁 Naming Conventions

Consistent naming makes navigating the multi-stage pipeline seamless.

* **Directories & Packages**: All folder names must be lowercase `snake_case` (e.g., `backend/processing/`, `tests/unit/`).
* **Python Files**: All file names must be lowercase `snake_case` (e.g., `ad_blocker.py`, `schemas.py`).
* **Python Classes**: Must use `PascalCase` (e.g., `BrowserExecutor`, `VerificationEngine`).
* **Python Functions & Variables**: Must use lowercase `snake_case` (e.g., `clean_dom()`, `page_source`).
* **Frontend React Components**: Must use `PascalCase` (e.g., `PlanVisualizer.tsx`, `ReportView.tsx`).

---

## 🚨 Error Handling Policy

All errors must be handled safely to prevent the orchestrator loop from crashing when navigating unstable sites.

1. **Custom Exceptions**: Define specific domain exceptions extending a base exception `AWAException`.
   * For Browser: `BrowserActionError`, `SelectorNotFoundError`, `NavigationTimeoutError`.
   * For Processing: `MarkdownConversionError`, `EntityExtractionError`.
2. **No Bare Excepts**: Banish `except: pass` and generic `except Exception:` blocks unless logging the traceback at the topmost orchestrator loop level.
3. **Graceful Failures**: If a step fails, return a `BrowserResult` with `status="failed"` and populate the `error_message` field instead of letting the exception bubble up and kill the service.

---

## 📝 Logging Standard

We forbid the use of `print()` statements in backend execution code. Instead, we use Python's built-in `logging` module.

### Logger Setup

Always obtain a logger configured for the active module namespace:

```python
import logging

logger = logging.getLogger(__name__)
```

### Log Level Protocol

* **`DEBUG`**: Diagnostic information about browser selectors, raw step execution steps, and schema serialization.
  * *Example*: `logger.debug("Clicking selector '%s' on url '%s'", selector, url)`
* **`INFO`**: Core state transitions of the 5-stage pipeline.
  * *Example*: `logger.info("Transitioning to Stage 4 (Verify) for goal %s", goal_id)`
* **`WARNING`**: Non-fatal operational hiccups, retry loops, or page elements that took longer to load than usual.
  * *Example*: `logger.warning("Selector '%s' not found on try 1, retrying...", selector)`
* **`ERROR`**: Action failures that prevent a step from completing, or third-party api credential drops.
  * *Example*: `logger.error("Failed to run Playwright browser: %s", str(e), exc_info=True)`

---

## 💡 Comments & Google Style Docstrings

Code must explain *why* something is written, not *what* it is doing.

* **Inline Comments**: Place inline comments sparingly, explaining complex regex patterns, DOM selector query paths, or custom mathematical scoring.
* **Docstrings**: Document all classes, methods, and functions using the **Google Python Docstring Style**:

```python
def extract_entities(markdown_content: str, target_keys: List[str]) -> Dict[str, str]:
    """Uses LLM services to extract targeted properties from cleaned page text.

    Args:
        markdown_content: Cleaned markdown output from the page.
        target_keys: List of properties to locate (e.g. ['price', 'sku']).

    Returns:
        A dictionary mapping the target keys to their located string values.

    Raises:
        EntityExtractionError: If the LLM call fails or returns invalid formats.
    """
```
