"""
Database models for Digital Assignments (Classwork & Homework).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import Class, Subject
    from app.models.user import User
    from app.models.journal import Grade


class AssignmentType(str, PyEnum):
    """Type of assignment."""
    HOMEWORK = "HOMEWORK"
    CLASSWORK = "CLASSWORK"
    PROJECT = "PROJECT"


class Assignment(Base):
    """
    Task assigned to a class (Homework or Classwork).
    Teachers create this.
    """
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignment_type: Mapped[AssignmentType] = mapped_column(Enum(AssignmentType), default=AssignmentType.HOMEWORK)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # Teacher's file/guide
    
    # Timing
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    class_: Mapped["Class"] = relationship("Class")
    subject: Mapped["Subject"] = relationship("Subject")
    teacher: Mapped["User"] = relationship("User")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="assignment")


class Submission(Base):
    """
    Student's work for an assignment.
    Can be text or a file (tablet capture).
    """
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Content
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Text answer from tablet
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # File/Image from tablet
    
    # Grading linkage (Optional, if graded)
    grade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("grades.id"), nullable=True)
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student: Mapped["User"] = relationship("User")
    grade: Mapped["Grade"] = relationship("Grade")
