"""
API endpoints for Digital Journal (Attendance and Grading).
"""
from typing import Annotated, List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.school import Class, Subject
from app.models.journal import Attendance, Grade, AttendanceStatus, GradeType
from app.schemas.journal import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    BulkAttendanceCreate,
    GradeCreate,
    GradeResponse,
    GradeUpdate,
    StudentJournalEntry
)

router = APIRouter(tags=["Journal (Attendance & Grades)"])


# ==================== Attendance ====================

@router.post("/attendance/bulk", response_model=List[AttendanceResponse])
async def mark_bulk_attendance(
    attendance_data: BulkAttendanceCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER, UserRole.SCHOOL_ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark attendance for multiple students in a class."""
    # Teacher can only mark for own school
    if current_user.role == UserRole.TEACHER:
        if current_user.school_id is None: # Should not happen, but safe check
             raise HTTPException(status_code=400, detail="Teacher must be assigned to a school")
        
        # Verify class belongs to teacher's school (basic check)
        # Ideally, check if teacher teaches this class, but for MVP school-level check is okay
        class_result = await db.execute(select(Class).where(Class.id == attendance_data.class_id))
        class_obj = class_result.scalar_one_or_none()
        if not class_obj or class_obj.school_id != current_user.school_id:
             raise HTTPException(status_code=403, detail="Cannot mark attendance for this class")

    created_records = []
    
    for item in attendance_data.items:
        # Check if attendance already exists for this student on this date
        stmt = select(Attendance).where(
            Attendance.student_id == item.student_id,
            Attendance.date == attendance_data.date
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.status = item.status
            existing.remarks = item.remarks
            existing.marker_id = current_user.id
            created_records.append(existing)
        else:
            # Create new
            new_record = Attendance(
                date=attendance_data.date,
                student_id=item.student_id,
                class_id=attendance_data.class_id,
                marker_id=current_user.id,
                status=item.status,
                remarks=item.remarks
            )
            db.add(new_record)
            created_records.append(new_record)
    
    await db.commit()
    for record in created_records:
        await db.refresh(record)
        
    return created_records


@router.get("/attendance/{class_id}", response_model=List[AttendanceResponse])
async def get_class_attendance(
    class_id: int,
    date_from: date,
    date_to: date,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get attendance records for a class within a date range."""
    query = select(Attendance).where(
        Attendance.class_id == class_id,
        Attendance.date >= date_from,
        Attendance.date <= date_to
    ).order_by(Attendance.date, Attendance.student_id)
    
    result = await db.execute(query)
    return result.scalars().all()


# ==================== Grades ====================

@router.post("/grades/", response_model=GradeResponse)
async def create_grade(
    grade_data: GradeCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER, UserRole.SCHOOL_ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Assign a grade to a student."""
    # Verify student exists and belongs to correct context (omitted for brevity, can add later)
    
    new_grade = Grade(
        **grade_data.model_dump(),
        teacher_id=current_user.id
    )
    db.add(new_grade)
    await db.commit()
    await db.refresh(new_grade)
    return new_grade


@router.get("/journal/{class_id}/{subject_id}", response_model=List[StudentJournalEntry])
async def get_class_journal(
    class_id: int,
    subject_id: int,
    date_from: date,
    date_to: date,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get aggregated journal view for a class and subject.
    Returns list of daily entries for each student in the class.
    Note: For a real grid view, frontend usually usually expects: 
    [ { student: ..., data: { date1: {att...}, date2: {grade...} } } ]
    But here we return a flat list of daily summaries per student.
    """
    # 1. Get all students in the class
    students_query = select(User).where(
        User.class_id == class_id, 
        User.role == UserRole.STUDENT
    ).order_by(User.last_name, User.first_name)
    students_result = await db.execute(students_query)
    students = students_result.scalars().all()
    
    # 2. Get attendance for the date range
    att_query = select(Attendance).where(
        Attendance.class_id == class_id,
        Attendance.date >= date_from,
        Attendance.date <= date_to
    )
    att_result = await db.execute(att_query)
    attendance_records = att_result.scalars().all()
    
    # Map attendance by (student_id, date) -> record
    att_map = {(r.student_id, r.date): r for r in attendance_records}

    # 3. Get grades for the date range
    grade_query = select(Grade).where(
        Grade.subject_id == subject_id,
        Grade.student_id.in_([s.id for s in students]) if students else False,
        Grade.date >= date_from,
        Grade.date <= date_to
    )
    grade_result = await db.execute(grade_query)
    grade_records = grade_result.scalars().all()
    
    # Map grades by (student_id, date) -> list of grades
    grade_map = {}
    for g in grade_records:
        key = (g.student_id, g.date)
        if key not in grade_map:
            grade_map[key] = []
        grade_map[key].append(g)

    # 4. Construct response
    journal_entries = []
    
    # We iterate through each date in the range
    from datetime import timedelta
    
    current_date = date_from
    while current_date <= date_to:
        for student in students:
            # Check for data
            attendance = att_map.get((student.id, current_date))
            grades = grade_map.get((student.id, current_date), [])
            
            # If we have data, add an entry
            if attendance or grades:
                entry = StudentJournalEntry(
                    date=current_date,
                    student_id=student.id,
                    student_name=f"{student.last_name} {student.first_name}",
                    attendance=AttendanceResponse.model_validate(attendance) if attendance else None,
                    grades=[GradeResponse.model_validate(g) for g in grades]
                )
                journal_entries.append(entry)
        
        current_date += timedelta(days=1)
    
    return journal_entries


@router.get("/grades/student/{student_id}", response_model=List[GradeResponse])
async def get_student_grades(
    student_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_id: Optional[int] = None,
):
    """Get grades for a specific student."""
    query = select(Grade).where(Grade.student_id == student_id)
    
    if subject_id:
        query = query.where(Grade.subject_id == subject_id)
        
    query = query.order_by(Grade.date.desc())
    
    result = await db.execute(query)
    return result.scalars().all()
