"""
Database models for Live Lesson Sessions (Active Classroom).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import Class, Subject
    from app.models.user import User
    from app.models.timetable import Schedule


class LessonSessionStatus(str, PyEnum):
    """Status of a lesson session."""
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class LessonSession(Base):
    """
    An active lesson happening now.
    Teacher starts this based on the timetable schedule.
    """
    __tablename__ = "lesson_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    
    # Status
    status: Mapped[LessonSessionStatus] = mapped_column(Enum(LessonSessionStatus), default=LessonSessionStatus.ACTIVE)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Optional: Topic/Description for this specific session
    topic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    schedule: Mapped["Schedule"] = relationship("Schedule")
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])
    class_: Mapped["Class"] = relationship("Class")
    subject: Mapped["Subject"] = relationship("Subject")
    notes: Mapped[list["StudentNote"]] = relationship("StudentNote", back_populates="lesson_session")


class StudentNote(Base):
    """
    Notes taken by a student during a lesson session.
    Digital notebook replacement.
    """
    __tablename__ = "student_notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    lesson_session_id: Mapped[int] = mapped_column(ForeignKey("lesson_sessions.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text) # The actual notes (markdown/plain text)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # Images, drawings from tablet
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lesson_session: Mapped["LessonSession"] = relationship("LessonSession", back_populates="notes")
    student: Mapped["User"] = relationship("User")
