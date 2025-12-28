"""
Notification model for push notifications and alerts.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    SYSTEM = "SYSTEM"
    EXAM_REMINDER = "EXAM_REMINDER"
    EXAM_RESULT = "EXAM_RESULT"
    GRADE_UPDATE = "GRADE_UPDATE"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    MESSAGE = "MESSAGE"
    ALERT = "ALERT"


class NotificationPriority(str, enum.Enum):
    """Priority levels for notifications."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Notification(Base):
    """Notification for users."""
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Recipient
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority), 
        default=NotificationPriority.NORMAL
    )
    
    # Action (optional deep link or action data)
    action_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_push_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    push_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
