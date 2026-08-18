import logging
from typing import Any, Dict, List
from shared.schemas import GoalSchema, PlanStep

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service failures."""

    pass


class LLMService:
    """Service abstraction wrapper for LLM requests (FreeLLMAPI calls)."""

    def __init__(self, api_key: str = "mock-api-key") -> None:
        """Initializes the LLM service.

        Args:
            api_key: Secret access token for the FreeLLMAPI endpoint.
        """
        self.api_key = api_key
        logger.debug("LLM Service initialized.")

    def parse_user_goal(self, raw_query: str, goal_id: str) -> GoalSchema:
        """Parses raw unstructured user text to extract structural constraints and intents.

        Args:
            raw_query: The raw query input text from the client.
            goal_id: Pre-generated execution transaction tracking ID.

        Returns:
            A populated GoalSchema conforming to pipeline standards.

        Raises:
            LLMServiceError: If the downstream LLM processing fails.
        """
        logger.info("Parsing user goal for query: '%s'", raw_query)
        if not raw_query.strip():
            raise LLMServiceError("Raw user query cannot be blank.")

        # In a real environment, this makes an HTTP call to FreeLLMAPI.
        # We mock this behavior here to return verified schemas.
        objective = f"Extracted Goal: {raw_query}"
        constraints = [
            "Exclude third-party marketplace sellers",
            "Prefer HTTPS websites only",
        ]
        metadata = {"source_query_length": len(raw_query)}

        return GoalSchema(
            goal_id=goal_id,
            objective=objective,
            constraints=constraints,
            metadata=metadata,
        )

    def generate_plan(self, goal: GoalSchema) -> List[PlanStep]:
        """Generates a list of browser steps to execute target objectives.

        Args:
            goal: The parsed GoalSchema containing constraints.

        Returns:
            A list of ordered PlanStep actions.
        """
        logger.info("Generating execution steps for goal ID: %s", goal.goal_id)

        # Mocking step plan output.
        # Steps determine target search pages and clicks.
        return [
            PlanStep(
                step_id=1,
                action="navigate",
                url="https://www.bestbuy.com/site/searchpage?st=Kindle",
                description="Navigate to Best Buy kindle search results",
            ),
            PlanStep(
                step_id=2,
                action="click",
                selector="a.product-title-link",
                description="Click the first Kindle product match link",
            ),
        ]
