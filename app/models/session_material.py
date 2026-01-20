"""
Database models for Session-Material associations.
Auto-links learning materials to live sessions based on subject.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import Integer, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lesson_session import LessonSession
    from app.models.lesson import Material
    from app.models.user import User


class SessionMaterial(Base):
    """
    Links materials to live sessions.
    Tracks which materials are available during a session.
    """
    __tablename__ = "session_materials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    session_id: Mapped[int] = mapped_column(ForeignKey("lesson_sessions.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    
    # Auto-linked or manually added by teacher
    is_auto_linked: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session: Mapped["LessonSession"] = relationship("LessonSession")
    material: Mapped["Material"] = relationship("Material")


class AccessType(str, PyEnum):
    VIEW = "VIEW"
    DOWNLOAD = "DOWNLOAD"


class MaterialAccess(Base):
    """
    Tracks when students access materials during a session.
    Used for engagement analytics.
    """
    __tablename__ = "material_access"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    session_id: Mapped[int] = mapped_column(ForeignKey("lesson_sessions.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Type of access
    access_type: Mapped[AccessType] = mapped_column(Enum(AccessType), default=AccessType.VIEW)
    
    # Timing
    accessed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session: Mapped["LessonSession"] = relationship("LessonSession")
    material: Mapped["Material"] = relationship("Material")
    student: Mapped["User"] = relationship("User")
