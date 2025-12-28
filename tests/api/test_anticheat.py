"""
Anti-cheating API tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_log_cheating_event(client: AsyncClient, user_token_headers: dict, teacher_token_headers: dict, admin_token_headers: dict):
    """Student logs a cheating event (e.g. app exit)."""
    # 1. Setup Exam & Attempt
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "Biology", "code": "BIO-101"}
    )
    subject_id = subject_resp.json()["id"]
    
    exam_resp = await client.post(
        "/api/v1/exams/",
        headers=teacher_token_headers,
        json={"title": "Bio Quiz", "subject_id": subject_id, "duration_minutes": 20, "is_published": True}
    )
    exam_id = exam_resp.json()["id"]
    
    attempt_resp = await client.post(
        f"/api/v1/exams/{exam_id}/start",
        headers=user_token_headers
    )
    attempt_id = attempt_resp.json()["attempt_id"]
    
    # 2. Log Event
    response = await client.post(
        "/api/v1/anti-cheat/event",
        headers=user_token_headers,
        json={
            "attempt_id": attempt_id,
            "event_type": "app_exit",
            "occurred_at": "2024-01-01T12:00:00Z",
            "metadata": {"reason": "Home button pressed"}
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "app_exit"


@pytest.mark.asyncio
async def test_get_cheating_report(client: AsyncClient, teacher_token_headers: dict, user_token_headers: dict, admin_token_headers: dict):
    """Teacher can view cheating report."""
    # Setup similar to above
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "Math", "code": "MATH-202"}
    )
    subject_id = subject_resp.json()["id"]
    
    exam_resp = await client.post(
        "/api/v1/exams/",
        headers=teacher_token_headers,
        json={"title": "Math Quiz", "subject_id": subject_id, "duration_minutes": 20, "is_published": True}
    )
    exam_id = exam_resp.json()["id"]
    
    attempt_resp = await client.post(
        f"/api/v1/exams/{exam_id}/start",
        headers=user_token_headers
    )
    attempt_id = attempt_resp.json()["attempt_id"]
    
    # Get Report
    response = await client.get(
        f"/api/v1/anti-cheat/report/{attempt_id}",
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] >= 0
