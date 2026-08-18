import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from backend.integration.config import settings
from shared.schemas import BrowserAction, GoalSchema, PlanStep

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Exception raised for unrecoverable LLM service errors."""

    pass


class LLMService:
    """Production LLM Service supporting HTTP API providers with rule-based heuristic fallbacks."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """Initializes the LLM provider configuration.

        Args:
            api_key: Optional API key. Defaults to settings.LLM_API_KEY.
            base_url: Optional API base URL. Defaults to settings.LLM_BASE_URL.
            model: Optional model name. Defaults to settings.LLM_MODEL.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        logger.info(
            "LLMService initialized (Model: %s, BaseURL: %s, Key Configured: %s)",
            self.model,
            self.base_url,
            bool(self.api_key),
        )

    def _call_llm_api(self, system_prompt: str, user_prompt: str) -> str:
        """Performs an HTTP POST request to an OpenAI-compatible / FreeLLMAPI chat endpoint.

        Args:
            system_prompt: The system instruction for the LLM.
            user_prompt: The user instruction or payload.

        Returns:
            The raw text content returned by the LLM.

        Raises:
            LLMServiceError: If the request fails or times out.
        """
        if not self.api_key:
            raise LLMServiceError("No LLM API key configured.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "AutonomousWebAgent/1.0",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                data = json.loads(body)
                content = data["choices"][0]["message"]["content"]
                return content
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError) as e:
            logger.warning("LLM API call failed (%s). Triggering fallback heuristics.", str(e))
            raise LLMServiceError(f"HTTP LLM failure: {e}")

    def parse_user_goal(self, raw_query: str, goal_id: str) -> GoalSchema:
        """Stage 1: Analyzes user prompt and generates structured GoalSchema.

        Args:
            raw_query: Unstructured query string from user.
            goal_id: Pre-assigned tracking UUID.

        Returns:
            Validated GoalSchema object.
        """
        query = raw_query.strip()
        if not query:
            raise LLMServiceError("User query cannot be empty.")

        system_prompt = (
            "You are an expert AI Goal Parser for an Autonomous Web Agent.\n"
            "Analyze the user's objective and extract:\n"
            "1. 'objective': Concise, clear target objective.\n"
            "2. 'constraints': Array of explicit or inferred constraints (e.g. site exclusions, price ranges, currency).\n"
            "3. 'metadata': Key-value dictionary of extracted parameters.\n"
            "Return JSON matching: {\"objective\": \"...\", \"constraints\": [...], \"metadata\": {...}}"
        )

        try:
            raw_json = self._call_llm_api(system_prompt, f"User Goal: {query}")
            parsed = json.loads(raw_json)
            return GoalSchema(
                goal_id=goal_id,
                objective=parsed.get("objective", query),
                constraints=parsed.get("constraints", []),
                metadata=parsed.get("metadata", {}),
            )
        except Exception:
            # Fallback heuristic parser
            return self._heuristic_parse_goal(query, goal_id)

    def generate_plan(self, goal: GoalSchema, max_steps: int = 5) -> List[PlanStep]:
        """Stage 2: Decomposes structured goal into discrete ordered browser steps.

        Args:
            goal: The structured GoalSchema.
            max_steps: Maximum number of execution steps permitted.

        Returns:
            List of ordered PlanStep objects.
        """
        system_prompt = (
            "You are an expert Autonomous Web Agent Browser Planner.\n"
            "Generate a sequential list of browser steps to accomplish the goal.\n"
            "Supported actions: 'navigate', 'click', 'input', 'scroll', 'wait'.\n"
            f"Limit the plan to at most {max_steps} steps.\n"
            "Return JSON: {\"steps\": [{\"step_id\": 1, \"action\": \"navigate\", \"url\": \"...\", \"selector\": null, \"input_value\": null, \"description\": \"...\"}]}"
        )

        user_content = (
            f"Objective: {goal.objective}\n"
            f"Constraints: {json.dumps(goal.constraints)}\n"
            f"Metadata: {json.dumps(goal.metadata)}"
        )

        try:
            raw_json = self._call_llm_api(system_prompt, user_content)
            parsed = json.loads(raw_json)
            step_dicts = parsed.get("steps", [])

            steps: List[PlanStep] = []
            for s in step_dicts[:max_steps]:
                action_str = s.get("action", "navigate").lower()
                action_enum = (
                    BrowserAction(action_str)
                    if action_str in BrowserAction._value2member_map_
                    else BrowserAction.NAVIGATE
                )
                steps.append(
                    PlanStep(
                        step_id=int(s.get("step_id", len(steps) + 1)),
                        action=action_enum,
                        url=s.get("url"),
                        selector=s.get("selector"),
                        input_value=s.get("input_value"),
                        description=s.get("description", f"Execute action {action_str}"),
                    )
                )
            if steps:
                return steps
        except Exception:
            pass

        # Fallback heuristic planner
        return self._heuristic_generate_plan(goal, max_steps)

    def _heuristic_parse_goal(self, query: str, goal_id: str) -> GoalSchema:
        """Heuristic rule-based goal parser when LLM is offline or unconfigured."""
        logger.info("Using heuristic goal parser for query: '%s'", query)

        constraints: List[str] = ["Prefer authoritative HTTPS sources", "Extract structured facts"]
        metadata: Dict[str, Any] = {"mode": "heuristic"}

        # Detect comparison intent
        if re.search(r"\b(compare|vs|versus|difference)\b", query, re.I):
            constraints.append("Cross-reference multiple candidate sources")
            metadata["intent"] = "comparison"

        # Detect price/product intent (e.g. price, cheapest, cost, buy, discount)
        if re.search(r"\b(price\w*|cost\w*|buy\w*|cheap\w*|deal\w*|discount\w*|quote\w*)\b", query, re.I):
            constraints.append("Extract current currency and pricing metrics")
            metadata["intent"] = "pricing"

        # Detect academic / research intent
        if re.search(r"\b(university\w*|scholarship\w*|paper\w*|research\w*|study|studies)\b", query, re.I):
            constraints.append("Verify requirements and eligibility criteria")
            metadata["intent"] = "academic"

        return GoalSchema(
            goal_id=goal_id,
            objective=query,
            constraints=constraints,
            metadata=metadata,
        )

    def _heuristic_generate_plan(self, goal: GoalSchema, max_steps: int) -> List[PlanStep]:
        """Heuristic domain-aware planner creating optimal search and browse steps."""
        logger.info("Using heuristic step planner for goal: '%s'", goal.objective)

        query = goal.objective.lower()
        steps: List[PlanStep] = []
        encoded_query = urllib.parse.quote_plus(goal.objective)

        # 1. Comparison across retail sites
        if "compare" in query or "price" in query:
            steps.append(
                PlanStep(
                    step_id=1,
                    action=BrowserAction.NAVIGATE,
                    url=f"https://www.google.com/search?q={encoded_query}",
                    description=f"Search Google for: '{goal.objective}'",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    action=BrowserAction.SCROLL,
                    description="Scroll down to load organic search results",
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    action=BrowserAction.CLICK,
                    selector="div.g a",
                    description="Click the primary organic search result link",
                )
            )
        # 2. General research query
        else:
            steps.append(
                PlanStep(
                    step_id=1,
                    action=BrowserAction.NAVIGATE,
                    url=f"https://www.google.com/search?q={encoded_query}",
                    description=f"Search web index for: '{goal.objective}'",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    action=BrowserAction.CLICK,
                    selector="div.g a",
                    description="Navigate into the top authoritative citation",
                )
            )

        return steps[:max_steps]
