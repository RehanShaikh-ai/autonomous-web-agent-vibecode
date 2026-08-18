import os
import pytest
from backend.integration.database import SessionDatabase, DatabaseError
from backend.integration.orchestrator import OrchestrationEngine
from shared.schemas import GoalSchema, PlanStep, BrowserAction, BrowserResult


@pytest.fixture
def temp_db_path(tmp_path):
    """Fixture supplying a temporary path for the SQLite database."""
    db_file = tmp_path / "test_sessions.db"
    return str(db_file)


def test_database_init(temp_db_path):
    """Verify that tables are created on database initialization."""
    db = SessionDatabase(temp_db_path)
    assert os.path.exists(temp_db_path)

    # Basic fetch check
    assert db.get_session("non_existent") is None


def test_database_session_insert(temp_db_path):
    """Verify writing and retrieving sessions and steps from database."""
    db = SessionDatabase(temp_db_path)

    goal = GoalSchema(
        goal_id="goal_test1",
        objective="Verify SQLite insertion",
        constraints=["constraint1"],
        metadata={"run": 1},
    )

    steps = [
        PlanStep(
            step_id=1,
            action=BrowserAction.NAVIGATE,
            url="https://example.com",
            description="Nav task",
        )
    ]

    db.create_session(goal, steps)

    session = db.get_session("goal_test1")
    assert session is not None
    assert session["objective"] == "Verify SQLite insertion"
    assert session["status"] == "planned"
    assert len(session["steps"]) == 1
    assert session["steps"][0]["action"] == "navigate"


def test_database_browser_result_insert(temp_db_path):
    """Verify saving browser action results."""
    db = SessionDatabase(temp_db_path)

    goal = GoalSchema(
        goal_id="goal_test2",
        objective="Verify browser outcomes",
        constraints=[],
    )
    db.create_session(goal, [])

    result = BrowserResult(
        step_id=1,
        status="success",
        final_url="https://example.com/done",
        raw_html="<html><body>Done</body></html>",
        screenshot_path="/screenshot.webp",
        error_message=None,
    )

    db.save_browser_result("goal_test2", result)

    session = db.get_session("goal_test2")
    assert len(session["results"]) == 1
    assert session["results"][0]["status"] == "success"
    assert session["results"][0]["final_url"] == "https://example.com/done"


def test_orchestration_flow(temp_db_path):
    """Verify the orchestration pipeline handles states and real executions correctly."""
    engine = OrchestrationEngine(temp_db_path)

    # Stage 1 & 2: Start new run
    goal, steps = engine.start_new_run("Test Orchestration query")
    assert goal.goal_id.startswith("goal_")
    assert len(steps) >= 1

    # Stage 3: Run step
    step = steps[0]
    result = engine.run_browser_step(goal.goal_id, step)
    assert result.status in ("success", "failed", "timeout")
    assert len(result.raw_html) > 0

    # Stage 3 (Cont): Processing
    processed = engine.run_process_step(
        goal.goal_id, step.step_id, result.raw_html, "example.com"
    )
    assert processed.source_domain == "example.com"
    assert isinstance(processed.entities, dict)

    # Stage 4 & 5: Verify & finalize
    report = engine.run_verification(goal.goal_id, [processed])
    assert report.goal_id == goal.goal_id
    assert 0.0 <= report.confidence_score <= 1.0
    assert len(report.sources) >= 1

    # Check state update in database
    session = engine.db.get_session(goal.goal_id)
    assert session["status"] == "completed"
