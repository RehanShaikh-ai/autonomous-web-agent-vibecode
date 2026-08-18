import pytest
from backend.integration.llm import LLMService, LLMServiceError
from shared.schemas import BrowserAction, GoalSchema


def test_heuristic_goal_parsing():
    """Verify that heuristic goal parser extracts intent and constraints."""
    llm = LLMService(api_key="")  # Force heuristic fallback

    # Comparison query
    goal_comp = llm.parse_user_goal("Compare iPhone 15 vs Samsung S24", "goal_test_1")
    assert goal_comp.goal_id == "goal_test_1"
    assert "Cross-reference multiple candidate sources" in goal_comp.constraints
    assert goal_comp.metadata.get("intent") == "comparison"

    # Pricing query
    goal_price = llm.parse_user_goal("Find the cheapest flight to Tokyo", "goal_test_2")
    assert "Extract current currency and pricing metrics" in goal_price.constraints
    assert goal_price.metadata.get("intent") == "pricing"

    # Blank query check
    with pytest.raises(LLMServiceError):
        llm.parse_user_goal("", "goal_blank")


def test_heuristic_plan_generation():
    """Verify that heuristic step planner produces ordered steps with browser actions."""
    llm = LLMService(api_key="")

    goal = GoalSchema(
        goal_id="goal_test_plan",
        objective="Compare Kindle prices",
        constraints=[],
    )

    steps = llm.generate_plan(goal, max_steps=3)
    assert len(steps) == 3
    assert steps[0].step_id == 1
    assert steps[0].action == BrowserAction.NAVIGATE
    assert "google.com" in steps[0].url
    assert steps[1].action in (BrowserAction.SCROLL, BrowserAction.CLICK)
