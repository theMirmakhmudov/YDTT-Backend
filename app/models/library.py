"""
Library Book model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import Subject
    from app.models.user import User


class LibraryBook(Base):
    """Digital library book."""
    __tablename__ = "library_books"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Classification
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    grade: Mapped[int] = mapped_column(Integer)  # 1-11
    
    # File Info
    file_path: Mapped[str] = mapped_column(String(500))  # MinIO path
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    
    # Metadata
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Created by
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Relationships
    subject: Mapped["Subject"] = relationship("Subject")
    created_by: Mapped["User"] = relationship("User")
