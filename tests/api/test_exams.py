"""
Exam lifecycle API tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_exam_teacher(client: AsyncClient, teacher_token_headers: dict, admin_token_headers: dict):
    """Teacher can create an exam."""
    # Setup dependencies
    # 1. Subject
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "Physics", "code": "PHYS-101"}
    )
    subject_id = subject_resp.json()["id"]
    
    # Create Exam
    response = await client.post(
        "/api/v1/exams/",
        headers=teacher_token_headers,
        json={
            "title": "Physics Midterm",
            "subject_id": subject_id,
            "duration_minutes": 60,
            "exam_type": "MIDTERM",
            "passing_score": 60.0
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Physics Midterm"
    return data["id"]


@pytest.mark.asyncio
async def test_add_questions_to_exam(client: AsyncClient, teacher_token_headers: dict, admin_token_headers: dict):
    """Teacher can add questions to an exam."""
    # 1. Subject & Exam
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "History", "code": "HIST-101"}
    )
    subject_id = subject_resp.json()["id"]
    
    exam_resp = await client.post(
        "/api/v1/exams/",
        headers=teacher_token_headers,
        json={
            "title": "History Quiz",
            "subject_id": subject_id,
            "duration_minutes": 30
        }
    )
    exam_id = exam_resp.json()["id"]
    
    # 2. Add Questions
    response = await client.post(
        f"/api/v1/exams/{exam_id}/questions",
        headers=teacher_token_headers,
        json={
            "question_type": "MULTIPLE_CHOICE",
            "text": "When was the Magna Carta signed?",
            "points": 5.0,
            "options": [
                {"id": 1, "text": "1215"},
                {"id": 2, "text": "1492"},
                {"id": 3, "text": "1776"}
            ],
            "correct_answer": "1"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "When was the Magna Carta signed?"


@pytest.mark.asyncio
async def test_start_exam_attempt(client: AsyncClient, user_token_headers: dict, teacher_token_headers: dict, admin_token_headers: dict):
    """Student can start an exam attempt."""
    # 1. Setup Exam (published)
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "Chemistry", "code": "CHEM-101"}
    )
    subject_id = subject_resp.json()["id"]
    
    exam_resp = await client.post(
        "/api/v1/exams/",
        headers=teacher_token_headers,
        json={
            "title": "Chem Final",
            "subject_id": subject_id,
            "duration_minutes": 90,
            "is_published": True  # Important
        }
    )
    exam_id = exam_resp.json()["id"]
    
    # 2. Start Attempt
    response = await client.post(
        f"/api/v1/exams/{exam_id}/start",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "attempt_id" in data
    assert "questions" in data
