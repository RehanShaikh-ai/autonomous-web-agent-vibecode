import pytest
from pydantic import ValidationError
from shared.schemas import GoalSchema, PlanStep, BrowserAction, BrowserResult


def test_goal_schema_validation():
    """Verify that GoalSchema parses correct input and catches validation errors."""
    valid_data = {
        "goal_id": "goal_123",
        "objective": "Test objective",
        "constraints": ["limit 1", "limit 2"],
        "metadata": {"key": "value"},
    }
    goal = GoalSchema(**valid_data)
    assert goal.goal_id == "goal_123"
    assert len(goal.constraints) == 2

    invalid_data = {
        "objective": "Missing goal_id",
    }
    with pytest.raises(ValidationError):
        GoalSchema(**invalid_data)


def test_plan_step_enum():
    """Verify PlanStep only accepts valid enum values for action."""
    valid_step = {
        "step_id": 1,
        "action": "navigate",
        "url": "https://example.com",
        "description": "Navigate to homepage",
    }
    step = PlanStep(**valid_step)
    assert step.action == BrowserAction.NAVIGATE

    invalid_step = {
        "step_id": 2,
        "action": "invalid_action_value",
        "description": "Invalid action test",
    }
    with pytest.raises(ValidationError):
        PlanStep(**invalid_step)
