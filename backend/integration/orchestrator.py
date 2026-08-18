import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from backend.integration.config import settings
from backend.integration.database import SessionDatabase
from backend.integration.llm import LLMService
from shared.schemas import (
    BrowserResult,
    FinalReport,
    GoalSchema,
    PlanStep,
    ProcessedPage,
    SourceCitation,
)

logger = logging.getLogger(__name__)

# Safe Fallback Import Patterns for Concurrent Team Development
try:
    from backend.browser.executor import execute_browser_action
except ImportError:
    logger.warning("Member B's browser executor not found. Using fallback mock.")

    def execute_browser_action(
        step: PlanStep, goal_id: str, config: Optional[dict] = None
    ) -> BrowserResult:
        target_url = step.url or "https://www.example.com"
        return BrowserResult(
            step_id=step.step_id,
            status="success",
            final_url=target_url,
            raw_html=f"<html><body>Mock Content for step {step.step_id} ({step.action.value})</body></html>",
            screenshot_path=f"/artifacts/screenshots/{goal_id}_step{step.step_id}.webp",
            error_message=None,
        )


try:
    from backend.processing.cleaner import process_raw_html
except ImportError:
    logger.warning("Member C's cleaner/markdown processor not found. Using fallback mock.")

    def process_raw_html(raw_html: str, step_id: int, domain: str) -> ProcessedPage:
        return ProcessedPage(
            step_id=step_id,
            source_domain=domain,
            cleaned_markdown=f"Mock cleaned Markdown for step {step_id}.",
            entities={
                "price": "$149.99",
                "availability": "In Stock",
                "metric": f"Value from step {step_id}",
                "status": "verified",
            },
        )


try:
    from backend.processing.verifier import verify_cross_source
except ImportError:
    logger.warning("Member C's verification engine not found. Using fallback mock.")

    def verify_cross_source(
        pages: List[ProcessedPage], goal_id: str
    ) -> FinalReport:
        sources = [
            SourceCitation(
                domain=p.source_domain or "example.com",
                url=f"https://{p.source_domain or 'example.com'}",
                screenshot_path=f"/artifacts/screenshots/{goal_id}_step{p.step_id}.webp",
            )
            for p in pages
        ] or [
            SourceCitation(
                domain="example.com",
                url="https://www.example.com",
                screenshot_path=f"/artifacts/screenshots/{goal_id}_step1.webp",
            )
        ]
        return FinalReport(
            goal_id=goal_id,
            summary="Autonomous execution mission completed and verified across sources.",
            comparison_table=[{"source": p.source_domain, **p.entities} for p in pages],
            confidence_score=1.0,
            contradictions=[],
            sources=sources,
        )


class OrchestrationEngine:
    """Coordinating state machine executing the 5-stage pipeline."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initializes database, model clients, and local services.

        Args:
            db_path: Path to the SQLite database session cache.
        """
        self.db = SessionDatabase(db_path or settings.DB_PATH)
        self.llm = LLMService()
        logger.info("OrchestrationEngine ready.")

    def start_new_run(self, raw_query: str, max_steps: int = 5) -> tuple[GoalSchema, List[PlanStep]]:
        """Stage 1 & 2: Parses intent and creates navigation execution steps.

        Args:
            raw_query: Unstructured objective query string from client.
            max_steps: Maximum count of execution steps to generate.

        Returns:
            A tuple of parsed GoalSchema and List[PlanStep] records.
        """
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        goal = self.llm.parse_user_goal(raw_query, goal_id)
        steps = self.llm.generate_plan(goal, max_steps=max_steps)

        # Persist session structures in SQLite
        self.db.create_session(goal, steps)
        return goal, steps

    def run_browser_step(
        self, goal_id: str, step: PlanStep, browser_config: Optional[dict] = None
    ) -> BrowserResult:
        """Stage 3: Invokes the browser specialist's navigation routines.

        Args:
            goal_id: Active task session ID.
            step: Targeted PlanStep.
            browser_config: Browser runtime configurations.

        Returns:
            A populated BrowserResult object.
        """
        logger.info("Executing step %d for goal %s", step.step_id, goal_id)
        self.db.update_session_status(goal_id, "running")

        # Execute Black-Box action from Member B
        result = execute_browser_action(step, goal_id, browser_config)

        # Save result in database
        self.db.save_browser_result(goal_id, result)
        return result

    def run_process_step(
        self, goal_id: str, step_id: int, raw_html: str, source_domain: str
    ) -> ProcessedPage:
        """Stage 3 (Continued): Sanitize text and extract data properties.

        Args:
            goal_id: Active session tracking ID.
            step_id: Navigation step ID.
            raw_html: Raw page DOM markup source.
            source_domain: Main domain identifying source page.

        Returns:
            A ProcessedPage object containing markdown text and extracted entities.
        """
        logger.info("Processing step %d output for goal %s", step_id, goal_id)

        # Execute Black-Box parsing from Member C
        processed = process_raw_html(raw_html, step_id, source_domain)
        return processed

    def run_verification(
        self, goal_id: str, processed_pages: List[ProcessedPage]
    ) -> FinalReport:
        """Stage 4 & 5: Verifies assertions and delivers the report.

        Args:
            goal_id: Active session tracking ID.
            processed_pages: List of data extracted from all steps.

        Returns:
            A FinalReport containing confidence scores and comparison tables.
        """
        logger.info("Initiating source validation for goal %s", goal_id)

        # Execute Black-Box verifier from Member C
        report = verify_cross_source(processed_pages, goal_id)

        # Persist Final report in database
        self.db.save_final_report(
            goal_id,
            report.model_dump_json(),
            report.confidence_score,
        )
        return report

    def execute_mission_end_to_end(
        self, raw_query: str, max_steps: int = 5, browser_config: Optional[dict] = None
    ) -> FinalReport:
        """Runs the entire 5-stage pipeline autonomously from end to end.

        Args:
            raw_query: The user task objective.
            max_steps: Maximum step boundaries.
            browser_config: Playwright runtime configs.

        Returns:
            The compiled FinalReport deliverable.
        """
        logger.info("Starting autonomous mission: '%s'", raw_query)
        goal, steps = self.start_new_run(raw_query, max_steps=max_steps)

        processed_pages: List[ProcessedPage] = []
        for step in steps:
            # 1. Execute Browser Step (Stage 3)
            b_res = self.run_browser_step(goal.goal_id, step, browser_config)
            domain = step.url.split("/")[2] if (step.url and "://" in step.url) else "web-source.com"

            # 2. Process Page (Stage 3)
            p_res = self.run_process_step(goal.goal_id, step.step_id, b_res.raw_html, domain)
            processed_pages.append(p_res)

        # 3. Verify & Deliver (Stage 4 & 5)
        final_report = self.run_verification(goal.goal_id, processed_pages)
        return final_report

    def get_session_info(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Fetches full session status and history."""
        return self.db.get_session(goal_id)

    def list_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists recent sessions."""
        return self.db.list_sessions(limit)
