"""
Anti-cheating event logging models.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.exam import ExamAttempt


class CheatingEventType(str, enum.Enum):
    """Types of cheating events that can be detected."""
    APP_EXIT = "app_exit"
    SCREEN_LOCK = "screen_lock"
    DEVICE_CHANGE = "device_change"
    TIME_ANOMALY = "time_anomaly"
    DUPLICATE_ANSWER_PATTERN = "duplicate_answer_pattern"
    NETWORK_DISCONNECT = "network_disconnect"
    SCREENSHOT_ATTEMPT = "screenshot_attempt"
    SCREEN_SHARE = "screen_share"
    COPY_PASTE = "copy_paste"
    FOCUS_LOST = "focus_lost"
    BROWSER_TAB_SWITCH = "browser_tab_switch"
    SUSPICIOUS_TIMING = "suspicious_timing"
    MULTIPLE_SESSIONS = "multiple_sessions"


class CheatingEvent(Base):
    """
    Immutable cheating event log.
    These records cannot be modified or deleted once created.
    """
    __tablename__ = "cheating_events"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("exam_attempts.id"), index=True)
    
    # Event details
    event_type: Mapped[CheatingEventType] = mapped_column(Enum(CheatingEventType))
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Technical details
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Additional metadata (JSON)
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamp (this is the immutable record time)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Offline sync
    offline_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="cheating_events")
