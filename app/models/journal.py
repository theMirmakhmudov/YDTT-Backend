"""
Attendance and Grade models for the Digital Journal system.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Date, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.school import Class, Subject


class AttendanceStatus(str, PyEnum):
    """Student attendance status."""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class GradeType(str, PyEnum):
    """Type of grade/assessment."""
    CLASSWORK = "CLASSWORK"
    HOMEWORK = "HOMEWORK" 
    CONTROL_WORK = "CONTROL_WORK"
    EXAM = "EXAM"
    PROJECT = "PROJECT"


class Attendance(Base):
    """Daily attendance record for a student."""
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    
    # Foreign Keys
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    marker_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Teacher who marked it

    # Data
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    class_: Mapped["Class"] = relationship("Class")
    marker: Mapped["User"] = relationship("User", foreign_keys=[marker_id])


class Grade(Base):
    """Academic grade for a student."""
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    
    # Foreign Keys
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id")) # Teacher who graded

    # Data
    grade_type: Mapped[GradeType] = mapped_column(Enum(GradeType), default=GradeType.CLASSWORK)
    score: Mapped[int] = mapped_column(Integer) # e.g. 5, 4, 3, 2 OR 100, 90...
    max_score: Mapped[int] = mapped_column(Integer, default=5) # e.g. 5 or 100
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    subject: Mapped["Subject"] = relationship("Subject")
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])
