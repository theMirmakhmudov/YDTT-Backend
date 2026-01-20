"""
Database models for Live Whiteboard functionality.
Teacher-only drawing with student read-only viewing.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lesson_session import LessonSession
    from app.models.user import User


class WhiteboardEventType(str, PyEnum):
    """Type of whiteboard event."""
    DRAW = "DRAW"
    ERASE = "ERASE"
    CLEAR = "CLEAR"


class WhiteboardEvent(Base):
    """
    Whiteboard drawing event for live lessons.
    Teacher creates events, students receive them in real-time.
    Events are persisted for state recovery when students join mid-session.
    """
    __tablename__ = "whiteboard_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    session_id: Mapped[int] = mapped_column(ForeignKey("lesson_sessions.id"), index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Event data
    event_type: Mapped[WhiteboardEventType] = mapped_column(Enum(WhiteboardEventType))
    payload: Mapped[dict] = mapped_column(JSON)  # {x, y, color, size} for DRAW, {x, y} for ERASE, {} for CLEAR
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session: Mapped["LessonSession"] = relationship("LessonSession")
    created_by: Mapped["User"] = relationship("User")
