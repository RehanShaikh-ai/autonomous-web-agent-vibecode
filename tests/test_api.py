import pytest
from fastapi.testclient import TestClient
from backend.integration.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify GET /api/v1/health returns 200 OK and expected services."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data["services"]


def test_plan_endpoint_success():
    """Verify POST /api/v1/plan successfully compiles goals and steps."""
    payload = {"query": "Find scholarships for engineering students", "max_steps": 3}
    response = client.post("/api/v1/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "goal_id" in data
    assert data["structured_goal"]["objective"] == "Find scholarships for engineering students"
    assert len(data["steps"]) <= 3


def test_plan_endpoint_empty_query():
    """Verify POST /api/v1/plan rejects blank queries with 400 Bad Request."""
    response = client.post("/api/v1/plan", json={"query": "   "})
    assert response.status_code == 400


def test_browse_endpoint():
    """Verify POST /api/v1/browse executes single step."""
    payload = {
        "goal_id": "goal_test_browse",
        "step": {
            "step_id": 1,
            "action": "navigate",
            "url": "https://example.com",
            "description": "Navigate to example page",
        },
    }
    response = client.post("/api/v1/browse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["step_id"] == 1
    assert data["status"] in ("success", "failed", "timeout")


def test_process_endpoint():
    """Verify POST /api/v1/process cleans DOM and extracts entities."""
    payload = {
        "goal_id": "goal_test_process",
        "step_id": 1,
        "raw_html": "<html><body><div>Scholarship: $5,000</div></body></html>",
        "source_domain": "scholarships.com",
    }
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["step_id"] == 1
    assert data["source_domain"] == "scholarships.com"


def test_verify_endpoint():
    """Verify POST /api/v1/verify delivers final confidence report."""
    payload = {
        "goal_id": "goal_test_verify",
        "extracted_data": [
            {
                "source": "scholarships.com",
                "entities": {"amount": "$5,000", "deadline": "May 1"},
            }
        ],
    }
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == "goal_test_verify"
    assert 0.0 <= data["confidence_score"] <= 1.0
    assert len(data["sources"]) >= 1


def test_execute_mission_endpoint():
    """Verify POST /api/v1/execute runs complete autonomous mission end-to-end."""
    payload = {"query": "Compare M3 MacBook Air prices", "max_steps": 2}
    response = client.post("/api/v1/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "goal_id" in data
    assert 0.0 <= data["confidence_score"] <= 1.0
    assert len(data["comparison_table"]) >= 1


def test_sessions_listing_and_detail_endpoints():
    """Verify GET /api/v1/sessions and GET /api/v1/sessions/{goal_id}."""
    # Run a quick plan to ensure at least one session exists
    plan_res = client.post("/api/v1/plan", json={"query": "Test session lookup query"})
    goal_id = plan_res.json()["goal_id"]

    # Test list endpoint
    list_res = client.get("/api/v1/sessions")
    assert list_res.status_code == 200
    assert any(s["goal_id"] == goal_id for s in list_res.json())

    # Test detail endpoint
    detail_res = client.get(f"/api/v1/sessions/{goal_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["goal_id"] == goal_id

    # Test 404 for unknown session
    not_found_res = client.get("/api/v1/sessions/goal_nonexistent_xyz")
    assert not_found_res.status_code == 404
