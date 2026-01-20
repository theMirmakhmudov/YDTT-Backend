"""
Database models for Session-Based Attendance.
Automatic attendance tracking when students join live sessions.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lesson_session import LessonSession
    from app.models.user import User


class SessionAttendance(Base):
    """
    Automatic attendance record created when student joins a live session.
    Replaces manual attendance marking with session-based tracking.
    """
    __tablename__ = "session_attendance"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    session_id: Mapped[int] = mapped_column(ForeignKey("lesson_sessions.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Timing - automatically recorded
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    session: Mapped["LessonSession"] = relationship("LessonSession")
    student: Mapped["User"] = relationship("User")
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate session duration in minutes."""
        if not self.left_at:
            return None
        delta = self.left_at - self.joined_at
        return int(delta.total_seconds() / 60)
    
    @property
    def is_late(self) -> bool:
        """Check if student joined late (after session started)."""
        # Will be implemented based on session start time comparison
        return False
