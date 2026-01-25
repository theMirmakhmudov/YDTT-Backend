"""
User and Role models.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import School, Class
    from app.models.exam import ExamAttempt
    from app.models.notification import Notification


class UserRole(str, enum.Enum):
    """User role enumeration."""
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    REGION_ADMIN = "REGION_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
    TECH_ADMIN = "TECH_ADMIN"


class User(Base):
    """User model for all system users."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    
    # Profile
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Role and permissions
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT)
    
    # School association
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id"), nullable=True)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classes.id"), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # Soft delete
    
    # Profile customization
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "male", "female", "other"
    
    # Contact & Address
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Uzbekistan")
    
    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(5), default="uz")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    school: Mapped[Optional["School"]] = relationship("School", back_populates="users")
    class_: Mapped[Optional["Class"]] = relationship("Class", back_populates="students")
    exam_attempts: Mapped[List["ExamAttempt"]] = relationship("ExamAttempt", back_populates="student")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")
    
    @property
    def full_name(self) -> str:
        """Get full name of user."""
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)


class RefreshToken(Base):
    """Stored refresh tokens for token invalidation."""
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
