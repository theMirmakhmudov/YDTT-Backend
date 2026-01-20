"""
Tests for Session-Based Lesson API.
Tests session lifecycle, auto-attendance, and WebSocket integration.
"""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.lesson_session import LessonSession, LessonSessionStatus
from app.models.session_attendance import SessionAttendance
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_teacher_start_session(
    client: AsyncClient,
    teacher_token: str,
    db_session: AsyncSession,
    test_schedule
):
    """Test that teacher can start a session."""
    response = await client.post(
        "/api/v1/sessions/start",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "schedule_id": test_schedule.id,
            "topic": "Introduction to Fractions"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ACTIVE"
    assert data["topic"] == "Introduction to Fractions"
    assert data["teacher_id"] == test_schedule.teacher_id
    assert "subject_name" in data
    assert "class_name" in data


@pytest.mark.asyncio
async def test_prevent_duplicate_active_sessions(
    client: AsyncClient,
    teacher_token: str,
    test_schedule,
    active_session
):
    """Test that only one active session per schedule is allowed."""
    response = await client.post(
        "/api/v1/sessions/start",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "schedule_id": test_schedule.id,
            "topic": "Another Topic"
        }
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_student_join_session_auto_attendance(
    client: AsyncClient,
    student_token: str,
    db_session: AsyncSession,
    active_session,
    test_student
):
    """Test that joining session automatically creates attendance record."""
    response = await client.post(
        f"/api/v1/sessions/{active_session.id}/join",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == active_session.id
    
    # Verify attendance record created
    attendance = await db_session.execute(
        select(SessionAttendance).where(
            SessionAttendance.session_id == active_session.id,
            SessionAttendance.student_id == test_student.id
        )
    )
    attendance_record = attendance.scalar_one_or_none()
    
    assert attendance_record is not None
    assert attendance_record.joined_at is not None
    assert attendance_record.left_at is None


@pytest.mark.asyncio
async def test_student_cannot_join_other_class_session(
    client: AsyncClient,
    student_token: str,
    session_different_class
):
    """Test that student cannot join session from different class."""
    response = await client.post(
        f"/api/v1/sessions/{session_different_class.id}/join",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403
    assert "not your class" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_teacher_end_session(
    client: AsyncClient,
    teacher_token: str,
    db_session: AsyncSession,
    active_session
):
    """Test that teacher can end a session."""
    response = await client.post(
        f"/api/v1/sessions/{active_session.id}/end",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ENDED"
    assert data["ended_at"] is not None
    
    # Verify in database
    await db_session.refresh(active_session)
    assert active_session.status == LessonSessionStatus.ENDED


@pytest.mark.asyncio
async def test_teacher_cancel_session(
    client: AsyncClient,
    teacher_token: str,
    db_session: AsyncSession,
    active_session
):
    """Test that teacher can cancel a session."""
    response = await client.post(
        f"/api/v1/sessions/{active_session.id}/cancel",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "CANCELLED"
    assert data["ended_at"] is not None


@pytest.mark.asyncio
async def test_get_active_sessions_student(
    client: AsyncClient,
    student_token: str,
    active_session,
    test_student
):
    """Test that student sees their class's active session."""
    response = await client.get(
        "/api/v1/sessions/active",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 1
    assert any(s["id"] == active_session.id for s in data)


@pytest.mark.asyncio
async def test_get_active_sessions_teacher(
    client: AsyncClient,
    teacher_token: str,
    active_session
):
    """Test that teacher sees their active sessions."""
    response = await client.get(
        "/api/v1/sessions/active",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 1
    session = next(s for s in data if s["id"] == active_session.id)
    assert "participant_count" in session


@pytest.mark.asyncio
async def test_session_lifecycle_complete_flow(
    client: AsyncClient,
    teacher_token: str,
    student_token: str,
    db_session: AsyncSession,
    test_schedule,
    test_student
):
    """Test complete session lifecycle from start to end."""
    # 1. Teacher starts session
    start_response = await client.post(
        "/api/v1/sessions/start",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"schedule_id": test_schedule.id, "topic": "Complete Flow Test"}
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["id"]
    
    # 2. Student joins session
    join_response = await client.post(
        f"/api/v1/sessions/{session_id}/join",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert join_response.status_code == 200
    
    # 3. Verify attendance created
    attendance = await db_session.execute(
        select(SessionAttendance).where(
            SessionAttendance.session_id == session_id,
            SessionAttendance.student_id == test_student.id
        )
    )
    assert attendance.scalar_one_or_none() is not None
    
    # 4. Teacher ends session
    end_response = await client.post(
        f"/api/v1/sessions/{session_id}/end",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert end_response.status_code == 200
    assert end_response.json()["status"] == "ENDED"
