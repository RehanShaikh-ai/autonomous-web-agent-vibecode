from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoalSchema(BaseModel):
    """Represents the user's initial objective parsed into structured constraints."""

    goal_id: str = Field(..., description="Unique transaction ID tracking this agent task run.")
    objective: str = Field(..., description="The main consolidated target of the user query.")
    constraints: List[str] = Field(
        default_factory=list,
        description="Extracted rules to restrict browsing (e.g. site blacklists, price limits).",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional properties or context tokens parsed from intent."
    )


class BrowserAction(str, Enum):
    """Supported browser operations for Playwright navigation steps."""

    NAVIGATE = "navigate"
    CLICK = "click"
    INPUT = "input"
    SCROLL = "scroll"
    WAIT = "wait"


class PlanStep(BaseModel):
    """Represents a single atomic plan step to be executed by the browser."""

    step_id: int = Field(..., description="Order of execution index (1-indexed).")
    action: BrowserAction = Field(..., description="The browser action to execute.")
    url: Optional[str] = Field(None, description="The target website URL. Required if action is 'navigate'.")
    selector: Optional[str] = Field(None, description="CSS selector for target elements (clicks or inputs).")
    input_value: Optional[str] = Field(None, description="Text string to input. Required if action is 'input'.")
    description: str = Field(..., description="Human-readable explanation of why this step is running.")


class BrowserResult(BaseModel):
    """The raw payload returned after performing browser actions."""

    step_id: int = Field(..., description="The ID of the plan step this result relates to.")
    status: str = Field(..., description="Execution status: 'success', 'failed', 'timeout'.")
    final_url: str = Field(..., description="The actual loaded URL (handles redirection).")
    raw_html: str = Field(..., description="Raw HTML DOM text captured post-execution.")
    screenshot_path: Optional[str] = Field(
        None, description="Relative file path of captured viewport image."
    )
    error_message: Optional[str] = Field(
        None, description="Detail string of failures if status is not success."
    )


class ProcessedPage(BaseModel):
    """Saves the result of cleaning DOM text and extracting key entities."""

    step_id: int = Field(..., description="The plan step this processed data belongs to.")
    source_domain: str = Field(..., description="The domain of the source site (e.g., 'bestbuy.com').")
    cleaned_markdown: str = Field(
        ..., description="Sanitized, script-free Markdown representation of page contents."
    )
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs extracted matching the user query (e.g. {'price': '$149.99'}).",
    )


class SourceCitation(BaseModel):
    """Citation metadata for information sourcing."""

    domain: str = Field(..., description="The domain citation.")
    url: str = Field(..., description="The full URL reference.")
    screenshot_path: str = Field(..., description="Saved screenshot image path.")


class FinalReport(BaseModel):
    """The final compiled deliverable delivered to the client UI."""

    goal_id: str = Field(..., description="The transaction ID this report is delivering on.")
    summary: str = Field(..., description="Consolidated natural language response of findings.")
    comparison_table: List[Dict[str, Any]] = Field(
        ..., description="Structured array representing comparative results."
    )
    confidence_score: float = Field(
        ...,
        description="Synthesized confidence value calculated from cross-site source verification.",
    )
    contradictions: List[str] = Field(
        ..., description="List of source assertions that did not match."
    )
    sources: List[SourceCitation] = Field(..., description="List of citations verifying the data.")
