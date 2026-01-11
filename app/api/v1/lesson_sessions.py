"""
API endpoints for Live Lesson Sessions (Active Classroom).
"""
from typing import Annotated, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.school import Class, Subject
from app.models.timetable import Schedule
from app.models.lesson_session import LessonSession, StudentNote, LessonSessionStatus
from app.schemas.lesson_session import (
    LessonSessionCreate,
    LessonSessionResponse,
    StudentNoteCreate,
    StudentNoteResponse,
    StudentNoteUpdate
)

router = APIRouter(tags=["Live Lessons"])


# ==================== Lesson Sessions (Teacher) ====================

@router.post("/lessons/start", response_model=LessonSessionResponse)
async def start_lesson(
    session_data: LessonSessionCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Teacher starts a lesson from the timetable schedule."""
    # Verify schedule exists and belongs to teacher
    stmt = select(Schedule).where(Schedule.id == session_data.schedule_id)
    stmt = stmt.options(selectinload(Schedule.subject), selectinload(Schedule.class_))
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if schedule.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your scheduled lesson")
    
    # Check if already active session for this schedule today?
    # For simplicity, allow multiple sessions
    
    new_session = LessonSession(
        schedule_id=session_data.schedule_id,
        teacher_id=current_user.id,
        class_id=schedule.class_id,
        subject_id=schedule.subject_id,
        topic=session_data.topic,
        status=LessonSessionStatus.ACTIVE
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Add display info
    response = LessonSessionResponse.model_validate(new_session)
    response.subject_name = schedule.subject.name if schedule.subject else None
    response.class_name = schedule.class_.name if schedule.class_ else None
    return response


@router.post("/lessons/{session_id}/end", response_model=LessonSessionResponse)
async def end_lesson(
    session_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Teacher ends the active lesson."""
    session = await db.get(LessonSession, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")
    
    session.status = LessonSessionStatus.ENDED
    session.ended_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/lessons/active", response_model=List[LessonSessionResponse])
async def get_active_lessons(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get currently active lessons for the user's class (Student view) or school (Teacher/Admin)."""
    query = select(LessonSession).where(LessonSession.status == LessonSessionStatus.ACTIVE)
    
    if current_user.role == UserRole.STUDENT:
        # Show only my class's active lesson
        if not current_user.class_id:
            return []
        query = query.where(LessonSession.class_id == current_user.class_id)
    elif current_user.role == UserRole.TEACHER:
        # Show my active lessons
        query = query.where(LessonSession.teacher_id == current_user.id)
    
    query = query.options(
        selectinload(LessonSession.subject),
        selectinload(LessonSession.class_)
    ).order_by(desc(LessonSession.started_at))
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Enrich with display info
    responses = []
    for s in sessions:
        resp = LessonSessionResponse.model_validate(s)
        resp.subject_name = s.subject.name if s.subject else None
        resp.class_name = s.class_.name if s.class_ else None
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
):
    """Student gets all their notes, optionally filtered by subject."""
    query = select(StudentNote).where(StudentNote.student_id == current_user.id)
    
    if subject_id:
        # Join to filter by subject? Need to join through lesson_session
        query = query.join(LessonSession).where(LessonSession.subject_id == subject_id)
    
    query = query.order_by(desc(StudentNote.created_at))
    
    result = await db.execute(query)
    return result.scalars().all()
