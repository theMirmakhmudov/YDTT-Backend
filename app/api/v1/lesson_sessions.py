"""
API endpoints for Live Lesson Sessions (Active Classroom).
"""
from typing import Annotated, List, Optional
from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser, require_session_access
from app.core.websocket import manager
from app.models.user import User, UserRole
from app.models.school import Class, Subject
from app.models.timetable import Schedule
from app.models.lesson_session import LessonSession, StudentNote, LessonSessionStatus
from app.models.session_attendance import SessionAttendance
from app.schemas.lesson_session import (
    LessonSessionCreate,
    LessonSessionResponse,
    StudentNoteCreate,
    StudentNoteResponse,
    StudentNoteUpdate
)
from app.schemas.websocket_events import WSEventType, WSSessionEvent, WSParticipantEvent

router = APIRouter(tags=["Live Lessons"])


# ==================== Lesson Sessions (Teacher) ====================

@router.post("/sessions/start", response_model=LessonSessionResponse)
async def start_session(
    session_data: LessonSessionCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Teacher starts a live lesson session.
    
    Business Rules:
    - Only assigned teacher can start
    - Only one active session per schedule at a time
    - Auto-creates session if not exists, or activates pending session
    """
    # Verify schedule exists and belongs to teacher
    stmt = select(Schedule).where(Schedule.id == session_data.schedule_id)
    stmt = stmt.options(selectinload(Schedule.subject), selectinload(Schedule.class_))
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if schedule.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your scheduled lesson")
    
    # Check for existing active session
    existing_stmt = select(LessonSession).where(
        and_(
            LessonSession.schedule_id == session_data.schedule_id,
            LessonSession.status == LessonSessionStatus.ACTIVE
        )
    )
    existing_res = await db.execute(existing_stmt)
    existing_session = existing_res.scalar_one_or_none()
    
    if existing_session:
        raise HTTPException(
            status_code=400,
            detail="An active session already exists for this schedule"
        )
    
    # Create or activate session
    new_session = LessonSession(
        schedule_id=session_data.schedule_id,
        teacher_id=current_user.id,
        class_id=schedule.class_id,
        subject_id=schedule.subject_id,
        topic=session_data.topic,
        status=LessonSessionStatus.ACTIVE,
        started_at=datetime.utcnow()
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Broadcast session started event via WebSocket
    session_event = WSSessionEvent(
        type=WSEventType.SESSION_STARTED,
        session_id=new_session.id,
        teacher_id=current_user.id,
        teacher_name=current_user.full_name,
        subject_name=schedule.subject.name if schedule.subject else None,
        class_name=schedule.class_.name if schedule.class_ else None
    )
    await manager.broadcast_to_session(
        new_session.id,
        session_event.model_dump(mode='json')
    )
    
    # Add display info
    response = LessonSessionResponse.model_validate(new_session)
    response.subject_name = schedule.subject.name if schedule.subject else None
    response.class_name = schedule.class_.name if schedule.class_ else None
    return response


@router.post("/sessions/{session_id}/join", response_model=LessonSessionResponse)
async def join_session(
    session_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Student joins a live session.
    Automatically creates attendance record.
    """
    session = await db.get(LessonSession, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != LessonSessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Verify student belongs to session's class
    if current_user.class_id != session.class_id:
        raise HTTPException(status_code=403, detail="Not your class session")
    
    # Check if already joined
    existing_attendance = await db.execute(
        select(SessionAttendance).where(
            and_(
                SessionAttendance.session_id == session_id,
                SessionAttendance.student_id == current_user.id
            )
        )
    )
    attendance = existing_attendance.scalar_one_or_none()
    
    if not attendance:
        # Create attendance record (auto-mark present)
        attendance = SessionAttendance(
            session_id=session_id,
            student_id=current_user.id,
            joined_at=datetime.utcnow()
        )
        db.add(attendance)
        await db.commit()
    
    # Load session with relationships
    await db.refresh(session)
    stmt = select(LessonSession).where(LessonSession.id == session_id)
    stmt = stmt.options(selectinload(LessonSession.subject), selectinload(LessonSession.class_))
    result = await db.execute(stmt)
    session = result.scalar_one()
    
    # Build response
    response = LessonSessionResponse.model_validate(session)
    response.subject_name = session.subject.name if session.subject else None
    response.class_name = session.class_.name if session.class_ else None
    
    return response


@router.post("/sessions/{session_id}/end", response_model=LessonSessionResponse)
async def end_session(
    session_id: int,
    session: Annotated[LessonSession, Depends(require_session_access)],
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Teacher ends the active session."""
    # RBAC check handled by dependency: checks if teacher owns the session
    
    session.status = LessonSessionStatus.ENDED
    session.ended_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    # Broadcast session ended event
    session_event = WSSessionEvent(
        type=WSEventType.SESSION_ENDED,
        session_id=session.id,
        teacher_id=current_user.id,
        teacher_name=current_user.full_name
    )
    await manager.broadcast_to_session(
        session.id,
        session_event.model_dump(mode='json')
    )
    
    return session


@router.post("/sessions/{session_id}/cancel", response_model=LessonSessionResponse)
async def cancel_session(
    session_id: int,
    session: Annotated[LessonSession, Depends(require_session_access)],
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Teacher cancels a session."""
    # RBAC check handled by dependency
    
    if session.status == LessonSessionStatus.ENDED:
        raise HTTPException(status_code=400, detail="Cannot cancel ended session")
    
    session.status = LessonSessionStatus.CANCELLED
    session.ended_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    # Broadcast cancellation event
    session_event = WSSessionEvent(
        type=WSEventType.SESSION_CANCELLED,
        session_id=session.id,
        teacher_id=current_user.id,
        teacher_name=current_user.full_name
    )
    await manager.broadcast_to_session(
        session.id,
        session_event.model_dump(mode='json')
    )
    
    return session


@router.get("/sessions/active", response_model=List[LessonSessionResponse])
async def get_active_sessions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get currently active sessions.
    - Students: see their class's active session
    - Teachers: see their active sessions
    """
    query = select(LessonSession).where(LessonSession.status == LessonSessionStatus.ACTIVE)
    
    if current_user.role == UserRole.STUDENT:
        # Show only my class's active session
        if not current_user.class_id:
            return []
        query = query.where(LessonSession.class_id == current_user.class_id)
    elif current_user.role == UserRole.TEACHER:
        # Show my active sessions
        query = query.where(LessonSession.teacher_id == current_user.id)
    
    query = query.options(
        selectinload(LessonSession.subject),
        selectinload(LessonSession.class_)
    ).order_by(desc(LessonSession.started_at))
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Enrich with display info and participant count
    responses = []
    for s in sessions:
        resp = LessonSessionResponse.model_validate(s)
        resp.subject_name = s.subject.name if s.subject else None
        resp.class_name = s.class_.name if s.class_ else None
        
        # Get participant count from attendance
        count_stmt = select(func.count(SessionAttendance.id)).where(
            SessionAttendance.session_id == s.id
        )
        count_result = await db.execute(count_stmt)
        resp.participant_count = count_result.scalar() or 0
        
        responses.append(resp)
    
    return responses


# ==================== Student Notes ====================

@router.post("/notes/", response_model=StudentNoteResponse)
async def create_note(
    note_data: StudentNoteCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Student creates/updates a note during a lesson."""
    # Verify lesson session is active
    session = await db.get(LessonSession, note_data.lesson_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Lesson session not found")
    
    if session.class_id != current_user.class_id:
        raise HTTPException(status_code=403, detail="Not your class's lesson")
    
    # Check if student already has a note for this session
    stmt = select(StudentNote).where(
        StudentNote.lesson_session_id == note_data.lesson_session_id,
        StudentNote.student_id == current_user.id
    )
    res = await db.execute(stmt)
    existing_note = res.scalar_one_or_none()
    
    if existing_note:
        # Update existing
        existing_note.content = note_data.content
        existing_note.attachment_url = note_data.attachment_url
        existing_note.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_note)
        return existing_note
    
    # Create new
    new_note = StudentNote(
        **note_data.model_dump(),
        student_id=current_user.id
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note


@router.get("/notes/session/{session_id}", response_model=List[StudentNoteResponse])
async def get_session_notes(
    session_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get notes for a lesson session. Students see their own, teachers see all."""
    query = select(StudentNote).where(StudentNote.lesson_session_id == session_id)
    
    if current_user.role == UserRole.STUDENT:
        query = query.where(StudentNote.student_id == current_user.id)
    
    query = query.order_by(StudentNote.created_at)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/notes/my", response_model=List[StudentNoteResponse])
async def get_my_notes(
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    q: Optional[str] = None,
):
    """
    Student gets all their notes.
    Filters:
    - subject_id: Filter by subject
    - start_date/end_date: Filter by creation date range
    - q: Keyword search in content or topic
    """
    query = select(StudentNote).where(StudentNote.student_id == current_user.id)
    
    if subject_id:
        query = query.join(LessonSession).where(LessonSession.subject_id == subject_id)
        
    if start_date:
        query = query.where(StudentNote.created_at >= start_date)
        
    if end_date:
        query = query.where(StudentNote.created_at <= end_date)
        
    if q:
        # If not already joined
        if not subject_id:
             query = query.join(LessonSession)
        
        search_term = f"%{q}%"
        query = query.where(
            (StudentNote.content.ilike(search_term)) | 
            (LessonSession.topic.ilike(search_term))
        )
    
    query = query.order_by(desc(StudentNote.created_at))
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/notes/{note_id}/export")
async def export_note(
    note_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Export a note as a downloadable text file.
    """
    stmt = select(StudentNote).where(
        StudentNote.id == note_id,
        StudentNote.student_id == current_user.id
    )
    stmt = stmt.options(selectinload(StudentNote.lesson_session).options(selectinload(LessonSession.subject)))
    res = await db.execute(stmt)
    note = res.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Format content
    subject_name = note.lesson_session.subject.name if note.lesson_session.subject else "Unknown Subject"
    topic = note.lesson_session.topic or "No Topic"
    date_str = note.created_at.strftime("%Y-%m-%d")
    
    file_content = f"""Subject: {subject_name}
Date: {date_str}
Topic: {topic}
----------------------------------------

{note.content}
"""
    
    from fastapi.responses import Response
    return Response(
        content=file_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="note_{note_id}_{date_str}.txt"'
        }
    )
