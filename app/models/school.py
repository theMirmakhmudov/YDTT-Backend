"""
School, Class, and Subject models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lesson import Lesson


class School(Base):
    """School entity model."""
    __tablename__ = "schools"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # Official school code
    
    # Location
    region: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Management
    director_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Student capacity
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="school")
    classes: Mapped[List["Class"]] = relationship("Class", back_populates="school")


class Class(Base):
    """Class within a school."""
    __tablename__ = "classes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))  # e.g., "9-A", "10-B"
    grade: Mapped[int] = mapped_column(Integer)  # 1-11
    
    # School association
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    
    # Academic year
    academic_year: Mapped[str] = mapped_column(String(20))  # e.g., "2024-2025"
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="classes")
    students: Mapped[List["User"]] = relationship("User", back_populates="class_")
    subjects: Mapped[List["ClassSubject"]] = relationship("ClassSubject", back_populates="class_")


class Subject(Base):
    """Academic subject."""
    __tablename__ = "subjects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    classes: Mapped[List["ClassSubject"]] = relationship("ClassSubject", back_populates="subject")
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="subject")


class ClassSubject(Base):
    """Association between classes and subjects with teacher assignment."""
    __tablename__ = "class_subjects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    class_: Mapped["Class"] = relationship("Class", back_populates="subjects")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="classes")
