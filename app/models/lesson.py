"""
Lesson and Material models for learning content.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Enum, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import Subject
    from app.models.exam import Exam


class MaterialType(str, enum.Enum):
    """Type of learning material."""
    PDF = "PDF"
    VIDEO = "VIDEO"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


class Lesson(Base):
    """Learning lesson/unit."""
    __tablename__ = "lessons"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Rich text content
    
    # Subject and order
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)  # Lesson order within subject
    
    # Grade level
    grade: Mapped[int] = mapped_column(Integer)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Created by
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="lessons")
    materials: Mapped[List["Material"]] = relationship("Material", back_populates="lesson")
    exams: Mapped[List["Exam"]] = relationship("Exam", back_populates="lesson")


class Material(Base):
    """Learning material (PDF, video, etc.)."""
    __tablename__ = "materials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # File information
    file_path: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(BigInteger)  # Size in bytes
    mime_type: Mapped[str] = mapped_column(String(100))
    material_type: Mapped[MaterialType] = mapped_column(Enum(MaterialType))
    
    # Integrity
    checksum: Mapped[str] = mapped_column(String(64))  # SHA-256 hash for offline verification
    
    # Lesson association
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Download tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Created by
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="materials")
