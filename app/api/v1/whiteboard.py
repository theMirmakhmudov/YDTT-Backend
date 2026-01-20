"""
API endpoints for Whiteboard functionality.
Teacher-only drawing with real-time student viewing.
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser, require_session_access
from app.models.user import User, UserRole
from app.models.lesson_session import LessonSession, LessonSessionStatus
from app.models.whiteboard import WhiteboardEvent, WhiteboardEventType
from app.schemas.whiteboard import (
    WhiteboardEventCreate,
    WhiteboardEventResponse,
    WhiteboardStateResponse
)

router = APIRouter(tags=["Whiteboard"])


@router.get("/sessions/{session_id}/whiteboard", response_model=WhiteboardStateResponse)
async def get_whiteboard_state(
    session_id: int,
    session: Annotated[LessonSession, Depends(require_session_access)],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get complete whiteboard state for a session.
    Used for state recovery when student joins mid-session.
    """
    # RBAC check handled by dependency
    
    # Get all whiteboard events for session, ordered by time
    stmt = select(WhiteboardEvent).where(
        WhiteboardEvent.session_id == session_id
    ).order_by(WhiteboardEvent.created_at)
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    # Build response
    event_responses = [
        WhiteboardEventResponse.model_validate(event)
        for event in events
    ]
    
    return WhiteboardStateResponse(
        session_id=session_id,
        events=event_responses,
        total_events=len(event_responses)
    )


@router.post("/sessions/{session_id}/whiteboard/clear")
async def clear_whiteboard(
    session_id: int,
    session: Annotated[LessonSession, Depends(require_session_access)],
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Clear the whiteboard.
    Teacher-only endpoint.
    """
    # RBAC check handled by dependencies (Teacher role + Session access)
    
    if session.status != LessonSessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Create clear event
    clear_event = WhiteboardEvent(
        session_id=session_id,
        created_by_id=current_user.id,
        event_type=WhiteboardEventType.CLEAR,
        payload={}
    )
    db.add(clear_event)
    await db.commit()
    
    return {"message": "Whiteboard cleared", "session_id": session_id}
