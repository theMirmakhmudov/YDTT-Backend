"""
Pydantic schemas for Session Attendance.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionAttendanceResponse(BaseModel):
    """Response schema for session attendance record."""
    id: int
    session_id: int
    student_id: int
    joined_at: datetime
    left_at: Optional[datetime] = None
    
    # Computed fields
    student_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_late: bool = False
    
    class Config:
        from_attributes = True


class AttendanceStatsResponse(BaseModel):
    """Aggregated attendance statistics for a session."""
    session_id: int
    total_students: int
    present_count: int
    late_count: int
    attendance_rate: float  # Percentage
    average_join_time: Optional[datetime] = None
