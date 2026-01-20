"""
WebSocket API endpoint for Live Lesson Sessions.
Real-time communication between teachers and students.
"""
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.websocket import manager
from app.core.security import verify_access_token
from app.models.lesson_session import LessonSession, LessonSessionStatus
from app.models.user import User, UserRole
from app.models.whiteboard import WhiteboardEvent, WhiteboardEventType
from app.schemas.websocket_events import (
    WSEventType,
    WSSessionEvent,
    WSParticipantEvent,
    WSWhiteboardEvent,
    WSTeacherPresenceEvent,
    WSErrorEvent,
    WSPingPongEvent
)

import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


async def get_current_user_ws(
    token: str,
    db: AsyncSession
) -> User:
    """
    Authenticate WebSocket connection using JWT token.
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = await db.get(User, int(user_id))
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.websocket("/ws/sessions/{session_id}")
async def websocket_session_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(..., description="JWT access token"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for live lesson sessions.
    
    Handles real-time communication for:
    - Whiteboard events (teacher → students)
    - Session lifecycle events
    - Participant join/leave notifications
    - Teacher presence heartbeat
    
    Args:
        websocket: WebSocket connection
        session_id: Lesson session ID
        token: JWT access token for authentication
        db: Database session
    """
    try:
        # Authenticate user
        current_user = await get_current_user_ws(token, db)
        
        # Verify session exists and is active
        session = await db.get(LessonSession, session_id)
        
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return
        
        if session.status not in [LessonSessionStatus.ACTIVE, LessonSessionStatus.PENDING]:
            await websocket.close(code=4003, reason="Session not active")
            return
        
        # Verify user has access to session
        if current_user.role == UserRole.STUDENT:
            if current_user.class_id != session.class_id:
                await websocket.close(code=4003, reason="Not your class session")
                return

            # CHECK DAILY ATTENDANCE
            # Student must be PRESENT or LATE or EXCUSED for today to join online session
            today = datetime.utcnow().date()
            from app.models.journal import Attendance, AttendanceStatus
            
            attendance_query = select(Attendance).where(
                Attendance.student_id == current_user.id,
                Attendance.date == today
            )
            result = await db.execute(attendance_query)
            daily_attendance = result.scalar_one_or_none()
            
            if not daily_attendance:
                # If no record found, assume they haven't arrived at school yet
                await websocket.close(code=4003, reason="School attendance not marked yet")
                return
                
            if daily_attendance.status == AttendanceStatus.ABSENT:
                await websocket.close(code=4003, reason="You are marked ABSENT today")
                return

        elif current_user.role == UserRole.TEACHER:
            if current_user.id != session.teacher_id:
                await websocket.close(code=4003, reason="Not your session")
                return
        
        # Connect to session room
        await manager.connect(websocket, session_id, current_user.id)
        
        # Notify others about participant join
        if current_user.role == UserRole.STUDENT:
            join_event = WSParticipantEvent(
                type=WSEventType.STUDENT_JOINED,
                session_id=session_id,
                student_id=current_user.id,
                student_name=current_user.full_name
            )
            await manager.broadcast_to_all_except_sender(
                websocket,
                join_event.model_dump(mode='json')
            )
        
        # Main message loop
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                event_type = data.get("type")
                
                # Handle PING/PONG
                if event_type == WSEventType.PING:
                    pong = WSPingPongEvent(type=WSEventType.PONG)
                    await manager.send_personal_message(
                        pong.model_dump(mode='json'),
                        websocket
                    )
                    continue
                
                # Handle teacher presence heartbeat
                if event_type == WSEventType.TEACHER_PRESENCE:
                    if current_user.role == UserRole.TEACHER:
                        presence_event = WSTeacherPresenceEvent(
                            type=WSEventType.TEACHER_PRESENCE,
                            session_id=session_id,
                            teacher_id=current_user.id,
                            is_online=True
                        )
                        await manager.broadcast_to_all_except_sender(
                            websocket,
                            presence_event.model_dump(mode='json')
                        )
                    continue
                
                # Handle whiteboard events (teacher only)
                if event_type in [
                    WSEventType.WHITEBOARD_DRAW,
                    WSEventType.WHITEBOARD_ERASE,
                    WSEventType.WHITEBOARD_CLEAR
                ]:
                    if current_user.role != UserRole.TEACHER:
                        error_event = WSErrorEvent(
                            type=WSEventType.ERROR,
                            session_id=session_id,
                            error_code="PERMISSION_DENIED",
                            error_message="Only teachers can draw on whiteboard"
                        )
                        await manager.send_personal_message(
                            error_event.model_dump(mode='json'),
                            websocket
                        )
                        continue
                    
                    # Persist whiteboard event to database
                    wb_event_type = {
                        WSEventType.WHITEBOARD_DRAW: WhiteboardEventType.DRAW,
                        WSEventType.WHITEBOARD_ERASE: WhiteboardEventType.ERASE,
                        WSEventType.WHITEBOARD_CLEAR: WhiteboardEventType.CLEAR
                    }[event_type]
                    
                    wb_event = WhiteboardEvent(
                        session_id=session_id,
                        created_by_id=current_user.id,
                        event_type=wb_event_type,
                        payload=data.get("payload", {})
                    )
                    db.add(wb_event)
                    await db.commit()
                    
                    # Broadcast to all students
                    ws_event = WSWhiteboardEvent(
                        type=event_type,
                        session_id=session_id,
                        payload=data.get("payload", {}),
                        created_by_id=current_user.id
                    )
                    await manager.broadcast_to_all_except_sender(
                        websocket,
                        ws_event.model_dump(mode='json')
                    )
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {current_user.id} in session {session_id}")
        
    except HTTPException as e:
        logger.error(f"Authentication error: {e.detail}")
        await websocket.close(code=4001, reason=e.detail)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        # Clean up connection
        manager.disconnect(websocket)
        
        # Notify others about participant leave
        if current_user and current_user.role == UserRole.STUDENT:
            leave_event = WSParticipantEvent(
                type=WSEventType.STUDENT_LEFT,
                session_id=session_id,
                student_id=current_user.id,
                student_name=current_user.full_name
            )
            await manager.broadcast_to_session(
                session_id,
                leave_event.model_dump(mode='json')
            )
