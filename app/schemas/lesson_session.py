"""
Pydantic schemas for Live Lesson Sessions.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field


class LessonSessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


# --- LessonSession Schemas ---

class LessonSessionCreate(BaseModel):
    schedule_id: int
    topic: Optional[str] = None

class LessonSessionResponse(BaseModel):
    id: int
    schedule_id: int
    teacher_id: int
    class_id: int
    subject_id: int
    status: LessonSessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    topic: Optional[str] = None
    
    # Extra info for display
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# --- StudentNote Schemas ---

class StudentNoteCreate(BaseModel):
    lesson_session_id: int
    content: str
    attachment_url: Optional[str] = None

class StudentNoteUpdate(BaseModel):
    content: Optional[str] = None
    attachment_url: Optional[str] = None

class StudentNoteResponse(BaseModel):
    id: int
    lesson_session_id: int
    student_id: int
    content: str
    attachment_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    student_name: Optional[str] = None
    
    class Config:
        from_attributes = True
