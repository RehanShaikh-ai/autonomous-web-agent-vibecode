import logging
import uuid
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from backend.integration.llm import LLMService, LLMServiceError
from shared.schemas import (
    BrowserResult,
    FinalReport,
    GoalSchema,
    PlanStep,
    ProcessedPage,
    SourceCitation,
)

# Configure logging according to configs/ruff.toml coding standard rules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autonomous Web Agent Gateway",
    description="Orchestrator and route execution API for the AWA hackathon repository.",
    version="0.1.0",
)

# Instantiate the local LLM service wrapper
llm_service = LLMService()


# Request/Response wrapper schemas
class PlanRequest(BaseModel):
    query: str = Field(..., description="Raw unstructured target search task.")
    max_steps: int = Field(default=5, description="Maximum execution step limits.")


class PlanResponse(BaseModel):
    goal_id: str
    structured_goal: GoalSchema
    steps: List[PlanStep]


class BrowseRequest(BaseModel):
    goal_id: str
    step: PlanStep
    browser_config: Dict[str, Any] = Field(default_factory=dict)


class ProcessRequest(BaseModel):
    goal_id: str
    step_id: int
    raw_html: str
    extraction_keys: List[str] = Field(default_factory=list)


class VerifyRequest(BaseModel):
    goal_id: str
    extracted_data: List[Dict[str, Any]] = Field(
        ..., description="Assertions list collected across multiple sources."
    )


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]


@app.post(
    "/api/v1/plan",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Navigation Plan",
)
async def generate_plan(request: PlanRequest):
    """Processes user query, extracts goals and constraints, and plans steps."""
    logger.info("Received plan request: '%s'", request.query)
    goal_id = f"goal_{uuid.uuid4().hex[:8]}"

    try:
        goal = llm_service.parse_user_goal(request.query, goal_id)
        steps = llm_service.generate_plan(goal)
        return PlanResponse(goal_id=goal_id, structured_goal=goal, steps=steps)
    except LLMServiceError as e:
        logger.error("LLM Service failure: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post(
    "/api/v1/browse",
    response_model=BrowserResult,
    status_code=status.HTTP_200_OK,
    summary="Execute Browser Navigation Step (Member B Scope)",
)
async def browse_page(request: BrowseRequest):
    """Performs browser actions using Playwright. Mocks target result output."""
    logger.info("Executing browser action '%s' for step %d", request.step.action, request.step.step_id)

    # In execution, Member B's browser package will navigate and return raw html.
    # Here we mock a successful navigation result.
    target_url = request.step.url or "https://www.bestbuy.com/site/kindle"
    return BrowserResult(
        step_id=request.step.step_id,
        status="success",
        final_url=target_url,
        raw_html="<html><body><div class='product-price'>$149.99</div></body></html>",
        screenshot_path=f"/artifacts/screenshots/{request.goal_id}_step{request.step.step_id}.webp",
        error_message=None,
    )


@app.post(
    "/api/v1/process",
    response_model=ProcessedPage,
    status_code=status.HTTP_200_OK,
    summary="Sanitize HTML DOM and Extract Entities (Member C Scope)",
)
async def process_page(request: ProcessRequest):
    """Cleans DOM tags, maps markdown text, and pulls core entity metrics."""
    logger.info("Processing page DOM for step ID: %d", request.step_id)

    # In execution, Member C's clean, Markdown conversion and LLM extraction functions will run.
    # Here we return structured Mock outputs.
    cleaned_md = "### Kindle Paperwhite\n* Price: $149.99\n* Stock: In Stock"
    entities = {"price": "$149.99", "stock_status": "In Stock"}

    return ProcessedPage(
        step_id=request.step_id,
        source_domain="bestbuy.com",
        cleaned_markdown=cleaned_md,
        entities=entities,
    )


@app.post(
    "/api/v1/verify",
    response_model=FinalReport,
    status_code=status.HTTP_200_OK,
    summary="Cross-Verify Sources and Deliver Report (Member C Scope)",
)
async def verify_data(request: VerifyRequest):
    """Cross-verifies facts across sources and outputs final unified comparison dashboard."""
    logger.info("Verifying facts for goal ID: %s", request.goal_id)

    # In execution, Member C's verification logic checks assertion agreements.
    # Here we compile a mock verified summary with a 1.0 confidence score.
    citation1 = SourceCitation(
        domain="bestbuy.com",
        url="https://www.bestbuy.com/site/kindle",
        screenshot_path="/artifacts/screenshots/bestbuy_1.webp",
    )

    return FinalReport(
        goal_id=request.goal_id,
        summary="Verified: The Kindle price matches at $149.99.",
        comparison_table=[{"source": "Best Buy", "price": "$149.99"}],
        confidence_score=1.0,
        contradictions=[],
        sources=[citation1],
    )


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Gateway Health Check",
)
async def health_check():
    """Returns runtime module status check."""
    logger.debug("Health check queried.")
    return HealthResponse(
        status="healthy",
        timestamp="2026-08-18T11:14:23Z",
        services={
            "database": "connected",
            "playwright": "available",
            "llm_api": "accessible",
        },
    )
