"""
API endpoints for Digital Timetable.
"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.school import School, Class, Subject
from app.models.timetable import TimeSlot, Schedule, DayOfWeek
from app.schemas.timetable import (
    TimeSlotCreate,
    TimeSlotResponse,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
    WeeklyTimetableResponse,
    DailySchedule
)

router = APIRouter(tags=["Timetable"])


# ==================== Time Slots ====================

@router.post("/timeslots/", response_model=TimeSlotResponse)
async def create_time_slot(
    slot_data: TimeSlotCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.SCHOOL_ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a time slot for the school."""
    # Ensure order is unique for school? Or just trust admin?
    # Create
    new_slot = TimeSlot(
        **slot_data.model_dump(),
        school_id=current_user.school_id
    )
    db.add(new_slot)
    await db.commit()
    await db.refresh(new_slot)
    return new_slot


@router.get("/timeslots/", response_model=List[TimeSlotResponse])
async def list_time_slots(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List time slots for the current school."""
    query = select(TimeSlot).where(TimeSlot.school_id == current_user.school_id).order_by(TimeSlot.order)
    result = await db.execute(query)
    return result.scalars().all()


# ==================== Schedule ====================

@router.post("/schedules/", response_model=ScheduleResponse)
async def create_schedule_entry(
    schedule_data: ScheduleCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.SCHOOL_ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a schedule entry (assign class/subject/teacher to a slot)."""
    # 1. Verify Class belongs to school
    class_res = await db.execute(select(Class).where(Class.id == schedule_data.class_id))
    cls = class_res.scalar_one_or_none()
    if not cls or cls.school_id != current_user.school_id:
        raise HTTPException(status_code=400, detail="Invalid class")

    # 2. Check for conflicts
    # A. Class is busy at this time?
    conflict_class = await db.execute(select(Schedule).where(
        Schedule.class_id == schedule_data.class_id,
        Schedule.day_of_week == schedule_data.day_of_week,
        Schedule.time_slot_id == schedule_data.time_slot_id
    ))
    if conflict_class.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Class already has a lesson at this time")

    # B. Teacher is busy at this time?
    conflict_teacher = await db.execute(select(Schedule).where(
        Schedule.teacher_id == schedule_data.teacher_id,
        Schedule.day_of_week == schedule_data.day_of_week,
        Schedule.time_slot_id == schedule_data.time_slot_id
    ))
    if conflict_teacher.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Teacher is busy at this time")
         
    new_schedule = Schedule(
        **schedule_data.model_dump(),
        school_id=current_user.school_id
    )
    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)
    return new_schedule


@router.get("/timetable/class/{class_id}", response_model=WeeklyTimetableResponse)
async def get_class_timetable(
    class_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get weekly timetable for a class."""
    # Fetch all schedule entries
    query = select(Schedule).where(Schedule.class_id == class_id)
    # Join to get details
    # Eager load relationships
    # query = query.options(selectinload(Schedule.subject), selectinload(Schedule.teacher), selectinload(Schedule.time_slot))
    # For now, explicit load not strictly needed if lazy loading works or we format manually?
    # Async sqlalchemy requires explicit eager loading to avoid errors usually.
    # Let's simple fetch and rely on implicit fetching if session active, OR join.
    
    # Proper eager loading
    from sqlalchemy.orm import selectinload
    query = query.options(
        selectinload(Schedule.subject),
        selectinload(Schedule.teacher),
        selectinload(Schedule.time_slot)
    )
    
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    # Group by Day
    days_map = {day: [] for day in DayOfWeek}
    
    for sch in schedules:
        # Populate display fields for response
        # Using model_validate is cleaner, but we need to inject extra fields
        # ScheduleResponse has: subject_name, teacher_name, start_time, end_time
        
        # We can construct Pydantic obj manually or use validation
        # Let's map it manually to match response schema
        resp = ScheduleResponse(
            id=sch.id,
            school_id=sch.school_id,
            class_id=sch.class_id,
            subject_id=sch.subject_id,
            teacher_id=sch.teacher_id,
            time_slot_id=sch.time_slot_id,
            day_of_week=sch.day_of_week,
            room_number=sch.room_number,
            subject_name=sch.subject.name if sch.subject else "Unknown",
            teacher_name=f"{sch.teacher.last_name} {sch.teacher.first_name}" if sch.teacher else "Unknown",
            start_time=sch.time_slot.start_time if sch.time_slot else None,
            end_time=sch.time_slot.end_time if sch.time_slot else None
        )
        days_map[sch.day_of_week].append(resp)
    
    # Sort lessons by start time for each day
    for day in days_map:
        days_map[day].sort(key=lambda x: x.start_time or x.time_slot_id)
        
    daily_schedules = [
        DailySchedule(day=day, lessons=lessons) 
        for day, lessons in days_map.items() 
        if lessons # Only include days with lessons? Or All days? Let's include all.
    ]
    
    # Ensure standard order of days
    day_order = {d: i for i, d in enumerate(DayOfWeek)}
    daily_schedules.sort(key=lambda x: day_order[x.day])
    
    return WeeklyTimetableResponse(class_id=class_id, schedule=daily_schedules)
