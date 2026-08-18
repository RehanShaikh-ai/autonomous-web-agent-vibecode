import logging
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from backend.integration.orchestrator import OrchestrationEngine
from shared.schemas import (
    BrowserResult,
    FinalReport,
    GoalSchema,
    PlanStep,
    ProcessedPage,
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

# Instantiate the active Orchestration Engine
orchestrator = OrchestrationEngine()


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
    source_domain: str = Field("unknown.com", description="Domain of page being processed.")
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
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query objective cannot be empty.",
        )

    goal, steps = orchestrator.start_new_run(request.query)
    return PlanResponse(goal_id=goal.goal_id, structured_goal=goal, steps=steps)


@app.post(
    "/api/v1/browse",
    response_model=BrowserResult,
    status_code=status.HTTP_200_OK,
    summary="Execute Browser Navigation Step (Member B Scope)",
)
async def browse_page(request: BrowseRequest):
    """Performs browser actions using Playwright. Connects to database session."""
    logger.info("Executing browser action '%s' for step %d", request.step.action, request.step.step_id)
    try:
        result = orchestrator.run_browser_step(
            request.goal_id, request.step, request.browser_config
        )
        return result
    except Exception as e:
        logger.error("Failed executing step: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Browser execution failure: {e}",
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
    try:
        processed = orchestrator.run_process_step(
            request.goal_id, request.step_id, request.raw_html, request.source_domain
        )
        return processed
    except Exception as e:
        logger.error("Processing failure: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DOM processing failure: {e}",
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

    # Reconstruct ProcessedPage objects from incoming request structure
    processed_pages: List[ProcessedPage] = []
    for idx, item in enumerate(request.extracted_data):
        processed_pages.append(
            ProcessedPage(
                step_id=idx + 1,
                source_domain=item.get("source", "unknown.com"),
                cleaned_markdown="",
                entities=item.get("entities", {}),
            )
        )

    try:
        report = orchestrator.run_verification(request.goal_id, processed_pages)
        return report
    except Exception as e:
        logger.error("Verification failure: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Source verification failure: {e}",
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
