import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.websocket_events import WSEventType
from app.models.journal import Attendance, AttendanceStatus

@pytest.mark.asyncio
async def test_whiteboard_broadcasting(
    teacher_token: str,
    student_token: str,
    active_session,
    test_student,
    db_session,
    test_db_engine
):
    """
    Test real-time whiteboard event broadcasting.
    Using TestClient for WebSocket support.
    """
    # 0. Ensure student attendance is marked for today
    from datetime import datetime
    today = datetime.utcnow().date()
    attendance = Attendance(
        student_id=test_student.id,
        class_id=active_session.class_id,
        marker_id=active_session.teacher_id,
        date=today,
        status=AttendanceStatus.PRESENT
    )
    db_session.add(attendance)
    await db_session.commit()
    
    # Override get_db to use the test engine but create a FRESH session
    # This avoids sharing the loop-bound session object while pointing to proper DB
    from app.core.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    
    async def override_get_db():
        async_session = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session
            
    app.dependency_overrides[get_db] = override_get_db
    
    ws_url = f"/api/v1/ws/sessions/{active_session.id}"
    
    # 1. Use TestClient (synchronous context manager)
    client = TestClient(app)
    
    with client.websocket_connect(f"{ws_url}?token={student_token}") as ws_student:
        with client.websocket_connect(f"{ws_url}?token={teacher_token}") as ws_teacher:
            
            # 3. Teacher sends DRAW event
            draw_payload = {
                "type": WSEventType.WHITEBOARD_DRAW,
                "payload": {
                    "x": 100, 
                    "y": 200, 
                    "color": "#FF0000", 
                    "width": 5
                }
            }
            ws_teacher.send_json(draw_payload)
            
            # 4. Student receives event
            received_draw = False
            for _ in range(5):
                try:
                    data = ws_student.receive_json()
                    if data.get("type") == WSEventType.WHITEBOARD_DRAW:
                        assert data["payload"] == draw_payload["payload"]
                        received_draw = True
                        break
                except Exception:
                    break
            
            assert received_draw, "Student did not receive DRAW event"


@pytest.mark.asyncio
async def test_whiteboard_permission_denied(
    student_token: str,
    active_session,
    test_student,
    db_session,
    test_db_engine
):
    """Test that students cannot draw on the whiteboard."""
    from datetime import datetime
    today = datetime.utcnow().date()
    attendance = Attendance(
        student_id=test_student.id,
        class_id=active_session.class_id,
        marker_id=active_session.teacher_id,
        date=today,
        status=AttendanceStatus.PRESENT
    )
    db_session.add(attendance)
    await db_session.commit()
    
    # Override get_db
    from app.core.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    
    async def override_get_db():
        async_session = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session
            
    app.dependency_overrides[get_db] = override_get_db
    
    ws_url = f"/api/v1/ws/sessions/{active_session.id}"
    
    client = TestClient(app)
    
    with client.websocket_connect(f"{ws_url}?token={student_token}") as ws_student:
        # Attempt to send DRAW event
        draw_payload = {
            "type": WSEventType.WHITEBOARD_DRAW,
            "payload": {"x": 0, "y": 0}
        }
        ws_student.send_json(draw_payload)
        
        # Should receive ERROR
        found_error = False
        for _ in range(5):
            data = ws_student.receive_json()
            if data.get("type") == WSEventType.ERROR:
                assert data["error_code"] == "PERMISSION_DENIED"
                found_error = True
                break
        
        assert found_error
