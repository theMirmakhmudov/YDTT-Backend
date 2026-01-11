"""
Pydantic schemas for Digital Timetable.
"""
from datetime import time
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field

# Re-export Enum
class DayOfWeek(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

# --- TimeSlot Schemas ---

class TimeSlotBase(BaseModel):
    order: int = Field(ge=1, description="Period number (1st, 2nd, etc)")
    start_time: time
    end_time: time

class TimeSlotCreate(TimeSlotBase):
    pass # school_id injected from context

class TimeSlotResponse(TimeSlotBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

# --- Schedule Schemas ---

class ScheduleBase(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: int
    time_slot_id: int
    day_of_week: DayOfWeek
    room_number: Optional[str] = None

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    room_number: Optional[str] = None

class ScheduleResponse(ScheduleBase):
    id: int
    school_id: int
    
    # Include details for display
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
    class Config:
        from_attributes = True

# --- Aggregated View Schemas ---

class DailySchedule(BaseModel):
    day: DayOfWeek
    lessons: List[ScheduleResponse]

class WeeklyTimetableResponse(BaseModel):
    class_id: int
    schedule: List[DailySchedule]
