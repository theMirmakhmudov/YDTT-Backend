"""
Audit log model for tracking all system actions.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    
    # User management
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_RESTORE = "USER_RESTORE"
    ROLE_CHANGE = "ROLE_CHANGE"
    
    # School management
    SCHOOL_CREATE = "SCHOOL_CREATE"
    SCHOOL_UPDATE = "SCHOOL_UPDATE"
    CLASS_CREATE = "CLASS_CREATE"
    CLASS_UPDATE = "CLASS_UPDATE"
    
    # Content management
    LESSON_CREATE = "LESSON_CREATE"
    LESSON_UPDATE = "LESSON_UPDATE"
    LESSON_PUBLISH = "LESSON_PUBLISH"
    MATERIAL_UPLOAD = "MATERIAL_UPLOAD"
    MATERIAL_DELETE = "MATERIAL_DELETE"
    
    # Exam lifecycle
    EXAM_CREATE = "EXAM_CREATE"
    EXAM_UPDATE = "EXAM_UPDATE"
    EXAM_PUBLISH = "EXAM_PUBLISH"
    EXAM_START = "EXAM_START"
    EXAM_SUBMIT = "EXAM_SUBMIT"
    EXAM_EVALUATE = "EXAM_EVALUATE"
    QUESTION_CREATE = "QUESTION_CREATE"
    QUESTION_UPDATE = "QUESTION_UPDATE"
    
    # Grade changes
    GRADE_OVERRIDE = "GRADE_OVERRIDE"
    RESULT_RECOMPUTE = "RESULT_RECOMPUTE"
    
    # Administrative
    SYSTEM_CONFIG_CHANGE = "SYSTEM_CONFIG_CHANGE"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_IMPORT = "DATA_IMPORT"


class AuditLog(Base):
    """
    Immutable audit log for tracking all system actions.
    This table is append-only - records cannot be modified or deleted.
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Actor
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Action
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), index=True)
    
    # Target resource
    resource_type: Mapped[str] = mapped_column(String(50), index=True)
    resource_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Change tracking (JSON)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Timestamp (immutable)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Index for common queries
    __table_args__ = (
        Index("ix_audit_logs_user_action", "user_id", "action"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_date_range", "created_at", "action"),
    )
