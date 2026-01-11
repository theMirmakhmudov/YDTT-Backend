"""
Pydantic schemas for Digital Journal (Attendance and Grading).
"""
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field

# Re-export enums for API usage
class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"

class GradeType(str, Enum):
    CLASSWORK = "CLASSWORK"
    HOMEWORK = "HOMEWORK" 
    CONTROL_WORK = "CONTROL_WORK"
    EXAM = "EXAM"
    PROJECT = "PROJECT"


# --- Attendance Schemas ---

class AttendanceBase(BaseModel):
    date: date
    student_id: int
    status: AttendanceStatus = AttendanceStatus.PRESENT
    remarks: Optional[str] = Field(None, max_length=255)

class AttendanceCreate(AttendanceBase):
    class_id: int # Often inferred, but good to have explicit or context-based

class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    remarks: Optional[str] = None

class AttendanceResponse(AttendanceBase):
    id: int
    class_id: int
    marker_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BulkAttendanceItem(BaseModel):
    student_id: int
    status: AttendanceStatus
    remarks: Optional[str] = None

class BulkAttendanceCreate(BaseModel):
    class_id: int
    date: date
    items: List[BulkAttendanceItem]


# --- Grade Schemas ---

class GradeBase(BaseModel):
    date: date
    student_id: int
    subject_id: int
    grade_type: GradeType = GradeType.CLASSWORK
    score: int
    max_score: int = 5
    comment: Optional[str] = None

class GradeCreate(GradeBase):
    pass

class GradeUpdate(BaseModel):
    score: Optional[int] = None
    max_score: Optional[int] = None
    comment: Optional[str] = None
    grade_type: Optional[GradeType] = None

class GradeResponse(GradeBase):
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Aggregated View Schemas ---

class StudentJournalEntry(BaseModel):
    """Aggregated daily info for a student."""
    date: date
    student_id: int
    student_name: str
    attendance: Optional[AttendanceResponse] = None
    grades: List[GradeResponse] = []
